# ADR-0025: Advanced HTML Processing Architecture

## Status

Accepted

## Context

F-038 (Web Archive Support) introduced trafilatura for content extraction from SingleFile archives. However, general HTML processing remained basic:

1. BeautifulSoup is used for all HTML parsing (slow)
2. Metadata extraction is limited to basic tags
3. Document structure (tables, headings, lists) is flattened
4. No tiered processing based on document complexity

We needed to decide how to extend HTML capabilities without duplicating F-038 functionality.

## Decision

Implement F-039 as an **enhancement layer** on top of F-038, extending `src/ragd/web/` rather than creating a new module.

### Architecture

```
HTML Input
    ↓
[Check] Is SingleFile archive?
    ├─ YES → WebArchiveProcessor (F-038)
    └─ NO → F-039 enhanced processing
    ↓
[Tier 1] selectolax parse (<5ms)
    ↓
[Tier 2] Complexity detection
    ├─ Simple → selectolax fast path
    └─ Complex → trafilatura (reuse F-038)
    ↓
[Tier 3] Rich metadata extraction (lazy)
    ↓
[Tier 4] Structure extraction (optional)
    ↓
ExtractionResult
```

### Key Decisions

1. **Extend, don't duplicate**: Reuse F-038's trafilatura integration
2. **selectolax for speed**: 10-100x faster than BeautifulSoup
3. **Optional dependencies**: Graceful fallback when selectolax unavailable
4. **Tiered processing**: Balance speed vs quality based on content

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| parser.py | `src/ragd/web/` | Fast selectolax parsing |
| metadata.py | `src/ragd/web/` | Rich metadata extraction |
| structure.py | `src/ragd/web/` | Structure preservation |
| StructureChunker | `src/ragd/ingestion/chunker.py` | Structure-aware chunking |
| AdvancedHTMLExtractor | `src/ragd/ingestion/extractor.py` | Unified interface |

## Consequences

### Positive

- Significant performance improvement (10-100x for parsing)
- Rich metadata available for search/filtering
- Tables and headings preserved for better RAG context
- Backwards compatible (existing code unchanged)
- Optional dependencies keep base install small

### Negative

- Added complexity in processing pipeline
- More optional dependencies to manage
- selectolax less mature than BeautifulSoup

### Neutral

- Requires `pip install 'ragd[web]'` for full features
- Two code paths (selectolax vs BeautifulSoup fallback)

## Alternatives Considered

### 1. Create new `src/ragd/html/` module

**Rejected**: Would duplicate trafilatura integration from F-038.

### 2. Replace all HTML processing with trafilatura

**Rejected**: trafilatura is optimised for web content extraction, not general HTML parsing. It's also slower for simple documents.

### 3. Make selectolax a core dependency

**Rejected**: Increases base install size. Optional dependency approach is more flexible.

## Related

- [F-038: Web Archive Support](../../features/completed/F-038-web-archive-support.md)
- [F-039: Advanced HTML Processing](../../features/planned/F-039-advanced-html-processing.md)
- [ADR-0024: Optional Dependencies](./0024-optional-dependencies.md)

---

**Last Updated**: 2025-11-27
