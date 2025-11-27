"""Fast HTML parser for ragd.

This module implements F-039: Advanced HTML Processing, providing
high-performance HTML parsing using selectolax with graceful fallback
to BeautifulSoup.

The tiered processing approach:
- Tier 1: Simple pages with <article>/<main> → selectolax fast path
- Tier 2: Clean HTML with low boilerplate → selectolax + cleanup
- Tier 3: Complex pages (ads, sidebars) → trafilatura
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    from selectolax.parser import HTMLParser as SelectolaxParser

    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


class ComplexityTier(Enum):
    """HTML document complexity tier."""

    SIMPLE = auto()  # Has <article>/<main>, clean structure
    MODERATE = auto()  # Clean HTML but no semantic markers
    COMPLEX = auto()  # Ads, sidebars, needs content extraction


@dataclass
class ParseResult:
    """Result of HTML parsing.

    Contains the parsed document and metadata about parsing.
    """

    html: str
    title: str = ""
    text: str = ""
    tier: ComplexityTier = ComplexityTier.MODERATE
    parse_time_ms: float = 0.0
    parser_used: str = "unknown"
    success: bool = True
    error: str | None = None

    # Optional parsed tree (for further processing)
    _tree: Any = field(default=None, repr=False)

    @property
    def tree(self) -> Any:
        """Get the parsed tree (selectolax or BeautifulSoup)."""
        return self._tree


def detect_complexity(html: str) -> ComplexityTier:
    """Detect HTML document complexity.

    Uses heuristics to determine the best processing tier:
    - SIMPLE: Has semantic content markers (<article>, <main>)
    - MODERATE: Clean HTML without heavy boilerplate
    - COMPLEX: Ads, multiple sidebars, navigation-heavy

    Args:
        html: HTML content to analyse

    Returns:
        ComplexityTier indicating processing approach
    """
    html_lower = html[:50000].lower()  # Check first 50KB

    # Check for semantic content markers
    has_article = "<article" in html_lower
    has_main = "<main" in html_lower
    has_schema = 'type="application/ld+json"' in html_lower

    # Check for complexity indicators
    nav_count = html_lower.count("<nav")
    aside_count = html_lower.count("<aside")
    ad_patterns = len(re.findall(r'class="[^"]*(?:ad|advertisement|sponsor)[^"]*"', html_lower))
    iframe_count = html_lower.count("<iframe")

    # Simple tier: has semantic markers, low boilerplate
    if (has_article or has_main) and nav_count <= 2 and aside_count <= 1:
        return ComplexityTier.SIMPLE

    # Complex tier: heavy boilerplate
    if nav_count > 3 or aside_count > 2 or ad_patterns > 2 or iframe_count > 3:
        return ComplexityTier.COMPLEX

    # Default to moderate
    return ComplexityTier.MODERATE


def parse_html(html: str, *, use_fallback: bool = True) -> ParseResult:
    """Parse HTML content using the fastest available parser.

    Uses selectolax if available (10-100x faster than BeautifulSoup),
    with graceful fallback to BeautifulSoup.

    Args:
        html: HTML content to parse
        use_fallback: Whether to use BeautifulSoup if selectolax fails

    Returns:
        ParseResult with parsed content and metadata
    """
    import time

    start = time.perf_counter()
    tier = detect_complexity(html)

    if SELECTOLAX_AVAILABLE:
        try:
            result = _parse_with_selectolax(html, tier)
            result.parse_time_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            logger.warning("selectolax parsing failed: %s", e)
            if not use_fallback:
                return ParseResult(
                    html=html,
                    tier=tier,
                    success=False,
                    error=str(e),
                    parser_used="selectolax",
                )

    if BEAUTIFULSOUP_AVAILABLE:
        try:
            result = _parse_with_beautifulsoup(html, tier)
            result.parse_time_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            logger.warning("BeautifulSoup parsing failed: %s", e)
            return ParseResult(
                html=html,
                tier=tier,
                success=False,
                error=str(e),
                parser_used="beautifulsoup",
            )

    # No parser available
    return ParseResult(
        html=html,
        tier=tier,
        success=False,
        error="No HTML parser available. Install selectolax or beautifulsoup4.",
        parser_used="none",
    )


def _parse_with_selectolax(html: str, tier: ComplexityTier) -> ParseResult:
    """Parse HTML using selectolax.

    Args:
        html: HTML content
        tier: Detected complexity tier

    Returns:
        ParseResult with selectolax tree
    """
    tree = SelectolaxParser(html)

    # Extract title
    title = ""
    title_tag = tree.css_first("title")
    if title_tag:
        title = title_tag.text(strip=True) or ""

    # Extract text based on tier
    if tier == ComplexityTier.SIMPLE:
        text = _extract_simple_content(tree)
    else:
        text = _extract_all_text(tree)

    return ParseResult(
        html=html,
        title=title,
        text=text,
        tier=tier,
        parser_used="selectolax",
        success=True,
        _tree=tree,
    )


def _extract_simple_content(tree: Any) -> str:
    """Extract content from simple pages with semantic markers.

    Args:
        tree: selectolax HTMLParser tree

    Returns:
        Extracted text content
    """
    # Try article first
    article = tree.css_first("article")
    if article:
        return _clean_text(article.text(strip=True))

    # Then main
    main = tree.css_first("main")
    if main:
        return _clean_text(main.text(strip=True))

    # Fallback to body
    body = tree.css_first("body")
    if body:
        return _clean_text(body.text(strip=True))

    return ""


def _extract_all_text(tree: Any) -> str:
    """Extract all text from HTML, removing scripts/styles.

    Args:
        tree: selectolax HTMLParser tree

    Returns:
        Extracted text content
    """
    # Remove unwanted tags
    for tag in tree.css("script, style, nav, footer, aside, noscript"):
        tag.decompose()

    body = tree.css_first("body")
    if body:
        return _clean_text(body.text(strip=True))

    return _clean_text(tree.text(strip=True))


def _clean_text(text: str) -> str:
    """Clean extracted text.

    Args:
        text: Raw text

    Returns:
        Cleaned text with normalised whitespace
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _parse_with_beautifulsoup(html: str, tier: ComplexityTier) -> ParseResult:
    """Parse HTML using BeautifulSoup (fallback).

    Args:
        html: HTML content
        tier: Detected complexity tier

    Returns:
        ParseResult with BeautifulSoup tree
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    # Remove unwanted tags
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "noscript"]):
        tag.decompose()

    # Extract text based on tier
    if tier == ComplexityTier.SIMPLE:
        article = soup.find("article") or soup.find("main") or soup.body
        text = article.get_text(strip=True) if article else ""
    else:
        text = soup.body.get_text(strip=True) if soup.body else ""

    text = _clean_text(text)

    return ParseResult(
        html=html,
        title=title,
        text=text,
        tier=tier,
        parser_used="beautifulsoup",
        success=True,
        _tree=soup,
    )


def get_element_by_selector(html: str, selector: str) -> str | None:
    """Get element content by CSS selector.

    Args:
        html: HTML content
        selector: CSS selector

    Returns:
        Element text content or None if not found
    """
    if SELECTOLAX_AVAILABLE:
        tree = SelectolaxParser(html)
        element = tree.css_first(selector)
        if element:
            return element.text(strip=True)
    elif BEAUTIFULSOUP_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    return None


def get_attribute(html: str, selector: str, attribute: str) -> str | None:
    """Get element attribute by CSS selector.

    Args:
        html: HTML content
        selector: CSS selector
        attribute: Attribute name

    Returns:
        Attribute value or None if not found
    """
    if SELECTOLAX_AVAILABLE:
        tree = SelectolaxParser(html)
        element = tree.css_first(selector)
        if element:
            return element.attributes.get(attribute)
    elif BEAUTIFULSOUP_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        element = soup.select_one(selector)
        if element:
            return element.get(attribute)
    return None
