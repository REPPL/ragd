# Test Fixtures Specification

Specification for test documents and expected results used in ragd testing.

## Overview

ragd uses a **two-pronged fixture strategy**:

| Fixture Type | Location | Git Status | Purpose |
|--------------|----------|------------|---------|
| **Generated** | `tests/fixtures/generated/` | `.gitignore`d | Runtime-created test documents |
| **Reference** | `tests/fixtures/sources.yaml` | Committed | Archive.org URLs for real documents |
| **Minimal** | `tests/fixtures/samples/` | Committed | Tiny samples (<100KB) for offline CI |

---

## Directory Structure

```
tests/
├── fixtures/
│   ├── README.md                 # Explains fixture strategy
│   ├── sources.yaml              # Archive.org URLs for download
│   ├── samples/                  # Committed minimal samples
│   │   ├── simple.txt            # 500 chars, basic text
│   │   ├── simple.md             # 1KB, markdown with headers
│   │   └── simple.pdf            # <100KB, digital-native PDF
│   └── generated/                # .gitignore'd
│       ├── .gitkeep
│       ├── multi_page.pdf        # Generated: 10-page PDF
│       ├── complex_layout.pdf    # Generated: Multi-column
│       └── ...
├── conftest.py                   # Pytest fixtures
└── ...
```

---

## Committed Sample Files

Minimal files committed to repository for offline CI testing.

### samples/simple.txt

Plain text file for basic extraction testing.

**Requirements:**
- Size: ~500 characters
- Content: 3-4 paragraphs of sample text
- Encoding: UTF-8
- No special characters beyond ASCII

**Expected results:**
- 1 document created
- 1-2 chunks (depending on chunk size)
- Format detected as `txt`

### samples/simple.md

Markdown file with structure for header detection.

**Requirements:**
- Size: ~1KB
- Content: H1, H2, H3 headers, paragraphs, bullet list
- No images or external links
- UTF-8 encoding

**Expected results:**
- 1 document created
- 2-4 chunks
- Section headers extracted
- Format detected as `md`

### samples/simple.pdf

Digital-native PDF for basic PDF extraction.

**Requirements:**
- Size: <100KB (critical for repository size)
- Pages: 2-3 pages
- Content: Text-based (not scanned)
- No images, tables, or complex formatting
- Searchable text layer present

**Expected results:**
- 1 document created
- 3-6 chunks
- Page numbers tracked
- Format detected as `pdf`

---

## Archive.org Reference Documents

Real-world documents for comprehensive testing. Downloaded on first test run and cached.

### sources.yaml Format (v2)

The registry uses schema version 2 with categories and golden answers for validation:

```yaml
# tests/fixtures/sources.yaml
version: 2

# Category definitions for filtering
categories:
  complexity:
    - simple      # Clean digital PDFs, single column
    - moderate    # Headers, footers, basic formatting
    - complex     # Multi-column, mixed content
    - scanned     # OCR required, no text layer
    - degraded    # Poor quality scans, noise

  language:
    - english
    - german
    - french
    - spanish
    - multilingual
    - non_latin   # CJK, Arabic, Cyrillic

  document_type:
    - magazine    # Periodicals, illustrated weeklies
    - academic    # Research papers, journals
    - technical   # Manuals, specifications
    - government  # Reports, regulations
    - book        # Full books, chapters
    - historical  # Pre-1950 documents
    - form        # Structured forms, tables

documents:
  - id: alice_in_wonderland
    url: "https://archive.org/download/AlicesAdventuresInWonderland/alice-in-wonderland.pdf"
    filename: alice_in_wonderland.pdf
    source: archive.org
    license: public_domain

    categories:
      complexity: simple
      language: english
      document_type: book

    metadata:
      title: "Alice's Adventures in Wonderland"
      author: "Lewis Carroll"
      date: "1865"
      pages: 77

    characteristics:
      has_text_layer: true
      is_scanned: false
      has_images: true
      multi_column: false

    golden_answers:
      must_contain:
        - text: "Down the Rabbit-Hole"
          confidence: exact
        - text: "Cheshire Cat"
          confidence: exact

      structure:
        min_chunks: 10
        max_chunks: 50

      quality:
        min_text_extraction_ratio: 0.95

  - id: compute_gazette_1987_04
    url: "https://archive.org/download/1987-04-computegazette/Compute_Gazette_Issue_46_1987_Apr.pdf"
    filename: compute_gazette_1987_04.pdf
    source: archive.org
    license: public_domain

    categories:
      complexity: complex
      language: english
      document_type: magazine

    metadata:
      title: "Compute!'s Gazette Issue 46"
      date: "1987-04"
      pages: 100

    characteristics:
      has_text_layer: true
      is_scanned: true
      multi_column: true

    golden_answers:
      must_contain:
        - text: "Gazette"
          confidence: fuzzy
          fuzzy_threshold: 0.85
        - text: "Commodore"
          confidence: fuzzy
          fuzzy_threshold: 0.80

      quality:
        min_text_extraction_ratio: 0.70
        max_ocr_error_rate: 0.20
```

See `tests/fixtures/sources.yaml` for the complete registry with 11+ curated documents.

### Fixture Download Implementation

```python
# tests/conftest.py
import pytest
from pathlib import Path
import yaml
import urllib.request
import hashlib

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GENERATED_DIR = FIXTURES_DIR / "generated"
SOURCES_FILE = FIXTURES_DIR / "sources.yaml"

def load_sources() -> dict:
    """Load fixture sources configuration."""
    with open(SOURCES_FILE) as f:
        return yaml.safe_load(f)

def download_fixture(doc: dict) -> Path:
    """Download fixture from archive.org if not cached."""
    target = GENERATED_DIR / doc["filename"]

    if target.exists():
        return target

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {doc['id']} from {doc['url']}...")
    urllib.request.urlretrieve(doc["url"], target)

    return target

@pytest.fixture(scope="session")
def simple_digital_pdf() -> Path:
    """Fixture: simple digital PDF."""
    sources = load_sources()
    doc = next(d for d in sources["documents"] if d["id"] == "simple_digital")
    return download_fixture(doc)

@pytest.fixture(scope="session")
def scanned_pdf() -> Path:
    """Fixture: scanned document requiring OCR."""
    sources = load_sources()
    doc = next(d for d in sources["documents"] if d["id"] == "scanned_historical")
    return download_fixture(doc)

@pytest.fixture(scope="session")
def complex_pdf() -> Path:
    """Fixture: complex multi-column PDF."""
    sources = load_sources()
    doc = next(d for d in sources["documents"] if d["id"] == "academic_paper")
    return download_fixture(doc)
```

---

## Programmatically Generated Fixtures

Created at test runtime for specific test scenarios.

### Generator Functions

```python
# tests/fixtures/generators.py
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap

GENERATED_DIR = Path(__file__).parent / "generated"

def create_multi_page_pdf(pages: int = 10, filename: str = "multi_page.pdf") -> Path:
    """Generate a multi-page PDF for pagination testing."""
    target = GENERATED_DIR / filename
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(target), pagesize=letter)

    for i in range(pages):
        c.drawString(100, 750, f"Page {i + 1} of {pages}")
        c.drawString(100, 700, f"This is sample content for page {i + 1}.")
        c.drawString(100, 650, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        c.showPage()

    c.save()
    return target

def create_chunking_test_text(
    paragraphs: int = 20,
    words_per_paragraph: int = 100,
    filename: str = "chunking_test.txt"
) -> Path:
    """Generate text file for chunking boundary testing."""
    target = GENERATED_DIR / filename
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    content = []
    for i in range(paragraphs):
        para = f"Paragraph {i + 1}. " + " ".join(
            [f"word{j}" for j in range(words_per_paragraph)]
        )
        content.append(textwrap.fill(para, width=80))

    target.write_text("\n\n".join(content))
    return target

def create_markdown_with_headers(
    sections: int = 5,
    filename: str = "headers_test.md"
) -> Path:
    """Generate markdown with headers for section detection testing."""
    target = GENERATED_DIR / filename
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    content = ["# Main Title\n", "Introduction paragraph.\n"]

    for i in range(sections):
        content.append(f"## Section {i + 1}\n")
        content.append(f"Content for section {i + 1}.\n")
        content.append(f"### Subsection {i + 1}.1\n")
        content.append(f"Detailed content for subsection.\n")

    target.write_text("\n".join(content))
    return target
```

### Pytest Fixtures for Generated Documents

```python
# tests/conftest.py
from tests.fixtures.generators import (
    create_multi_page_pdf,
    create_chunking_test_text,
    create_markdown_with_headers,
)

@pytest.fixture(scope="session")
def multi_page_pdf() -> Path:
    """Generated: 10-page PDF for pagination testing."""
    return create_multi_page_pdf(pages=10)

@pytest.fixture(scope="session")
def chunking_test_text() -> Path:
    """Generated: Large text file for chunk boundary testing."""
    return create_chunking_test_text(paragraphs=50)

@pytest.fixture(scope="session")
def headers_markdown() -> Path:
    """Generated: Markdown with headers for section detection."""
    return create_markdown_with_headers(sections=10)
```

---

## Expected Results Specification

Each fixture has defined expected results for validation.

### Results Schema

```python
from pydantic import BaseModel
from typing import Optional

class ExpectedIndexResult(BaseModel):
    """Expected results from indexing a document."""
    doc_count: int = 1
    chunk_count_min: int
    chunk_count_max: int
    format: str
    has_pages: bool = False
    has_sections: bool = False

class ExpectedSearchResult(BaseModel):
    """Expected results from a search query."""
    query: str
    min_results: int
    max_results: int
    top_result_contains: Optional[str] = None
    min_score: float = 0.0
```

### Validation in Tests

```python
# tests/test_indexing.py
import pytest
from ragd.indexer import Indexer

def test_index_simple_txt(simple_txt_sample: Path):
    """Test indexing simple text file."""
    indexer = Indexer()
    result = indexer.index(simple_txt_sample)

    expected = ExpectedIndexResult(
        doc_count=1,
        chunk_count_min=1,
        chunk_count_max=2,
        format="txt",
        has_pages=False,
        has_sections=False,
    )

    assert result.doc_count == expected.doc_count
    assert expected.chunk_count_min <= result.chunk_count <= expected.chunk_count_max
    assert result.format == expected.format

def test_index_complex_pdf(complex_pdf: Path):
    """Test indexing complex multi-column PDF."""
    indexer = Indexer()
    result = indexer.index(complex_pdf)

    expected = ExpectedIndexResult(
        doc_count=1,
        chunk_count_min=20,
        chunk_count_max=100,
        format="pdf",
        has_pages=True,
        has_sections=True,
    )

    assert result.doc_count == expected.doc_count
    assert expected.chunk_count_min <= result.chunk_count <= expected.chunk_count_max
    assert result.has_pages == expected.has_pages
```

---

## Golden Answer Validation

The `tests/fixtures/validator.py` module provides validation against golden answers defined in `sources.yaml`.

### Using the Validator

```python
from tests.fixtures.validator import (
    GoldenAnswerValidator,
    get_documents_by_category,
)

# Validate extracted text against golden answers
validator = GoldenAnswerValidator()
report = validator.validate_document(
    document_id="alice_in_wonderland",
    extracted_text=extracted_text,
    chunk_count=25,
    pages_with_text=77,
    total_pages=77,
)

assert report.passed, f"Failed: {report.failed_checks} checks"
print(f"Pass rate: {report.pass_rate:.0%}")

# Get documents by category for parametrised tests
simple_docs = get_documents_by_category("complexity", "simple")
scanned_docs = get_documents_by_category("complexity", "scanned")
```

### Validation Types

| Type | Description | Example |
|------|-------------|---------|
| `must_contain` | Text presence (exact or fuzzy) | "Down the Rabbit-Hole" |
| `patterns` | Regex pattern matching | `Issue \d+` |
| `structure` | Chunk count ranges | min_chunks: 10, max_chunks: 50 |
| `quality` | Extraction quality metrics | min_text_extraction_ratio: 0.90 |

### Fuzzy Matching for OCR

For scanned documents with OCR errors, use fuzzy matching:

```yaml
golden_answers:
  must_contain:
    - text: "Commodore"
      confidence: fuzzy
      fuzzy_threshold: 0.80  # Allow 20% character difference
```

The validator uses `rapidfuzz` for fuzzy string matching (falls back to substring search if not installed).

---

## CI/CD Considerations

### Offline Mode

Tests run without network access using committed samples:

```python
# tests/conftest.py
import os

OFFLINE_MODE = os.getenv("RAGD_TEST_OFFLINE", "false").lower() == "true"

@pytest.fixture(scope="session")
def pdf_fixture() -> Path:
    """PDF fixture - uses committed sample in offline mode."""
    if OFFLINE_MODE:
        return FIXTURES_DIR / "samples" / "simple.pdf"
    return download_fixture("simple_digital")
```

### CI Configuration

```yaml
# .github/workflows/test.yml
jobs:
  test-offline:
    name: Tests (Offline)
    runs-on: ubuntu-latest
    env:
      RAGD_TEST_OFFLINE: "true"
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/

  test-full:
    name: Tests (Full)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/ --slow  # Downloads archive.org fixtures
```

---

## .gitignore Configuration

```gitignore
# tests/fixtures/.gitignore

# Generated fixtures (created at runtime)
generated/
!generated/.gitkeep

# Downloaded fixtures (from archive.org)
*.downloaded

# Large files that shouldn't be committed
*.pdf
!samples/*.pdf
```

---

## Related Documentation

- [ADR-0019: PDF Processing](../development/decisions/adrs/0019-pdf-processing.md) - Quality detection for fixtures
- [State-of-the-Art PDF Processing](../development/research/state-of-the-art-pdf-processing.md) - Messy PDF research
- [F-002: Text Extraction](../development/features/planned/F-002-text-extraction.md) - Extraction testing

---

**Status**: Reference specification for v0.1.0
