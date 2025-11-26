"""Tests for utility functions."""

import tempfile
from pathlib import Path

from ragd.utils.paths import (
    get_file_type,
    is_supported_file,
    discover_files,
    SUPPORTED_EXTENSIONS,
)


class TestGetFileType:
    """Tests for get_file_type function."""

    def test_pdf(self) -> None:
        """Test PDF file type detection."""
        assert get_file_type(Path("doc.pdf")) == "pdf"
        assert get_file_type(Path("doc.PDF")) == "pdf"

    def test_txt(self) -> None:
        """Test TXT file type detection."""
        assert get_file_type(Path("doc.txt")) == "txt"
        assert get_file_type(Path("doc.text")) == "txt"

    def test_markdown(self) -> None:
        """Test Markdown file type detection."""
        assert get_file_type(Path("doc.md")) == "md"
        assert get_file_type(Path("doc.markdown")) == "md"

    def test_html(self) -> None:
        """Test HTML file type detection."""
        assert get_file_type(Path("doc.html")) == "html"
        assert get_file_type(Path("doc.htm")) == "html"

    def test_unknown(self) -> None:
        """Test unknown file type."""
        assert get_file_type(Path("doc.xyz")) == "unknown"
        assert get_file_type(Path("doc.docx")) == "unknown"


class TestIsSupportedFile:
    """Tests for is_supported_file function."""

    def test_supported_files(self) -> None:
        """Test supported file detection."""
        assert is_supported_file(Path("doc.pdf"))
        assert is_supported_file(Path("doc.txt"))
        assert is_supported_file(Path("doc.md"))
        assert is_supported_file(Path("doc.html"))

    def test_unsupported_files(self) -> None:
        """Test unsupported file detection."""
        assert not is_supported_file(Path("doc.docx"))
        assert not is_supported_file(Path("doc.xlsx"))
        assert not is_supported_file(Path("doc.png"))


class TestDiscoverFiles:
    """Tests for discover_files function."""

    def test_discover_single_file(self) -> None:
        """Test discovering a single file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = Path(f.name)

        try:
            files = discover_files(path)
            assert len(files) == 1
            assert files[0] == path
        finally:
            path.unlink()

    def test_discover_unsupported_file(self) -> None:
        """Test discovering unsupported file returns empty."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            path = Path(f.name)

        try:
            files = discover_files(path)
            assert len(files) == 0
        finally:
            path.unlink()

    def test_discover_directory(self) -> None:
        """Test discovering files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "doc1.txt").write_text("content")
            (Path(tmpdir) / "doc2.md").write_text("content")
            (Path(tmpdir) / "doc3.xyz").write_text("content")

            files = discover_files(Path(tmpdir))
            assert len(files) == 2
            filenames = [f.name for f in files]
            assert "doc1.txt" in filenames
            assert "doc2.md" in filenames
            assert "doc3.xyz" not in filenames

    def test_discover_recursive(self) -> None:
        """Test recursive file discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            (Path(tmpdir) / "doc1.txt").write_text("content")
            (subdir / "doc2.txt").write_text("content")

            files = discover_files(Path(tmpdir), recursive=True)
            assert len(files) == 2

            files_non_recursive = discover_files(Path(tmpdir), recursive=False)
            assert len(files_non_recursive) == 1

    def test_discover_nonexistent(self) -> None:
        """Test discovering from nonexistent path."""
        files = discover_files(Path("/nonexistent/path"))
        assert len(files) == 0


class TestSupportedExtensions:
    """Tests for SUPPORTED_EXTENSIONS constant."""

    def test_extensions_exist(self) -> None:
        """Test that extensions are defined."""
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".md" in SUPPORTED_EXTENSIONS
        assert ".html" in SUPPORTED_EXTENSIONS

    def test_extension_mapping(self) -> None:
        """Test extension to type mapping."""
        assert SUPPORTED_EXTENSIONS[".pdf"] == "pdf"
        assert SUPPORTED_EXTENSIONS[".txt"] == "txt"
        assert SUPPORTED_EXTENSIONS[".text"] == "txt"
        assert SUPPORTED_EXTENSIONS[".md"] == "md"
        assert SUPPORTED_EXTENSIONS[".markdown"] == "md"
        assert SUPPORTED_EXTENSIONS[".html"] == "html"
        assert SUPPORTED_EXTENSIONS[".htm"] == "html"
