# Docling Integration Guide

Implementation-specific guidance for integrating IBM's Docling into ragd v0.2.

---

## Overview

This guide complements [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) with implementation details for Docling integration in ragd.

**Package:** `docling` (PyPI)
**Version:** 2.63.0+ (Python 3.9-3.14)
**Licence:** MIT
**Project:** [LF AI & Data Foundation](https://github.com/docling-project/docling)

---

## Installation

### Basic Installation

```bash
pip install docling
```

### With OCR Support

```bash
# For PaddleOCR (recommended)
pip install docling[paddleocr]

# For EasyOCR
pip install docling[easyocr]

# For macOS native OCR
pip install docling[ocrmac]

# For Tesseract
pip install docling[tesserocr]
```

### With Vision Language Model

```bash
pip install docling[vlm]  # Adds GraniteDocling support
```

### ragd Optional Dependency Group

```toml
# pyproject.toml
[project.optional-dependencies]
pdf = [
    "docling>=2.63.0",
]
```

---

## Core API Usage

### Basic Document Conversion

```python
from docling.document_converter import DocumentConverter

# Create converter (downloads models on first use, ~2.5 min)
converter = DocumentConverter()

# Convert local or remote document
result = converter.convert("document.pdf")
# Or: converter.convert("https://arxiv.org/pdf/2408.09869")

# Export to Markdown
markdown = result.document.export_to_markdown()

# Access structured document
doc = result.document
```

### Conversion Result Structure

```python
# ConversionResult contains:
result.document        # DoclingDocument with structured content
result.input           # InputDocument (source info)
result.status          # ConversionStatus (SUCCESS, PARTIAL_SUCCESS, FAILURE)
result.errors          # List of conversion errors
result.pages           # Page-level information
```

### Document Structure

```python
# Access document elements
for element in result.document.body:
    print(element.text)
    print(element.type)  # paragraph, heading, table, list, etc.
    print(element.page_no)

# Access tables specifically
for table in result.document.tables:
    print(table.export_to_markdown())
    df = table.export_to_dataframe()  # As pandas DataFrame
```

---

## Configuration Options

### PdfPipelineOptions

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Create pipeline options
pipeline_options = PdfPipelineOptions(
    # Table structure extraction
    do_table_structure=True,

    # OCR settings
    do_ocr=True,  # Enable OCR for scanned documents

    # Optional enrichments
    do_code_enrichment=False,     # Code block recognition
    do_formula_enrichment=False,  # LaTeX formula extraction

    # Image handling
    generate_page_images=False,
    generate_picture_images=False,
    images_scale=1.0,
)

# Create converter with options
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

### TableStructureOptions

```python
from docling.datamodel.pipeline_options import TableFormerMode

# Configure table extraction
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # or FAST
pipeline_options.table_structure_options.do_cell_matching = True  # Match to PDF text cells
```

### OCR Options

```python
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    TesseractOcrOptions,
    OcrMacOptions,
)

# Use specific OCR engine
pipeline_options.ocr_options = EasyOcrOptions(lang=["en"])
# Or: TesseractOcrOptions(lang="eng")
# Or: OcrMacOptions() for macOS

# Auto-select based on available backends
from docling.datamodel.pipeline_options import OcrAutoOptions
pipeline_options.ocr_options = OcrAutoOptions()
```

---

## Model Management

### Model Downloads

Models download automatically on first use (~1.5GB total):
- DocLayNet (layout analysis): ~1GB
- TableFormer (table structure): ~500MB

### Custom Model Path

```python
# Set custom artifacts path
pipeline_options = PdfPipelineOptions(
    artifacts_path="/path/to/models"
)

# Or via environment variable
# export DOCLING_ARTIFACTS_PATH="/path/to/models"

# Or via CLI
# docling --artifacts-path="/path/to/models" document.pdf
```

### Pre-Download Models

```bash
# Download models before first use
docling-tools models download
```

### Model Location (Default)

Models are cached in the Hugging Face cache directory:
- macOS: `~/.cache/huggingface/hub/`
- Linux: `~/.cache/huggingface/hub/`

---

## Memory and Performance

### Memory Requirements

| Operation | Estimated Memory |
|-----------|------------------|
| Model loading | ~2-3GB |
| Per-page processing | ~500MB-1GB |
| Table extraction | Additional ~500MB |

### CPU Thread Control

```python
import os
os.environ["OMP_NUM_THREADS"] = "4"  # Limit CPU threads (default: 4)
```

### Document Size Limits

```python
result = converter.convert(
    source,
    max_num_pages=100,        # Limit pages processed
    max_file_size=20971520,   # 20MB limit
)
```

### Lazy Loading Pattern for ragd

```python
class DoclingProcessor:
    """Lazy-loaded Docling processor."""

    def __init__(self, config: PDFConfig):
        self._converter: DocumentConverter | None = None
        self._config = config

    def _ensure_converter(self) -> DocumentConverter:
        """Lazy load the converter on first use."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            pipeline_options = PdfPipelineOptions(
                do_table_structure=self._config.extract_tables,
                do_ocr=self._config.enable_ocr,
                artifacts_path=self._config.model_path,
            )

            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )
        return self._converter

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from PDF using Docling."""
        converter = self._ensure_converter()
        result = converter.convert(str(path))

        if result.status == ConversionStatus.FAILURE:
            return ExtractionResult(
                text="",
                success=False,
                error=str(result.errors),
            )

        return ExtractionResult(
            text=result.document.export_to_markdown(),
            metadata=self._extract_metadata(result),
            pages=len(result.pages),
            success=True,
        )
```

---

## Table Extraction

### Basic Table Export

```python
# Export all tables to Markdown
for i, table in enumerate(result.document.tables):
    markdown_table = table.export_to_markdown()
    print(f"Table {i + 1}:\n{markdown_table}\n")
```

### Export to DataFrame

```python
import pandas as pd

for table in result.document.tables:
    df: pd.DataFrame = table.export_to_dataframe()
    print(df.head())
```

### Export to CSV/HTML

```python
for i, table in enumerate(result.document.tables):
    # To CSV
    df = table.export_to_dataframe()
    df.to_csv(f"table_{i}.csv", index=False)

    # To HTML
    html = table.export_to_html()
    with open(f"table_{i}.html", "w") as f:
        f.write(html)
```

### Table Metadata

```python
for table in result.document.tables:
    print(f"Page: {table.page_no}")
    print(f"Rows: {table.num_rows}")
    print(f"Cols: {table.num_cols}")
    print(f"Caption: {table.caption}")
```

---

## Error Handling

### Conversion Status

```python
from docling.datamodel.document import ConversionStatus

result = converter.convert(source)

if result.status == ConversionStatus.SUCCESS:
    # Full success
    pass
elif result.status == ConversionStatus.PARTIAL_SUCCESS:
    # Some pages or elements failed
    for error in result.errors:
        print(f"Warning: {error}")
elif result.status == ConversionStatus.FAILURE:
    # Complete failure
    raise RuntimeError(f"Conversion failed: {result.errors}")
```

### Exception Handling

```python
from docling.exceptions import (
    ConversionError,
    DocumentNotSupportedError,
    ModelLoadingError,
)

try:
    result = converter.convert(source)
except DocumentNotSupportedError as e:
    # Unsupported document format
    raise
except ModelLoadingError as e:
    # Model download or loading failed
    raise
except ConversionError as e:
    # General conversion error
    raise
```

### Graceful Fallback Pattern

```python
def extract_with_fallback(path: Path) -> ExtractionResult:
    """Try Docling, fall back to PyMuPDF on failure."""
    try:
        result = docling_extract(path)
        if result.success:
            return result
    except Exception as e:
        logger.warning(f"Docling failed: {e}, trying PyMuPDF")

    # Fallback to simpler extraction
    return pymupdf_extract(path)
```

---

## Binary Stream Input

For documents already in memory:

```python
from io import BytesIO
from docling.datamodel.base_models import DocumentStream

# From bytes
pdf_bytes = open("document.pdf", "rb").read()
buf = BytesIO(pdf_bytes)
source = DocumentStream(name="document.pdf", stream=buf)

result = converter.convert(source)
```

---

## Integration with ragd Architecture

### Fitting into TextExtractor Protocol

```python
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExtractionResult:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    pages: int | None = None
    extraction_method: str = "unknown"
    success: bool = True
    error: str | None = None

    # v0.2 additions
    quality_score: float | None = None
    tables: list[str] | None = None  # Markdown tables
    structure: dict | None = None

class DoclingExtractor:
    """Docling-based PDF extractor following ragd Protocol."""

    def __init__(self, config: PDFConfig):
        self._processor = DoclingProcessor(config)

    def extract(self, path: Path) -> ExtractionResult:
        return self._processor.extract(path)

    def supported_extensions(self) -> set[str]:
        return {".pdf"}
```

### Quality-Based Routing

```python
def select_extractor(path: Path, quality: QualityInfo) -> TextExtractor:
    """Select extractor based on document quality assessment."""

    if quality.is_scanned or quality.complexity_score > 0.7:
        # Complex or scanned → Docling with OCR
        return DoclingExtractor(config=PDFConfig(enable_ocr=True))
    elif quality.has_tables:
        # Tables present → Docling for structure
        return DoclingExtractor(config=PDFConfig(extract_tables=True))
    else:
        # Simple digital PDF → Fast path
        return PyMuPDFExtractor()
```

---

## Testing Strategy

### Unit Tests (Mocked)

```python
from unittest.mock import Mock, patch

@pytest.fixture
def mock_docling():
    """Mock Docling for fast unit tests."""
    with patch("docling.document_converter.DocumentConverter") as mock:
        instance = Mock()

        # Mock conversion result
        mock_result = Mock()
        mock_result.status = ConversionStatus.SUCCESS
        mock_result.document.export_to_markdown.return_value = "# Test\n\nContent"
        mock_result.document.tables = []
        mock_result.pages = [Mock()]
        mock_result.errors = []

        instance.convert.return_value = mock_result
        mock.return_value = instance
        yield mock
```

### Integration Tests (Slow)

```python
@pytest.mark.slow
@pytest.mark.integration
def test_docling_real_conversion(sample_pdf_path):
    """Integration test with real Docling."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(sample_pdf_path))

    assert result.status == ConversionStatus.SUCCESS
    markdown = result.document.export_to_markdown()
    assert len(markdown) > 0
```

---

## Related Documentation

- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Research context
- [ADR-0019: PDF Processing](../decisions/adrs/0019-pdf-processing.md) - Library selection
- [F-026: Docling Integration](../features/completed/F-026-docling-integration.md) - Feature spec
- [Official Docling Docs](https://docling-project.github.io/docling/)
- [Docling GitHub](https://github.com/docling-project/docling)

---

## Sources

- [IBM Docling Blog](https://research.ibm.com/blog/docling-generative-AI)
- [Docling PyPI](https://pypi.org/project/docling/)
- [Docling Advanced Options](https://docling-project.github.io/docling/usage/advanced_options/)
- [Pipeline Options Reference](https://docling-project.github.io/docling/reference/pipeline_options/)
- [DeepWiki Configuration Guide](https://deepwiki.com/docling-project/docling/2.3-configuration-and-settings)

---

**Status**: Research complete
