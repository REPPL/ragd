# F-038: Web Archive Support

## Overview

**Use Case**: Index and search saved web pages
**Milestone**: v0.2
**Priority**: P1

## Problem Statement

Users save web pages for offline reference using browser extensions like SingleFile, but these archives become unsearchable silos. Without web archive support, users must manually search through saved HTML files or remember where they stored specific content. This is particularly painful for researchers, students, and knowledge workers who accumulate hundreds of saved articles.

## Design Approach

Support SingleFile HTML archives as a first-class document type, extracting content into a clean "reader view" format while preserving links to original sources.

**Command Interface:**

```bash
ragd index ~/Archives/article.html           # Index single archive
ragd index ~/Archives/*.html --type web      # Index multiple archives
ragd index ~/Archives/ --watch               # Watch folder for new archives
```

**Search Output:**

```
ragd search "neural network training"

Results
───────────────────────────────────────────────────────

1. Introduction to Deep Learning
   ~/Archives/deep-learning-intro.html
   Original: https://example.com/deep-learning-intro
   Archived: 2025-01-15

   "...backpropagation is the key algorithm for training
   neural networks. The gradient descent process..."

2. PyTorch Tutorial: Building Your First Model
   ~/Archives/pytorch-tutorial.html
   Original: https://pytorch.org/tutorials/beginner
   Archived: 2025-01-10

   "...neural network training requires careful
   initialisation of weights and proper..."
```

**Reader View Generation:**

```bash
ragd view ~/Archives/article.html            # Open reader view
ragd view --original ~/Archives/article.html # Open original URL
```

## Implementation Tasks

### Phase 1: SingleFile Parsing

- [ ] Detect SingleFile HTML format (via metadata tags)
- [ ] Extract original URL from `savepage-url` meta tag
- [ ] Extract archive date from `savepage-date` meta tag
- [ ] Handle data URI embedded images
- [ ] Parse preserved `data-savepage-href` attributes

### Phase 2: Content Extraction

- [ ] Integrate trafilatura for content extraction
- [ ] Extract article title, author, publication date
- [ ] Convert content to Markdown for indexing
- [ ] Preserve table structure
- [ ] Handle multi-page articles

### Phase 3: Reader View Storage

- [ ] Design reader view HTML template
- [ ] Generate clean reader view from extracted content
- [ ] Store reader view in `~/.ragd/reader_views/`
- [ ] Link reader view to original archive
- [ ] Link reader view to original URL

### Phase 4: Metadata & Search

- [ ] Store web archive metadata in document store
- [ ] Index original URL as searchable field
- [ ] Index archive date for filtering
- [ ] Include source attribution in search results
- [ ] Support `--type web` filter in search

### Phase 5: CLI Integration

- [ ] Add `--type web` option to `ragd index`
- [ ] Add `ragd view` command for reader view
- [ ] Add `--original` flag to open source URL
- [ ] Display archive metadata in search results

## Success Criteria

- [ ] SingleFile HTML archives indexed successfully
- [ ] Original URL preserved and displayed in results
- [ ] Archive date tracked and filterable
- [ ] Reader view generated for each archive
- [ ] Content extraction accuracy >90% (trafilatura benchmark)
- [ ] Processing time <2 seconds per archive

## Dependencies

- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Ingestion pipeline
- [F-002: Text Extraction](./F-002-text-extraction.md) - Text extraction base
- trafilatura library (content extraction)
- selectolax library (HTML parsing)

## Technical Notes

**SingleFile Detection:**

```python
from selectolax.parser import HTMLParser

def is_singlefile_archive(html: str) -> bool:
    """Detect if HTML is a SingleFile archive."""
    tree = HTMLParser(html)

    # Check for SingleFile metadata
    url_meta = tree.css_first('meta[name="savepage-url"]')
    date_meta = tree.css_first('meta[name="savepage-date"]')

    return url_meta is not None or date_meta is not None
```

**Metadata Extraction:**

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class WebArchiveMetadata:
    """Metadata extracted from SingleFile archive."""
    source_file: Path
    original_url: str | None
    archive_date: datetime | None
    title: str
    author: str | None
    publication_date: datetime | None
    word_count: int
    language: str | None

def extract_singlefile_metadata(html: str, path: Path) -> WebArchiveMetadata:
    """Extract metadata from SingleFile HTML."""
    tree = HTMLParser(html)

    # SingleFile metadata
    url_meta = tree.css_first('meta[name="savepage-url"]')
    date_meta = tree.css_first('meta[name="savepage-date"]')

    original_url = url_meta.attributes.get("content") if url_meta else None
    archive_date = None
    if date_meta:
        try:
            archive_date = datetime.fromisoformat(
                date_meta.attributes.get("content", "").replace("Z", "+00:00")
            )
        except ValueError:
            pass

    # Content extraction via trafilatura
    import trafilatura
    result = trafilatura.bare_extraction(html)

    return WebArchiveMetadata(
        source_file=path,
        original_url=original_url,
        archive_date=archive_date,
        title=result.get("title", path.stem),
        author=result.get("author"),
        publication_date=_parse_date(result.get("date")),
        word_count=len(result.get("text", "").split()),
        language=result.get("language"),
    )
```

**Reader View Template:**

```python
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
        article img {{
            max-width: 100%;
            height: auto;
        }}
        article a {{
            color: var(--link-color);
        }}
        pre, code {{
            font-family: "SF Mono", Menlo, monospace;
            font-size: 0.9em;
            background: rgba(128, 128, 128, 0.1);
            border-radius: 3px;
        }}
        pre {{
            padding: 1em;
            overflow-x: auto;
        }}
        code {{
            padding: 0.2em 0.4em;
        }}
        blockquote {{
            border-left: 3px solid var(--border-color);
            margin-left: 0;
            padding-left: 1em;
            color: var(--meta-color);
        }}
    </style>
</head>
<body>
    <header class="ragd-header">
        <h1>{title}</h1>
        <div class="ragd-meta">
            {author_line}
            <p>
                <a href="{original_url}">View original</a>
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
    content_html: str,
) -> str:
    """Generate reader view HTML."""
    author_line = f"<p>By {metadata.author}</p>" if metadata.author else ""
    archive_date_line = ""
    if metadata.archive_date:
        archive_date_line = f" · Archived {metadata.archive_date.strftime('%d %B %Y')}"

    return READER_VIEW_TEMPLATE.format(
        language=metadata.language or "en",
        doc_id=doc_id,
        original_url=metadata.original_url or "",
        archive_date=metadata.archive_date.isoformat() if metadata.archive_date else "",
        source_file=str(metadata.source_file),
        title=metadata.title,
        author_line=author_line,
        archive_date_line=archive_date_line,
        content=content_html,
    )
```

**Document Store Schema Extension:**

```python
# Additional fields for web archives
WEB_ARCHIVE_FIELDS = {
    "original_url": str,        # Source URL
    "archive_date": datetime,   # When archived
    "publication_date": datetime,  # When originally published
    "author": str,              # Article author
    "reader_view_path": Path,   # Path to generated reader view
    "content_type": "web_archive",
}
```

## Competitive Analysis

**ArchiveBox:**
- Full-featured self-hosted archiver
- Multiple output formats (SingleFile, PDF, WARC, screenshot)
- No semantic search
- Complex setup (Docker recommended)

**Zotero:**
- Academic reference manager
- Saves web snapshots
- Full-text search but not semantic
- Focused on citations

**ragd Advantages:**
- Semantic search across web archives
- Reader view with original source links
- Integrated with document corpus
- Simple CLI workflow
- Works with existing SingleFile archives

## Related Documentation

- [State-of-the-Art HTML Processing](../../research/state-of-the-art-html-processing.md) - Research on parsing and extraction
- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Base ingestion pipeline
- [F-037: Watch Folder](./F-037-watch-folder.md) - Auto-indexing for archive folders

---

**Status**: Completed
