"""Tests for HTML parser module (F-039).

Tests the selectolax-based fast HTML parser with complexity detection
and graceful fallback to BeautifulSoup.
"""

import pytest

from ragd.web.parser import (
    ComplexityTier,
    ParseResult,
    detect_complexity,
    get_attribute,
    get_element_by_selector,
    parse_html,
    SELECTOLAX_AVAILABLE,
    BEAUTIFULSOUP_AVAILABLE,
)


class TestComplexityDetection:
    """Tests for HTML complexity detection."""

    def test_simple_with_article_tag(self) -> None:
        """Article tag indicates simple complexity."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>Content here.</p>
            </article>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        assert tier == ComplexityTier.SIMPLE

    def test_simple_with_main_tag(self) -> None:
        """Main tag indicates simple complexity."""
        html = """
        <html>
        <body>
            <main>
                <h1>Main Content</h1>
                <p>Content here.</p>
            </main>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        assert tier == ComplexityTier.SIMPLE

    def test_moderate_without_semantic_markers(self) -> None:
        """HTML without semantic markers is moderate complexity."""
        html = """
        <html>
        <body>
            <div class="content">
                <h1>Title</h1>
                <p>Content here.</p>
            </div>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        assert tier == ComplexityTier.MODERATE

    def test_complex_with_many_navs(self) -> None:
        """Multiple nav elements indicate complex page."""
        html = """
        <html>
        <body>
            <nav>Menu 1</nav>
            <nav>Menu 2</nav>
            <nav>Menu 3</nav>
            <nav>Menu 4</nav>
            <article><p>Content</p></article>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        assert tier == ComplexityTier.COMPLEX

    def test_complex_with_many_asides(self) -> None:
        """Multiple aside elements indicate complex page."""
        html = """
        <html>
        <body>
            <aside>Sidebar 1</aside>
            <aside>Sidebar 2</aside>
            <aside>Sidebar 3</aside>
            <main><p>Content</p></main>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        assert tier == ComplexityTier.COMPLEX

    def test_complex_with_ad_classes(self) -> None:
        """Ad-related classes indicate complex page (when no article tag)."""
        html = """
        <html>
        <body>
            <div class="advertisement">Ad 1</div>
            <div class="ad-banner">Ad 2</div>
            <div class="sponsor-link">Ad 3</div>
            <div><p>Content</p></div>
        </body>
        </html>
        """
        tier = detect_complexity(html)
        # Ad classes without article tag → COMPLEX
        # Ad classes with article tag → may still be SIMPLE (semantic wins)
        assert tier == ComplexityTier.COMPLEX


class TestParseHtml:
    """Tests for HTML parsing."""

    def test_parse_simple_html(self) -> None:
        """Parse simple HTML document."""
        html = """
        <html>
        <head><title>Test Title</title></head>
        <body>
            <article>
                <h1>Heading</h1>
                <p>Paragraph content here.</p>
            </article>
        </body>
        </html>
        """
        result = parse_html(html)

        assert result.success
        assert result.title == "Test Title"
        assert "Heading" in result.text or "Paragraph" in result.text
        assert result.parse_time_ms >= 0

    def test_parse_returns_result(self) -> None:
        """Parsing returns ParseResult object."""
        html = "<html><body><p>Test</p></body></html>"
        result = parse_html(html)

        assert isinstance(result, ParseResult)
        assert isinstance(result.tier, ComplexityTier)
        assert result.parser_used in ["selectolax", "beautifulsoup", "none"]

    def test_parse_malformed_html(self) -> None:
        """Parser handles malformed HTML gracefully."""
        html = "<html><body><p>Unclosed paragraph<div>Nested wrong</p></div>"
        result = parse_html(html)

        # Should not crash
        assert isinstance(result, ParseResult)

    def test_parse_empty_html(self) -> None:
        """Parser handles empty HTML."""
        html = ""
        result = parse_html(html)

        assert isinstance(result, ParseResult)
        # Empty content should still parse

    def test_parse_html_only_body(self) -> None:
        """Parser handles HTML with only body content."""
        html = "<body><p>Just a paragraph</p></body>"
        result = parse_html(html)

        assert result.success
        assert "Just a paragraph" in result.text

    def test_scripts_and_styles_removed(self) -> None:
        """Scripts and styles are removed from text output."""
        html = """
        <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert('test');</script>
        </head>
        <body>
            <p>Visible content</p>
            <script>more script</script>
        </body>
        </html>
        """
        result = parse_html(html)

        assert "Visible content" in result.text
        assert "alert" not in result.text
        assert "color: red" not in result.text


class TestElementSelectors:
    """Tests for element selection helpers."""

    def test_get_element_by_selector(self) -> None:
        """Get element text by CSS selector."""
        html = """
        <html>
        <body>
            <h1 class="title">Main Title</h1>
            <p class="intro">Introduction text</p>
        </body>
        </html>
        """
        title = get_element_by_selector(html, "h1.title")
        assert title == "Main Title"

        intro = get_element_by_selector(html, "p.intro")
        assert intro == "Introduction text"

    def test_get_element_not_found(self) -> None:
        """Returns None when element not found."""
        html = "<html><body><p>Content</p></body></html>"
        result = get_element_by_selector(html, "h1.nonexistent")
        assert result is None

    def test_get_attribute(self) -> None:
        """Get element attribute by CSS selector."""
        html = """
        <html>
        <body>
            <a href="https://example.com" title="Example">Link</a>
            <img src="image.jpg" alt="Test image">
        </body>
        </html>
        """
        href = get_attribute(html, "a", "href")
        assert href == "https://example.com"

        alt = get_attribute(html, "img", "alt")
        assert alt == "Test image"

    def test_get_attribute_not_found(self) -> None:
        """Returns None when attribute not found."""
        html = "<html><body><a>No href</a></body></html>"
        result = get_attribute(html, "a", "href")
        assert result is None


class TestParserPerformance:
    """Performance-related tests."""

    def test_parser_reports_timing(self) -> None:
        """Parser reports parse time."""
        html = "<html><body><p>Test</p></body></html>"
        result = parse_html(html)

        assert result.parse_time_ms >= 0
        assert isinstance(result.parse_time_ms, float)

    def test_parser_identifies_parser_used(self) -> None:
        """Parser identifies which backend was used."""
        html = "<html><body><p>Test</p></body></html>"
        result = parse_html(html)

        assert result.parser_used in ["selectolax", "beautifulsoup", "none"]

    @pytest.mark.skipif(
        not SELECTOLAX_AVAILABLE,
        reason="selectolax not installed"
    )
    def test_selectolax_used_when_available(self) -> None:
        """selectolax is used when available."""
        html = "<html><body><p>Test</p></body></html>"
        result = parse_html(html)

        assert result.parser_used == "selectolax"

    @pytest.mark.skipif(
        SELECTOLAX_AVAILABLE,
        reason="selectolax is installed"
    )
    def test_beautifulsoup_fallback(self) -> None:
        """BeautifulSoup is used as fallback."""
        html = "<html><body><p>Test</p></body></html>"
        result = parse_html(html)

        assert result.parser_used == "beautifulsoup"


class TestEncodingHandling:
    """Tests for encoding detection and handling."""

    def test_utf8_content(self) -> None:
        """Handles UTF-8 encoded content."""
        html = "<html><body><p>Héllo Wörld — ñ</p></body></html>"
        result = parse_html(html)

        assert "Héllo Wörld" in result.text or "Héllo" in result.text

    def test_unicode_in_title(self) -> None:
        """Handles Unicode in title."""
        html = "<html><head><title>日本語タイトル</title></head><body></body></html>"
        result = parse_html(html)

        assert result.title == "日本語タイトル"

    def test_special_characters(self) -> None:
        """Handles special characters."""
        html = '<html><body><p>Quotes: "test" and &amp; symbol</p></body></html>'
        result = parse_html(html)

        assert result.success
