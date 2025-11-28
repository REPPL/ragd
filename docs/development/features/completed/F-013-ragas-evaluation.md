# F-013: RAGAS Evaluation

## Overview

**Research**: [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)
**ADR**: [ADR-0008: Evaluation Framework](../../decisions/adrs/0008-evaluation-framework.md)
**Milestone**: v0.5
**Priority**: P1

## Problem Statement

RAG systems need objective quality measurement for:
- Regression detection during development
- Configuration tuning (chunk size, model selection)
- User confidence in search results

Manual evaluation is time-consuming and subjective. RAGAS provides automated, industry-standard metrics.

## Design Approach

### Architecture

```
Evaluation Request
    ↓
┌─────────────────────────┐
│ RAGAS Evaluation Engine │
├─────────────────────────┤
│ • Context Precision     │
│ • Context Recall        │
│ • Faithfulness          │
│ • Answer Relevancy      │
└─────────────────────────┘
    ↓
Evaluation Report
```

### Metrics

| Metric | Description | Requires LLM |
|--------|-------------|--------------|
| **Context Precision** | Are retrieved docs relevant to the query? | No |
| **Context Recall** | Were all relevant docs retrieved? | No* |
| **Faithfulness** | Is response grounded in retrieved context? | Yes |
| **Answer Relevancy** | Does answer address the question? | Yes |

*Requires ground truth for full accuracy

### Implementation Phases

**Phase 1 (v0.5.0):** Retrieval-only metrics
- Context Precision
- Basic relevance scoring

**Phase 2 (v0.5.1):** Full evaluation
- Faithfulness (requires Ollama)
- Answer Relevancy
- Ground truth support

## Implementation Tasks

### Phase 1
- [ ] Integrate ragas library
- [ ] Implement Context Precision metric
- [ ] Design evaluation CLI interface
- [ ] Add `ragd evaluate` command
- [ ] Implement result storage/history
- [ ] Write unit tests

### Phase 2
- [ ] Implement Faithfulness metric with Ollama
- [ ] Implement Answer Relevancy metric
- [ ] Add ground truth file support
- [ ] Add batch evaluation from file
- [ ] Add metric comparison reports
- [ ] Write integration tests

## Success Criteria

- [ ] `ragd evaluate` command functional
- [ ] Context Precision metric accurate
- [ ] Evaluation history stored locally
- [ ] JSON output for automation
- [ ] Ollama integration for full metrics

## Dependencies

- ragas library
- Ollama (for Faithfulness/Relevancy)
- F-005: Semantic Search

## Technical Notes

### CLI Interface

```bash
# Single query evaluation
ragd evaluate --query "What is machine learning?"

# With expected answer (for recall)
ragd evaluate --query "..." --expected "ML is a subset of AI..."

# Batch evaluation
ragd evaluate --test-file queries.yaml

# Specific metrics
ragd evaluate --query "..." --metrics precision,recall

# JSON output
ragd evaluate --query "..." --format json
```

### Test File Format

```yaml
# queries.yaml
evaluations:
  - query: "What is machine learning?"
    expected: "Machine learning is a subset of AI..."
    tags: [ml, basics]

  - query: "How does OAuth work?"
    expected: "OAuth is an authorization framework..."
    tags: [security, auth]
```

### Output Format

```json
{
  "query": "What is machine learning?",
  "metrics": {
    "context_precision": 0.85,
    "context_recall": 0.78,
    "faithfulness": 0.92,
    "answer_relevancy": 0.88
  },
  "overall_score": 0.86,
  "retrieved_chunks": 5,
  "evaluation_time_ms": 1234
}
```

### Configuration

```yaml
evaluation:
  metrics:
    - context_precision
    - context_recall
    - faithfulness
    - answer_relevancy
  llm_provider: ollama
  llm_model: llama3.2:3b
  store_history: true
  history_path: ~/.ragd/evaluations/
```

### Data Model

```python
@dataclass
class EvaluationResult:
    query: str
    metrics: dict[str, float]
    overall_score: float
    retrieved_chunks: int
    timestamp: datetime
    config: dict

@dataclass
class EvaluationReport:
    results: list[EvaluationResult]
    summary: dict[str, float]  # Averages
    comparison: dict | None    # vs previous
```

## Related Documentation

- [ADR-0008: Evaluation Framework](../../decisions/adrs/0008-evaluation-framework.md)
- [State-of-the-Art RAG Research](../../research/state-of-the-art-rag.md)
- [RAGAS Documentation](https://docs.ragas.io/)

---
