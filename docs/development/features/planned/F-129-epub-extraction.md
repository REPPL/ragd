# F-129: EPUB/Ebook Text Extraction

## Overview

**Research**: [State-of-the-Art NER](../../research/state-of-the-art-ner.md)
**Milestone**: [v1.1.0](../../milestones/v1.1.0.md)
**Priority**: P2

## Problem Statement

Users want to ingest ebooks (EPUB format) into ragd for:

1. Personal knowledge management from book collections
2. Research across multiple ebook sources
3. Building searchable libraries from DRM-free ebooks

Current limitations:
- ragd supports PDF, HTML, Markdown, and plain text
- EPUB is a common ebook format not currently supported
- EPUB contains rich metadata (Dublin Core) that should be extracted

## Design Approach

### EPUB Structure

EPUB files are ZIP archives containing:

```
book.epub (renamed .zip)
├── META-INF/
│   └── container.xml      # Points to content.opf
├── OEBPS/
│   ├── content.opf        # Package document (metadata + manifest)
│   ├── toc.ncx            # Table of contents (EPUB 2)
│   ├── nav.xhtml          # Navigation document (EPUB 3)
│   ├── chapter1.xhtml     # Chapter content
│   ├── chapter2.xhtml
│   └── ...
└── mimetype               # application/epub+zip
```

### Extraction Pipeline

```
EPUB File
    │
    ▼
EbookLib (read_epub)
    │
    ├─→ Metadata Extraction
    │   ├─ title (DC)
    │   ├─ creator/author (DC)
    │   ├─ language (DC)
    │   ├─ publisher (DC)
    │   └─ date (DC)
    │
    ├─→ Structure Extraction
    │   ├─ Table of Contents
    │   └─ Chapter order (spine)
    │
    └─→ Content Extraction
        ├─ Iterate ITEM_DOCUMENT items
        ├─ Parse XHTML with BeautifulSoup
        └─ Extract text preserving paragraphs
            │
            ▼
    Normalised Text + Dublin Core Metadata
            │
            ▼
    Standard Ingestion Pipeline
```

### Architecture

```python
from ebooklib import epub
from bs4 import BeautifulSoup

class EpubExtractor:
    """Extract text and metadata from EPUB files."""

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract content from EPUB."""
        book = epub.read_epub(file_path)

        # Extract Dublin Core metadata
        metadata = self._extract_metadata(book)

        # Extract chapter content
        chapters = []
        for item in book.get_items_of_type(epub.ITEM_DOCUMENT):
            if item.is_chapter():
                soup = BeautifulSoup(
                    item.get_body_content(),
                    'html.parser'
                )
                text = soup.get_text(separator='\n\n')
                chapters.append({
                    'title': self._get_chapter_title(soup),
                    'content': text.strip(),
                    'file_name': item.get_name(),
                })

        return ExtractionResult(
            text='\n\n'.join(c['content'] for c in chapters),
            metadata=metadata,
            chapters=chapters,
        )

    def _extract_metadata(self, book: epub.EpubBook) -> dict:
        """Extract Dublin Core metadata."""
        def get_first(field: str) -> str | None:
            values = book.get_metadata('DC', field)
            return values[0][0] if values else None

        return {
            'dc:title': get_first('title'),
            'dc:creator': get_first('creator'),
            'dc:language': get_first('language'),
            'dc:publisher': get_first('publisher'),
            'dc:date': get_first('date'),
            'dc:identifier': get_first('identifier'),
            'dc:subject': [
                s[0] for s in book.get_metadata('DC', 'subject')
            ],
        }

    def _get_chapter_title(self, soup: BeautifulSoup) -> str | None:
        """Extract chapter title from heading."""
        for tag in ['h1', 'h2', 'h3', 'title']:
            heading = soup.find(tag)
            if heading:
                return heading.get_text().strip()
        return None
```

### CLI Integration

```bash
# Ingest an EPUB file
ragd add book.epub

# Ingest with chapter-aware chunking
ragd add book.epub --chunk-strategy structure

# List ebooks in collection
ragd list --format epub

# Search across books
ragd search "machine learning" --format epub
```

### File Type Detection

Add EPUB to the file type detection:

```python
SUPPORTED_FORMATS = {
    '.pdf': 'pdf',
    '.txt': 'text',
    '.md': 'markdown',
    '.html': 'html',
    '.htm': 'html',
    '.epub': 'epub',  # NEW
}
```

## Implementation Tasks

- [ ] Add `ebooklib` as optional dependency in pyproject.toml
- [ ] Create `EpubExtractor` class in `src/ragd/ingestion/extractor.py`
- [ ] Register EPUB format in file type detection
- [ ] Extract Dublin Core metadata to document metadata
- [ ] Implement chapter-aware extraction with structure preservation
- [ ] Add chapter metadata to chunks (chapter title, position)
- [ ] Write unit tests with sample EPUB files
- [ ] Update documentation with EPUB examples

## Success Criteria

- [ ] EPUB files ingestible via `ragd add book.epub`
- [ ] Dublin Core metadata (title, author, language) extracted
- [ ] Chapter structure preserved in extraction
- [ ] Table of contents accessible for navigation
- [ ] Extraction handles both EPUB 2 and EPUB 3 formats
- [ ] No impact on users who don't use EPUB (optional dependency)

## Dependencies

- **ebooklib >= 0.18** (optional dependency)
- **beautifulsoup4** (already present)
- **lxml** (already present)

## Format Support Matrix

| Format | EPUB 2 | EPUB 3 | Notes |
|--------|--------|--------|-------|
| Content | XHTML 1.1 | XHTML 5 | Both supported via BeautifulSoup |
| ToC | NCX | Nav XHTML | EbookLib handles both |
| Metadata | OPF 2.0 | OPF 3.0 | Dublin Core in both |
| DRM | Not supported | Not supported | DRM-free only |

## Limitations

- **DRM-protected EPUBs**: Not supported (requires DRM removal)
- **Fixed-layout EPUBs**: Text extraction may lose layout context
- **Embedded fonts/styles**: Ignored (text-only extraction)
- **Audio/video**: Not extracted

---

## Related Documentation

- [State-of-the-Art NER](../../research/state-of-the-art-ner.md) - Document extraction research
- [F-002: Text Extraction](../completed/F-002-text-extraction.md) - Existing extraction pipeline
- [EbookLib GitHub](https://github.com/aerkalov/ebooklib) - Library documentation

---

**Status**: Planned
