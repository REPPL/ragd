"""Tests for web archive and folder watching modules."""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from ragd.web import (
    DEFAULT_DEBOUNCE_SECONDS,
    DEFAULT_EXCLUDES,
    DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_PATTERNS,
    ExtractedWebContent,
    WatchConfig,
    WatchEvent,
    WatchStatus,
    WebArchiveMetadata,
    WebArchiveProcessor,
    extract_singlefile_metadata,
    extract_web_content,
    generate_reader_view,
    is_singlefile_archive,
    should_index,
    WATCHDOG_AVAILABLE,
)


class TestWebArchiveDetection:
    """Tests for SingleFile archive detection."""

    def test_detect_singlefile_url_meta(self) -> None:
        """Test detection via savepage-url meta tag."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <meta name="savepage-url" content="https://example.com/article">
            <title>Test Article</title>
        </head>
        <body>Content</body>
        </html>'''

        assert is_singlefile_archive(html) is True

    def test_detect_singlefile_date_meta(self) -> None:
        """Test detection via savepage-date meta tag."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <meta name="savepage-date" content="2024-01-15T10:30:00Z">
            <title>Test Article</title>
        </head>
        <body>Content</body>
        </html>'''

        assert is_singlefile_archive(html) is True

    def test_detect_singlefile_keyword(self) -> None:
        """Test detection via singlefile keyword."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <!-- Saved by SingleFile -->
            <title>Test Article</title>
        </head>
        <body>Content</body>
        </html>'''

        assert is_singlefile_archive(html) is True

    def test_detect_regular_html(self) -> None:
        """Test regular HTML is not detected as SingleFile."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <title>Regular Page</title>
        </head>
        <body>Content</body>
        </html>'''

        assert is_singlefile_archive(html) is False


class TestWebArchiveMetadata:
    """Tests for metadata extraction."""

    def test_metadata_dataclass(self) -> None:
        """Test WebArchiveMetadata dataclass."""
        metadata = WebArchiveMetadata(
            source_file=Path("/test/article.html"),
            original_url="https://example.com/article",
            archive_date=datetime(2024, 1, 15, 10, 30),
            title="Test Article",
            author="John Doe",
            word_count=500,
        )

        assert metadata.source_file == Path("/test/article.html")
        assert metadata.original_url == "https://example.com/article"
        assert metadata.title == "Test Article"
        assert metadata.author == "John Doe"

    def test_metadata_to_dict(self) -> None:
        """Test metadata serialisation."""
        metadata = WebArchiveMetadata(
            source_file=Path("/test/article.html"),
            title="Test",
            archive_date=datetime(2024, 1, 15),
        )

        data = metadata.to_dict()
        assert data["source_file"] == "/test/article.html"
        assert data["title"] == "Test"
        assert "2024-01-15" in data["archive_date"]

    def test_extract_singlefile_metadata(self, tmp_path: Path) -> None:
        """Test extracting metadata from SingleFile HTML."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <meta name="savepage-url" content="https://example.com/article">
            <meta name="savepage-date" content="2024-01-15T10:30:00Z">
            <meta name="author" content="Jane Smith">
            <title>Test Article Title</title>
        </head>
        <body>Content</body>
        </html>'''

        test_file = tmp_path / "test.html"
        metadata = extract_singlefile_metadata(html, test_file)

        assert metadata.original_url == "https://example.com/article"
        assert metadata.title == "Test Article Title"
        assert metadata.author == "Jane Smith"
        assert metadata.archive_date is not None
        assert metadata.archive_date.year == 2024


class TestWebContentExtraction:
    """Tests for content extraction."""

    def test_extract_simple_content(self, tmp_path: Path) -> None:
        """Test extracting content from simple HTML."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <meta name="savepage-url" content="https://example.com">
            <title>Test Page</title>
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is the main content of the article.</p>
            <p>It has multiple paragraphs with useful information.</p>
        </body>
        </html>'''

        test_file = tmp_path / "test.html"
        result = extract_web_content(html, test_file)

        assert result.success is True
        assert "Main Title" in result.text or "main content" in result.text.lower()
        assert result.metadata is not None
        assert result.metadata.original_url == "https://example.com"

    def test_extract_filters_scripts(self, tmp_path: Path) -> None:
        """Test that scripts are filtered from extracted content."""
        html = '''<!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <p>Real content here.</p>
            <script>var secret = "hidden";</script>
            <p>More content.</p>
        </body>
        </html>'''

        test_file = tmp_path / "test.html"
        result = extract_web_content(html, test_file)

        assert result.success is True
        assert "secret" not in result.text.lower()
        assert "hidden" not in result.text.lower()

    def test_extract_handles_empty_html(self, tmp_path: Path) -> None:
        """Test handling of empty HTML."""
        result = extract_web_content("", tmp_path / "empty.html")

        assert result.success is True
        assert result.text == ""


class TestReaderViewGeneration:
    """Tests for reader view generation."""

    def test_generate_reader_view(self) -> None:
        """Test generating reader view HTML."""
        metadata = WebArchiveMetadata(
            source_file=Path("/test/article.html"),
            original_url="https://example.com/article",
            archive_date=datetime(2024, 1, 15),
            title="Test Article",
            author="John Doe",
            language="en",
        )

        html = generate_reader_view("doc-001", metadata, "Article content here.")

        assert "Test Article" in html
        assert "John Doe" in html
        assert "https://example.com/article" in html
        assert "ragd-document-id" in html
        assert "doc-001" in html

    def test_generate_reader_view_no_author(self) -> None:
        """Test reader view without author."""
        metadata = WebArchiveMetadata(
            source_file=Path("/test/article.html"),
            title="Test Article",
        )

        html = generate_reader_view("doc-001", metadata, "Content")

        assert "Test Article" in html
        assert "By" not in html

    def test_generate_reader_view_escapes_html(self) -> None:
        """Test that content is properly escaped."""
        metadata = WebArchiveMetadata(
            source_file=Path("/test/article.html"),
            title="Test <script>",
        )

        html = generate_reader_view("doc-001", metadata, "<script>alert('xss')</script>")

        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestWebArchiveProcessor:
    """Tests for WebArchiveProcessor class."""

    @pytest.fixture
    def processor(self, tmp_path: Path) -> WebArchiveProcessor:
        """Create a processor with temp reader view directory."""
        return WebArchiveProcessor(reader_view_dir=tmp_path / "reader_views")

    @pytest.fixture
    def sample_archive(self, tmp_path: Path) -> Path:
        """Create a sample SingleFile archive."""
        html = '''<!DOCTYPE html>
        <html>
        <head>
            <meta name="savepage-url" content="https://example.com/article">
            <meta name="savepage-date" content="2024-01-15T10:30:00Z">
            <title>Sample Article</title>
        </head>
        <body>
            <h1>Sample Article</h1>
            <p>This is sample content for testing.</p>
        </body>
        </html>'''

        path = tmp_path / "sample.html"
        path.write_text(html)
        return path

    def test_is_web_archive_singlefile(
        self, processor: WebArchiveProcessor, sample_archive: Path
    ) -> None:
        """Test detection of SingleFile archive."""
        assert processor.is_web_archive(sample_archive) is True

    def test_is_web_archive_regular_file(
        self, processor: WebArchiveProcessor, tmp_path: Path
    ) -> None:
        """Test regular HTML is not detected."""
        regular = tmp_path / "regular.html"
        regular.write_text("<html><body>Hello</body></html>")
        assert processor.is_web_archive(regular) is False

    def test_is_web_archive_nonexistent(
        self, processor: WebArchiveProcessor, tmp_path: Path
    ) -> None:
        """Test nonexistent file returns False."""
        assert processor.is_web_archive(tmp_path / "nonexistent.html") is False

    def test_is_web_archive_non_html(
        self, processor: WebArchiveProcessor, tmp_path: Path
    ) -> None:
        """Test non-HTML files return False."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Plain text")
        assert processor.is_web_archive(txt_file) is False

    def test_process_archive(
        self, processor: WebArchiveProcessor, sample_archive: Path
    ) -> None:
        """Test processing a SingleFile archive."""
        result = processor.process(sample_archive)

        assert result.success is True
        assert "Sample Article" in result.text or "sample content" in result.text.lower()
        assert result.metadata is not None
        assert result.metadata.original_url == "https://example.com/article"

    def test_process_nonexistent(
        self, processor: WebArchiveProcessor, tmp_path: Path
    ) -> None:
        """Test processing nonexistent file."""
        result = processor.process(tmp_path / "nonexistent.html")

        assert result.success is False
        assert result.error is not None

    def test_generate_reader_view_file(
        self, processor: WebArchiveProcessor, sample_archive: Path
    ) -> None:
        """Test generating reader view file."""
        result = processor.process(sample_archive)
        view_path = processor.generate_reader_view("doc-001", result)

        assert view_path is not None
        assert view_path.exists()
        content = view_path.read_text()
        assert "Sample Article" in content


class TestWatchConfig:
    """Tests for WatchConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = WatchConfig()

        assert config.patterns == DEFAULT_PATTERNS
        assert config.excludes == DEFAULT_EXCLUDES
        assert config.debounce_seconds == DEFAULT_DEBOUNCE_SECONDS
        assert config.max_file_size_mb == DEFAULT_MAX_FILE_SIZE_MB
        assert config.recursive is True

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = WatchConfig(
            directories=[Path("/test")],
            patterns=["*.md"],
            debounce_seconds=10,
        )

        assert config.directories == [Path("/test")]
        assert config.patterns == ["*.md"]
        assert config.debounce_seconds == 10

    def test_config_to_dict(self) -> None:
        """Test config serialisation."""
        config = WatchConfig(directories=[Path("/test")])
        data = config.to_dict()

        assert data["directories"] == ["/test"]
        assert "patterns" in data
        assert "excludes" in data

    def test_config_from_dict(self) -> None:
        """Test config deserialisation."""
        data = {
            "directories": ["/test1", "/test2"],
            "patterns": ["*.pdf"],
            "debounce_seconds": 15,
        }
        config = WatchConfig.from_dict(data)

        assert config.directories == [Path("/test1"), Path("/test2")]
        assert config.patterns == ["*.pdf"]
        assert config.debounce_seconds == 15


class TestShouldIndex:
    """Tests for should_index function."""

    def test_should_index_matching_pattern(self, tmp_path: Path) -> None:
        """Test file matching pattern."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("content")

        should, reason = should_index(
            str(pdf_file),
            patterns=["*.pdf"],
            excludes=[],
            max_size_bytes=100 * 1024 * 1024,
        )

        assert should is True
        assert reason == ""

    def test_should_not_index_no_match(self, tmp_path: Path) -> None:
        """Test file not matching any pattern."""
        exe_file = tmp_path / "test.exe"
        exe_file.write_text("content")

        should, reason = should_index(
            str(exe_file),
            patterns=["*.pdf", "*.txt"],
            excludes=[],
            max_size_bytes=100 * 1024 * 1024,
        )

        assert should is False
        assert "no matching pattern" in reason

    def test_should_not_index_excluded(self, tmp_path: Path) -> None:
        """Test excluded file."""
        # Create node_modules directory
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        txt_file = nm_dir / "test.txt"
        txt_file.write_text("content")

        should, reason = should_index(
            str(txt_file),
            patterns=["*.txt"],
            excludes=["**/node_modules/**"],
            max_size_bytes=100 * 1024 * 1024,
        )

        assert should is False
        assert "excluded" in reason

    def test_should_not_index_too_large(self, tmp_path: Path) -> None:
        """Test file too large."""
        big_file = tmp_path / "big.txt"
        # Create a file larger than limit
        big_file.write_bytes(b"x" * 1000)

        should, reason = should_index(
            str(big_file),
            patterns=["*.txt"],
            excludes=[],
            max_size_bytes=500,  # 500 bytes limit
        )

        assert should is False
        assert "too large" in reason

    def test_should_not_index_nonexistent(self) -> None:
        """Test nonexistent file."""
        should, reason = should_index(
            "/nonexistent/file.txt",
            patterns=["*.txt"],
            excludes=[],
            max_size_bytes=100 * 1024 * 1024,
        )

        assert should is False
        assert "not found" in reason

    def test_should_not_index_directory(self, tmp_path: Path) -> None:
        """Test directory returns False."""
        should, reason = should_index(
            str(tmp_path),
            patterns=["*"],
            excludes=[],
            max_size_bytes=100 * 1024 * 1024,
        )

        assert should is False
        assert "directory" in reason


class TestWatchStatus:
    """Tests for WatchStatus dataclass."""

    def test_watch_status(self) -> None:
        """Test WatchStatus dataclass."""
        status = WatchStatus(
            running=True,
            pid=12345,
            uptime_seconds=3600,
            directories=["/test"],
            files_indexed=100,
        )

        assert status.running is True
        assert status.pid == 12345
        assert status.uptime_seconds == 3600
        assert status.files_indexed == 100


class TestWatchEvent:
    """Tests for WatchEvent dataclass."""

    def test_watch_event(self) -> None:
        """Test WatchEvent dataclass."""
        event = WatchEvent(
            timestamp=datetime.now(),
            event_type="indexed",
            path="/test/file.pdf",
            reason="",
        )

        assert event.event_type == "indexed"
        assert event.path == "/test/file.pdf"


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
class TestFolderWatcher:
    """Tests for FolderWatcher class."""

    def test_watcher_requires_watchdog(self) -> None:
        """Test watcher requires watchdog library."""
        from ragd.web.watcher import FolderWatcher

        # This should work since watchdog is available
        config = WatchConfig(directories=[Path(".")])
        watcher = FolderWatcher(config, lambda p: True)
        assert watcher is not None

    def test_is_running_no_pid(self) -> None:
        """Test is_running with no PID file."""
        from ragd.web.watcher import FolderWatcher

        # Clean up any existing PID file
        if FolderWatcher.PID_FILE.exists():
            FolderWatcher.PID_FILE.unlink()

        assert FolderWatcher.is_running() is False

    def test_read_status_no_file(self) -> None:
        """Test read_status with no status file."""
        from ragd.web.watcher import FolderWatcher

        # Clean up any existing status file
        if FolderWatcher.STATUS_FILE.exists():
            FolderWatcher.STATUS_FILE.unlink()

        status = FolderWatcher.read_status()
        assert status is None
