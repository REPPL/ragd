# F-039: Advanced HTML Processing

## Problem Statement

While F-038 (Web Archive Support) provides excellent handling of SingleFile archives, general HTML processing remains basic:
- BeautifulSoup is slow (10-100x slower than alternatives)
- Metadata extraction is limited (no Open Graph, JSON-LD, Schema.org)
- Structure is lost (tables become plain text, heading hierarchy discarded)
- No structure-aware chunking (tables split mid-row)

## Design Approach

### Tiered Processing Architecture

F-039 implements a tiered approach that balances speed and quality:

| Tier | Detection | Method | Time Target |
|------|-----------|--------|-------------|
| 1 | Has `<article>/<main>` + Schema.org | selectolax fast path | <10ms |
| 2 | Clean HTML (low boilerplate) | selectolax + cleanup | <15ms |
| 3 | Complex page (ads, sidebars) | trafilatura | <50ms |

### Key Components

1. **Fast Parser** (`src/ragd/web/parser.py`)
   - selectolax-based parsing (10-100x faster)
   - Complexity detection for routing
   - Graceful fallback to BeautifulSoup

2. **Rich Metadata** (`src/ragd/web/metadata.py`)
   - Open Graph extraction
   - JSON-LD/Schema.org parsing with @graph support
   - Dublin Core metadata
   - Twitter Cards
   - Priority-based resolution

3. **Structure Preservation** (`src/ragd/web/structure.py`)
   - Heading hierarchy extraction
   - Table-to-Markdown conversion
   - List structure preservation
   - Code block detection

4. **Structure-Aware Chunking** (`src/ragd/ingestion/chunker.py`)
   - `StructureChunker` class
   - Respects heading boundaries
   - Keeps tables together
   - Preserves list integrity

5. **Enhanced Extractor** (`src/ragd/ingestion/extractor.py`)
   - `AdvancedHTMLExtractor` class
   - Integrates all F-039 components
   - Routes SingleFile archives to F-038
   - Falls back gracefully without optional dependencies

## Implementation Tasks

- [x] Create `src/ragd/web/parser.py` - Fast HTML parsing
- [x] Create `src/ragd/web/metadata.py` - Rich metadata extraction
- [x] Create `src/ragd/web/structure.py` - Structure preservation
- [x] Add `StructureChunker` to `chunker.py`
- [x] Create `AdvancedHTMLExtractor` in `extractor.py`
- [x] Add selectolax/trafilatura feature detection to `features.py`
- [x] Update `web/__init__.py` exports
- [x] Create unit tests for parser, metadata, structure
- [x] Create manual test script (`manual_v025_tests.py`)

## Success Criteria

- [x] selectolax parsing 10x+ faster than BeautifulSoup
- [x] Open Graph, JSON-LD, Schema.org metadata extracted
- [x] Tables converted to Markdown format
- [x] Heading hierarchy preserved
- [x] Structure-aware chunking available
- [x] All existing tests pass (backwards compatible)
- [x] 78 new unit tests pass

## Dependencies

- **F-038**: Web Archive Support (provides trafilatura integration)
- **Optional**: selectolax (for fast parsing)
- **Optional**: trafilatura (for complex page extraction)

## Data Structures

### HTMLMetadata

```python
@dataclass
class HTMLMetadata:
    # Basic
    title: str | None = None
    description: str | None = None
    author: str | None = None
    language: str | None = None
    publication_date: datetime | None = None

    # Open Graph
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None
    og_site_name: str | None = None

    # Schema.org/JSON-LD
    schema_type: str | None = None
    schema_data: dict[str, Any] = field(default_factory=dict)

    # Web archive (F-038 compatibility)
    original_url: str | None = None
    archive_date: datetime | None = None
```

### HTMLStructure

```python
@dataclass
class HTMLStructure:
    headings: list[HeadingInfo]
    tables: list[TableInfo]
    lists: list[ListInfo]
    code_blocks: list[CodeBlockInfo]
```

## Related Documentation

- [F-038: Web Archive Support](../completed/F-038-web-archive-support.md)
- [ADR-0019: PDF Processing](../../decisions/adrs/0019-pdf-processing.md)
- [v0.2.5 Retrospective](../../process/retrospectives/v0.2.5-retrospective.md)
