# ADR-0015: Web Archive Processing Architecture

## Status

Accepted

## Context

Users save web pages for offline reference using browser extensions like SingleFile. These archives become unsearchable silos - users must manually browse saved files or remember where specific content was stored.

ragd can index these archives like any other document, but web archives have unique characteristics:
- Self-contained HTML with embedded resources
- Original URL and archive date metadata
- Content mixed with navigation, ads, and boilerplate
- Often saved with different filenames than the article title

To provide a good search experience, ragd needs to:
1. Detect web archive format
2. Extract original URL and archive date
3. Strip boilerplate to extract main content
4. Generate clean "reader view" for display
5. Preserve attribution to original source

## Decision

Support **SingleFile HTML as the primary web archive format** with **trafilatura for content extraction** and **reader view generation**.

### Processing Pipeline

```
SingleFile HTML
       │
       ▼
┌──────────────────┐
│  Format Detection │◄── Check for savepage-url meta tag
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Metadata Extract  │◄── Original URL, archive date, title
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Content Extract   │◄── trafilatura (best precision/recall)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Reader View Gen   │◄── Clean HTML template
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Index Content    │◄── Markdown to chunks to embeddings
└──────────────────┘
```

### SingleFile Detection

SingleFile embeds metadata in HTML:

```html
<meta name="savepage-url" content="https://example.com/article">
<meta name="savepage-date" content="2025-01-15T10:30:00Z">
```

Detection:

```python
from selectolax.parser import HTMLParser

def is_singlefile_archive(html: str) -> bool:
    """Detect if HTML is a SingleFile archive."""
    tree = HTMLParser(html)
    url_meta = tree.css_first('meta[name="savepage-url"]')
    return url_meta is not None
```

### Content Extraction

Using trafilatura (best-in-class for article extraction):

```python
import trafilatura

def extract_web_content(html: str) -> dict:
    """Extract main content from web archive."""
    # Full extraction with metadata
    result = trafilatura.bare_extraction(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )

    return {
        "title": result.get("title"),
        "author": result.get("author"),
        "date": result.get("date"),
        "text": result.get("text"),
        "language": result.get("language"),
    }

def extract_as_markdown(html: str) -> str:
    """Extract content as Markdown for indexing."""
    return trafilatura.extract(html, output_format="markdown")
```

### Library Selection

| Task | Library | Rationale |
|------|---------|-----------|
| HTML Parsing | selectolax | 10-100x faster than BeautifulSoup |
| Content Extraction | trafilatura | Best precision/recall in benchmarks |
| Markdown Conversion | trafilatura | Integrated output format |

**Phased Introduction:**
- v0.1: BeautifulSoup (already dependency)
- v0.2: Add trafilatura + selectolax

### Reader View Storage

Generated reader views stored at `~/.ragd/reader_views/{doc_id}.html`:

```python
READER_VIEW_TEMPLATE = '''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="utf-8">
    <meta name="ragd-document-id" content="{doc_id}">
    <meta name="ragd-original-url" content="{original_url}">
    <meta name="ragd-archive-date" content="{archive_date}">
    <title>{title} - ragd Reader View</title>
    <style>
        body {
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            font-family: Georgia, serif;
            line-height: 1.7;
        }
        .ragd-header {
            border-bottom: 1px solid #ddd;
            margin-bottom: 2em;
        }
        .ragd-meta { color: #666; font-size: 0.9em; }
        @media (prefers-color-scheme: dark) {
            body { background: #1a1a1a; color: #e0e0e0; }
        }
    </style>
</head>
<body>
    <header class="ragd-header">
        <h1>{title}</h1>
        <p class="ragd-meta">
            <a href="{original_url}">View original</a>
            {archive_info}
        </p>
    </header>
    <article>{content}</article>
</body>
</html>'''
```

### Document Metadata Schema

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class WebArchiveDocument:
    """Metadata for indexed web archive."""
    id: str
    source_file: Path
    original_url: str | None
    archive_date: datetime | None
    title: str
    author: str | None
    content_type: str = "web_archive"
    reader_view_path: Path | None = None
```

### Search Result Attribution

```
ragd search "machine learning"

Results
─────────────────────────────────────────────────────────

1. Introduction to Neural Networks
   ~/Archives/deep-learning.html
   Original: https://example.com/neural-networks
   Archived: 2025-01-15

   "...backpropagation is the key algorithm for training..."
```

## Consequences

### Positive

- Semantic search across saved web pages
- Original source attribution preserved
- Clean reader view for distraction-free reading
- Integrates with watch folder for automatic indexing
- Standard HTML processing (no special format handlers)

### Negative

- SingleFile-specific (other formats not supported initially)
- trafilatura adds ~10MB dependency
- Reader view storage uses additional disk space
- Content extraction not perfect (may miss some layouts)

## Alternatives Considered

### MHTML Format

- **Pros:** Standard format, Chrome support
- **Cons:** Chrome-only, larger files, complex parsing
- **Rejected:** Less portable than SingleFile HTML

### WARC Format

- **Pros:** Industry standard for web archiving
- **Cons:** Complex format, overkill for personal use
- **Rejected:** Designed for institutional archives

### Readability.js (Mozilla)

- **Pros:** Powers Firefox Reader View, proven
- **Cons:** Requires Node.js runtime
- **Rejected:** Python-native solution preferred

### BeautifulSoup + Custom Extraction

- **Pros:** No new dependencies
- **Cons:** Significant development effort, lower quality
- **Rejected:** trafilatura is purpose-built and benchmarked

### Store Only Extracted Text

- **Pros:** Simpler, less storage
- **Cons:** Loses formatting, can't generate reader view
- **Rejected:** Reader view important for UX

## Related Documentation

- [State-of-the-Art HTML Processing](../../research/state-of-the-art-html-processing.md)
- [F-038: Web Archive Support](../../features/completed/F-038-web-archive-support.md)
- [F-037: Watch Folder](../../features/completed/F-037-watch-folder.md)
- [ADR-0014: Daemon Process Management](./0014-daemon-management.md)
