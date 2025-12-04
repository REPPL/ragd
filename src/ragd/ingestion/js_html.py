"""JavaScript-enabled HTML extraction (F-098).

Provides Playwright-based rendering for JavaScript-heavy web pages.
Falls back to static extraction when JS rendering is unnecessary or fails.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from ragd.ingestion.extractor import ExtractionResult


logger = logging.getLogger(__name__)


@dataclass
class JSRenderConfig:
    """Configuration for JavaScript rendering."""

    render_javascript: str = "auto"  # auto | always | never
    render_timeout: int = 30  # seconds
    wait_for_selector: str | None = None  # CSS selector to wait for
    wait_for_timeout: int = 5000  # ms to wait after page load


def _detect_js_required(html_content: str) -> bool:
    """Detect if JavaScript rendering is likely required.

    Args:
        html_content: Raw HTML content

    Returns:
        True if JS rendering is likely needed
    """
    # Indicators that content is JS-rendered
    js_indicators = [
        # React/Vue/Angular markers
        r'<div id="(root|app|__next)">\s*</div>',
        r'data-reactroot',
        r'ng-app',
        r'v-cloak',
        # Empty body with scripts
        r'<body[^>]*>\s*<script',
        # Common SPA patterns
        r'__NUXT__',
        r'__NEXT_DATA__',
        r'window\.__INITIAL_STATE__',
        # Loading placeholders
        r'<div[^>]*class="[^"]*loading[^"]*"',
        r'<div[^>]*class="[^"]*skeleton[^"]*"',
    ]

    for pattern in js_indicators:
        if re.search(pattern, html_content, re.IGNORECASE):
            return True

    # Check if body has minimal content
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.find("body")
    if body:
        text = body.get_text(strip=True)
        # Very little text content but lots of scripts
        scripts = soup.find_all("script")
        if len(text) < 200 and len(scripts) > 5:
            return True

    return False


def _check_playwright_available() -> bool:
    """Check if Playwright is available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def render_with_playwright(
    html_path: Path,
    config: JSRenderConfig | None = None,
) -> ExtractionResult:
    """Render HTML with Playwright and extract text.

    Args:
        html_path: Path to HTML file
        config: Rendering configuration

    Returns:
        ExtractionResult with rendered content
    """
    if config is None:
        config = JSRenderConfig()

    if not _check_playwright_available():
        return ExtractionResult(
            text="",
            success=False,
            error="Playwright not available. Run 'playwright install chromium'.",
            extraction_method="playwright_unavailable",
        )

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Use headless Chromium
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Set timeout
            page.set_default_timeout(config.render_timeout * 1000)

            # Load local HTML file
            file_url = f"file://{html_path.absolute()}"
            page.goto(file_url, wait_until="networkidle")

            # Wait for specific selector if configured
            if config.wait_for_selector:
                try:
                    page.wait_for_selector(
                        config.wait_for_selector,
                        timeout=config.wait_for_timeout,
                    )
                except Exception:
                    pass  # Continue even if selector not found

            # Get rendered HTML
            rendered_html = page.content()

            # Extract text from rendered content
            soup = BeautifulSoup(rendered_html, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            # Get title
            title = None
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            browser.close()

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(html_path),
                    "format": "html",
                    "title": title,
                    "js_rendered": True,
                },
                extraction_method="playwright",
                success=True,
            )

    except Exception as e:
        logger.warning(f"Playwright rendering failed: {e}")
        return ExtractionResult(
            text="",
            success=False,
            error=str(e),
            extraction_method="playwright_error",
        )


class JSHTMLExtractor:
    """HTML extractor with JavaScript rendering support (F-098).

    Automatically detects when JS rendering is needed and uses Playwright.
    Falls back to static extraction when:
    - JS rendering is disabled
    - Playwright is unavailable
    - Rendering fails
    - Content doesn't require JS
    """

    def __init__(
        self,
        config: JSRenderConfig | None = None,
        fallback_extractor: Any = None,
    ) -> None:
        """Initialise JS-enabled HTML extractor.

        Args:
            config: JS rendering configuration
            fallback_extractor: Extractor for static fallback
        """
        self.config = config or JSRenderConfig()
        self.fallback_extractor = fallback_extractor
        self._playwright_available = _check_playwright_available()

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from HTML, using JS rendering if needed.

        Args:
            path: Path to HTML file

        Returns:
            ExtractionResult with extracted text
        """
        # Read HTML content
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
        except Exception as e:
            return ExtractionResult(
                text="",
                success=False,
                error=str(e),
                extraction_method="read_error",
            )

        # Determine if JS rendering is needed
        should_render = self._should_render_js(html_content)

        if should_render and self._playwright_available:
            # Try JS rendering
            result = render_with_playwright(path, self.config)
            if result.success:
                return result
            # Fall back to static on failure
            logger.info(f"Falling back to static extraction for {path}")

        # Use static extraction
        return self._extract_static(html_content, path)

    def _should_render_js(self, html_content: str) -> bool:
        """Determine if JS rendering should be used.

        Args:
            html_content: Raw HTML content

        Returns:
            True if JS rendering should be attempted
        """
        mode = self.config.render_javascript

        if mode == "never":
            return False
        elif mode == "always":
            return True
        else:  # auto
            return _detect_js_required(html_content)

    def _extract_static(
        self,
        html_content: str,
        path: Path,
    ) -> ExtractionResult:
        """Extract text statically without JS rendering.

        Args:
            html_content: HTML content
            path: Source path

        Returns:
            ExtractionResult with extracted text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            # Get title
            title = None
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "html",
                    "title": title,
                    "js_rendered": False,
                },
                extraction_method="beautifulsoup",
                success=True,
            )

        except Exception as e:
            return ExtractionResult(
                text="",
                success=False,
                error=str(e),
                extraction_method="static_error",
            )


def is_playwright_installed() -> bool:
    """Check if Playwright browser is installed.

    Returns:
        True if Playwright browsers are available
    """
    if not _check_playwright_available():
        return False

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Try to get executable path
            return p.chromium.name is not None
    except Exception:
        return False
