# F-057: Model Comparison Mode

## Overview

**Research**: [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md)
**ADR**: [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md)
**Milestone**: v1.0+
**Priority**: P3

## Problem Statement

Users want to compare outputs from different models to:

1. Choose the best model for their use case
2. Evaluate quality vs speed trade-offs
3. Identify which model handles their content type best
4. Build confidence in model selection

Research shows that LLM-as-Judge and Panel of LLMs (PoLL) ensembles provide robust evaluation mechanisms.

## Design Approach

### Comparison Modes

1. **Side-by-Side**: Show outputs from multiple models without ranking
2. **Judged**: A third model evaluates and ranks the outputs
3. **Ensemble**: Multiple models vote on best answer

### Architecture

```
Query + Context
    |
    v
+------------------------------------------+
| Parallel Model Execution                  |
|   - Model A: llama3.2:3b                  |
|   - Model B: qwen2.5:3b                   |
|   - Model C: gemma2:2b (optional)         |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Results Aggregation                       |
|   - Collect all responses                 |
|   - Measure timing and tokens             |
+------------------------------------------+
    |
    v (if --judge specified)
+------------------------------------------+
| Judge Model Evaluation                    |
|   - Compare responses                     |
|   - Rank by criteria                      |
|   - Provide reasoning                     |
+------------------------------------------+
    |
    v
Formatted Comparison Output
```

### CLI Commands

```bash
# Side-by-side comparison
ragd ask "What is RAG?" --compare llama3.2:3b,qwen2.5:3b

# Compare all available models
ragd ask "What is RAG?" --compare all

# With judge evaluation
ragd ask "What is RAG?" --compare llama3.2:3b,qwen2.5:3b --judge llama3.1:8b

# Ensemble mode (majority voting)
ragd ask "What is RAG?" --ensemble llama3.2:3b,qwen2.5:3b,gemma2:2b
```

## Implementation Tasks

- [ ] Create ModelComparator class for parallel execution
- [ ] Implement side-by-side comparison output
- [ ] Add `--compare` flag to `ragd ask` command
- [ ] Implement judge prompt template
- [ ] Add `--judge` flag for evaluation
- [ ] Create comparison result formatter (Rich panels)
- [ ] Implement timing and token counting per model
- [ ] Add `--ensemble` mode for majority voting
- [ ] Handle model loading/availability gracefully
- [ ] Write unit tests for comparison logic
- [ ] Write integration tests for multi-model comparison
- [ ] Document comparison features

## Success Criteria

- [ ] Multiple models can be queried in parallel
- [ ] Side-by-side output displays clearly
- [ ] Judge model provides ranking and reasoning
- [ ] Timing and token counts are accurate
- [ ] Ensemble voting works correctly
- [ ] Graceful handling when models unavailable
- [ ] Documentation complete

## Dependencies

- F-055: Multi-Model Orchestration (model registry, routing)
- F-020: Ollama LLM Integration (generation)
- Multiple Ollama models installed

## Technical Notes

### ModelComparator Implementation

```python
import asyncio
from dataclasses import dataclass

@dataclass
class ModelResponse:
    model: str
    response: str
    time_ms: float
    tokens: int
    error: str | None = None

class ModelComparator:
    """Compare outputs from multiple models."""

    def __init__(self, ollama_client: OllamaClient, registry: ModelRegistry):
        self.ollama = ollama_client
        self.registry = registry

    async def compare(
        self,
        prompt: str,
        models: list[str],
        context: str | None = None
    ) -> list[ModelResponse]:
        """Query multiple models in parallel."""

        async def query_model(model: str) -> ModelResponse:
            start = time.time()
            try:
                response = await self.ollama.generate(
                    prompt=prompt,
                    model=model,
                    context=context
                )
                return ModelResponse(
                    model=model,
                    response=response.content,
                    time_ms=(time.time() - start) * 1000,
                    tokens=response.tokens_used
                )
            except Exception as e:
                return ModelResponse(
                    model=model,
                    response="",
                    time_ms=0,
                    tokens=0,
                    error=str(e)
                )

        # Execute all models in parallel
        tasks = [query_model(m) for m in models]
        return await asyncio.gather(*tasks)
```

### Judge Prompt Template

```python
JUDGE_PROMPT = """You are evaluating responses from different language models.

Question: {question}

Context provided:
{context}

---

Response from {model_a}:
{response_a}

---

Response from {model_b}:
{response_b}

---

Evaluate which response better answers the question based on:
1. Accuracy - Does it correctly use information from the context?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it well-structured and easy to understand?
4. Citations - Does it reference source material?

Respond in JSON format:
{{
    "winner": "A" or "B" or "tie",
    "scores": {{
        "A": {{"accuracy": 1-5, "completeness": 1-5, "clarity": 1-5, "citations": 1-5}},
        "B": {{"accuracy": 1-5, "completeness": 1-5, "clarity": 1-5, "citations": 1-5}}
    }},
    "reasoning": "Brief explanation of the decision"
}}
"""
```

### Panel of LLMs (PoLL) Implementation

```python
class PanelOfLLMs:
    """Ensemble evaluation using multiple judge models."""

    def __init__(self, judges: list[str], ollama: OllamaClient):
        self.judges = judges
        self.ollama = ollama

    async def evaluate(
        self,
        question: str,
        responses: list[ModelResponse]
    ) -> dict:
        """Get consensus from panel of judges."""

        votes = []
        for judge in self.judges:
            vote = await self._get_judgment(
                judge, question,
                responses[0], responses[1]
            )
            votes.append(vote)

        # Majority voting
        winner = max(set(votes), key=votes.count)
        confidence = votes.count(winner) / len(votes)

        return {
            "winner": winner,
            "confidence": confidence,
            "votes": votes,
            "consensus": confidence >= 0.66
        }
```

### CLI Output Examples

```bash
$ ragd ask "What is retrieval-augmented generation?" \
    --compare llama3.2:3b,qwen2.5:3b

╭─ Model Comparison ─────────────────────────────────────────────────────╮
│ Query: What is retrieval-augmented generation?                         │
│ Context: 3 chunks from knowledge base                                  │
╰────────────────────────────────────────────────────────────────────────╯

╭─ llama3.2:3b ──────────────────────────────────────────────────────────╮
│ Retrieval-Augmented Generation (RAG) is a technique that combines      │
│ information retrieval with text generation. It works by:               │
│                                                                        │
│ 1. Taking a user query                                                 │
│ 2. Retrieving relevant documents from a knowledge base                 │
│ 3. Using those documents as context for an LLM                         │
│ 4. Generating a response grounded in the retrieved information         │
│                                                                        │
│ Time: 1,247ms | Tokens: 89                                             │
╰────────────────────────────────────────────────────────────────────────╯

╭─ qwen2.5:3b ───────────────────────────────────────────────────────────╮
│ RAG (Retrieval-Augmented Generation) enhances LLM responses by         │
│ incorporating external knowledge. The process involves semantic        │
│ search to find relevant context, which is then provided to the         │
│ language model alongside the user's question.                          │
│                                                                        │
│ Key benefits include reduced hallucination and access to up-to-date    │
│ information beyond the model's training data.                          │
│                                                                        │
│ Time: 982ms | Tokens: 76                                               │
╰────────────────────────────────────────────────────────────────────────╯


$ ragd ask "What is RAG?" --compare llama3.2:3b,qwen2.5:3b --judge llama3.1:8b

[... comparison output as above ...]

╭─ Judge Evaluation (llama3.1:8b) ───────────────────────────────────────╮
│ Winner: qwen2.5:3b                                                     │
│                                                                        │
│ Scores:                                                                │
│ ┌─────────────────┬────────────┬────────────┐                          │
│ │ Criterion       │ llama3.2   │ qwen2.5    │                          │
│ ├─────────────────┼────────────┼────────────┤                          │
│ │ Accuracy        │ ★★★★☆      │ ★★★★★      │                          │
│ │ Completeness    │ ★★★★☆      │ ★★★★☆      │                          │
│ │ Clarity         │ ★★★★★      │ ★★★★☆      │                          │
│ │ Citations       │ ★★☆☆☆      │ ★★★☆☆      │                          │
│ └─────────────────┴────────────┴────────────┘                          │
│                                                                        │
│ Reasoning: Both responses are accurate and well-structured. qwen2.5    │
│ edges ahead by mentioning key benefits (reduced hallucination,         │
│ up-to-date information) that llama3.2 omits.                           │
╰────────────────────────────────────────────────────────────────────────╯
```

## Related Documentation

- [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md) - LLM-as-Judge research
- [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md) - Decision
- [F-055: Multi-Model Orchestration](./F-055-multi-model-orchestration.md) - Model registry
- [F-020: Ollama LLM Integration](./F-020-ollama-llm-integration.md) - Generation

---
