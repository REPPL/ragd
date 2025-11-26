# Test Fixtures

Test documents and validation framework for ragd testing.

## Directory Structure

```
fixtures/
├── README.md           # This file
├── sources.yaml        # Registry of test documents with golden answers
├── validator.py        # Golden answer validation framework
├── samples/            # Committed minimal samples (<100KB)
│   └── (to be added)
└── generated/          # Runtime-generated fixtures (.gitignore'd)
    └── .gitkeep
```

## Test Document Registry

The `sources.yaml` file contains a curated registry of publicly available test documents from Archive.org and other sources. Each document includes:

- **Categories**: Complexity tier, language, document type
- **Metadata**: Title, author, date, page count
- **Characteristics**: Text layer, scanned status, content types
- **Golden Answers**: Expected text snippets for validation

### Categories

#### Complexity Tiers

| Tier | Description | Example |
|------|-------------|---------|
| `simple` | Clean digital PDFs, single column | Alice in Wonderland |
| `moderate` | Headers, footers, basic formatting | Technical manuals |
| `complex` | Multi-column, mixed content | Compute! Gazette magazine |
| `scanned` | OCR required, no native text layer | Historical newspapers |
| `degraded` | Poor quality scans, noise | Medieval manuscripts |

#### Languages

- `english`, `german`, `french`, `spanish`
- `multilingual` - Multiple languages in one document
- `non_latin` - CJK, Arabic, Cyrillic scripts

#### Document Types

- `magazine`, `academic`, `technical`, `government`
- `book`, `historical`, `form`

## Using the Validator

```python
from tests.fixtures.validator import (
    GoldenAnswerValidator,
    get_documents_by_category,
    list_all_document_ids,
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

print(f"Passed: {report.passed}")
print(f"Pass rate: {report.pass_rate:.0%}")
for result in report.results:
    print(f"  {result.check_type}: {result.message}")

# Get documents by category
simple_docs = get_documents_by_category("complexity", "simple")
english_docs = get_documents_by_category("language", "english")

# List all document IDs
all_ids = list_all_document_ids()
```

## Adding New Test Documents

### Discovery Guidelines

1. **Search Archive.org** for public domain or Creative Commons content
2. **Verify licence status** on the item page
3. **Use stable download URLs**:
   ```
   # Preferred: Direct download link
   https://archive.org/download/{identifier}/{filename}

   # Avoid: Reader page (may change)
   https://archive.org/details/{identifier}/mode/2up
   ```
4. **Test URL stability** before adding

### Recommended Collections

- `computemagazines` - Vintage computing magazines
- `arxiv` - Academic papers
- `gutenberg` - Public domain books
- `us_government_documents` - Government reports
- `biodiversitylibrary` - Scientific journals

### Document Entry Template

```yaml
- id: unique_identifier
  url: "https://archive.org/download/identifier/filename.pdf"
  filename: local_filename.pdf
  source: archive.org
  license: public_domain

  categories:
    complexity: simple|moderate|complex|scanned|degraded
    language: english|german|french|...
    document_type: magazine|academic|technical|...

  metadata:
    title: "Document Title"
    author: "Author Name"
    date: "YYYY-MM"
    pages: 100

  characteristics:
    has_text_layer: true
    is_scanned: false
    has_images: true
    has_tables: false
    multi_column: false

  golden_answers:
    must_contain:
      - text: "Expected text snippet"
        confidence: exact|fuzzy
        fuzzy_threshold: 0.85  # Only for fuzzy
        description: "Why this text matters"

    patterns:
      - pattern: "regex\\d+"
        min_matches: 1
        description: "What this pattern validates"

    structure:
      min_chunks: 10
      max_chunks: 50

    quality:
      min_text_extraction_ratio: 0.90
```

### Extracting Golden Answers

1. **Download the document** and manually inspect
2. **Identify key text** that should always be extracted:
   - Title and headers
   - Distinctive phrases
   - Author names, dates
3. **Set appropriate fuzzy thresholds**:
   - Digital PDFs: 0.95+ (exact preferred)
   - Clean scans: 0.85-0.90
   - Historical/degraded: 0.70-0.80

## CI/CD Integration

### Offline Mode

Tests run without network access using the committed `samples/` directory:

```python
@pytest.fixture
def offline_mode():
    return os.environ.get("RAGD_OFFLINE_TESTS", "0") == "1"
```

### Downloading Fixtures

Fixtures are downloaded on first test run and cached in `generated/`:

```python
@pytest.fixture(scope="session")
def alice_in_wonderland_pdf():
    return download_fixture("alice_in_wonderland")
```

---

## Related Documentation

- [Test Fixtures Specification](../../docs/reference/test-fixtures.md)

---
