# F-100: New File Type Support

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Users have documents in EPUB, DOCX, and XLSX formats that cannot be indexed. Need to expand file type support.

## Design Approach

Add extractors for common office and ebook formats using established libraries.

### Supported Types
- **EPUB** - EBooks (ebooklib)
- **DOCX** - Word documents (python-docx)
- **XLSX** - Excel spreadsheets (openpyxl)

### Architecture
```python
class EPUBExtractor:
    """Extract text from EPUB ebooks."""

class DOCXExtractor:
    """Extract text from Word documents."""

class XLSXExtractor:
    """Extract text from Excel spreadsheets."""
```

## Implementation

### Files Created
- `src/ragd/ingestion/office.py` - Office document extractors

### Key Components

**DOCXExtractor** (lines 14-72):
- Extracts paragraphs from Word documents
- Extracts table content with pipe-separated cells
- Returns metadata: source, format, paragraph count, table count

**XLSXExtractor** (lines 75-136):
- Reads all sheets in workbook
- Formats each sheet with header
- Pipe-separated cell values per row
- Returns metadata: source, format, sheet count

**EPUBExtractor** (lines 139-203):
- Extracts all document items from EPUB
- Parses HTML content using BeautifulSoup
- Extracts title and author metadata
- Returns: source, format, chapter count, title, creator

**Factory Function** (lines 206-224):
- `get_office_extractor(path)` - Returns appropriate extractor based on extension
- Case-insensitive extension matching

## Implementation Tasks

- [x] Add ebooklib, python-docx, openpyxl dependencies
- [x] Create EPUBExtractor class
- [x] Create DOCXExtractor class
- [x] Create XLSXExtractor class
- [x] Register extractors in factory
- [x] Update file type detection
- [x] Add tests for each format

## Success Criteria

- [x] EPUB files indexed correctly
- [x] DOCX files indexed with formatting preserved
- [x] XLSX files indexed with sheet structure

## Testing

- 6 tests in `tests/test_ingestion_enhanced.py`
- Tests extractor factory, extension matching, error handling
- All tests passing

## Dependencies

- ebooklib (optional)
- python-docx (optional)
- openpyxl (optional)

## Related Documentation

- [F-002: Text Extraction](./F-002-text-extraction.md)
- [v0.9.0 Implementation](../../implementation/v0.9.0.md)

---

**Status**: Completed
