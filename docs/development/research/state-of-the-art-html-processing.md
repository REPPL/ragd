# State-of-the-Art HTML Processing and Web Archiving

Strategies for HTML parsing, content extraction, and web archive handling in local RAG systems.

## Executive Summary

HTML processing for RAG involves three distinct challenges:

1. **Parsing**: Converting HTML to a navigable data structure
2. **Extraction**: Identifying and extracting the main content (reader view)
3. **Archiving**: Preserving web content for offline reference

BeautifulSoup remains the most beginner-friendly option, but **selectolax** offers 10-100x better performance. For content extraction, **trafilatura** consistently outperforms alternatives. For web archiving, **SingleFile** format provides self-contained HTML that can be processed with standard tools.

---

## Part 1: HTML Parsing Libraries

### Performance Comparison

| Library | Speed | Memory | Ease of Use | Best For |
|---------|-------|--------|-------------|----------|
| **selectolax** | Fastest | Low | Medium | Production, large documents |
| **lxml** | Fast | Medium | Medium | XPath/XSLT needs |
| **BeautifulSoup** | Slowest | High | Easiest | Prototyping, learning |
| **html5lib** | Slow | High | Easy | Browser-accurate parsing |
| **parsel** | Fast | Medium | Medium | Scrapy integration |

### Recommendation for ragd

**Primary:** Use **selectolax** for production HTML parsing.

**Rationale:**
- 10-100x faster than BeautifulSoup
- Built on Modest/Lexbor C engines
- CSS selector support
- Minimal memory footprint

```python
from selectolax.parser import HTMLParser

def parse_html(content: str) -> HTMLParser:
    """Fast HTML parsing with selectolax."""
    return HTMLParser(content)

def extract_text(html: str, selector: str = "body") -> str:
    """Extract text from HTML using CSS selector."""
    tree = HTMLParser(html)
    node = tree.css_first(selector)
    return node.text() if node else ""
```

### Library Details

#### selectolax

The fastest Python HTML parser, using Cython bindings to C libraries.

```python
from selectolax.parser import HTMLParser

tree = HTMLParser(html_content)

# CSS selectors
for node in tree.css("article p"):
    print(node.text())

# First match
title = tree.css_first("h1")
if title:
    print(title.text())
```

**Pros:**
- 10-100x faster than BeautifulSoup
- Low memory footprint
- CSS selector support
- Actively maintained

**Cons:**
- Less battle-tested than lxml/BeautifulSoup
- No XPath support
- Smaller community

#### lxml

The established high-performance parser with XPath support.

```python
from lxml import html

tree = html.fromstring(html_content)

# XPath queries
paragraphs = tree.xpath("//article//p/text()")

# CSS selectors (via cssselect)
from lxml.cssselect import CSSSelector
sel = CSSSelector("article p")
for elem in sel(tree):
    print(elem.text_content())
```

**Pros:**
- Fast (C-based)
- Full XPath/XSLT support
- Standards-compliant
- Very stable

**Cons:**
- Steeper learning curve
- C dependency (compilation required)
- Error messages can be cryptic

#### BeautifulSoup

The beginner-friendly parser with forgiving HTML handling.

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, "lxml")  # Use lxml parser

# Find elements
title = soup.find("h1").get_text()
paragraphs = soup.find_all("p")

# CSS selectors
articles = soup.select("article.main")
```

**Pros:**
- Very forgiving with malformed HTML
- Excellent documentation
- Largest community
- Multiple parser backends

**Cons:**
- Slowest option (3-10x slower than lxml)
- High memory usage
- Overkill for simple tasks

---

## Part 2: Content Extraction (Reader View)

### The Reader View Problem

Web pages contain navigation, ads, sidebars, and other "boilerplate" alongside the actual content. Reader view algorithms identify and extract only the main article content.

### Library Comparison

| Library | Precision | Recall | Speed | Maintenance |
|---------|-----------|--------|-------|-------------|
| **trafilatura** | Excellent | Excellent | Fast | Active |
| **readability-lxml** | Good | Good | Fast | Active |
| **newspaper4k** | Good | Medium | Slow | Active |
| **goose3** | Excellent | Low | Slow | Moderate |
| **boilerpy3** | Medium | Medium | Fast | Low |

### Recommendation for ragd

**Primary:** Use **trafilatura** for content extraction.

**Rationale:**
- Best precision/recall in academic benchmarks
- Fast performance
- Multiple output formats (text, markdown, XML)
- Extracts metadata (author, date, title)
- Actively maintained

```python
import trafilatura

def extract_article(html: str) -> dict:
    """Extract main content and metadata from HTML."""
    # Basic extraction
    text = trafilatura.extract(html)

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
        "url": result.get("url"),
    }

def extract_as_markdown(html: str) -> str:
    """Extract content as Markdown."""
    return trafilatura.extract(html, output_format="markdown")
```

### Library Details

#### trafilatura

The benchmark leader for web content extraction.

```python
import trafilatura

# From URL
downloaded = trafilatura.fetch_url("https://example.com/article")
content = trafilatura.extract(downloaded)

# From HTML string
content = trafilatura.extract(html_content)

# With options
content = trafilatura.extract(
    html_content,
    output_format="markdown",  # or "txt", "xml", "json"
    include_comments=False,
    include_tables=True,
    include_images=True,
    favor_precision=True,      # Higher precision, lower recall
    # favor_recall=True,       # Higher recall, lower precision
)

# Full metadata
from trafilatura import bare_extraction
result = bare_extraction(html_content)
# Returns: title, author, date, url, text, language, etc.
```

**Features:**
- Multiple output formats
- Metadata extraction
- Language detection
- Table extraction
- Comment extraction (optional)

#### readability-lxml (python-readability)

Python port of Mozilla's Readability.js used in Firefox Reader View.

```python
from readability import Document

doc = Document(html_content)
title = doc.title()
content = doc.summary()  # Returns cleaned HTML

# With options
doc = Document(
    html_content,
    positive_keywords=["article", "content"],
    negative_keywords=["sidebar", "comment"],
)
```

**Algorithm Overview:**

1. Remove scripts, styles, and font tags
2. Score elements based on:
   - Tag type (article: +8, section: +8, p: +5, div: +2-5)
   - Class/ID keywords (+25 for "article", -25 for "sidebar")
   - Content signals (commas, character length)
   - Link density (penalises navigation-heavy sections)
3. Select highest-scoring candidate
4. Clean up the result

#### Mozilla Readability.js

The original JavaScript implementation used in Firefox.

```javascript
// Node.js usage
const { Readability } = require("@mozilla/readability");
const { JSDOM } = require("jsdom");

const dom = new JSDOM(htmlContent, { url: pageUrl });
const reader = new Readability(dom.window.document);
const article = reader.parse();

// Returns:
// {
//   title: "Article Title",
//   content: "<div>Cleaned HTML content</div>",
//   textContent: "Plain text content",
//   length: 12345,
//   excerpt: "First paragraph...",
//   byline: "By Author Name",
//   siteName: "Example Site"
// }
```

**Key Options:**
- `charThreshold` (default 500): Minimum characters for valid article
- `nbTopCandidates` (default 5): Candidates to consider
- `disableJSONLD`: Skip Schema.org parsing

**Python Wrappers:**
- `readability-lxml`: Fast, uses lxml (recommended)
- `readability-python`: Direct port via Node.js
- `breadability`: Alternative port

---

## Part 3: HTML to Text/Markdown Conversion

### When to Use

After extracting content, you may need to convert HTML to plain text or Markdown for:
- RAG indexing (text chunks)
- Storage efficiency
- Human-readable output

### Library Comparison

| Library | Output | Formatting | Tables | Links |
|---------|--------|------------|--------|-------|
| **html2text** | Markdown | Good | Basic | Yes |
| **markdownify** | Markdown | Good | Good | Yes |
| **inscriptis** | Text | Excellent | Good | No |
| **trafilatura** | Both | Good | Good | Yes |

### Recommendation for ragd

**Primary:** Use **trafilatura** (already handles extraction + conversion).

**Fallback:** Use **html2text** for simple HTML-to-Markdown conversion.

```python
import html2text

def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    return h.handle(html)

def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = True
    return h.handle(html)
```

---

## Part 4: Web Archive Processing

### The Web Archive Problem

Users want to save web pages for offline reference and later retrieval. This creates several challenges:

1. **Preservation**: Capturing the complete page (HTML, CSS, images)
2. **Storage**: Efficient format that's easy to process
3. **Reference**: Linking back to originals

### Archive Format Comparison

| Format | Self-Contained | Browser Support | Size | Processable |
|--------|----------------|-----------------|------|-------------|
| **SingleFile HTML** | Yes | All | Medium | Excellent |
| **MHTML** | Yes | Chrome only | Large | Medium |
| **WARC** | Yes | None | Large | Good |
| **HTML + folder** | No | All | Large | Complex |

### Recommendation for ragd

**Support SingleFile HTML as the primary web archive format.**

**Rationale:**
- Self-contained (single .html file)
- Opens in any browser
- Standard HTML processing tools work
- Smaller than MHTML
- Popular browser extension

### SingleFile Format

SingleFile creates a single HTML file with all resources embedded:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <!-- Original metadata preserved -->
  <meta name="savepage-url" content="https://example.com/article">
  <meta name="savepage-date" content="2025-01-15T10:30:00Z">

  <style>
    /* Embedded CSS with images as data URIs */
    .logo { background-image: url(data:image/png;base64,...); }
  </style>
</head>
<body>
  <!-- Content with embedded images -->
  <img src="data:image/jpeg;base64,...">

  <!-- Original URLs preserved in data attributes -->
  <a data-savepage-href="https://example.com/link">Link</a>
</body>
</html>
```

### Processing SingleFile Archives

```python
from selectolax.parser import HTMLParser
import trafilatura
from datetime import datetime
from pathlib import Path

def parse_singlefile(path: Path) -> dict:
    """Extract content and metadata from SingleFile archive."""
    html = path.read_text(encoding="utf-8")
    tree = HTMLParser(html)

    # Extract SingleFile metadata
    url_meta = tree.css_first('meta[name="savepage-url"]')
    date_meta = tree.css_first('meta[name="savepage-date"]')

    original_url = url_meta.attributes.get("content") if url_meta else None
    archive_date = date_meta.attributes.get("content") if date_meta else None

    # Extract main content using trafilatura
    content = trafilatura.extract(html, output_format="markdown")
    metadata = trafilatura.bare_extraction(html)

    return {
        "source_file": str(path),
        "original_url": original_url,
        "archive_date": archive_date,
        "title": metadata.get("title"),
        "author": metadata.get("author"),
        "content": content,
        "content_type": "web_archive",
    }
```

---

## Part 5: ragd Reader View Concept

### Design: Web Archive → Reader View → Index

The proposed workflow:

```
User saves web page
        ↓
    SingleFile
        ↓
    ragd ingest
        ↓
┌───────────────────────────────────────────┐
│  1. Parse HTML (selectolax)               │
│  2. Extract original URL + archive date   │
│  3. Extract content (trafilatura)         │
│  4. Generate reader view HTML             │
│  5. Store both versions                   │
│  6. Index content for RAG                 │
└───────────────────────────────────────────┘
        ↓
    Vector DB + Metadata
```

### Reader View Storage Model

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class WebArchiveDocument:
    """Represents a processed web archive."""

    # Identity
    id: str                          # Unique document ID

    # Source
    original_url: str | None         # Where it came from
    archive_date: datetime | None    # When it was saved
    source_file: Path                # Path to SingleFile

    # Extracted content
    title: str
    author: str | None
    content_text: str                # Plain text for indexing
    content_markdown: str            # Markdown for display
    content_html: str                # Cleaned reader view HTML

    # Metadata
    word_count: int
    language: str | None

    @property
    def reader_view_path(self) -> Path:
        """Path to stored reader view HTML."""
        return Path(f"~/.ragd/reader_views/{self.id}.html")
```

### Reader View HTML Template

```python
READER_VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="ragd-document-id" content="{doc_id}">
    <meta name="ragd-original-url" content="{original_url}">
    <meta name="ragd-archive-date" content="{archive_date}">
    <title>{title}</title>
    <style>
        body {{
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            font-family: Georgia, serif;
            line-height: 1.6;
        }}
        .ragd-header {{
            border-bottom: 1px solid #ccc;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }}
        .ragd-meta {{
            font-size: 0.9em;
            color: #666;
        }}
        .ragd-original-link {{
            color: #0066cc;
        }}
    </style>
</head>
<body>
    <header class="ragd-header">
        <h1>{title}</h1>
        <div class="ragd-meta">
            {author_line}
            <p>
                <a href="{original_url}" class="ragd-original-link">Original source</a>
                {archive_date_line}
            </p>
        </div>
    </header>
    <article>
        {content}
    </article>
</body>
</html>
"""

def generate_reader_view(doc: WebArchiveDocument) -> str:
    """Generate reader view HTML from processed document."""
    author_line = f"<p>By {doc.author}</p>" if doc.author else ""
    archive_date_line = (
        f" | Archived {doc.archive_date.strftime('%Y-%m-%d')}"
        if doc.archive_date else ""
    )

    return READER_VIEW_TEMPLATE.format(
        language=doc.language or "en",
        doc_id=doc.id,
        original_url=doc.original_url or "",
        archive_date=doc.archive_date.isoformat() if doc.archive_date else "",
        title=doc.title,
        author_line=author_line,
        archive_date_line=archive_date_line,
        content=doc.content_html,
    )
```

### CLI Integration

```bash
# Index a SingleFile archive
ragd index ~/Downloads/article.html --type web-archive

# Index multiple archives
ragd index ~/Archives/*.html --type web-archive

# Search returns links to both reader view and original
ragd search "machine learning"

# Output:
# 1. Introduction to Neural Networks
#    ~/Archives/article.html → Reader View
#    Original: https://example.com/neural-networks
#    Archived: 2025-01-15
```

---

## Part 6: Implementation Recommendations

### Phase 1: v0.1 (Core)

Keep BeautifulSoup for initial implementation. It's already a dependency and sufficient for basic HTML handling.

```python
# Current v0.1 approach (simple)
from bs4 import BeautifulSoup

def extract_text_from_html(html: str) -> str:
    """Basic text extraction."""
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=" ", strip=True)
```

### Phase 2: v0.2 or v0.3 (Enhanced)

Introduce trafilatura for proper content extraction and selectolax for performance.

**New Dependencies:**
```toml
[project.dependencies]
trafilatura = "^2.0"
selectolax = "^0.3"
```

**New Feature:**
- F-038: Web Archive Support
  - SingleFile HTML ingestion
  - Reader view generation
  - Original URL tracking

### Phase 3: Future (Advanced)

- Watch folder integration for archive folders
- Browser extension for direct-to-ragd saving
- Archive.org integration for missing originals

---

## Performance Considerations

### Benchmarks (Approximate)

| Task | BeautifulSoup | lxml | selectolax | trafilatura |
|------|---------------|------|------------|-------------|
| Parse 100KB HTML | 50ms | 5ms | 2ms | - |
| Extract article | - | 20ms | 15ms | 30ms |
| Convert to Markdown | - | - | - | 10ms |

### Memory Usage

| Library | 1MB HTML | 10MB HTML |
|---------|----------|-----------|
| BeautifulSoup | ~50MB | ~500MB |
| lxml | ~10MB | ~100MB |
| selectolax | ~5MB | ~50MB |
| trafilatura | ~20MB | ~150MB |

---

## References

### HTML Parsing
- [selectolax GitHub](https://github.com/rushter/selectolax)
- [lxml Documentation](https://lxml.de/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [Efficient Web Scraping Comparison](https://medium.com/@yahyamrafe202/in-depth-comparison-of-web-scraping-parsers-lxml-beautifulsoup-and-selectolax-4f268ddea8df)

### Content Extraction
- [trafilatura Documentation](https://trafilatura.readthedocs.io/)
- [Mozilla Readability](https://github.com/mozilla/readability)
- [python-readability](https://github.com/buriy/python-readability)
- [newspaper4k](https://github.com/AndyTheFactory/newspaper4k)

### HTML Conversion
- [html2text](https://github.com/Alir3z4/html2text)
- [markdownify](https://github.com/matthewwithanm/python-markdownify)

### Web Archiving
- [SingleFile Extension](https://github.com/gildas-lormeau/SingleFile)
- [ArchiveBox](https://archivebox.io/)
- [Web Archiving Community](https://github.com/ArchiveBox/ArchiveBox/wiki/Web-Archiving-Community)

---

## Related Documentation

- [ADR-0015: Web Archive Processing](../decisions/adrs/0015-web-archive-processing.md) - SingleFile + trafilatura decision
- [ADR-0017: HTML-to-Text Conversion](../decisions/adrs/0017-html-to-text-conversion.md) - Library selection rationale
- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Document extraction
- [F-002: Text Extraction](../features/completed/F-002-text-extraction.md) - Current text extraction feature
- [F-001: Document Ingestion](../features/completed/F-001-document-ingestion.md) - Ingestion pipeline

---

**Status**: Research complete
