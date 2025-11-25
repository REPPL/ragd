# ADR-0006: Citation System Architecture

## Status

Accepted

## Context

RAG systems often produce responses without clear attribution, making it difficult for users to verify information or locate original sources. This undermines trust and limits academic/professional use.

ragd needs a citation system that:
- Shows where information comes from
- Supports academic citation formats
- Links to original documents
- Works across all output modes

## Decision

Implement a multi-layer citation system:

### 1. Source Metadata Storage

Store rich metadata with each chunk:

```python
{
    "chunk_id": "abc123",
    "content": "The text...",
    "source": {
        "file_path": "/path/to/document.pdf",
        "file_name": "document.pdf",
        "file_type": "pdf",
        "title": "Document Title",
        "author": "Author Name",
        "date": "2024-01-15"
    },
    "location": {
        "page_number": 5,
        "char_start": 1234,
        "char_end": 5678
    }
}
```

### 2. Citation Output Formats

**Inline Citations (default):**
```
Machine learning enables... [1]. Applications include healthcare [2].

Sources:
[1] document.pdf, p.5
[2] medical.pdf, p.12
```

**Direct Quotes (`--quotes`):**
```
From "Document Title" (document.pdf, page 5):
> "Machine learning enables systems to..."
```

**JSON (`--format json`):**
```json
{
  "answer": "...",
  "citations": [
    {"id": 1, "source": {...}, "quote": "..."}
  ]
}
```

### 3. Academic Citation Styles

Support configurable styles:
- **APA**: `Smith, J. (2024). Title. Publisher.`
- **IEEE**: `[1] J. Smith, "Title," Publisher, 2024.`
- **ACM**: `John Smith. 2024. Title. Publisher.`
- **Chicago**: `Smith, John. Title. Publisher, 2024.`
- **Plain**: `document.pdf, p.5` (default)

### 4. Source Linking

Generate clickable links to original documents:
- PDF: `file:///path/document.pdf#page=5`
- HTML: `https://example.com/article.html#section`
- Local: Platform-appropriate `file://` URLs

### 5. Configuration

```yaml
citations:
  style: plain        # apa | ieee | acm | chicago | plain
  show_page: true     # Include page numbers
  link_to_source: true
  max_quote_length: 200
```

## Consequences

### Positive

- Users can verify information sources
- Academic/professional citation requirements met
- Transparent attribution builds trust
- Multiple format options for different use cases
- Foundation for future features (bibliography export)

### Negative

- Additional metadata storage overhead
- More complex document processing
- Citation formatting logic to maintain
- User education needed for citation options

## Implementation Phases

**v0.1 (MVP):**
- Store page numbers with PDF chunks
- Display source file in search results
- Include source in JSON output

**v0.3:**
- Full citation metadata storage
- Academic citation style support
- Source linking

**v0.5:**
- Bibliography export (BibTeX, RIS)
- Citation quality metrics

## Related Documentation

- [Citation Systems Research](../../research/citation-systems.md)
- [F-009: Citation Output](../../features/planned/F-009-citation-output.md)
- [F-005: Semantic Search](../../features/planned/F-005-semantic-search.md)

---
