# F-002: Text Extraction

## Overview

**Use Case**: [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Documents come in various formats (PDF, TXT, Markdown, HTML). We need reliable text extraction that preserves document structure and handles edge cases gracefully.

## Design Approach

### Architecture

```
Document
    ↓
Format Router
    ├── PDF → PyMuPDF (fast, native text)
    ├── TXT → Direct read (UTF-8, encoding detection)
    ├── MD  → Direct read (preserve structure)
    └── HTML → BeautifulSoup (strip tags, preserve text)
    ↓
Extracted Text + Metadata
```

### Technologies

- **PyMuPDF (fitz)**: Fast PDF text extraction for clean PDFs
- **BeautifulSoup**: HTML parsing and text extraction
- **chardet**: Character encoding detection for text files

### Extractor Interface

```python
class TextExtractor(Protocol):
    def extract(self, path: Path) -> ExtractionResult:
        """Extract text and metadata from document."""
        ...

@dataclass
class ExtractionResult:
    text: str
    metadata: dict[str, Any]
    pages: int | None
    extraction_method: str
```

## Implementation Tasks

- [ ] Define `TextExtractor` protocol and `ExtractionResult` dataclass
- [ ] Implement `PDFExtractor` using PyMuPDF
- [ ] Implement `PlainTextExtractor` with encoding detection
- [ ] Implement `MarkdownExtractor` preserving structure
- [ ] Implement `HTMLExtractor` using BeautifulSoup
- [ ] Create `ExtractorFactory` for format routing
- [ ] Add metadata extraction (title, author, dates)
- [ ] Write unit tests for each extractor
- [ ] Write integration tests for extraction pipeline

## Success Criteria

- [ ] PDF text extraction works for clean, text-based PDFs
- [ ] TXT files read correctly regardless of encoding
- [ ] Markdown structure preserved (headings, lists)
- [ ] HTML stripped to clean text
- [ ] Metadata extracted where available
- [ ] Extraction failures return partial results with warnings

## Dependencies

- PyMuPDF (pymupdf)
- BeautifulSoup4 (bs4)
- chardet

## Technical Notes

### PDF Extraction Strategy

For v0.1, use simple PyMuPDF text extraction. This works well for clean, text-based PDFs. Messy PDF handling (OCR, Docling) comes in v0.2 via F-010.

### Encoding Handling

```python
def detect_encoding(path: Path) -> str:
    with open(path, 'rb') as f:
        result = chardet.detect(f.read(10000))
    return result['encoding'] or 'utf-8'
```

### Markdown Preservation

Keep Markdown syntax intact - it aids chunking by providing natural section boundaries.

### Error Recovery

If extraction fails:
1. Log the error with context
2. Return empty text with error metadata
3. Pipeline continues with warning

## Related Documentation

- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Upstream orchestrator
- [F-003: Chunking Engine](./F-003-chunking-engine.md) - Downstream consumer
- [F-010: Docling Integration](./F-010-docling-integration.md) - v0.2 enhancement for messy PDFs

---
