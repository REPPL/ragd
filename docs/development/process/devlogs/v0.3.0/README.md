# Devlog: v0.3.0 Advanced Search

**Version:** v0.3.0
**Status:** Backfilled 2025-12-03

---

## Summary

Implementation of advanced search capabilities: hybrid search (BM25 + semantic), contextual retrieval, late chunking, and academic citation formats.

## Key Decisions

### Hybrid Search Architecture

1. **BM25 + Semantic**: Lexical and semantic retrieval combined
2. **Reciprocal Rank Fusion**: Elegant score combination method
3. **Configurable weights**: User control over retrieval balance

### Contextual Retrieval (Anthropic-style)

- LLM-powered context generation for chunks
- Ollama integration for local processing
- Optional enhancement (not required for basic search)

### Citation System

| Format | Use Case |
|--------|----------|
| APA | Academic papers |
| MLA | Humanities |
| Chicago | Publishing |
| BibTeX | LaTeX integration |
| Inline | Quick reference |

## Challenges

1. **Score fusion**: Normalising scores across different retrieval methods
2. **Context generation latency**: Balancing quality vs speed
3. **Citation edge cases**: Handling missing metadata gracefully

## Lessons Learned

- RRF is surprisingly effective with minimal tuning
- Late chunking improves retrieval for long documents
- Citation formats have many subtle variations

---

**Note:** This devlog was created retroactively to establish documentation consistency.
