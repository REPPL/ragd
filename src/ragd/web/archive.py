"""Web archive support for ragd.

This module implements F-038: Web Archive Support, enabling indexing
and searching of saved web pages (SingleFile archives).
"""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser as StdHTMLParser
from pathlib import Path
from typing import Any

from ragd.features import DependencyError

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    from selectolax.parser import HTMLParser

    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False

try:
    import trafilatura

    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False


@dataclass
class WebArchiveMetadata:
    """Metadata extracted from a web archive.

    Contains information about the original source, archive date,
    and extracted content attributes.
    """

    source_file: Path
    original_url: str | None = None
    archive_date: datetime | None = None
    title: str = ""
    author: str | None = None
    publication_date: datetime | None = None
    word_count: int = 0
    language: str | None = None
    description: str | None = None
    sitename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_file": str(self.source_file),
            "original_url": self.original_url,
            "archive_date": self.archive_date.isoformat() if self.archive_date else None,
            "title": self.title,
            "author": self.author,
            "publication_date": (
                self.publication_date.isoformat() if self.publication_date else None
            ),
            "word_count": self.word_count,
            "language": self.language,
            "description": self.description,
            "sitename": self.sitename,
        }


@dataclass
class ExtractedWebContent:
    """Content extracted from a web archive."""

    text: str
    html: str = ""
    title: str = ""
    metadata: WebArchiveMetadata | None = None
    success: bool = True
    error: str | None = None


class SimpleHTMLTextExtractor(StdHTMLParser):
    """Simple HTML to text converter using stdlib."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.skip_tags = {"script", "style", "head", "nav", "footer", "aside"}
        self.block_tags = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br"}
        self._in_skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.skip_tags:
            self._in_skip += 1
        elif tag.lower() in self.block_tags and self.text_parts:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.skip_tags:
            self._in_skip = max(0, self._in_skip - 1)
        elif tag.lower() in self.block_tags:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_skip == 0:
            text = data.strip()
            if text:
                self.text_parts.append(text + " ")

    def get_text(self) -> str:
        """Get extracted text."""
        text = "".join(self.text_parts)
        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)
        return text.strip()


def is_singlefile_archive(html_content: str) -> bool:
    """Detect if HTML is a SingleFile archive.

    SingleFile archives contain specific meta tags that identify them:
    - savepage-url: Original page URL
    - savepage-date: When the page was archived

    Args:
        html_content: HTML content to check

    Returns:
        True if this appears to be a SingleFile archive
    """
    html_lower = html_content[:10000].lower()  # Check first 10KB for efficiency

    # Check for SingleFile metadata tags
    return (
        'name="savepage-url"' in html_lower
        or 'name="savepage-date"' in html_lower
        or "singlefile" in html_lower
    )


def extract_singlefile_metadata(html_content: str, path: Path) -> WebArchiveMetadata:
    """Extract metadata from SingleFile HTML archive.

    Args:
        html_content: HTML content of archive
        path: Path to the archive file

    Returns:
        WebArchiveMetadata with extracted information
    """
    metadata = WebArchiveMetadata(source_file=path, title=path.stem)

    if SELECTOLAX_AVAILABLE:
        metadata = _extract_with_selectolax(html_content, path)
    else:
        metadata = _extract_with_regex(html_content, path)

    # Use trafilatura for additional metadata if available
    if TRAFILATURA_AVAILABLE:
        try:
            result = trafilatura.bare_extraction(html_content)
            if result:
                if not metadata.title and result.get("title"):
                    metadata.title = result["title"]
                if not metadata.author and result.get("author"):
                    metadata.author = result["author"]
                if not metadata.language and result.get("language"):
                    metadata.language = result["language"]
                if result.get("date"):
                    try:
                        metadata.publication_date = datetime.fromisoformat(
                            result["date"]
                        )
                    except (ValueError, TypeError):
                        pass
                if result.get("description"):
                    metadata.description = result["description"]
                if result.get("sitename"):
                    metadata.sitename = result["sitename"]
        except Exception as e:
            logger.warning("trafilatura extraction failed: %s", e)

    return metadata


def _extract_with_selectolax(html_content: str, path: Path) -> WebArchiveMetadata:
    """Extract metadata using selectolax."""
    tree = HTMLParser(html_content)
    metadata = WebArchiveMetadata(source_file=path)

    # SingleFile metadata
    url_meta = tree.css_first('meta[name="savepage-url"]')
    if url_meta:
        metadata.original_url = url_meta.attributes.get("content")

    date_meta = tree.css_first('meta[name="savepage-date"]')
    if date_meta:
        date_str = date_meta.attributes.get("content", "")
        try:
            metadata.archive_date = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    # Standard HTML metadata
    title_tag = tree.css_first("title")
    if title_tag:
        metadata.title = title_tag.text() or path.stem

    og_title = tree.css_first('meta[property="og:title"]')
    if og_title and not metadata.title:
        metadata.title = og_title.attributes.get("content", "") or path.stem

    author_meta = tree.css_first('meta[name="author"]')
    if author_meta:
        metadata.author = author_meta.attributes.get("content")

    return metadata


def _extract_with_regex(html_content: str, path: Path) -> WebArchiveMetadata:
    """Extract metadata using regex (fallback when selectolax unavailable)."""
    metadata = WebArchiveMetadata(source_file=path, title=path.stem)

    # Extract savepage-url
    url_match = re.search(
        r'<meta\s+name=["\']savepage-url["\']\s+content=["\']([^"\']+)["\']',
        html_content,
        re.IGNORECASE,
    )
    if url_match:
        metadata.original_url = url_match.group(1)

    # Extract savepage-date
    date_match = re.search(
        r'<meta\s+name=["\']savepage-date["\']\s+content=["\']([^"\']+)["\']',
        html_content,
        re.IGNORECASE,
    )
    if date_match:
        try:
            metadata.archive_date = datetime.fromisoformat(
                date_match.group(1).replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    # Extract title
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html_content, re.IGNORECASE)
    if title_match:
        metadata.title = html.unescape(title_match.group(1).strip())

    # Extract author
    author_match = re.search(
        r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']+)["\']',
        html_content,
        re.IGNORECASE,
    )
    if author_match:
        metadata.author = author_match.group(1)

    return metadata


def extract_web_content(html_content: str, path: Path) -> ExtractedWebContent:
    """Extract text content from a web archive.

    Uses trafilatura for best results, falls back to simple extraction
    if trafilatura is not available.

    Args:
        html_content: HTML content of archive
        path: Path to the archive file

    Returns:
        ExtractedWebContent with text and metadata
    """
    try:
        # Extract metadata
        metadata = extract_singlefile_metadata(html_content, path)

        # Extract text content
        if TRAFILATURA_AVAILABLE:
            text = trafilatura.extract(
                html_content,
                include_tables=True,
                include_links=True,
                include_images=False,
                output_format="txt",
            )
            if text:
                metadata.word_count = len(text.split())
                return ExtractedWebContent(
                    text=text,
                    title=metadata.title,
                    metadata=metadata,
                    success=True,
                )

        # Fallback to simple extraction
        extractor = SimpleHTMLTextExtractor()
        extractor.feed(html_content)
        text = extractor.get_text()
        metadata.word_count = len(text.split())

        return ExtractedWebContent(
            text=text,
            title=metadata.title,
            metadata=metadata,
            success=True,
        )

    except Exception as e:
        logger.exception("Failed to extract web content: %s", e)
        return ExtractedWebContent(
            text="",
            success=False,
            error=str(e),
        )


# Reader view template
READER_VIEW_TEMPLATE = '''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="ragd-document-id" content="{doc_id}">
    <meta name="ragd-original-url" content="{original_url}">
    <meta name="ragd-archive-date" content="{archive_date}">
    <meta name="ragd-source-file" content="{source_file}">
    <title>{title} - ragd Reader View</title>
    <style>
        :root {{
            --text-color: #1a1a1a;
            --bg-color: #fafafa;
            --link-color: #0066cc;
            --meta-color: #666;
            --border-color: #ddd;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --text-color: #e0e0e0;
                --bg-color: #1a1a1a;
                --link-color: #6db3f2;
                --meta-color: #999;
                --border-color: #333;
            }}
        }}
        body {{
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            font-family: Georgia, "Times New Roman", serif;
            font-size: 18px;
            line-height: 1.7;
            color: var(--text-color);
            background: var(--bg-color);
        }}
        .ragd-header {{
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2em;
            padding-bottom: 1em;
        }}
        h1 {{
            font-size: 1.8em;
            line-height: 1.3;
            margin-bottom: 0.5em;
        }}
        .ragd-meta {{
            font-size: 0.85em;
            color: var(--meta-color);
        }}
        .ragd-meta a {{
            color: var(--link-color);
        }}
        article {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        article a {{
            color: var(--link-color);
        }}
    </style>
</head>
<body>
    <header class="ragd-header">
        <h1>{title}</h1>
        <div class="ragd-meta">
            {author_line}
            <p>
                {original_link}
                {archive_date_line}
            </p>
        </div>
    </header>
    <article>
{content}
    </article>
</body>
</html>'''


def generate_reader_view(
    doc_id: str,
    metadata: WebArchiveMetadata,
    content_text: str,
) -> str:
    """Generate a reader view HTML page.

    Args:
        doc_id: Document identifier
        metadata: Archive metadata
        content_text: Extracted text content

    Returns:
        HTML string for reader view
    """
    author_line = f"<p>By {html.escape(metadata.author)}</p>" if metadata.author else ""

    archive_date_line = ""
    if metadata.archive_date:
        archive_date_line = (
            f" &middot; Archived {metadata.archive_date.strftime('%d %B %Y')}"
        )

    original_link = ""
    if metadata.original_url:
        original_link = f'<a href="{html.escape(metadata.original_url)}">View original</a>'

    # Escape content for HTML
    content_html = html.escape(content_text)

    return READER_VIEW_TEMPLATE.format(
        language=metadata.language or "en",
        doc_id=doc_id,
        original_url=html.escape(metadata.original_url or ""),
        archive_date=(
            metadata.archive_date.isoformat() if metadata.archive_date else ""
        ),
        source_file=html.escape(str(metadata.source_file)),
        title=html.escape(metadata.title),
        author_line=author_line,
        archive_date_line=archive_date_line,
        original_link=original_link,
        content=content_html,
    )


class WebArchiveProcessor:
    """Processor for web archive files.

    Handles detection, metadata extraction, and content extraction
    from SingleFile and other HTML archives.

    Example:
        >>> processor = WebArchiveProcessor()
        >>> result = processor.process(Path("article.html"))
        >>> print(result.metadata.original_url)
        https://example.com/article
    """

    def __init__(self, reader_view_dir: Path | None = None) -> None:
        """Initialise the processor.

        Args:
            reader_view_dir: Directory to store generated reader views.
                           Defaults to ~/.ragd/reader_views/
        """
        if reader_view_dir is None:
            reader_view_dir = Path.home() / ".ragd" / "reader_views"
        self._reader_view_dir = reader_view_dir
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def is_web_archive(self, path: Path) -> bool:
        """Check if file is a web archive.

        Args:
            path: Path to file

        Returns:
            True if file appears to be a web archive
        """
        if not path.exists():
            return False

        if path.suffix.lower() not in {".html", ".htm"}:
            return False

        try:
            # Read first 10KB to check
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
            return is_singlefile_archive(content)
        except Exception:
            return False

    def process(self, path: Path) -> ExtractedWebContent:
        """Process a web archive file.

        Args:
            path: Path to HTML archive

        Returns:
            ExtractedWebContent with text and metadata
        """
        if not path.exists():
            return ExtractedWebContent(
                text="",
                success=False,
                error=f"File not found: {path}",
            )

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

            return extract_web_content(html_content, path)

        except Exception as e:
            self._logger.exception("Failed to process %s: %s", path, e)
            return ExtractedWebContent(
                text="",
                success=False,
                error=str(e),
            )

    def generate_reader_view(
        self, doc_id: str, result: ExtractedWebContent
    ) -> Path | None:
        """Generate and save a reader view.

        Args:
            doc_id: Document identifier
            result: Extraction result with content and metadata

        Returns:
            Path to generated reader view, or None if failed
        """
        if not result.success or not result.metadata:
            return None

        try:
            self._reader_view_dir.mkdir(parents=True, exist_ok=True)

            html_content = generate_reader_view(
                doc_id,
                result.metadata,
                result.text,
            )

            output_path = self._reader_view_dir / f"{doc_id}.html"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return output_path

        except Exception as e:
            self._logger.exception("Failed to generate reader view: %s", e)
            return None
