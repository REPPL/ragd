# F-026: Docling Integration

## Overview

**Use Case**: [UC-004](../../../use-cases/briefs/UC-004-process-messy-pdfs.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Traditional PDF text extraction loses document structure—tables become garbled text, multi-column layouts merge incorrectly, and figures lose context. This "structure loss" degrades RAG retrieval quality because chunks no longer represent coherent semantic units.

## Design Approach

Integrate IBM's Docling library as the primary document understanding pipeline. Docling uses specialised AI models (DocLayNet for layout, TableFormer for tables) to preserve document structure in the output.

**Processing Pipeline:**
```
PDF → Docling Pipeline
         ↓
    Layout Analysis (DocLayNet)
         ↓
    Element Detection
         ↓
    ┌────────────────────────────────────────┐
    │  Text Blocks  │  Tables  │  Figures   │
    └────────────────────────────────────────┘
         ↓              ↓           ↓
    Direct Extract  TableFormer  Caption+Ref
         ↓              ↓           ↓
    Structured Output (JSON/Markdown)
```

**Key Capabilities:**
- Multi-format support: PDF, DOCX, PPTX, XLSX, HTML, images
- Reading order detection for multi-column layouts
- Table extraction with 97.9% cell accuracy
- Formula recognition
- Code block detection

## Implementation Tasks

- [ ] Add docling as optional dependency (`pip install ragd[pdf]`)
- [ ] Create DoclingProcessor class wrapping docling API
- [ ] Implement structured output to Markdown conversion
- [ ] Preserve element metadata (page, section, coordinates)
- [ ] Handle processing errors gracefully with fallback to basic extraction
- [ ] Add progress callbacks for long documents
- [ ] Configure Docling models (GPU vs CPU inference)

## Success Criteria

- [ ] Multi-column PDFs processed with correct reading order
- [ ] Tables extracted as structured Markdown/HTML
- [ ] Processing time acceptable (<5s per page for complex docs)
- [ ] Graceful fallback when Docling fails
- [ ] Integration tests with diverse PDF samples

## Dependencies

- [F-025: PDF Quality Detection](./F-025-pdf-quality-detection.md) - Routes documents to Docling
- [F-002: Text Extraction](./F-002-text-extraction.md) - Fallback extraction
- Docling library (MIT licensed, LF AI & Data Foundation)

## Technical Notes

**Installation:**
```bash
pip install docling
# Or with GPU acceleration
pip install docling[gpu]
```

**Basic Usage:**
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")

# Export to Markdown
markdown = result.document.export_to_markdown()

# Access structured elements
for element in result.document.iterate_items():
    if element.type == "table":
        # Handle table specifically
        table_md = element.export_to_markdown()
```

**Memory Considerations:**
- DocLayNet model: ~1GB
- TableFormer model: ~500MB
- Consider lazy loading for CLI startup time

## Related Documentation

- [State-of-the-Art PDF Processing](../../research/state-of-the-art-pdf-processing.md)
- [Docling GitHub](https://github.com/docling-project/docling)
- [F-028: Table Extraction](./F-028-table-extraction.md)

---

**Status**: Completed
