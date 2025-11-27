# F-010: Contextual Retrieval

## Overview

**Research**: [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)
**ADR**: [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
**Milestone**: v0.3
**Priority**: P1

## Problem Statement

Chunks lose context when separated from their document. A chunk saying "These regulations apply..." doesn't indicate what regulations or from which document. This causes:
- Retrieval failures (67% improvement possible with contextual retrieval)
- Ambiguous results for users
- Poor ranking of semantically relevant content

## Design Approach

### Architecture

```
Document
    ↓
Chunking (F-003)
    ↓
For each chunk:
    ↓
[LLM Context Generation] → "This chunk discusses OAuth authentication
                            from the security documentation..."
    ↓
Embed(Context + Chunk)
    ↓
Store (context stored separately for display)
```

### Context Generation

**Prompt template:**
```
Given this document excerpt, write a brief context statement (1-2 sentences)
that explains what this text is about and where it comes from.

Document title: {title}
Document type: {type}
Section: {section}

Text:
{chunk_content}

Context:
```

**Example output:**
```
This chunk is from the "Security Best Practices" guide
and discusses OAuth 2.0 token validation procedures.
```

### LLM Options

| Provider | Model | Cost | Speed |
|----------|-------|------|-------|
| Ollama | llama3.2:3b | Free (local) | Medium |
| Ollama | phi3:mini | Free (local) | Fast |
| Ollama | qwen2.5:3b | Free (local) | Fast |

> Cloud LLM providers (Claude, OpenAI) are not supported until v2.0+.

## Implementation Tasks

- [ ] Design context generation prompt
- [ ] Implement LLM client interface (Ollama primary)
- [ ] Add context generation to indexing pipeline
- [ ] Store context separately from chunk content
- [ ] Combine context + chunk for embedding
- [ ] Add configuration for enable/disable
- [ ] Add model selection configuration
- [ ] Handle LLM failures gracefully (fallback to no context)
- [ ] Add batch processing for efficiency
- [ ] Write unit tests for context generation
- [ ] Write integration tests for full pipeline
- [ ] Benchmark retrieval improvement

## Success Criteria

- [ ] Context generated for each chunk during indexing
- [ ] Configurable enable/disable per index
- [ ] Works with Ollama (local, free)
- [ ] Graceful fallback when LLM unavailable
- [ ] Measurable retrieval quality improvement
- [ ] Indexing time increase < 5x

## Dependencies

- F-003: Chunking Engine
- F-004: Embedding Generation
- Ollama (or alternative LLM provider)

## Technical Notes

### Data Model

```python
@dataclass
class ContextualChunk:
    content: str           # Original chunk text
    context: str          # Generated context
    combined: str         # Context + Content (for embedding)
    metadata: dict
```

### Configuration

```yaml
retrieval:
  contextual:
    enabled: true
    provider: ollama      # Local only (cloud providers in v2.0+)
    model: llama3.2:3b
    batch_size: 10
    timeout_seconds: 30
```

### CLI

```bash
# Index with contextual retrieval
ragd index ~/Documents/ --contextual

# Disable contextual retrieval
ragd index ~/Documents/ --no-contextual

# Check if contextual is enabled
ragd config show retrieval.contextual.enabled
```

## Related Documentation

- [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
- [F-011: Late Chunking](./F-011-late-chunking.md) - Alternative approach
- [F-012: Hybrid Search](./F-012-hybrid-search.md) - Complementary feature
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

---
