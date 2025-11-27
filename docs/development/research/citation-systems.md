# Citation Systems Research

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

Best practices for citing documents in RAG systems.

## Executive Summary

Citations in RAG systems serve verifiability, trust, accountability, and compliance. This research covers source metadata storage, citation output formats, academic citation styles, and quality metrics from the ALCE benchmark.

---

## 1. Why Citations Matter in RAG

| Benefit | Description |
|---------|-------------|
| **Verifiability** | Users can check original sources |
| **Trust** | Transparent attribution builds confidence |
| **Accountability** | Clear provenance of information |
| **Compliance** | Academic/professional citation requirements |

Without citations, RAG systems become "black boxes" where users cannot verify the accuracy of generated responses.

---

## 2. Citation Architecture

### Source Metadata Storage

Each chunk should store rich metadata for citation:

```python
{
    "chunk_id": "abc123",
    "content": "The actual text content...",
    "source": {
        "file_path": "/documents/paper.pdf",
        "file_name": "paper.pdf",
        "file_type": "pdf",
        "title": "Introduction to Machine Learning",
        "author": "J. Smith",
        "date": "2024-01-15",
        "url": "https://example.com/paper.pdf"  # if applicable
    },
    "location": {
        "page_number": 5,           # 1-indexed for humans
        "page_range": [5, 6],       # if spans pages
        "paragraph": 3,
        "char_start": 1234,         # for precise quotes
        "char_end": 1567,
        "bounding_box": {...}       # for visual attribution
    }
}
```

### Metadata Extraction Points

| Document Type | Available Metadata |
|---------------|-------------------|
| PDF | Title, author, page numbers, bounding boxes |
| Markdown | Headings, line numbers |
| HTML | Title, URL, anchors |
| Plain Text | Line numbers, character offsets |

---

## 3. Citation Output Formats

### Format 1: Inline Citations (Default)

Numeric markers with source list at end:

```
Machine learning is "a subset of artificial intelligence that enables
systems to learn from data" [1]. This approach has revolutionised
many fields including healthcare [2] and finance [1, 3].

Sources:
[1] paper.pdf, p.5
[2] medical-ai.pdf, p.12-13
[3] finance-report.pdf, p.8
```

### Format 2: Direct Quotes with Attribution

For `--quotes` flag:

```
From "Introduction to Machine Learning" (paper.pdf, page 5):

> "Machine learning is a subset of artificial intelligence that
> enables systems to learn from data without being explicitly
> programmed."
```

### Format 3: Structured JSON

For `--format json`:

```json
{
  "answer": "Machine learning is...",
  "citations": [
    {
      "id": 1,
      "quote": "a subset of artificial intelligence...",
      "source": {
        "title": "Introduction to Machine Learning",
        "file": "paper.pdf",
        "page": 5,
        "link": "file:///documents/paper.pdf#page=5"
      }
    }
  ]
}
```

---

## 4. Academic Citation Styles

### APA (7th Edition)

```
Smith, J. (2024). Introduction to machine learning. Publisher.
```

Format: `Author, A. A. (Year). Title of work. Publisher.`

### IEEE

```
[1] J. Smith, "Introduction to Machine Learning," Publisher, 2024.
```

Format: `[N] A. Author, "Title," Publisher, Year.`

### ACM

```
John Smith. 2024. Introduction to Machine Learning. Publisher.
```

Format: `Full Name. Year. Title. Publisher.`

### Chicago (Author-Date)

```
Smith, John. 2024. Introduction to Machine Learning. Publisher.
```

Format: `Last, First. Year. Title. Publisher.`

### Plain (Default)

```
paper.pdf, p.5
```

Minimal format for quick reference.

---

## 5. Source Linking

### PDF Links (Fragment Identifiers)

```
file:///path/to/document.pdf#page=5
```

PDF viewers support `#page=N` fragments for direct navigation.

### HTML Links (Anchors)

```
https://example.com/article.html#section-3
```

Link to specific sections when anchors are available.

### Local File Links (Platform-Specific)

| Platform | Format |
|----------|--------|
| macOS | `file:///Users/name/Documents/paper.pdf` |
| Linux | `file:///home/name/Documents/paper.pdf` |
| Windows | `file:///C:/Users/name/Documents/paper.pdf` |

---

## 6. Citation Generation Workflow

```
1. RETRIEVE relevant chunks with metadata
        ↓
2. EXTRACT quotes and source info
        ↓
3. GENERATE response with inline markers [1], [2]
        ↓
4. FORMAT citations based on user preference
        ↓
5. RENDER with links to original sources
```

### Implementation Considerations

1. **Deduplication** - Same source across multiple chunks gets single citation number
2. **Page ranges** - Combine consecutive pages: `p.5-6` not `p.5, p.6`
3. **Quote truncation** - Long quotes truncated with ellipsis
4. **Link validation** - Verify file exists before generating link

---

## 7. Configuration

### User Settings

```yaml
# ~/.ragd/config.yaml
citations:
  style: apa           # apa | ieee | acm | chicago | plain
  inline_format: numeric  # numeric [1] | author-date (Smith, 2024)
  show_quotes: true    # Include direct quotes
  show_page: true      # Include page numbers
  link_to_source: true # Create clickable links
  max_quote_length: 200  # Characters before truncating
```

### CLI Flags

```bash
# Default: inline citations with source list
ragd search "machine learning definition"

# Include direct quotes
ragd search "machine learning definition" --quotes

# Specific citation format
ragd search "neural networks" --cite-style ieee

# Export bibliography
ragd search "deep learning" --bibliography bibtex > refs.bib

# JSON with full citation metadata
ragd search "AI ethics" --format json --citations
```

---

## 8. Bibliography Export

### BibTeX Format

```bibtex
@misc{paper_pdf,
    title = {Introduction to Machine Learning},
    author = {Smith, J.},
    year = {2024},
    howpublished = {paper.pdf},
    note = {Local document}
}
```

### RIS Format

```
TY  - GEN
TI  - Introduction to Machine Learning
AU  - Smith, J.
PY  - 2024
ER  -
```

---

## 9. Citation Quality Metrics

From the ALCE (Automatic LLM Citation Evaluation) benchmark:

| Metric | Definition |
|--------|------------|
| **Citation Precision** | Percentage of citations that support their claims |
| **Citation Recall** | Percentage of citation-worthy claims that are cited |
| **Citation F1** | Harmonic mean of precision and recall |

### Quality Targets

| Metric | Target |
|--------|--------|
| Citation Precision | > 90% |
| Citation Recall | > 80% |
| Citation F1 | > 85% |

**Source**: [ALCE: Enabling LLMs to Generate Text with Citations](https://arxiv.org/abs/2305.14627)

---

## 10. Implementation in ragd

### v0.1 (MVP) Requirements

- Store page numbers with PDF chunks
- Display source file in search results
- Include source in JSON output

### Future Enhancements

- Full academic citation style support
- Bibliography export
- Author-date inline citations
- Citation quality metrics

---

## Research Sources

| Source | Topic | URL |
|--------|-------|-----|
| ALCE Benchmark | Citation Evaluation | [arXiv:2305.14627](https://arxiv.org/abs/2305.14627) |
| Claude Docs | Native Citations | [docs.claude.com](https://docs.claude.com/en/docs/build-with-claude/citations) |
| LlamaIndex | Citation Query Engine | [docs.llamaindex.ai](https://docs.llamaindex.ai/en/stable/examples/workflow/citation_query_engine/) |
| LangChain | Citations | [python.langchain.com](https://python.langchain.com/v0.1/docs/use_cases/question_answering/citations/) |
| SciRAG | Citation-Aware RAG | [arXiv:2511.14362](https://arxiv.org/html/2511.14362) |
| Tensorlake | Fine-Grained Citations | [tensorlake.ai](https://www.tensorlake.ai/blog/rag-citations) |

---

## Related Documentation

- [ADR-0006: Citation System](../decisions/adrs/0006-citation-system.md)
- [F-009: Citation Output](../features/completed/F-009-citation-output.md)
- [F-005: Semantic Search](../features/completed/F-005-semantic-search.md)

---

**Status:** Research complete
