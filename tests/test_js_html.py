"""Tests for JavaScript-enabled HTML extraction (F-098)."""

import tempfile
from pathlib import Path

import pytest

from ragd.ingestion.js_html import (
    JSRenderConfig,
    JSHTMLExtractor,
    _detect_js_required,
    _check_playwright_available,
    is_playwright_installed,
)


class TestJSRenderConfig:
    """Tests for JSRenderConfig."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = JSRenderConfig()
        assert config.render_javascript == "auto"
        assert config.render_timeout == 30
        assert config.wait_for_selector is None

    def test_custom_config(self):
        """Should accept custom values."""
        config = JSRenderConfig(
            render_javascript="always",
            render_timeout=60,
            wait_for_selector="#content",
        )
        assert config.render_javascript == "always"
        assert config.render_timeout == 60
        assert config.wait_for_selector == "#content"


class TestJSDetection:
    """Tests for JavaScript detection."""

    def test_detect_react_app(self):
        """Should detect React app markers."""
        html = '''
        <html>
        <body>
            <div id="root"></div>
            <script src="bundle.js"></script>
        </body>
        </html>
        '''
        assert _detect_js_required(html) is True

    def test_detect_vue_app(self):
        """Should detect Vue app markers."""
        html = '''
        <html>
        <body>
            <div id="app" v-cloak></div>
        </body>
        </html>
        '''
        assert _detect_js_required(html) is True

    def test_detect_next_js(self):
        """Should detect Next.js markers."""
        html = '''
        <html>
        <body>
            <div id="__next"></div>
            <script>window.__NEXT_DATA__ = {}</script>
        </body>
        </html>
        '''
        assert _detect_js_required(html) is True

    def test_detect_static_content(self):
        """Should not flag static content."""
        html = '''
        <html>
        <body>
            <h1>Welcome</h1>
            <p>This is a static page with lots of content.</p>
            <p>More content here with plenty of text.</p>
            <p>And even more text to ensure we have enough.</p>
        </body>
        </html>
        '''
        assert _detect_js_required(html) is False


class TestJSHTMLExtractor:
    """Tests for JSHTMLExtractor."""

    @pytest.fixture
    def static_html_file(self):
        """Create a static HTML file."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            delete=False,
        ) as f:
            f.write('''
            <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>This is test content.</p>
            </body>
            </html>
            ''')
            path = Path(f.name)
        yield path
        path.unlink()

    def test_extract_static_html(self, static_html_file):
        """Should extract text from static HTML."""
        config = JSRenderConfig(render_javascript="never")
        extractor = JSHTMLExtractor(config=config)
        result = extractor.extract(static_html_file)

        assert result.success is True
        assert "Hello World" in result.text
        assert "test content" in result.text.lower()
        assert result.extraction_method == "beautifulsoup"

    def test_extract_with_auto_mode(self, static_html_file):
        """Auto mode should use static for simple pages."""
        config = JSRenderConfig(render_javascript="auto")
        extractor = JSHTMLExtractor(config=config)
        result = extractor.extract(static_html_file)

        assert result.success is True
        assert "Hello World" in result.text
        # Should not have used Playwright for static content
        assert result.metadata.get("js_rendered") is False

    def test_extract_nonexistent_file(self):
        """Should handle nonexistent files."""
        extractor = JSHTMLExtractor()
        result = extractor.extract(Path("/nonexistent/file.html"))

        assert result.success is False
        assert result.extraction_method == "read_error"

    def test_never_mode_skips_rendering(self, static_html_file):
        """Never mode should always skip JS rendering."""
        config = JSRenderConfig(render_javascript="never")
        extractor = JSHTMLExtractor(config=config)
        result = extractor.extract(static_html_file)

        assert result.success is True
        assert result.metadata.get("js_rendered") is False

    def test_extracts_title(self, static_html_file):
        """Should extract page title."""
        extractor = JSHTMLExtractor()
        result = extractor.extract(static_html_file)

        assert result.success is True
        assert result.metadata.get("title") == "Test Page"


class TestPlaywrightAvailability:
    """Tests for Playwright availability checks."""

    def test_check_playwright_returns_bool(self):
        """Should return boolean for Playwright availability."""
        result = _check_playwright_available()
        assert isinstance(result, bool)

    def test_is_playwright_installed_returns_bool(self):
        """Should return boolean for browser installation."""
        result = is_playwright_installed()
        assert isinstance(result, bool)
