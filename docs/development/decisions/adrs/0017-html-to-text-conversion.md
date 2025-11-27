# ADR-0017: HTML-to-Text Conversion Strategy

## Status

Accepted

## Context

ragd needs to convert HTML content to text or Markdown for:
- Indexing web archives (F-038)
- Text extraction from HTML documents (F-002)
- Creating searchable chunks with preserved structure

The state-of-the-art-html-processing.md research document compares several libraries for this task. The comparison shows inscriptis with "Excellent" formatting quality, yet trafilatura is recommended. This ADR clarifies the reasoning behind that choice.

### Key Requirements for RAG

1. **Semantic structure preservation**: Headings, lists, and emphasis improve chunking and retrieval
2. **Link preservation**: ragd's citation system requires source URLs for attribution
3. **Clean extraction**: Remove boilerplate (navigation, ads, sidebars)
4. **Consistent output**: Predictable format for downstream processing

## Decision

Use **trafilatura** as the primary HTML-to-text/Markdown converter, with **html2text** as a fallback for simple HTML-to-Markdown conversion when extraction is not needed.

### Library Comparison

| Library | Output Format | Link Preservation | Structure Type | Primary Use Case |
|---------|---------------|-------------------|----------------|------------------|
| **trafilatura** | Text + Markdown | Yes | Semantic | RAG indexing, article extraction |
| **inscriptis** | Text only | No | Visual layout | Accessibility, email rendering |
| **html2text** | Markdown | Yes | Semantic | Simple HTML→Markdown |
| **markdownify** | Markdown | Yes | Semantic | Direct HTML→Markdown |

### Why trafilatura?

1. **Dual capability**: Performs both content extraction AND format conversion
   - Identifies main article content (reader view)
   - Converts to Markdown with structure preserved
   - Single library, single pass

2. **Link preservation**: Maintains hyperlinks for citations
   - Critical for ragd's attribution requirements
   - Enables "View original source" functionality

3. **Semantic structure**: Outputs Markdown with proper hierarchy
   - Headings become `##`, `###` etc.
   - Lists become `-` or `1.` items
   - Enables better semantic chunking

4. **Benchmark performance**: Best precision/recall in academic benchmarks
   - Outperforms alternatives on article extraction accuracy
   - Actively maintained with regular updates

### Why Not inscriptis?

Despite inscriptis having "Excellent" formatting quality for text output:

1. **Text-only output**: No Markdown support
   - Loses semantic structure (headings become plain text)
   - No emphasis markers (bold, italic)
   - Harder to chunk semantically

2. **No link preservation**: URLs are stripped from output
   - Breaks citation system requirement
   - Cannot attribute content to sources

3. **Visual layout focus**: Preserves how content looks, not what it means
   - Tables rendered as ASCII art (good for display, bad for indexing)
   - Spacing preserved (useful for email, wasteful for RAG)

4. **No content extraction**: Works on full HTML, doesn't identify main content
   - Requires separate boilerplate removal step
   - Additional complexity in pipeline

### When inscriptis Is Appropriate

inscriptis remains a good choice for:
- **Email rendering**: Converting HTML emails to readable plain text
- **Accessibility**: Screen reader-friendly text output
- **CLI display**: When ASCII table layout improves comprehension
- **No attribution needs**: When links don't matter

### Implementation

```python
import trafilatura

def extract_for_indexing(html: str) -> str:
    """Extract main content as Markdown for RAG indexing."""
    return trafilatura.extract(
        html,
        output_format="markdown",
        include_links=True,      # Preserve for citations
        include_tables=True,
        favor_precision=True,    # Prefer accuracy over recall
    )

def extract_with_metadata(html: str) -> dict:
    """Extract content with full metadata."""
    result = trafilatura.bare_extraction(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    return {
        "title": result.get("title"),
        "author": result.get("author"),
        "date": result.get("date"),
        "text": result.get("text"),
        "url": result.get("url"),
        "language": result.get("language"),
    }
```

### Fallback: html2text

For simple HTML fragments where extraction isn't needed:

```python
import html2text

def html_fragment_to_markdown(html: str) -> str:
    """Convert HTML fragment to Markdown (no extraction)."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    return h.handle(html)
```

## Consequences

### Positive

- Single library for extraction + conversion
- Links preserved for citation system
- Semantic structure improves chunking quality
- Best-in-class accuracy for article extraction
- Markdown output integrates well with existing document pipeline

### Negative

- trafilatura is larger dependency (~10MB with dependencies)
- May over-extract from simple HTML (designed for articles)
- Markdown formatting may need post-processing for edge cases
- inscriptis' superior visual formatting not leveraged

## Alternatives Considered

### inscriptis

- **Pros:** Excellent text formatting, fast, lightweight
- **Cons:** No links, text-only, no extraction
- **Rejected:** Link preservation required for citations

### html2text

- **Pros:** Good Markdown output, lightweight
- **Cons:** No content extraction, less accurate
- **Rejected:** trafilatura handles full pipeline better

### markdownify

- **Pros:** Direct HTML→Markdown, simple
- **Cons:** No extraction, just format conversion
- **Rejected:** Need extraction + conversion together

### BeautifulSoup + custom extraction

- **Pros:** Full control, no additional dependencies
- **Cons:** Significant development effort, reinventing wheel
- **Rejected:** trafilatura already solves this well

## Related Documentation

- [State-of-the-Art HTML Processing](../../research/state-of-the-art-html-processing.md)
- [F-002: Text Extraction](../../features/completed/F-002-text-extraction.md)
- [F-038: Web Archive Support](../../features/completed/F-038-web-archive-support.md)
- [ADR-0015: Web Archive Processing](./0015-web-archive-processing.md)
- [ADR-0006: Citation System](./0006-citation-system.md)

