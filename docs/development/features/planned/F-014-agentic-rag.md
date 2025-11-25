# F-014: Agentic RAG

## Overview

**Research**: [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)
**Milestone**: v0.5
**Priority**: P2

## Problem Statement

Basic RAG has a "garbage in, garbage out" problem: if retrieval returns irrelevant chunks, the generated response will be poor. Users have no visibility into retrieval quality and no way to improve it.

Agentic RAG (CRAG, Self-RAG) addresses this by:
- Evaluating retrieval quality before generation
- Rewriting queries when results are poor
- Self-assessing response quality

## Design Approach

### Architecture

```
Query
    ↓
[Retrieve Chunks]
    ↓
[Evaluate Relevance] ──── Low ────┐
    │                             │
    │ Good                        ▼
    ▼                    [Rewrite Query]
[Generate Response]              │
    │                             │
    ▼                    [Retrieve Again]
[Self-Assess Quality]            │
    │                             │
    │ Poor                        │
    ▼                    ─────────┘
[Refine Response]
    │
    ▼
Final Response
```

### CRAG (Corrective RAG)

Evaluate and correct retrieval before generation:

1. **Retrieve** initial chunks
2. **Evaluate** relevance (LLM-based scoring)
3. **If low relevance**: Rewrite query and retry
4. **If still low**: Flag uncertainty in response

### Self-RAG

Self-assess generation quality:

1. **Generate** response from retrieved context
2. **Assess** faithfulness to context
3. **If unfaithful**: Regenerate with stricter prompt
4. **Add confidence** indicator to response

## Implementation Tasks

### CRAG (Phase 1)
- [ ] Design relevance evaluation prompt
- [ ] Implement relevance scoring (0-1 scale)
- [ ] Implement query rewriting
- [ ] Add retry logic with backoff
- [ ] Add "low confidence" flag for poor retrieval
- [ ] Write unit tests
- [ ] Write integration tests

### Self-RAG (Phase 2)
- [ ] Design self-assessment prompt
- [ ] Implement faithfulness checking
- [ ] Implement response regeneration
- [ ] Add confidence scoring
- [ ] Expose confidence in output
- [ ] Write tests

## Success Criteria

- [ ] Retrieval quality evaluated before generation
- [ ] Query rewriting improves poor retrieval
- [ ] Response confidence visible to users
- [ ] 20%+ improvement in response quality (measured via RAGAS)
- [ ] Configurable enable/disable

## Dependencies

- F-005: Semantic Search
- Ollama LLM integration
- F-013: RAGAS Evaluation (for measuring improvement)

## Technical Notes

### Configuration

```yaml
agentic:
  crag:
    enabled: true
    relevance_threshold: 0.6
    max_rewrites: 2
    rewrite_model: llama3.2:3b

  self_rag:
    enabled: true
    faithfulness_threshold: 0.7
    max_refinements: 1
```

### Relevance Evaluation Prompt

```
Given this query and retrieved context, rate the relevance on a scale of 0-1.

Query: {query}

Context:
{context}

Consider:
- Does the context contain information to answer the query?
- Is the context topically relevant?
- Would this context help generate a good response?

Relevance score (0-1):
```

### Query Rewriting Prompt

```
The original query returned irrelevant results. Rewrite it to be more specific.

Original query: {query}

Retrieved (irrelevant) content summary:
{summary}

Rewritten query:
```

### Output with Confidence

```json
{
  "response": "Machine learning is...",
  "confidence": 0.85,
  "retrieval_quality": "good",
  "rewrites_attempted": 0,
  "sources": [...]
}
```

### CLI Integration

```bash
# Default (agentic if configured)
ragd ask "What is machine learning?"

# Force agentic mode
ragd ask "..." --agentic

# Disable agentic (faster, less accurate)
ragd ask "..." --no-agentic

# Show confidence
ragd ask "..." --show-confidence
```

## Related Documentation

- [State-of-the-Art RAG Research](../../research/state-of-the-art-rag.md)
- [F-013: RAGAS Evaluation](./F-013-ragas-evaluation.md)
- [Agentic RAG Survey](https://arxiv.org/abs/2501.09136)

---
