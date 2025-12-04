"""Tests for error logging and recovery (F-111)."""

from pathlib import Path

import pytest

from ragd.operations.errors import (
    IndexingErrorCategory,
    DocumentResult,
    BatchResult,
    REMEDIATION_HINTS,
    categorise_error,
)


class TestIndexingErrorCategory:
    """Tests for IndexingErrorCategory enum."""

    def test_all_categories_have_hints(self):
        """Every category should have a remediation hint."""
        for category in IndexingErrorCategory:
            assert category in REMEDIATION_HINTS
            assert len(REMEDIATION_HINTS[category]) > 0

    def test_file_system_categories(self):
        """File system categories exist."""
        assert IndexingErrorCategory.FILE_NOT_FOUND
        assert IndexingErrorCategory.PERMISSION_DENIED
        assert IndexingErrorCategory.SIZE_EXCEEDED

    def test_content_categories(self):
        """Content error categories exist."""
        assert IndexingErrorCategory.UNSUPPORTED_FORMAT
        assert IndexingErrorCategory.EXTRACTION_FAILED
        assert IndexingErrorCategory.ENCODING_ERROR
        assert IndexingErrorCategory.CORRUPT_FILE
        assert IndexingErrorCategory.EMPTY_FILE

    def test_pdf_categories(self):
        """PDF-specific categories exist."""
        assert IndexingErrorCategory.IMAGE_ONLY
        assert IndexingErrorCategory.ENCRYPTED
        assert IndexingErrorCategory.MALFORMED

    def test_html_categories(self):
        """HTML-specific categories exist."""
        assert IndexingErrorCategory.JS_CONTENT

    def test_system_categories(self):
        """System error categories exist."""
        assert IndexingErrorCategory.DEPENDENCY_MISSING
        assert IndexingErrorCategory.TIMEOUT
        assert IndexingErrorCategory.MEMORY_ERROR


class TestDocumentResult:
    """Tests for DocumentResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        path = Path("/test/doc.pdf")
        result = DocumentResult.success(path, chunks=10, images=2, duration_ms=500)

        assert result.path == path
        assert result.status == "success"
        assert result.chunks_created == 10
        assert result.images_extracted == 2
        assert result.duration_ms == 500
        assert result.category is None
        assert result.hint is None

    def test_failed_result(self):
        """Test creating a failed result."""
        path = Path("/test/doc.pdf")
        result = DocumentResult.failed(
            path,
            IndexingErrorCategory.ENCRYPTED,
            "PDF is password-protected",
            duration_ms=100,
        )

        assert result.path == path
        assert result.status == "failed"
        assert result.category == IndexingErrorCategory.ENCRYPTED
        assert result.message == "PDF is password-protected"
        assert result.duration_ms == 100
        assert result.hint is not None
        assert "password" in result.hint.lower()

    def test_skipped_result(self):
        """Test creating a skipped result."""
        path = Path("/test/doc.pdf")
        result = DocumentResult.skipped(path, reason="duplicate", duration_ms=5)

        assert result.path == path
        assert result.status == "skipped"
        assert result.message == "duplicate"
        assert result.duration_ms == 5

    def test_hint_property(self):
        """Test hint property returns correct hint for category."""
        path = Path("/test/doc.pdf")

        # Test with category
        result = DocumentResult.failed(
            path, IndexingErrorCategory.FILE_NOT_FOUND, "File not found"
        )
        assert result.hint == REMEDIATION_HINTS[IndexingErrorCategory.FILE_NOT_FOUND]

        # Test without category
        result = DocumentResult.success(path)
        assert result.hint is None


class TestBatchResult:
    """Tests for BatchResult aggregation."""

    def test_empty_batch(self):
        """Test empty batch has correct defaults."""
        batch = BatchResult()

        assert batch.total == 0
        assert batch.succeeded == 0
        assert batch.failed == 0
        assert batch.skipped == 0
        assert batch.total_chunks == 0

    def test_add_results(self):
        """Test adding results to batch."""
        batch = BatchResult()

        batch.add(DocumentResult.success(Path("/a.pdf"), chunks=5))
        batch.add(DocumentResult.success(Path("/b.pdf"), chunks=3))
        batch.add(DocumentResult.failed(
            Path("/c.pdf"), IndexingErrorCategory.CORRUPT_FILE, "Bad file"
        ))
        batch.add(DocumentResult.skipped(Path("/d.pdf")))

        assert batch.total == 4
        assert batch.succeeded == 2
        assert batch.failed == 1
        assert batch.skipped == 1
        assert batch.total_chunks == 8

    def test_failures_by_category(self):
        """Test counting failures by category."""
        batch = BatchResult()

        batch.add(DocumentResult.failed(
            Path("/a.pdf"), IndexingErrorCategory.ENCRYPTED, "Password"
        ))
        batch.add(DocumentResult.failed(
            Path("/b.pdf"), IndexingErrorCategory.ENCRYPTED, "Password"
        ))
        batch.add(DocumentResult.failed(
            Path("/c.pdf"), IndexingErrorCategory.CORRUPT_FILE, "Bad"
        ))
        batch.add(DocumentResult.success(Path("/d.pdf")))

        counts = batch.failures_by_category
        assert counts[IndexingErrorCategory.ENCRYPTED] == 2
        assert counts[IndexingErrorCategory.CORRUPT_FILE] == 1
        assert len(counts) == 2

    def test_get_failed(self):
        """Test getting failed results."""
        batch = BatchResult()

        batch.add(DocumentResult.success(Path("/a.pdf")))
        batch.add(DocumentResult.failed(
            Path("/b.pdf"), IndexingErrorCategory.ENCRYPTED, "Password"
        ))
        batch.add(DocumentResult.skipped(Path("/c.pdf")))

        failed = batch.get_failed()
        assert len(failed) == 1
        assert failed[0].path == Path("/b.pdf")

    def test_get_by_category(self):
        """Test filtering by category."""
        batch = BatchResult()

        batch.add(DocumentResult.failed(
            Path("/a.pdf"), IndexingErrorCategory.ENCRYPTED, "Password"
        ))
        batch.add(DocumentResult.failed(
            Path("/b.pdf"), IndexingErrorCategory.CORRUPT_FILE, "Bad"
        ))
        batch.add(DocumentResult.failed(
            Path("/c.pdf"), IndexingErrorCategory.ENCRYPTED, "Password"
        ))

        encrypted = batch.get_by_category(IndexingErrorCategory.ENCRYPTED)
        assert len(encrypted) == 2

    def test_duration(self):
        """Test duration calculation."""
        batch = BatchResult()
        batch.add(DocumentResult.success(Path("/a.pdf")))
        batch.complete()

        assert batch.duration_seconds >= 0
        assert batch.end_time is not None

    def test_total_images(self):
        """Test total images calculation."""
        batch = BatchResult()

        batch.add(DocumentResult.success(Path("/a.pdf"), chunks=5, images=3))
        batch.add(DocumentResult.success(Path("/b.pdf"), chunks=3, images=2))

        assert batch.total_images == 5


class TestCategoriseError:
    """Tests for error categorisation."""

    def test_file_not_found(self):
        """FileNotFoundError should be categorised correctly."""
        error = FileNotFoundError("No such file")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.FILE_NOT_FOUND
        assert "file" in msg.lower()

    def test_permission_denied(self):
        """PermissionError should be categorised correctly."""
        error = PermissionError("Access denied")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.PERMISSION_DENIED

    def test_memory_error(self):
        """MemoryError should be categorised correctly."""
        error = MemoryError("Out of memory")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.MEMORY_ERROR

    def test_unicode_error(self):
        """Unicode errors should be categorised as encoding errors."""
        error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.ENCODING_ERROR

    def test_import_error(self):
        """ImportError should be categorised as dependency missing."""
        error = ImportError("No module named 'paddleocr'")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.DEPENDENCY_MISSING

    def test_timeout_in_message(self):
        """Timeout in error message should be categorised."""
        error = Exception("Operation timed out after 30 seconds")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.TIMEOUT

    def test_encrypted_in_message(self):
        """Encrypted in error message should be categorised."""
        error = Exception("PDF is encrypted")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.ENCRYPTED

    def test_corrupt_in_message(self):
        """Corrupt in error message should be categorised."""
        error = Exception("File is corrupted")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.CORRUPT_FILE

    def test_unknown_error(self):
        """Unknown errors should be categorised as unknown."""
        error = ValueError("Some random error")
        category, msg = categorise_error(error)

        assert category == IndexingErrorCategory.UNKNOWN
        assert "ValueError" in msg


class TestRemediationHints:
    """Tests for remediation hints quality."""

    def test_hints_are_actionable(self):
        """Hints should contain actionable suggestions."""
        action_words = ["try", "check", "run", "use", "install", "convert", "verify"]

        for category, hint in REMEDIATION_HINTS.items():
            has_action = any(word in hint.lower() for word in action_words)
            assert has_action, f"Hint for {category.name} should be actionable"

    def test_hints_not_too_long(self):
        """Hints should be reasonably concise."""
        for category, hint in REMEDIATION_HINTS.items():
            # Allow up to 300 chars (2-3 sentences)
            assert len(hint) <= 300, f"Hint for {category.name} is too long"

    def test_hints_not_empty(self):
        """No hint should be empty."""
        for category, hint in REMEDIATION_HINTS.items():
            assert hint.strip(), f"Hint for {category.name} is empty"
