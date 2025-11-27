"""Rich metadata extraction for HTML documents.

This module implements F-039: Advanced HTML Processing, providing
comprehensive metadata extraction from HTML documents including:
- Open Graph protocol (og:title, og:description, etc.)
- JSON-LD/Schema.org structured data
- Dublin Core metadata
- Twitter Card metadata
- Standard HTML meta tags
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class HTMLMetadata:
    """Rich metadata extracted from HTML document.

    Combines metadata from multiple sources with resolution priority:
    JSON-LD > Open Graph > Twitter Cards > Dublin Core > Standard meta
    """

    # Basic metadata
    title: str | None = None
    description: str | None = None
    author: str | None = None
    language: str | None = None
    publication_date: datetime | None = None
    modified_date: datetime | None = None

    # Open Graph
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None
    og_site_name: str | None = None
    og_url: str | None = None

    # Twitter Cards
    twitter_card: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None
    twitter_image: str | None = None
    twitter_creator: str | None = None

    # Schema.org/JSON-LD
    schema_type: str | None = None
    schema_data: dict[str, Any] = field(default_factory=dict)

    # Dublin Core
    dc_title: str | None = None
    dc_creator: str | None = None
    dc_date: str | None = None
    dc_description: str | None = None
    dc_subject: list[str] = field(default_factory=list)

    # Web archive (F-038 compatibility)
    original_url: str | None = None
    archive_date: datetime | None = None

    # Keywords and tags
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Canonical URL
    canonical_url: str | None = None

    def get_best_title(self) -> str | None:
        """Get best available title with priority resolution."""
        return (
            self.og_title
            or self.twitter_title
            or self.dc_title
            or self.title
            or self._get_schema_value("headline")
            or self._get_schema_value("name")
        )

    def get_best_description(self) -> str | None:
        """Get best available description with priority resolution."""
        return (
            self.og_description
            or self.twitter_description
            or self.dc_description
            or self.description
            or self._get_schema_value("description")
        )

    def get_best_author(self) -> str | None:
        """Get best available author with priority resolution."""
        author = self.author or self.dc_creator or self.twitter_creator

        # Try Schema.org author
        if not author and self.schema_data:
            schema_author = self._get_schema_value("author")
            if isinstance(schema_author, dict):
                author = schema_author.get("name")
            elif isinstance(schema_author, str):
                author = schema_author

        return author

    def get_best_image(self) -> str | None:
        """Get best available image URL."""
        return (
            self.og_image
            or self.twitter_image
            or self._get_schema_value("image")
        )

    def get_best_date(self) -> datetime | None:
        """Get best available publication date."""
        if self.publication_date:
            return self.publication_date

        # Try Schema.org dates
        for date_field in ["datePublished", "dateCreated", "dateModified"]:
            date_str = self._get_schema_value(date_field)
            if date_str:
                parsed = _parse_date(date_str)
                if parsed:
                    return parsed

        # Try Dublin Core
        if self.dc_date:
            parsed = _parse_date(self.dc_date)
            if parsed:
                return parsed

        return None

    def _get_schema_value(self, key: str) -> Any:
        """Get value from Schema.org data."""
        return self.schema_data.get(key)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "title": self.get_best_title(),
            "description": self.get_best_description(),
            "author": self.get_best_author(),
            "language": self.language,
            "publication_date": (
                self.get_best_date().isoformat() if self.get_best_date() else None
            ),
            "image": self.get_best_image(),
            "og_type": self.og_type,
            "site_name": self.og_site_name,
            "schema_type": self.schema_type,
            "keywords": self.keywords,
            "tags": self.tags,
            "canonical_url": self.canonical_url,
            "original_url": self.original_url,
            "archive_date": (
                self.archive_date.isoformat() if self.archive_date else None
            ),
        }


def extract_metadata(html: str) -> HTMLMetadata:
    """Extract rich metadata from HTML document.

    Uses selectolax if available, falls back to BeautifulSoup.

    Args:
        html: HTML content

    Returns:
        HTMLMetadata with extracted information
    """
    if SELECTOLAX_AVAILABLE:
        return _extract_with_selectolax(html)
    elif BEAUTIFULSOUP_AVAILABLE:
        return _extract_with_beautifulsoup(html)
    else:
        return _extract_with_regex(html)


def _extract_with_selectolax(html: str) -> HTMLMetadata:
    """Extract metadata using selectolax."""
    tree = SelectolaxParser(html)
    metadata = HTMLMetadata()

    # Basic meta tags
    metadata.title = _get_tag_text(tree, "title")
    metadata.description = _get_meta_content(tree, "description")
    metadata.author = _get_meta_content(tree, "author")
    metadata.keywords = _parse_keywords(_get_meta_content(tree, "keywords"))

    # Language
    html_tag = tree.css_first("html")
    if html_tag:
        metadata.language = html_tag.attributes.get("lang")

    # Canonical URL
    canonical = tree.css_first('link[rel="canonical"]')
    if canonical:
        metadata.canonical_url = canonical.attributes.get("href")

    # Open Graph
    metadata.og_title = _get_meta_property(tree, "og:title")
    metadata.og_description = _get_meta_property(tree, "og:description")
    metadata.og_image = _get_meta_property(tree, "og:image")
    metadata.og_type = _get_meta_property(tree, "og:type")
    metadata.og_site_name = _get_meta_property(tree, "og:site_name")
    metadata.og_url = _get_meta_property(tree, "og:url")

    # Twitter Cards
    metadata.twitter_card = _get_meta_name(tree, "twitter:card")
    metadata.twitter_title = _get_meta_name(tree, "twitter:title")
    metadata.twitter_description = _get_meta_name(tree, "twitter:description")
    metadata.twitter_image = _get_meta_name(tree, "twitter:image")
    metadata.twitter_creator = _get_meta_name(tree, "twitter:creator")

    # Dublin Core
    metadata.dc_title = _get_meta_name(tree, "DC.title") or _get_meta_name(tree, "dc.title")
    metadata.dc_creator = _get_meta_name(tree, "DC.creator") or _get_meta_name(tree, "dc.creator")
    metadata.dc_date = _get_meta_name(tree, "DC.date") or _get_meta_name(tree, "dc.date")
    metadata.dc_description = _get_meta_name(tree, "DC.description") or _get_meta_name(tree, "dc.description")

    # Dublin Core subjects (can be multiple)
    for tag in tree.css('meta[name="DC.subject"], meta[name="dc.subject"]'):
        content = tag.attributes.get("content")
        if content:
            metadata.dc_subject.append(content)

    # JSON-LD/Schema.org
    for script in tree.css('script[type="application/ld+json"]'):
        text = script.text()
        if text:
            schema_data = _parse_jsonld(text)
            if schema_data:
                metadata.schema_data = schema_data
                metadata.schema_type = schema_data.get("@type")
                break

    # Publication date from various sources
    date_str = (
        _get_meta_property(tree, "article:published_time")
        or _get_meta_name(tree, "date")
        or _get_meta_name(tree, "pubdate")
    )
    if date_str:
        metadata.publication_date = _parse_date(date_str)

    # Modified date
    modified_str = _get_meta_property(tree, "article:modified_time")
    if modified_str:
        metadata.modified_date = _parse_date(modified_str)

    # Article tags
    for tag in tree.css('meta[property="article:tag"]'):
        content = tag.attributes.get("content")
        if content:
            metadata.tags.append(content)

    # SingleFile archive metadata
    url_meta = tree.css_first('meta[name="savepage-url"]')
    if url_meta:
        metadata.original_url = url_meta.attributes.get("content")

    date_meta = tree.css_first('meta[name="savepage-date"]')
    if date_meta:
        date_str = date_meta.attributes.get("content", "")
        metadata.archive_date = _parse_date(date_str)

    return metadata


def _extract_with_beautifulsoup(html: str) -> HTMLMetadata:
    """Extract metadata using BeautifulSoup (fallback)."""
    soup = BeautifulSoup(html, "html.parser")
    metadata = HTMLMetadata()

    # Basic meta tags
    if soup.title:
        metadata.title = soup.title.get_text(strip=True)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        metadata.description = desc_tag.get("content")

    author_tag = soup.find("meta", attrs={"name": "author"})
    if author_tag:
        metadata.author = author_tag.get("content")

    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if keywords_tag:
        metadata.keywords = _parse_keywords(keywords_tag.get("content"))

    # Language
    html_tag = soup.find("html")
    if html_tag:
        metadata.language = html_tag.get("lang")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical:
        metadata.canonical_url = canonical.get("href")

    # Open Graph
    for prop in ["title", "description", "image", "type", "site_name", "url"]:
        tag = soup.find("meta", property=f"og:{prop}")
        if tag:
            setattr(metadata, f"og_{prop.replace('_', '')}" if prop != "site_name" else "og_site_name",
                   tag.get("content"))

    # Twitter Cards
    for name in ["card", "title", "description", "image", "creator"]:
        tag = soup.find("meta", attrs={"name": f"twitter:{name}"})
        if tag:
            setattr(metadata, f"twitter_{name}", tag.get("content"))

    # Dublin Core
    for dc_name in ["title", "creator", "date", "description"]:
        tag = soup.find("meta", attrs={"name": re.compile(f"^[Dd][Cc]\\.{dc_name}$")})
        if tag:
            setattr(metadata, f"dc_{dc_name}", tag.get("content"))

    # JSON-LD
    script = soup.find("script", type="application/ld+json")
    if script:
        schema_data = _parse_jsonld(script.string or "")
        if schema_data:
            metadata.schema_data = schema_data
            metadata.schema_type = schema_data.get("@type")

    # Publication date
    date_tag = soup.find("meta", property="article:published_time")
    if date_tag:
        metadata.publication_date = _parse_date(date_tag.get("content"))

    # SingleFile metadata
    url_meta = soup.find("meta", attrs={"name": "savepage-url"})
    if url_meta:
        metadata.original_url = url_meta.get("content")

    date_meta = soup.find("meta", attrs={"name": "savepage-date"})
    if date_meta:
        metadata.archive_date = _parse_date(date_meta.get("content"))

    return metadata


def _extract_with_regex(html: str) -> HTMLMetadata:
    """Extract basic metadata using regex (last resort fallback)."""
    metadata = HTMLMetadata()

    # Title
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if title_match:
        metadata.title = title_match.group(1).strip()

    # Description
    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if desc_match:
        metadata.description = desc_match.group(1)

    # Author
    author_match = re.search(
        r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if author_match:
        metadata.author = author_match.group(1)

    # Open Graph title
    og_title_match = re.search(
        r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if og_title_match:
        metadata.og_title = og_title_match.group(1)

    return metadata


def _get_tag_text(tree: Any, tag_name: str) -> str | None:
    """Get text content of a tag using selectolax."""
    tag = tree.css_first(tag_name)
    if tag:
        return tag.text(strip=True)
    return None


def _get_meta_content(tree: Any, name: str) -> str | None:
    """Get meta tag content by name attribute."""
    tag = tree.css_first(f'meta[name="{name}"]')
    if tag:
        return tag.attributes.get("content")
    return None


def _get_meta_property(tree: Any, prop: str) -> str | None:
    """Get meta tag content by property attribute (Open Graph)."""
    tag = tree.css_first(f'meta[property="{prop}"]')
    if tag:
        return tag.attributes.get("content")
    return None


def _get_meta_name(tree: Any, name: str) -> str | None:
    """Get meta tag content by name attribute (case-sensitive)."""
    tag = tree.css_first(f'meta[name="{name}"]')
    if tag:
        return tag.attributes.get("content")
    return None


def _parse_keywords(keywords_str: str | None) -> list[str]:
    """Parse comma-separated keywords string."""
    if not keywords_str:
        return []
    return [k.strip() for k in keywords_str.split(",") if k.strip()]


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse date string in various formats."""
    if not date_str:
        return None

    # ISO 8601 formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    # Handle Z suffix
    date_str = date_str.replace("Z", "+00:00")

    for fmt in formats:
        try:
            return datetime.strptime(date_str.split("+")[0].split(".")[0], fmt.replace("%z", ""))
        except ValueError:
            continue

    # Try ISO format as last resort
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def _parse_jsonld(json_str: str) -> dict[str, Any]:
    """Parse JSON-LD data, handling @graph arrays.

    Args:
        json_str: JSON-LD string

    Returns:
        Parsed JSON-LD data (flattened if @graph present)
    """
    try:
        data = json.loads(json_str)

        # Handle @graph array - find the main item
        if isinstance(data, dict) and "@graph" in data:
            graph = data["@graph"]
            if isinstance(graph, list):
                # Prefer Article, NewsArticle, BlogPosting types
                for item in graph:
                    if isinstance(item, dict):
                        item_type = item.get("@type", "")
                        if item_type in ["Article", "NewsArticle", "BlogPosting", "WebPage"]:
                            return item
                # Return first item if no preferred type found
                if graph:
                    return graph[0] if isinstance(graph[0], dict) else {}

        return data if isinstance(data, dict) else {}

    except json.JSONDecodeError:
        logger.debug("Failed to parse JSON-LD: invalid JSON")
        return {}
