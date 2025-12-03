# F-076: RAGAS Evaluation Metrics

## Overview

**Milestone**: v0.6.5
**Priority**: P1
**Depends On**: [F-013](../completed/F-013-ragas-evaluation.md)

## Problem Statement

The existing evaluation system (F-013) provides retrieval-focused metrics (context precision, recall) but lacks LLM-dependent metrics that assess response quality. RAGAS framework includes faithfulness and answer relevancy metrics that require LLM calls, which should be optional.

## Design Approach

### New Metrics

**Faithfulness**: Is the answer grounded in the retrieved context?
- Uses LLM to break answer into claims
- Verifies each claim against context
- Returns score 0-1 (higher = more grounded)

**Answer Relevancy**: Does the answer address the question?
- Uses LLM to assess if response is on-topic
- Returns score 0-1 (higher = more relevant)

### CLI Extension

```bash
ragd evaluate --query "What is RAG?" --expected "..." --include-llm
```

### Graceful Degradation

When Ollama unavailable:
- Metrics return `None` instead of failing
- CLI displays "LLM unavailable - metric skipped"
- Non-LLM metrics still calculated

## Implementation Tasks

- [x] Add `faithfulness_score()` to metrics module
- [x] Add `answer_relevancy_score()` to metrics module
- [x] Create LLM-dependent metric prompts
- [x] Add `--include-llm` flag to evaluate command
- [x] Graceful degradation when Ollama unavailable
- [x] Update evaluator to support optional LLM metrics
- [x] Write unit tests

## Success Criteria

- [x] Faithfulness metric returns 0-1 score
- [x] Answer relevancy metric returns 0-1 score
- [x] Metrics skip gracefully without Ollama
- [x] CLI flag controls LLM metric inclusion
- [x] Existing metrics unaffected

## Files Changed

- `src/ragd/evaluation/metrics.py` - New metric functions
- `src/ragd/evaluation/evaluator.py` - LLM metric integration
- `src/ragd/evaluation/__init__.py` - Exports
- `src/ragd/ui/cli/commands.py` - `--include-llm` flag

## Related Documentation

- [F-013: RAGAS Evaluation](../completed/F-013-ragas-evaluation.md)
- [F-020: Ollama LLM Integration](../completed/F-020-ollama-llm-integration.md)

---

**Status**: Complete
