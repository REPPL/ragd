# Devlog: v0.4.0 Multi-Modal

**Version:** v0.4.0
**Status:** Backfilled 2025-12-03

---

## Summary

Extension of ragd beyond text-only RAG with vision embeddings and image retrieval capabilities using ColPali/ColQwen2.

## Key Decisions

### Vision Architecture

1. **Separate ImageStore**: Different embedding dimensions from text (128 vs 384)
2. **ColPali embedder**: State-of-the-art vision-language model
3. **Lazy model loading**: Only load vision model when needed

### Image Extraction

- PyMuPDF (fitz) for PDF image extraction
- Configurable minimum dimensions
- Content-hash deduplication

### Multi-Modal Search

| Query Type | Function |
|------------|----------|
| Text → Images | `search_images()` |
| Image → Images | `search_similar_images()` |
| Bytes → Images | `search_images_by_bytes()` |

## Challenges

1. **Model size**: ColPali is large (~2GB), needed lazy loading
2. **Dimension mismatch**: Separate storage for text vs image vectors
3. **GPU memory**: Managing memory for multiple models

## Lessons Learned

- Vision embeddings require different architecture than text
- Lazy loading is essential for large models
- Users with limited hardware need graceful degradation

---

**Note:** This devlog was created retroactively to establish documentation consistency.
