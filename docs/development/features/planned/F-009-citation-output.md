# F-009: Citation Output

## Overview

**Use Case**: [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md)
**Milestone**: v0.1 (basic), v0.3 (full)
**Priority**: P1

## Problem Statement

Users need to verify where search results come from. Without clear source attribution, users cannot:
- Verify accuracy of retrieved information
- Navigate to original documents
- Create proper citations for academic/professional use

## Design Approach

### Architecture

```
Search Results (from F-005)
    ↓
Citation Formatter
    ├── Inline Citations [1], [2], [3]
    ├── Source List (document, page)
    ├── Direct Quotes (--quotes)
    └── Academic Styles (--cite-style)
    ↓
Formatted Output (to F-006)
```

### Citation Components

| Component | v0.1 | v0.3 |
|-----------|------|------|
| Source file name | ✓ | ✓ |
| Page number | ✓ | ✓ |
| Inline markers [1] | | ✓ |
| Direct quotes | | ✓ |
| Academic styles | | ✓ |
| Source links | | ✓ |
| Bibliography export | | ✓ |

### Output Formats

**v0.1 - Basic Attribution:**
```
1. document.pdf (Score: 0.89)
   Page 5
   ┌────────────────────────────────────┐
   │ Machine learning is a subset of   │
   │ artificial intelligence...        │
   └────────────────────────────────────┘
```

**v0.3 - Full Citations:**
```
Machine learning is "a subset of artificial intelligence" [1].

Sources:
[1] Smith, J. (2024). Introduction to ML. document.pdf, p.5
    file:///path/to/document.pdf#page=5
```

## Implementation Tasks

### v0.1 (MVP)
- [ ] Display source file name in search results
- [ ] Display page number for PDF chunks
- [ ] Include source data in JSON output
- [ ] Format source info in Rich output

### v0.3 (Full Citations)
- [ ] Implement inline citation markers [1], [2]
- [ ] Add `--quotes` flag for direct quotes
- [ ] Implement academic citation formatters (APA, IEEE, ACM, Chicago)
- [ ] Add `--cite-style` flag
- [ ] Generate clickable source links (PDF fragment identifiers)
- [ ] Add bibliography export (`--bibliography bibtex`)
- [ ] Support author-date inline format (Smith, 2024)
- [ ] Write unit tests for citation formatters
- [ ] Write integration tests for CLI flags

## Success Criteria

### v0.1
- [ ] Source file displayed with every search result
- [ ] Page number displayed for PDF sources
- [ ] JSON output includes source metadata

### v0.3
- [ ] Inline citations link to source list
- [ ] Direct quotes extracted correctly
- [ ] All 4 academic styles format correctly
- [ ] PDF links open at correct page
- [ ] BibTeX export is valid

## Dependencies

- F-005: Semantic Search (provides SearchResult with location)
- F-006: Result Formatting (renders citations)
- Rich (terminal formatting)
- pypdf or similar (page number extraction)

## Technical Notes

### Citation Data Model

```python
@dataclass
class Citation:
    """A citation reference."""
    id: int                    # [1], [2], etc.
    content: str               # Quoted text
    source: SourceMetadata     # Document info
    location: SourceLocation   # Page, char range

@dataclass
class SourceMetadata:
    """Document source information."""
    file_path: str
    file_name: str
    file_type: str
    title: str | None = None
    author: str | None = None
    date: str | None = None

@dataclass
class SourceLocation:
    """Location within document."""
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None
```

### Citation Style Interface

```python
class CitationStyle(Protocol):
    """Format citations in a specific style."""

    def format_inline(self, citation: Citation) -> str:
        """Format inline reference, e.g., [1] or (Smith, 2024)."""
        ...

    def format_reference(self, citation: Citation) -> str:
        """Format full reference for source list."""
        ...

    def format_bibtex(self, citation: Citation) -> str:
        """Format as BibTeX entry."""
        ...
```

### CLI Integration

```bash
# v0.1 - Basic (default)
ragd search "machine learning"

# v0.3 - With quotes
ragd search "machine learning" --quotes

# v0.3 - Academic style
ragd search "machine learning" --cite-style ieee

# v0.3 - Export bibliography
ragd search "machine learning" --bibliography bibtex > refs.bib

# v0.3 - JSON with full citation data
ragd search "machine learning" --format json
```

### JSON Output Schema

```json
{
  "query": "machine learning",
  "results": [
    {
      "content": "Machine learning is...",
      "score": 0.89,
      "source": {
        "file": "document.pdf",
        "page": 5,
        "link": "file:///path/to/document.pdf#page=5"
      },
      "citation": {
        "inline": "[1]",
        "reference": "Smith, J. (2024). Introduction to ML."
      }
    }
  ]
}
```

### Configuration

```yaml
# ~/.ragd/config.yaml
citations:
  style: plain           # apa | ieee | acm | chicago | plain
  inline_format: numeric # numeric | author-date
  show_page: true
  link_to_source: true
  max_quote_length: 200
```

## Related Documentation

- [F-005: Semantic Search](../completed/F-005-semantic-search.md) - Provides search results
- [F-006: Result Formatting](../completed/F-006-result-formatting.md) - Renders output
- [ADR-0006: Citation System](../../decisions/adrs/0006-citation-system.md) - Architecture decision
- [Citation Systems Research](../../research/citation-systems.md) - Research background

---
