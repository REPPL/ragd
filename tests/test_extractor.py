"""Tests for text extraction module."""

import tempfile
from pathlib import Path

from ragd.ingestion.extractor import (
    ExtractionResult,
    PDFExtractor,
    PlainTextExtractor,
    MarkdownExtractor,
    HTMLExtractor,
    extract_text,
    EXTRACTORS,
)


def test_extraction_result_defaults() -> None:
    """Test ExtractionResult default values."""
    result = ExtractionResult(text="test")
    assert result.text == "test"
    assert result.success is True
    assert result.error is None
    assert result.extraction_method == "unknown"


def test_extraction_result_failure() -> None:
    """Test ExtractionResult for failures."""
    result = ExtractionResult(
        text="",
        success=False,
        error="Test error",
    )
    assert result.success is False
    assert result.error == "Test error"


def test_plaintext_extractor() -> None:
    """Test plain text extraction."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, world!")
        f.flush()
        path = Path(f.name)

    try:
        extractor = PlainTextExtractor()
        result = extractor.extract(path)
        assert result.success
        assert result.text == "Hello, world!"
        assert result.extraction_method == "plaintext"
    finally:
        path.unlink()


def test_plaintext_extractor_utf8() -> None:
    """Test plain text extraction with UTF-8 content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Héllo, wörld! 你好")
        f.flush()
        path = Path(f.name)

    try:
        extractor = PlainTextExtractor()
        result = extractor.extract(path)
        assert result.success
        assert "Héllo" in result.text
        assert "你好" in result.text
    finally:
        path.unlink()


def test_markdown_extractor() -> None:
    """Test markdown extraction."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Title\n\nSome **bold** text.")
        f.flush()
        path = Path(f.name)

    try:
        extractor = MarkdownExtractor()
        result = extractor.extract(path)
        assert result.success
        assert "# Title" in result.text
        assert "**bold**" in result.text
        assert result.extraction_method == "markdown"
    finally:
        path.unlink()


def test_html_extractor() -> None:
    """Test HTML extraction."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write("<html><head><title>Test</title></head><body><p>Hello world</p></body></html>")
        f.flush()
        path = Path(f.name)

    try:
        extractor = HTMLExtractor()
        result = extractor.extract(path)
        assert result.success
        assert "Hello world" in result.text
        assert "<html>" not in result.text
        assert result.extraction_method == "beautifulsoup"
    finally:
        path.unlink()


def test_html_extractor_strips_scripts() -> None:
    """Test HTML extraction removes script tags."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write("<html><body><script>alert('hi')</script><p>Content</p></body></html>")
        f.flush()
        path = Path(f.name)

    try:
        extractor = HTMLExtractor()
        result = extractor.extract(path)
        assert result.success
        assert "Content" in result.text
        assert "alert" not in result.text
    finally:
        path.unlink()


def test_extract_text_txt() -> None:
    """Test extract_text function with TXT file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        f.flush()
        path = Path(f.name)

    try:
        result = extract_text(path)
        assert result.success
        assert result.text == "Test content"
    finally:
        path.unlink()


def test_extract_text_unsupported() -> None:
    """Test extract_text with unsupported file type."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
        f.write("Content")
        f.flush()
        path = Path(f.name)

    try:
        result = extract_text(path)
        assert not result.success
        assert "Unsupported" in result.error
    finally:
        path.unlink()


def test_extractors_registry() -> None:
    """Test extractors are registered."""
    assert "pdf" in EXTRACTORS
    assert "txt" in EXTRACTORS
    assert "md" in EXTRACTORS
    assert "html" in EXTRACTORS


def test_pdf_extractor() -> None:
    """Test PDF extraction with a programmatically created PDF."""
    import fitz

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)

    try:
        # Create a simple PDF with PyMuPDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello from PDF!")
        page.insert_text((72, 100), "This is page 1.")
        page2 = doc.new_page()
        page2.insert_text((72, 72), "Page 2 content.")
        doc.save(str(path))
        doc.close()

        # Extract text
        extractor = PDFExtractor()
        result = extractor.extract(path)

        assert result.success, f"Extraction failed: {result.error}"
        assert "Hello from PDF!" in result.text
        assert "Page 2 content" in result.text
        assert result.pages == 2
        assert result.extraction_method == "pymupdf"
    finally:
        path.unlink()


def test_pdf_extractor_empty_pdf() -> None:
    """Test PDF extraction with an empty PDF."""
    import fitz

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)

    try:
        # Create an empty PDF
        doc = fitz.open()
        doc.new_page()  # Blank page
        doc.save(str(path))
        doc.close()

        extractor = PDFExtractor()
        result = extractor.extract(path)

        assert result.success
        assert result.pages == 1
        # Empty page should have empty or whitespace-only text
        assert result.text.strip() == ""
    finally:
        path.unlink()


def test_html_extractor_utf8_smart_quotes() -> None:
    """Test HTML extraction handles UTF-8 smart quotes correctly."""
    # Smart quotes: " " ' ' (U+201C, U+201D, U+2018, U+2019)
    html_content = b'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Test</title></head>
<body>
<p>\xe2\x80\x9cHello, World!\xe2\x80\x9d said the \xe2\x80\x98developer\xe2\x80\x99.</p>
</body>
</html>'''

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="wb") as f:
        f.write(html_content)
        path = Path(f.name)

    try:
        extractor = HTMLExtractor()
        result = extractor.extract(path)

        assert result.success, f"Extraction failed: {result.error}"
        # Should contain proper smart quotes, not mojibake
        assert "\u201c" in result.text or '"Hello' in result.text  # Opening double quote
        assert "Hello, World!" in result.text
        assert "developer" in result.text
        # Should NOT contain mojibake patterns
        assert "\xe2\x80" not in result.text
        assert "â€" not in result.text  # Common mojibake pattern
    finally:
        path.unlink()


def test_html_extractor_with_charset_declaration() -> None:
    """Test HTML extraction respects meta charset declaration."""
    # HTML with explicit UTF-8 charset
    html_content = b'''<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Test \xc3\xa9ncoding</title>
</head>
<body>
<p>Caf\xc3\xa9 and na\xc3\xafve</p>
</body>
</html>'''

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="wb") as f:
        f.write(html_content)
        path = Path(f.name)

    try:
        extractor = HTMLExtractor()
        result = extractor.extract(path)

        assert result.success
        assert "Café" in result.text
        assert "naïve" in result.text
    finally:
        path.unlink()


def test_html_extractor_latin1_fallback() -> None:
    """Test HTML extraction with Latin-1 encoded content."""
    # Latin-1 encoded HTML (no UTF-8 BOM, no charset declaration)
    html_content = b'''<html>
<body>
<p>Caf\xe9 and na\xefve in Latin-1</p>
</body>
</html>'''

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="wb") as f:
        f.write(html_content)
        path = Path(f.name)

    try:
        extractor = HTMLExtractor()
        result = extractor.extract(path)

        assert result.success
        # BeautifulSoup should handle this gracefully
        # The text might be slightly different depending on detection
        assert "Caf" in result.text
        assert "Latin-1" in result.text
    finally:
        path.unlink()
