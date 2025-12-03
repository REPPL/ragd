# Devlog: v0.5.0 Chat

**Version:** v0.5.0
**Status:** Backfilled 2025-12-03

---

## Summary

Transformation of ragd from a retrieval tool into a conversational knowledge assistant with local LLM integration via Ollama.

## Key Decisions

### LLM Integration

1. **Ollama**: Privacy-first, fully local LLM serving
2. **Streaming responses**: Real-time token output for better UX
3. **Multi-model support**: Route tasks to appropriate models

### Agentic RAG

| Feature | Purpose |
|---------|---------|
| CRAG | Query rewriting when retrieval is poor |
| Self-RAG | Faithfulness verification |
| Confidence scores | User-facing quality indicators |

### Chat Architecture

- **Session persistence**: Resume conversations
- **History management**: Context window tracking
- **Citation integration**: Source attribution in responses

## Challenges

1. **Streaming complexity**: Async token handling
2. **Context window management**: Fitting history + context + query
3. **Model availability**: Graceful handling when Ollama unavailable

## Key Insight

Agentic RAG (CRAG + Self-RAG) significantly improves answer quality, but adds latency. Made configurable via `--agentic` flag.

## Lessons Learned

- Streaming UX is essential for LLM interactions
- Context window management is non-trivial
- Local LLMs vary significantly in quality

---

**Note:** This devlog was created retroactively to establish documentation consistency.
