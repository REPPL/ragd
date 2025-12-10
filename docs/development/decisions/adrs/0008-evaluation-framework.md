# ADR-0008: Evaluation Framework

## Status

Accepted

## Context

RAG systems need objective quality measurement for:
- Regression testing during development
- Configuration tuning (chunk size, model selection)
- User confidence in results

The RAGAS framework provides industry-standard metrics without human labelling.

## Decision

Integrate RAGAS for automated RAG quality evaluation in v0.5:

### Core Metrics

| Metric | Measures | Requires |
|--------|----------|----------|
| **Context Precision** | Are retrieved docs relevant? | Search only |
| **Context Recall** | Were all relevant docs retrieved? | Search + ground truth |
| **Faithfulness** | Is response grounded in context? | Generation |
| **Answer Relevancy** | Does answer address the question? | Generation |

### Implementation Phases

**v0.5.0 - Retrieval Metrics:**
- Context Precision (no generation needed)
- Basic relevance scoring

**v0.5.1 - Full Evaluation:**
- Faithfulness (requires Ollama/LLM)
- Answer Relevancy
- `ragd evaluate` CLI command

### CLI Integration

```bash
# Evaluate search quality
ragd evaluate --query "..." --expected "..."

# Batch evaluation
ragd evaluate --test-file queries.yaml

# Show metrics
ragd evaluate --metrics precision,recall
```

### Output

```json
{
  "metrics": {
    "context_precision": 0.85,
    "context_recall": 0.78,
    "faithfulness": 0.92,
    "answer_relevancy": 0.88
  },
  "overall_score": 0.86
}
```

## Consequences

### Positive

- Objective quality measurement
- Automated regression detection
- Industry-standard metrics
- No manual labelling required
- Enables informed tuning decisions

### Negative

- Full metrics require LLM integration (v0.5)
- RAGAS dependency
- Evaluation adds processing time
- Ground truth needed for recall metrics

## Related Documentation

- [State-of-the-Art RAG Research](../../research/state-of-the-art-rag.md)
- [F-013: RAGAS Evaluation](../../features/completed/F-013-ragas-evaluation.md)
- [RAGAS Documentation](https://docs.ragas.io/)

---
