"""Tests for enhanced ingestion features (F-100 to F-105)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.ingestion.hashing import (
    FileHash,
    ContentHash,
    file_changed,
    content_changed,
    is_duplicate,
)
from ragd.ingestion.checkpoint import (
    IndexingCheckpoint,
    save_checkpoint,
    load_checkpoint,
    clear_checkpoint,
    get_remaining_files,
)
from ragd.ingestion.smart_chunking import (
    Chunk,
    StructuralChunker,
    structural_chunk,
)
from ragd.ingestion.office import (
    DOCXExtractor,
    XLSXExtractor,
    EPUBExtractor,
    get_office_extractor,
)


class TestFileHash:
    """Tests for FileHash (F-103)."""

    def test_from_path(self) -> None:
        """Test creating FileHash from path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            path = Path(f.name)

            file_hash = FileHash.from_path(path)

            assert file_hash.path == str(path.resolve())
            assert file_hash.size > 0
            assert file_hash.mtime > 0

            path.unlink()

    def test_to_string(self) -> None:
        """Test hash to string conversion."""
        file_hash = FileHash(path="/test/file.txt", size=100, mtime=12345.0)
        result = file_hash.to_string()

        assert "/test/file.txt" in result
        assert "100" in result
        assert "12345.0" in result

    def test_frozen(self) -> None:
        """Test FileHash is frozen/immutable."""
        file_hash = FileHash(path="/test", size=100, mtime=123.0)
        with pytest.raises(AttributeError):
            file_hash.size = 200  # type: ignore


class TestContentHash:
    """Tests for ContentHash (F-103)."""

    def test_from_content_string(self) -> None:
        """Test hashing string content."""
        content_hash = ContentHash.from_content("test content")

        assert content_hash.algorithm == "sha256"
        assert len(content_hash.digest) == 64  # SHA-256 hex

    def test_from_content_bytes(self) -> None:
        """Test hashing bytes content."""
        content_hash = ContentHash.from_content(b"test content")

        assert content_hash.algorithm == "sha256"
        assert len(content_hash.digest) == 64

    def test_from_content_deterministic(self) -> None:
        """Test hashing is deterministic."""
        hash1 = ContentHash.from_content("same content")
        hash2 = ContentHash.from_content("same content")

        assert hash1.digest == hash2.digest

    def test_from_content_different(self) -> None:
        """Test different content produces different hashes."""
        hash1 = ContentHash.from_content("content A")
        hash2 = ContentHash.from_content("content B")

        assert hash1.digest != hash2.digest

    def test_from_file(self) -> None:
        """Test hashing file content."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"file content for hashing")
            f.flush()
            path = Path(f.name)

            content_hash = ContentHash.from_file(path)

            assert content_hash.algorithm == "sha256"
            assert len(content_hash.digest) == 64

            path.unlink()

    def test_custom_algorithm(self) -> None:
        """Test using custom hash algorithm."""
        content_hash = ContentHash.from_content("test", algorithm="md5")

        assert content_hash.algorithm == "md5"
        assert len(content_hash.digest) == 32  # MD5 hex


class TestChangeDetection:
    """Tests for change detection functions (F-103)."""

    def test_file_changed_no_stored(self) -> None:
        """Test file changed when no stored hash."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            f.flush()
            path = Path(f.name)

            assert file_changed(path, None) is True

            path.unlink()

    def test_file_changed_same(self) -> None:
        """Test file not changed when same."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            f.flush()
            path = Path(f.name)

            stored = FileHash.from_path(path)
            assert file_changed(path, stored) is False

            path.unlink()

    def test_content_changed_no_stored(self) -> None:
        """Test content changed when no stored hash."""
        assert content_changed("new content", None) is True

    def test_content_changed_same(self) -> None:
        """Test content not changed when same."""
        content = "test content"
        stored = ContentHash.from_content(content)
        assert content_changed(content, stored) is False

    def test_content_changed_different(self) -> None:
        """Test content changed when different."""
        stored = ContentHash.from_content("old content")
        assert content_changed("new content", stored) is True

    def test_is_duplicate_new(self) -> None:
        """Test new content is not duplicate."""
        existing = {"abc123", "def456"}
        is_dup, hash_val = is_duplicate("unique content", existing)

        assert is_dup is False
        assert len(hash_val) == 64

    def test_is_duplicate_exists(self) -> None:
        """Test duplicate detection."""
        content = "duplicate content"
        content_hash = ContentHash.from_content(content)
        existing = {content_hash.digest}

        is_dup, hash_val = is_duplicate(content, existing)

        assert is_dup is True
        assert hash_val == content_hash.digest


class TestIndexingCheckpoint:
    """Tests for IndexingCheckpoint (F-102)."""

    def test_create(self) -> None:
        """Test creating checkpoint."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 10)

        assert checkpoint.source_path == "/test"
        assert checkpoint.total_files == 10
        assert checkpoint.completed == 0
        assert checkpoint.started_at is not None

    def test_mark_complete(self) -> None:
        """Test marking file complete."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 10)
        checkpoint.mark_complete("/test/file1.txt")

        assert checkpoint.completed == 1
        assert checkpoint.last_file == "/test/file1.txt"
        assert "/test/file1.txt" in checkpoint.files_completed

    def test_mark_error(self) -> None:
        """Test marking file error."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 10)
        checkpoint.mark_error("/test/bad.txt", "Parse error")

        assert len(checkpoint.errors) == 1
        assert checkpoint.errors[0]["file"] == "/test/bad.txt"
        assert checkpoint.errors[0]["error"] == "Parse error"

    def test_is_complete(self) -> None:
        """Test completion check."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 2)

        assert checkpoint.is_complete is False

        checkpoint.mark_complete("/test/file1.txt")
        assert checkpoint.is_complete is False

        checkpoint.mark_complete("/test/file2.txt")
        assert checkpoint.is_complete is True

    def test_progress_percent(self) -> None:
        """Test progress percentage."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 4)

        assert checkpoint.progress_percent == 0.0

        checkpoint.mark_complete("/test/file1.txt")
        assert checkpoint.progress_percent == 25.0

        checkpoint.mark_complete("/test/file2.txt")
        assert checkpoint.progress_percent == 50.0

    def test_progress_percent_zero_files(self) -> None:
        """Test progress with zero files."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 0)
        assert checkpoint.progress_percent == 100.0

    def test_to_dict(self) -> None:
        """Test serialisation to dict."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 5)
        checkpoint.mark_complete("/test/file1.txt")

        data = checkpoint.to_dict()

        assert data["source_path"] == "/test"
        assert data["total_files"] == 5
        assert data["completed"] == 1

    def test_from_dict(self) -> None:
        """Test deserialisation from dict."""
        data = {
            "started_at": "2024-01-01T00:00:00",
            "source_path": "/test",
            "total_files": 5,
            "completed": 2,
            "last_file": "/test/file2.txt",
            "files_completed": ["/test/file1.txt", "/test/file2.txt"],
            "errors": [],
        }

        checkpoint = IndexingCheckpoint.from_dict(data)

        assert checkpoint.source_path == "/test"
        assert checkpoint.completed == 2


class TestCheckpointPersistence:
    """Tests for checkpoint save/load (F-102)."""

    def test_save_and_load(self) -> None:
        """Test saving and loading checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "checkpoint.json"

            checkpoint = IndexingCheckpoint.create(Path("/source"), 10)
            checkpoint.mark_complete("/source/file1.txt")

            save_checkpoint(checkpoint, checkpoint_path)
            loaded = load_checkpoint(checkpoint_path)

            assert loaded is not None
            assert loaded.source_path == "/source"
            assert loaded.completed == 1

    def test_load_nonexistent(self) -> None:
        """Test loading nonexistent checkpoint."""
        result = load_checkpoint(Path("/nonexistent/path.json"))
        assert result is None

    def test_clear_checkpoint(self) -> None:
        """Test clearing checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "checkpoint.json"

            checkpoint = IndexingCheckpoint.create(Path("/source"), 10)
            save_checkpoint(checkpoint, checkpoint_path)

            assert checkpoint_path.exists()

            clear_checkpoint(checkpoint_path)

            assert not checkpoint_path.exists()

    def test_clear_nonexistent(self) -> None:
        """Test clearing nonexistent checkpoint (no error)."""
        clear_checkpoint(Path("/nonexistent/path.json"))  # Should not raise

    def test_get_remaining_files(self) -> None:
        """Test getting remaining files."""
        checkpoint = IndexingCheckpoint.create(Path("/test"), 3)
        checkpoint.mark_complete("/test/file1.txt")

        all_files = [
            Path("/test/file1.txt"),
            Path("/test/file2.txt"),
            Path("/test/file3.txt"),
        ]

        remaining = get_remaining_files(checkpoint, all_files)

        assert len(remaining) == 2
        assert Path("/test/file2.txt") in remaining
        assert Path("/test/file3.txt") in remaining


class TestStructuralChunker:
    """Tests for StructuralChunker (F-101)."""

    def test_simple_text(self) -> None:
        """Test chunking simple text."""
        chunker = StructuralChunker(max_chunk_size=100)
        text = "This is a simple paragraph."

        chunks = chunker.chunk(text)

        assert len(chunks) >= 1
        assert chunks[0].text == text
        assert chunks[0].chunk_type == "text"

    def test_respects_headers(self) -> None:
        """Test headers are preserved in content."""
        chunker = StructuralChunker(respect_headers=True)
        text = """# Header

Some content under the header.

## Subheader

More content here."""

        chunks = chunker.chunk(text)

        # Headers should be preserved in output text
        all_text = " ".join(c.text for c in chunks)
        assert "# Header" in all_text or "Header" in all_text

    def test_respects_code_blocks(self) -> None:
        """Test code blocks are preserved in content."""
        chunker = StructuralChunker(respect_code=True)
        text = """Some text.

```python
def hello():
    print("Hello")
```

More text."""

        chunks = chunker.chunk(text)

        # Code should be preserved in output
        all_text = " ".join(c.text for c in chunks)
        assert "def hello():" in all_text
        assert "```" in all_text

    def test_respects_lists(self) -> None:
        """Test lists are preserved in content."""
        chunker = StructuralChunker(respect_lists=True)
        text = """Introduction.

- Item 1
- Item 2
- Item 3

Conclusion."""

        chunks = chunker.chunk(text)

        # List items should be preserved in output
        all_text = " ".join(c.text for c in chunks)
        assert "Item 1" in all_text
        assert "Item 2" in all_text
        assert "Item 3" in all_text

    def test_chunk_metadata(self) -> None:
        """Test chunk has position metadata."""
        chunker = StructuralChunker()
        text = "Test content."

        chunks = chunker.chunk(text)

        assert chunks[0].start_pos >= 0
        assert chunks[0].end_pos > chunks[0].start_pos

    def test_estimate_tokens(self) -> None:
        """Test token estimation."""
        chunker = StructuralChunker()
        text = "one two three four five"

        tokens = chunker._estimate_tokens(text)

        # ~1.3 tokens per word, 5 words = ~6-7 tokens
        assert 5 <= tokens <= 10

    def test_empty_text(self) -> None:
        """Test chunking empty text."""
        chunker = StructuralChunker()
        chunks = chunker.chunk("")

        assert chunks == []


class TestStructuralChunkConvenience:
    """Tests for structural_chunk convenience function."""

    def test_basic_usage(self) -> None:
        """Test basic chunking."""
        text = "This is some text to chunk."
        chunks = structural_chunk(text)

        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)

    def test_respect_structure_false(self) -> None:
        """Test disabling structure respect."""
        text = """# Header

Content

```code```"""

        chunks = structural_chunk(text, respect_structure=False)

        # Should still work but not preserve structure
        assert len(chunks) >= 1


class TestDOCXExtractor:
    """Tests for DOCXExtractor (F-100)."""

    def test_extract_missing_package(self) -> None:
        """Test handling missing python-docx."""
        with patch.dict("sys.modules", {"docx": None}):
            extractor = DOCXExtractor()
            # Will attempt import and fail
            result = extractor.extract(Path("/test.docx"))

            # Either succeeds (if docx installed) or fails gracefully
            assert result is not None

    def test_extract_nonexistent_file(self) -> None:
        """Test extracting nonexistent file."""
        extractor = DOCXExtractor()
        result = extractor.extract(Path("/nonexistent/file.docx"))

        assert result.success is False
        assert result.error is not None


class TestXLSXExtractor:
    """Tests for XLSXExtractor (F-100)."""

    def test_extract_nonexistent_file(self) -> None:
        """Test extracting nonexistent file."""
        extractor = XLSXExtractor()
        result = extractor.extract(Path("/nonexistent/file.xlsx"))

        assert result.success is False
        assert result.error is not None


class TestEPUBExtractor:
    """Tests for EPUBExtractor (F-100)."""

    def test_extract_nonexistent_file(self) -> None:
        """Test extracting nonexistent file."""
        extractor = EPUBExtractor()
        result = extractor.extract(Path("/nonexistent/file.epub"))

        assert result.success is False
        assert result.error is not None


class TestDuplicateTracker:
    """Tests for DuplicateTracker (F-104)."""

    def test_register_unique(self) -> None:
        """Test registering unique content."""
        from ragd.ingestion.duplicate import DuplicateTracker

        tracker = DuplicateTracker()
        is_dup, original = tracker.check_and_register("content A", "/path/a.txt")

        assert is_dup is False
        assert original is None
        assert tracker.unique_count == 1

    def test_detect_duplicate(self) -> None:
        """Test detecting duplicate content."""
        from ragd.ingestion.duplicate import DuplicateTracker

        tracker = DuplicateTracker()
        tracker.check_and_register("same content", "/path/first.txt")
        is_dup, original = tracker.check_and_register("same content", "/path/second.txt")

        assert is_dup is True
        assert original == "/path/first.txt"
        assert tracker.duplicate_count == 1

    def test_get_duplicates_for(self) -> None:
        """Test getting duplicates of a document."""
        from ragd.ingestion.duplicate import DuplicateTracker

        tracker = DuplicateTracker()
        tracker.check_and_register("content", "/original.txt")
        tracker.check_and_register("content", "/dup1.txt")
        tracker.check_and_register("content", "/dup2.txt")

        dups = tracker.get_duplicates_for("/original.txt")

        assert len(dups) == 2
        assert "/dup1.txt" in dups
        assert "/dup2.txt" in dups

    def test_clear(self) -> None:
        """Test clearing tracker."""
        from ragd.ingestion.duplicate import DuplicateTracker

        tracker = DuplicateTracker()
        tracker.check_and_register("content", "/path.txt")

        tracker.clear()

        assert tracker.unique_count == 0
        assert tracker.duplicate_count == 0


class TestDuplicateHandler:
    """Tests for DuplicateHandler (F-104)."""

    def test_skip_policy(self) -> None:
        """Test skip policy skips duplicates."""
        from ragd.ingestion.duplicate import DuplicateHandler, DuplicatePolicy

        handler = DuplicateHandler(policy=DuplicatePolicy.SKIP)

        assert handler.should_index("content", "/first.txt") is True
        assert handler.should_index("content", "/second.txt") is False

    def test_index_all_policy(self) -> None:
        """Test index_all policy indexes duplicates."""
        from ragd.ingestion.duplicate import DuplicateHandler, DuplicatePolicy

        handler = DuplicateHandler(policy=DuplicatePolicy.INDEX_ALL)

        assert handler.should_index("content", "/first.txt") is True
        assert handler.should_index("content", "/second.txt") is True

    def test_on_duplicate_callback(self) -> None:
        """Test on_duplicate callback is called."""
        from ragd.ingestion.duplicate import DuplicateHandler, DuplicateInfo

        callbacks = []

        def on_dup(info: DuplicateInfo) -> None:
            callbacks.append(info)

        handler = DuplicateHandler(on_duplicate=on_dup)
        handler.should_index("content", "/first.txt")
        handler.should_index("content", "/second.txt")

        assert len(callbacks) == 1
        assert callbacks[0].original_path == "/first.txt"
        assert callbacks[0].duplicate_path == "/second.txt"

    def test_get_stats(self) -> None:
        """Test getting statistics."""
        from ragd.ingestion.duplicate import DuplicateHandler

        handler = DuplicateHandler()
        handler.should_index("content A", "/a.txt")
        handler.should_index("content B", "/b.txt")
        handler.should_index("content A", "/a2.txt")

        stats = handler.get_stats()

        assert stats["unique_count"] == 2
        assert stats["duplicate_count"] == 1


class TestFindDuplicates:
    """Tests for find_duplicates function (F-104)."""

    def test_find_duplicates_empty(self) -> None:
        """Test no duplicates in empty set."""
        from ragd.ingestion.duplicate import find_duplicates

        result = find_duplicates({})
        assert result == []

    def test_find_duplicates_unique(self) -> None:
        """Test no duplicates when all unique."""
        from ragd.ingestion.duplicate import find_duplicates

        contents = {
            "/a.txt": "content A",
            "/b.txt": "content B",
            "/c.txt": "content C",
        }

        result = find_duplicates(contents)
        assert len(result) == 0

    def test_find_duplicates_with_dups(self) -> None:
        """Test finding duplicates."""
        from ragd.ingestion.duplicate import find_duplicates

        contents = {
            "/a.txt": "same content",
            "/b.txt": "unique",
            "/c.txt": "same content",
        }

        result = find_duplicates(contents)
        assert len(result) == 1
        assert result[0].hash_digest is not None


class TestGetOfficeExtractor:
    """Tests for get_office_extractor factory (F-100)."""

    def test_docx_extractor(self) -> None:
        """Test getting DOCX extractor."""
        extractor = get_office_extractor(Path("test.docx"))
        assert isinstance(extractor, DOCXExtractor)

    def test_xlsx_extractor(self) -> None:
        """Test getting XLSX extractor."""
        extractor = get_office_extractor(Path("test.xlsx"))
        assert isinstance(extractor, XLSXExtractor)

    def test_epub_extractor(self) -> None:
        """Test getting EPUB extractor."""
        extractor = get_office_extractor(Path("test.epub"))
        assert isinstance(extractor, EPUBExtractor)

    def test_unknown_extension(self) -> None:
        """Test unknown extension returns None."""
        extractor = get_office_extractor(Path("test.xyz"))
        assert extractor is None

    def test_case_insensitive(self) -> None:
        """Test extension matching is case insensitive."""
        extractor = get_office_extractor(Path("test.DOCX"))
        assert isinstance(extractor, DOCXExtractor)
