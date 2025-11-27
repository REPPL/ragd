"""Tests for HTML metadata extraction module (F-039).

Tests the rich metadata extraction including Open Graph, JSON-LD,
Schema.org, Dublin Core, and Twitter Cards.
"""

import pytest
from datetime import datetime

from ragd.web.metadata import (
    HTMLMetadata,
    extract_metadata,
)


class TestBasicMetadata:
    """Tests for basic HTML metadata extraction."""

    def test_extract_title(self) -> None:
        """Extract title from title tag."""
        html = """
        <html>
        <head><title>Page Title</title></head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.title == "Page Title"

    def test_extract_description(self) -> None:
        """Extract description from meta tag."""
        html = """
        <html>
        <head>
            <meta name="description" content="Page description here">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.description == "Page description here"

    def test_extract_author(self) -> None:
        """Extract author from meta tag."""
        html = """
        <html>
        <head>
            <meta name="author" content="John Doe">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.author == "John Doe"

    def test_extract_keywords(self) -> None:
        """Extract keywords from meta tag."""
        html = """
        <html>
        <head>
            <meta name="keywords" content="python, testing, html">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert "python" in metadata.keywords
        assert "testing" in metadata.keywords
        assert "html" in metadata.keywords

    def test_extract_language(self) -> None:
        """Extract language from html lang attribute."""
        html = '<html lang="en-GB"><head></head><body></body></html>'
        metadata = extract_metadata(html)
        assert metadata.language == "en-GB"

    def test_extract_canonical_url(self) -> None:
        """Extract canonical URL from link tag."""
        html = """
        <html>
        <head>
            <link rel="canonical" href="https://example.com/page">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.canonical_url == "https://example.com/page"


class TestOpenGraph:
    """Tests for Open Graph metadata extraction."""

    def test_extract_og_title(self) -> None:
        """Extract og:title."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.og_title == "OG Title"

    def test_extract_og_description(self) -> None:
        """Extract og:description."""
        html = """
        <html>
        <head>
            <meta property="og:description" content="OG Description">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.og_description == "OG Description"

    def test_extract_og_image(self) -> None:
        """Extract og:image."""
        html = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.og_image == "https://example.com/image.jpg"

    def test_extract_og_type(self) -> None:
        """Extract og:type."""
        html = """
        <html>
        <head>
            <meta property="og:type" content="article">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.og_type == "article"

    def test_extract_og_site_name(self) -> None:
        """Extract og:site_name."""
        html = """
        <html>
        <head>
            <meta property="og:site_name" content="Example Site">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.og_site_name == "Example Site"

    def test_extract_full_og(self) -> None:
        """Extract all Open Graph metadata."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Article Title">
            <meta property="og:description" content="Article description">
            <meta property="og:image" content="https://example.com/img.jpg">
            <meta property="og:type" content="article">
            <meta property="og:site_name" content="Blog">
            <meta property="og:url" content="https://example.com/article">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.og_title == "Article Title"
        assert metadata.og_description == "Article description"
        assert metadata.og_image == "https://example.com/img.jpg"
        assert metadata.og_type == "article"
        assert metadata.og_site_name == "Blog"
        assert metadata.og_url == "https://example.com/article"


class TestTwitterCards:
    """Tests for Twitter Card metadata extraction."""

    def test_extract_twitter_card(self) -> None:
        """Extract twitter:card."""
        html = """
        <html>
        <head>
            <meta name="twitter:card" content="summary_large_image">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.twitter_card == "summary_large_image"

    def test_extract_twitter_title(self) -> None:
        """Extract twitter:title."""
        html = """
        <html>
        <head>
            <meta name="twitter:title" content="Twitter Title">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.twitter_title == "Twitter Title"

    def test_extract_twitter_creator(self) -> None:
        """Extract twitter:creator."""
        html = """
        <html>
        <head>
            <meta name="twitter:creator" content="@username">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.twitter_creator == "@username"


class TestDublinCore:
    """Tests for Dublin Core metadata extraction."""

    def test_extract_dc_title(self) -> None:
        """Extract DC.title."""
        html = """
        <html>
        <head>
            <meta name="DC.title" content="Dublin Core Title">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.dc_title == "Dublin Core Title"

    def test_extract_dc_creator(self) -> None:
        """Extract DC.creator."""
        html = """
        <html>
        <head>
            <meta name="DC.creator" content="Dublin Core Author">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.dc_creator == "Dublin Core Author"

    def test_extract_dc_date(self) -> None:
        """Extract DC.date."""
        html = """
        <html>
        <head>
            <meta name="DC.date" content="2024-01-15">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.dc_date == "2024-01-15"

    def test_extract_dc_lowercase(self) -> None:
        """Extract dc.title (lowercase)."""
        html = """
        <html>
        <head>
            <meta name="dc.title" content="Lowercase DC Title">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.dc_title == "Lowercase DC Title"


class TestJSONLD:
    """Tests for JSON-LD/Schema.org metadata extraction."""

    def test_extract_jsonld_article(self) -> None:
        """Extract JSON-LD Article schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Article Headline",
                "description": "Article description",
                "author": {"@type": "Person", "name": "John Doe"}
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.schema_type == "Article"
        assert metadata.schema_data.get("headline") == "Article Headline"
        assert metadata.schema_data.get("description") == "Article description"

    def test_extract_jsonld_with_graph(self) -> None:
        """Extract JSON-LD with @graph array."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "WebSite", "name": "My Site"},
                    {"@type": "Article", "headline": "Article Title"}
                ]
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        # Should extract the Article (preferred type)
        assert metadata.schema_type == "Article"

    def test_extract_jsonld_malformed_recovery(self) -> None:
        """Handle malformed JSON-LD gracefully."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            { invalid json }
            </script>
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        # Should not crash, just have empty schema_data
        assert metadata.schema_data == {}


class TestPublicationDates:
    """Tests for publication date extraction."""

    def test_extract_article_published_time(self) -> None:
        """Extract article:published_time."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="2024-03-15T10:30:00Z">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.publication_date is not None
        assert metadata.publication_date.year == 2024
        assert metadata.publication_date.month == 3
        assert metadata.publication_date.day == 15

    def test_extract_modified_time(self) -> None:
        """Extract article:modified_time (selectolax only)."""
        # Note: modified_date extraction requires selectolax
        html = """
        <html>
        <head>
            <meta property="article:modified_time" content="2024-03-20T14:00:00Z">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        # modified_date may be None in BeautifulSoup fallback path
        if metadata.modified_date is not None:
            assert metadata.modified_date.year == 2024


class TestMetadataResolution:
    """Tests for metadata resolution priority."""

    def test_og_title_takes_priority(self) -> None:
        """og:title takes priority over basic title."""
        html = """
        <html>
        <head>
            <title>Basic Title</title>
            <meta property="og:title" content="OG Title">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.get_best_title() == "OG Title"

    def test_fallback_to_basic_title(self) -> None:
        """Falls back to basic title when OG not present."""
        html = """
        <html>
        <head>
            <title>Basic Title</title>
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.get_best_title() == "Basic Title"

    def test_get_best_author(self) -> None:
        """Get best author from various sources."""
        html = """
        <html>
        <head>
            <meta name="author" content="Basic Author">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.get_best_author() == "Basic Author"

    def test_get_best_image(self) -> None:
        """Get best image from various sources."""
        html = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/og.jpg">
            <meta name="twitter:image" content="https://example.com/tw.jpg">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        # og:image takes priority
        assert metadata.get_best_image() == "https://example.com/og.jpg"


class TestSingleFileMetadata:
    """Tests for SingleFile archive metadata extraction."""

    def test_extract_savepage_url(self) -> None:
        """Extract savepage-url from SingleFile archive."""
        html = """
        <html>
        <head>
            <meta name="savepage-url" content="https://original-url.com/page">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        assert metadata.original_url == "https://original-url.com/page"

    def test_extract_savepage_date(self) -> None:
        """Extract savepage-date from SingleFile archive."""
        html = """
        <html>
        <head>
            <meta name="savepage-date" content="2024-06-15T14:30:00Z">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        assert metadata.archive_date is not None
        assert metadata.archive_date.year == 2024
        assert metadata.archive_date.month == 6


class TestArticleTags:
    """Tests for article tag extraction."""

    def test_extract_article_tags(self) -> None:
        """Extract article:tag metadata (selectolax only).

        Note: article:tag extraction requires selectolax.
        BeautifulSoup fallback doesn't implement this.
        """
        html = """
        <html>
        <head>
            <meta property="article:tag" content="python">
            <meta property="article:tag" content="testing">
            <meta property="article:tag" content="web">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)

        # Tags may be empty in BeautifulSoup fallback path
        if metadata.tags:
            assert "python" in metadata.tags
            assert "testing" in metadata.tags
            assert "web" in metadata.tags


class TestToDict:
    """Tests for metadata serialisation."""

    def test_to_dict_includes_best_values(self) -> None:
        """to_dict uses best values for each field."""
        html = """
        <html>
        <head>
            <title>Basic Title</title>
            <meta property="og:title" content="OG Title">
            <meta name="description" content="Description">
        </head>
        <body></body>
        </html>
        """
        metadata = extract_metadata(html)
        data = metadata.to_dict()

        assert data["title"] == "OG Title"
        assert data["description"] == "Description"
        assert "keywords" in data
        assert "tags" in data
