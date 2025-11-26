# ADR-0019: PDF Processing Library Selection

## Status

Accepted

## Context

PDF processing is one of the most challenging problems in document understanding. PDFs vary widely:
- Digital-native vs scanned
- Simple text vs complex layouts (multi-column, tables)
- Clean vs degraded quality

Research from OHRBench (ICCV 2025) shows that **OCR errors cascade through RAG systems**, reducing accuracy by up to 50%. Traditional OCR-only approaches are insufficient.

The landscape has shifted toward:
1. **Document understanding** over raw text extraction
2. **Vision-based retrieval** that bypasses OCR entirely
3. **Hybrid approaches** combining layout analysis with structured extraction

ragd needs a PDF pipeline that handles diverse document quality while prioritising local-first operation.

## Decision

Use **quality-based routing** with **Docling as primary processor** and **PyMuPDF4LLM for fast path**. Reserve vision-based approaches (ColPali) for v0.4 multi-modal support.

### Processing Pipeline

```
Input PDF
    │
    ▼
┌──────────────────────────────────────────┐
│           Quality Detection               │
│  - Has text layer? (digital vs scanned)  │
│  - Layout complexity (tables, columns)   │
│  - Page count and structure              │
└─────────────────┬────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌────────────┐           ┌────────────────┐
│  Simple    │           │    Complex     │
│  Digital   │           │  or Scanned    │
└─────┬──────┘           └───────┬────────┘
      │                          │
      ▼                          ▼
┌────────────┐           ┌────────────────┐
│ PyMuPDF4LLM│           │    Docling     │
│ (0.12s/pg) │           │ + OCR fallback │
└─────┬──────┘           └───────┬────────┘
      │                          │
      └──────────┬───────────────┘
                 │
                 ▼
         Structured Markdown
```

### Library Roles

| Library | Role | Best For |
|---------|------|----------|
| **PyMuPDF4LLM** | Fast path | Digital PDFs with clear text layers |
| **Docling** | Primary processor | Complex layouts, tables, scanned documents |
| **PaddleOCR** | OCR fallback | Scanned documents when Docling needs OCR |

### Quality Detection

```python
from dataclasses import dataclass
from enum import Enum

class PDFComplexity(Enum):
    SIMPLE = "simple"      # Single column, no tables
    MODERATE = "moderate"  # Some formatting, basic tables
    COMPLEX = "complex"    # Multi-column, complex tables, figures

class PDFType(Enum):
    DIGITAL = "digital"    # Has text layer
    SCANNED = "scanned"    # Image-only, needs OCR
    HYBRID = "hybrid"      # Mix of text and scanned pages

@dataclass
class PDFQuality:
    pdf_type: PDFType
    complexity: PDFComplexity
    page_count: int
    has_tables: bool
    has_images: bool

def detect_pdf_quality(pdf_path: Path) -> PDFQuality:
    """Analyse PDF to determine processing strategy."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)

    # Check for text layer
    text_pages = sum(1 for page in doc if page.get_text().strip())
    has_text_layer = text_pages > len(doc) * 0.5

    # Check for tables (heuristic: many horizontal/vertical lines)
    has_tables = any(_detect_table_structure(page) for page in doc)

    # Check complexity (multi-column detection)
    complexity = _assess_layout_complexity(doc)

    return PDFQuality(
        pdf_type=PDFType.DIGITAL if has_text_layer else PDFType.SCANNED,
        complexity=complexity,
        page_count=len(doc),
        has_tables=has_tables,
        has_images=any(page.get_images() for page in doc),
    )
```

### Router Implementation

```python
def process_pdf(pdf_path: Path) -> Document:
    """Route PDF through appropriate processing pipeline."""
    quality = detect_pdf_quality(pdf_path)

    # Fast path: simple digital PDFs
    if quality.pdf_type == PDFType.DIGITAL and quality.complexity == PDFComplexity.SIMPLE:
        return pymupdf4llm_extract(pdf_path)

    # Standard path: Docling for everything else
    return docling_extract(pdf_path, use_ocr=quality.pdf_type == PDFType.SCANNED)
```

### Docling Integration

```python
from docling.document_converter import DocumentConverter

def docling_extract(pdf_path: Path, use_ocr: bool = False) -> Document:
    """Extract document using Docling."""
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    # Get structured Markdown
    markdown = result.document.export_to_markdown()

    return Document(
        content=markdown,
        metadata={
            "source": str(pdf_path),
            "page_count": len(result.document.pages),
            "tables_found": len(result.document.tables),
            "processor": "docling",
        }
    )
```

### PyMuPDF4LLM Fast Path

```python
import pymupdf4llm

def pymupdf4llm_extract(pdf_path: Path) -> Document:
    """Fast extraction for simple digital PDFs."""
    markdown = pymupdf4llm.to_markdown(
        str(pdf_path),
        page_chunks=True,  # Chunk by page
    )

    return Document(
        content=markdown,
        metadata={
            "source": str(pdf_path),
            "processor": "pymupdf4llm",
        }
    )
```

## Consequences

### Positive

- Quality-based routing optimises for each document type
- Docling handles complex layouts with 97.9% table accuracy
- PyMuPDF4LLM provides 100x speed improvement for simple PDFs
- Structured output (Markdown) integrates with existing pipeline
- No cloud dependencies (all local processing)

### Negative

- Docling adds significant dependency (~500MB with models)
- Quality detection adds overhead (~100ms per document)
- PaddleOCR fallback increases processing time for scanned docs
- Vision-based approaches deferred to v0.4

### Phased Implementation

| Version | Features |
|---------|----------|
| v0.1 | PyMuPDF basic extraction (current) |
| v0.2 | Add Docling + quality routing |
| v0.3 | Add PaddleOCR fallback for scanned |
| v0.4 | Add ColPali vision retrieval (optional) |

## Alternatives Considered

### PyMuPDF Only

- **Pros:** Fast, simple, small dependency
- **Cons:** Poor handling of complex layouts, no OCR
- **Rejected:** Insufficient for messy PDFs

### OCR-First (Tesseract/PaddleOCR)

- **Pros:** Works on any document
- **Cons:** OHRBench shows 50% accuracy degradation from OCR noise
- **Rejected:** OCR should be fallback, not primary

### Vision-Only (ColPali)

- **Pros:** Bypasses OCR entirely, excellent for visual documents
- **Cons:** High compute/storage, cannot extract text
- **Rejected:** Deferred to v0.4 multi-modal support

### Unstructured.io

- **Pros:** Comprehensive, semantic chunking
- **Cons:** Heavy dependency, SaaS-oriented
- **Rejected:** Docling provides similar quality, lighter weight

### Commercial OCR (Mistral, Azure)

- **Pros:** Highest accuracy (94%+)
- **Cons:** Cloud dependency, cost
- **Rejected:** Violates local-first principle; optional tier for enterprise

## Related Documentation

- [State-of-the-Art PDF Processing](../../research/state-of-the-art-pdf-processing.md)
- [F-025: PDF Quality Detection](../../features/planned/F-025-pdf-quality-detection.md)
- [F-026: Docling Integration](../../features/planned/F-026-docling-integration.md)
- [F-027: OCR Pipeline](../../features/planned/F-027-ocr-pipeline.md)
- [F-028: Table Extraction](../../features/planned/F-028-table-extraction.md)
- [UC-004: Process Messy PDFs](../../use-cases/briefs/UC-004-process-messy-pdfs.md)

