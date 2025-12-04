# ADR-0024: Optional Dependencies Strategy

## Status

Superseded by [ADR-0032](./0032-full-features-by-default.md)

> **Note (v1.0)**: This ADR documented the v0.x approach. For v1.0, see ADR-0032
> which inverts the model to "full features by default".

## Context

v0.2.0 introduces heavy dependencies for advanced PDF processing, OCR, and metadata extraction:

| Feature | Dependencies | Size Impact |
|---------|-------------|-------------|
| Docling | docling, docling-core, DocLayNet models | ~500MB |
| OCR | paddleocr/paddlepaddle OR easyocr, torch | ~800MB-2GB |
| Metadata | keybert, spacy, langdetect, en_core_web_sm | ~200MB |
| Export | pyarrow (for Parquet) | ~100MB |

**Problems with making these core dependencies:**

1. **Installation time**: Fresh install goes from ~30s to 5-10 minutes
2. **Disk space**: Base install grows from ~200MB to potentially 3GB+
3. **User friction**: Users who only need basic text extraction pay full cost
4. **CI/CD impact**: Test pipelines become significantly slower

### User Personas

Different users need different capabilities:

| User Type | Needs | Core Only? |
|-----------|-------|------------|
| Quick eval | Index text files, search | ✅ Yes |
| Researcher | Existing text-layer PDFs | ✅ Yes |
| Archivist | Scanned documents, OCR | ❌ Needs `[ocr]` |
| Librarian | Rich metadata, organisation | ❌ Needs `[metadata]` |
| Power user | Everything | ❌ Needs `[all]` |

## Decision

Implement **feature-based optional dependency groups** with graceful degradation:

### 1. Dependency Groups

```toml
[project.optional-dependencies]
# Advanced PDF processing (Docling)
pdf = [
    "docling>=2.0.0",
    "docling-core>=2.0.0",
]

# OCR for scanned documents
ocr = [
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.5.0",  # CPU version
    "easyocr>=1.7.0",        # Fallback
    "opencv-python-headless>=4.8.0",
]

# Metadata extraction
metadata = [
    "keybert>=0.8.0",
    "spacy>=3.7.0",
    "langdetect>=1.0.9",
]

# Export functionality
export = [
    "pyarrow>=14.0.0",
]

# All v0.2 features
v02 = [
    "ragd[pdf,ocr,metadata,export]",
]

# Development
dev = [
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

# Testing
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
]

# Security auditing
security = [
    "pip-audit>=2.6.0",
    "bandit>=1.7.0",
    "safety>=2.3.0",
]

# Everything
all = [
    "ragd[v02,dev,test,security]",
]
```

### 2. Installation Patterns

```bash
# Minimal install (text files, simple PDFs)
pip install ragd

# Add Docling for complex PDFs
pip install "ragd[pdf]"

# Add OCR for scanned documents
pip install "ragd[ocr]"

# Add metadata extraction
pip install "ragd[metadata]"

# All v0.2 features
pip install "ragd[v02]"

# Full development setup
pip install "ragd[all]"
```

### 3. Graceful Degradation

When optional dependencies are missing, the system degrades gracefully:

```python
def get_pdf_pipeline(doc_quality: PDFQuality) -> PDFProcessor:
    """Select PDF pipeline based on quality and available dependencies."""
    if doc_quality == PDFQuality.SCANNED:
        if not OCR_AVAILABLE:
            raise DependencyError(
                "OCR required for scanned documents.\n"
                "Install with: pip install 'ragd[ocr]'"
            )
        return OCRPipeline()

    if doc_quality == PDFQuality.COMPLEX_LAYOUT:
        if not DOCLING_AVAILABLE:
            logger.warning(
                "Docling not available, falling back to PyMuPDF.\n"
                "For better table/layout extraction: pip install 'ragd[pdf]'"
            )
            return PyMuPDFPipeline()
        return DoclingPipeline()

    return PyMuPDFPipeline()  # Always available
```

### 4. Feature Detection Pattern

```python
# src/ragd/features.py
"""Feature availability detection."""

def _check_import(module: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False

# Feature flags
DOCLING_AVAILABLE = _check_import("docling")
PADDLEOCR_AVAILABLE = _check_import("paddleocr")
EASYOCR_AVAILABLE = _check_import("easyocr")
OCR_AVAILABLE = PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE
KEYBERT_AVAILABLE = _check_import("keybert")
SPACY_AVAILABLE = _check_import("spacy")
LANGDETECT_AVAILABLE = _check_import("langdetect")
METADATA_AVAILABLE = KEYBERT_AVAILABLE and SPACY_AVAILABLE
PYARROW_AVAILABLE = _check_import("pyarrow")

def get_available_features() -> dict[str, bool]:
    """Return available features for status display."""
    return {
        "pdf_advanced": DOCLING_AVAILABLE,
        "ocr": OCR_AVAILABLE,
        "ocr_primary": PADDLEOCR_AVAILABLE,
        "ocr_fallback": EASYOCR_AVAILABLE,
        "metadata": METADATA_AVAILABLE,
        "export_parquet": PYARROW_AVAILABLE,
    }
```

### 5. Status Command Integration

```bash
$ ragd doctor

┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Core Features:                                              │
│ ✅ Storage          ChromaDB accessible                     │
│ ✅ Embedding        Model loaded successfully               │
│ ✅ PDF (basic)      PyMuPDF available                       │
│                                                             │
│ Optional Features:                                          │
│ ❌ PDF (advanced)   Install: pip install 'ragd[pdf]'        │
│ ❌ OCR              Install: pip install 'ragd[ocr]'        │
│ ⚠️  Metadata         spaCy model missing                    │
│                     Run: python -m spacy download en_core_web_sm │
│ ✅ Export           Parquet export ready                    │
└─────────────────────────────────────────────────────────────┘
```

### 6. Error Messages

Clear, actionable error messages when features are missing:

```python
class DependencyError(Exception):
    """Raised when an optional dependency is required but missing."""

    def __init__(self, message: str, install_command: str | None = None):
        self.install_command = install_command
        super().__init__(message)

# Usage
raise DependencyError(
    "Docling required for complex PDF layout extraction.",
    install_command="pip install 'ragd[pdf]'"
)
```

### 7. Documentation Requirements

Every feature using optional dependencies MUST document:
1. Which extra(s) are required
2. Installation command
3. What happens without it (graceful degradation)

## Consequences

### Positive

- **Fast default install**: Core ragd installs in ~30 seconds
- **User choice**: Pay only for features you need
- **Clear upgrade path**: Easy to add features incrementally
- **CI-friendly**: Tests can run with minimal dependencies
- **Graceful degradation**: System works at reduced capability

### Negative

- **Complexity**: More code paths to test
- **Documentation burden**: Must document all combinations
- **User confusion**: May not know which extras to install
- **Dependency conflicts**: More extras = more potential conflicts

### Mitigation

- **`ragd doctor`**: Shows what's available and what's missing
- **Clear error messages**: Tell users exactly what to install
- **`[v02]` meta-extra**: Easy "give me everything" option
- **Tutorials**: Each tutorial lists required extras upfront

## Alternatives Considered

### 1. Monolithic Install

**Rejected**: 3GB+ install for basic text search is unacceptable. Users evaluating ragd would abandon before installation completes.

### 2. Separate Packages

**Rejected**: `ragd-ocr`, `ragd-pdf`, etc. would fragment the ecosystem and complicate installation. Version synchronisation becomes a nightmare.

### 3. Plugin Architecture

**Rejected**: Overkill for v0.2. May reconsider for v1.0 if feature set grows significantly. Current optional dependencies pattern is simpler and sufficient.

### 4. Runtime Downloads

**Rejected**: Downloading models at runtime (like spaCy does) is acceptable for NLP models but not for entire packages. Users expect `pip install` to complete the setup.

## Implementation

### Phase 1: Update pyproject.toml

Add new dependency groups:

```toml
[project.optional-dependencies]
pdf = ["docling>=2.0.0", "docling-core>=2.0.0"]
ocr = ["paddleocr>=2.7.0", "paddlepaddle>=2.5.0", "easyocr>=1.7.0", "opencv-python-headless>=4.8.0"]
metadata = ["keybert>=0.8.0", "spacy>=3.7.0", "langdetect>=1.0.9"]
export = ["pyarrow>=14.0.0"]
v02 = ["ragd[pdf,ocr,metadata,export]"]
```

### Phase 2: Feature Detection

Create `src/ragd/features.py` with availability checks.

### Phase 3: Update ragd doctor

Add optional feature status to health check output.

### Phase 4: Graceful Degradation

Implement fallback logic in PDF, OCR, and metadata modules.

## Related Documentation

- [ADR-0019: PDF Processing](./0019-pdf-processing.md)
- [ADR-0023: Metadata Schema Evolution](./0023-metadata-schema-evolution.md)
- [F-025: PDF Quality Detection](../../features/completed/F-025-pdf-quality-detection.md)
- [F-027: OCR Pipeline](../../features/completed/F-027-ocr-pipeline.md)
- [Docling Integration Guide](../../research/docling-integration-guide.md)
- [PaddleOCR Integration Guide](../../research/paddleocr-integration-guide.md)

---

**Status**: Superseded by [ADR-0032](./0032-full-features-by-default.md)
