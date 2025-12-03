# Devlog: v0.6.0 Storage

**Version:** v0.6.0
**Status:** Backfilled 2025-12-03

---

## Summary

Storage layer abstraction enabling multiple vector database backends. ChromaDB remains default, FAISS added as high-performance alternative.

## Key Decisions

### Abstraction Pattern

1. **Protocol-based**: Python Protocols for type-safe duck typing
2. **Factory pattern**: Centralised backend instantiation
3. **Adapter pattern**: Consistent interface across backends

### FAISS Integration

| Challenge | Solution |
|-----------|----------|
| No metadata filtering | SQLite proxy layer |
| Score interpretation | Normalisation to 0-1 |
| Index selection | Auto-detect based on size |

### Score Normalisation (Critical)

Essential for Agentic RAG consistency:
- ChromaDB L2 distance → 0-1
- FAISS variable range → 0-1

Without this, CRAG/Self-RAG confidence thresholds would break across backends.

## Challenges

1. **Metadata filtering**: FAISS has no native filtering
2. **Score interpretation**: Different backends, different scales
3. **Index type selection**: IVF vs HNSW vs Flat

## Key Insight

SQLite metadata proxy was the elegant solution for FAISS filtering - simpler than custom index structures, and leverages well-tested technology.

## Lessons Learned

- Protocol-based abstraction > ABC inheritance
- Score normalisation is architectural, not cosmetic
- SQLite is underrated for metadata storage

---

**Note:** This devlog was created retroactively to establish documentation consistency.
