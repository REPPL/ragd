# State-of-the-Art RAG Evaluation Frameworks

## Executive Summary

**Key Recommendations for ragd:**

1. **Primary Framework:** Use RAGAS for comprehensive RAG evaluation with DeepEval as alternative for better debugging
2. **Retrieval Metrics:** Focus on NDCG@10 and Recall@K for retrieval quality measurement
3. **Generation Metrics:** Faithfulness (>0.85) and Answer Relevancy as primary generation quality indicators
4. **Local Model Challenge:** Expect 15-20% lower evaluation reliability with small local models due to JSON parsing failures
5. **Production Monitoring:** Integrate LangSmith or Langfuse for continuous evaluation and tracing

---

## Evaluation Framework Landscape

### Framework Comparison

| Framework | Focus | Local Model Support | Best For |
|-----------|-------|---------------------|----------|
| **RAGAS** | RAG-specific | Limited (JSON issues) | Quick evaluation, research |
| **DeepEval** | LLM + RAG | Better (with examples) | Production, debugging |
| **BEIR** | Retrieval only | N/A (no LLM needed) | Zero-shot retrieval benchmarking |
| **LangSmith** | Observability + Eval | Via integrations | Production monitoring |
| **Langfuse** | Open-source tracing | Via integrations | Self-hosted monitoring |
| **TruLens** | LLM apps | Limited | Feedback functions |
| **Braintrust** | Production eval | Via API | Continuous improvement |

### When to Use Each

```
Evaluation Need Decision Tree:
│
├─ Retrieval quality only?
│   └─ YES → BEIR + traditional IR metrics
│
├─ Full RAG pipeline evaluation?
│   ├─ Quick research/prototyping → RAGAS
│   └─ Production debugging → DeepEval
│
├─ Continuous production monitoring?
│   ├─ LangChain ecosystem → LangSmith
│   └─ Self-hosted requirement → Langfuse
│
└─ Human-in-the-loop evaluation?
    └─ Custom evaluation protocol + sampling
```

---

## Metric Categories

### Retrieval Metrics (Context Quality)

#### Order-Unaware Metrics

| Metric | Formula | Range | Use When |
|--------|---------|-------|----------|
| **Precision@K** | Relevant retrieved / K | 0-1 | Limited context window |
| **Recall@K** | Relevant retrieved / Total relevant | 0-1 | Need comprehensive coverage |
| **F1@K** | 2 × (P×R)/(P+R) | 0-1 | Balance precision/recall |

#### Order-Aware (Ranking) Metrics

| Metric | Description | Range | Use When |
|--------|-------------|-------|----------|
| **MRR** | 1/rank of first relevant | 0-1 | Single correct answer |
| **MAP@K** | Mean of precision at each relevant | 0-1 | Multiple relevant docs |
| **NDCG@K** | Position-weighted relevance | 0-1 | Graded relevance scores |
| **DCG@K** | Cumulative gain with log discount | 0-∞ | Raw ranking quality |

**Recommendation:** Use NDCG@10 as primary retrieval metric for RAG systems.

### Generation Metrics (Answer Quality)

#### RAGAS Core Metrics

| Metric | Measures | Requires | Range |
|--------|----------|----------|-------|
| **Faithfulness** | Factual consistency with context | Answer + Context | 0-1 |
| **Answer Relevancy** | How well answer addresses question | Question + Answer | 0-1 |
| **Context Precision** | Relevant chunks ranked higher | Question + Context | 0-1 |
| **Context Recall** | Required info retrieved | Ground truth + Context | 0-1 |

#### Additional Quality Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Answer Correctness** | Accuracy vs ground truth | When labels available |
| **Semantic Similarity** | Embedding similarity to reference | Approximate evaluation |
| **Noise Robustness** | Performance with irrelevant context | Stress testing |
| **Information Integration** | Multi-document synthesis quality | Complex queries |

---

## RAGAS Deep Dive

### Installation and Setup

```python
pip install ragas

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
```

### Basic Evaluation

```python
from datasets import Dataset
from ragas import evaluate

# Prepare evaluation data
eval_data = {
    "question": ["What is RAG?", "How does chunking work?"],
    "answer": ["RAG combines retrieval with generation...", "Chunking splits..."],
    "contexts": [["RAG is a technique..."], ["Documents are split..."]],
    "ground_truth": ["RAG combines...", "Chunking involves..."]  # Optional
}

dataset = Dataset.from_dict(eval_data)

# Run evaluation
results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)

print(results)
```

### Metric Interpretation Guide

#### Faithfulness Scores

| Score | Interpretation | Action |
|-------|----------------|--------|
| **0.95-1.0** | Excellent - all claims supported | Production ready |
| **0.85-0.94** | Good - minor unsupported claims | Monitor, acceptable |
| **0.70-0.84** | Moderate - some hallucination | Investigate generation |
| **0.50-0.69** | Poor - significant hallucination | Revise prompts/model |
| **<0.50** | Critical - unreliable output | Major intervention needed |

**Domain Calibration:**
- **Medical/Legal/Finance:** Target >0.95
- **Customer Support:** Target >0.85
- **Creative/Exploratory:** >0.70 may be acceptable

#### Answer Relevancy Scores

| Score | Interpretation | Likely Cause |
|-------|----------------|--------------|
| **0.90+** | Directly addresses question | Good alignment |
| **0.70-0.89** | Mostly relevant, some tangents | Prompt refinement needed |
| **<0.70** | Off-topic or incomplete | Retrieval or prompt issues |

#### Context Precision/Recall Trade-off

```
High Precision + Low Recall = Missing relevant information
Low Precision + High Recall = Noise in context (hallucination risk)
Balanced (>0.8 both) = Optimal retrieval configuration
```

---

## DeepEval Alternative

### Why Consider DeepEval

1. **Better Debugging:** Generates explanations for scores
2. **JSON Reliability:** Better handling of malformed outputs
3. **Local Model Support:** Documented Ollama integration
4. **Broader Scope:** Supports agentic workflows, not just RAG

### DeepEval Setup

```python
pip install deepeval

from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric
)
from deepeval.test_case import LLMTestCase
```

### Debugging Example

```python
from deepeval.metrics import FaithfulnessMetric

metric = FaithfulnessMetric(
    threshold=0.8,
    model="gpt-4",  # Or local model
    include_reason=True  # Key differentiator
)

test_case = LLMTestCase(
    input="What is RAG?",
    actual_output="RAG uses neural networks to fly rockets...",
    retrieval_context=["RAG combines retrieval with generation..."]
)

metric.measure(test_case)
print(f"Score: {metric.score}")
print(f"Reason: {metric.reason}")  # Explains why score is low
```

---

## Local Model Evaluation Challenges

### The JSON Problem

Small local models (7B and under) frequently fail evaluation due to:

1. **Preamble pollution:** "Sure, I can help with that!" before JSON
2. **Type coercion:** `{"score": "4"}` instead of `{"score": 4}`
3. **Incomplete output:** Truncated JSON responses
4. **Format drift:** Switching to markdown mid-response

### Reliability by Model Size

| Model Size | JSON Success Rate | Recommendation |
|------------|-------------------|----------------|
| **70B+** | 95%+ | Reliable for evaluation |
| **30-70B** | 85-95% | Generally reliable |
| **13-30B** | 70-85% | Use with retries |
| **7-13B** | 50-70% | Careful prompt engineering |
| **<7B** | 30-50% | Consider alternatives |

### Mitigation Strategies

#### 1. Structured Output Prompting

```python
EVALUATION_PROMPT = """
Evaluate the following answer for faithfulness.
Return ONLY a JSON object with no other text.

Question: {question}
Context: {context}
Answer: {answer}

Required JSON format:
{{"faithfulness_score": <number 0-1>, "reason": "<brief explanation>"}}

JSON:"""
```

#### 2. Retry with Parsing

```python
import json
import re

def robust_json_parse(response: str, max_retries: int = 3) -> dict:
    """Extract JSON from potentially messy LLM output."""
    # Try direct parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract anything that looks like JSON
    json_match = re.search(r'\{[^{}]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from: {response[:100]}...")
```

#### 3. Binary Simplification

For small models, simplify to binary judgments:

```python
BINARY_PROMPT = """
Is the following answer supported by the context?
Answer with exactly one word: YES or NO

Context: {context}
Answer: {answer}

Judgment:"""
```

#### 4. Use Larger Model for Evaluation Only

```python
# Use small model for generation, larger for evaluation
generation_model = "llama3:8b"
evaluation_model = "llama3:70b"  # Or API model for evaluation only
```

---

## BEIR for Retrieval Evaluation

### Overview

BEIR (Benchmarking Information Retrieval) evaluates retrieval systems across 18 diverse datasets without fine-tuning (zero-shot).

### Key Findings from BEIR

1. **BM25 remains strong:** Lexical search is a robust baseline
2. **Dense models overfit:** High in-domain scores don't transfer
3. **Rerankers generalise best:** Two-stage retrieval most robust
4. **Hybrid is optimal:** Combine lexical + dense for best results

### Using BEIR

```python
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from beir.retrieval.evaluation import EvaluateRetrieval

# Load dataset
dataset = "scifact"
url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
data_path = util.download_and_unzip(url, "datasets")
corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")

# Evaluate your retriever
evaluator = EvaluateRetrieval()
results = evaluator.evaluate(qrels, your_results, k_values=[1, 3, 5, 10])
print(results)  # NDCG@K, MAP@K, Recall@K, Precision@K
```

### ragd Retrieval Benchmarks

Target metrics for ragd retrieval component:

| Dataset Category | NDCG@10 Target | Notes |
|------------------|----------------|-------|
| **General QA** | >0.50 | MS MARCO, Natural Questions |
| **Scientific** | >0.45 | SciFact, TREC-COVID |
| **Domain-specific** | >0.40 | When using general embeddings |

---

## Continuous Production Evaluation

### Architecture

```
User Query → RAG Pipeline → Response
                ↓
           Trace Logger
                ↓
    ┌───────────────────────┐
    │   Evaluation Queue    │
    └───────────────────────┘
                ↓
    ┌───────────────────────┐
    │  Async Evaluators     │
    │  - Faithfulness       │
    │  - Relevancy          │
    │  - Custom metrics     │
    └───────────────────────┘
                ↓
    ┌───────────────────────┐
    │  Metrics Dashboard    │
    │  - Trends             │
    │  - Alerts             │
    │  - Drill-down         │
    └───────────────────────┘
```

### LangSmith Integration

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

from langsmith import traceable

@traceable(name="rag_query")
def query_rag(question: str) -> str:
    # Your RAG pipeline
    context = retrieve(question)
    answer = generate(question, context)
    return answer

# Traces automatically captured for analysis
```

### Self-Hosted Alternative: Langfuse

```python
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse = Langfuse()

@observe()
def rag_pipeline(question: str):
    with langfuse.trace(name="retrieval") as trace:
        context = retrieve(question)
        trace.update(output=context)

    with langfuse.trace(name="generation") as trace:
        answer = generate(question, context)
        trace.update(output=answer)

    return answer
```

### Alerting Thresholds

```yaml
# Example monitoring configuration
alerts:
  faithfulness:
    warning: 0.80
    critical: 0.70
    window: "1h"
    min_samples: 10

  answer_relevancy:
    warning: 0.75
    critical: 0.60
    window: "1h"
    min_samples: 10

  latency_p95:
    warning: 5000  # ms
    critical: 10000
    window: "15m"
```

---

## Human vs Automated Evaluation

### Trade-offs

| Aspect | Automated | Human |
|--------|-----------|-------|
| **Scale** | Unlimited | Limited by cost/time |
| **Consistency** | High (deterministic) | Variable |
| **Nuance** | Limited | Excellent |
| **Cost** | Low marginal cost | High per evaluation |
| **Speed** | Milliseconds | Minutes to hours |
| **Domain expertise** | Encoded in prompts | Natural |

### Hybrid Approach (Recommended)

```
All queries → Automated evaluation (RAGAS/DeepEval)
                        ↓
             Flag low-confidence cases
                        ↓
              Sample for human review
                        ↓
         Human annotations feed back to:
         1. Improve automated prompts
         2. Create regression test set
         3. Calibrate thresholds
```

### Human Evaluation Protocol

1. **Random Sampling:** 1-5% of production queries
2. **Stratified Selection:** Ensure coverage of query types
3. **Annotation Guidelines:**
   - Factual accuracy (1-5 scale)
   - Completeness (1-5 scale)
   - Relevance (1-5 scale)
   - Fluency (1-5 scale)
4. **Inter-annotator Agreement:** Require >0.7 Cohen's Kappa
5. **Feedback Loop:** Monthly calibration sessions

---

## Recommended Architecture for ragd

### Evaluation Configuration

```yaml
evaluation:
  # Framework selection
  primary_framework: "ragas"  # or "deepeval"

  # Metrics to compute
  metrics:
    retrieval:
      - ndcg@10
      - recall@5
      - precision@5
    generation:
      - faithfulness
      - answer_relevancy
    end_to_end:
      - answer_correctness  # When ground truth available

  # Thresholds for quality gates
  thresholds:
    faithfulness:
      minimum: 0.70
      target: 0.85
    answer_relevancy:
      minimum: 0.70
      target: 0.85
    ndcg@10:
      minimum: 0.40
      target: 0.55

  # Local model configuration
  local_evaluation:
    enabled: true
    model: "llama3:8b"
    fallback_to_api: true
    retry_on_json_failure: 3
```

### Evaluation Pipeline

```python
class RAGEvaluator:
    """Unified evaluation interface for ragd."""

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.metrics = self._init_metrics()

    def evaluate_retrieval(
        self,
        queries: list[str],
        retrieved: list[list[str]],
        relevant: list[list[str]]  # Ground truth
    ) -> RetrievalMetrics:
        """Evaluate retrieval component."""
        return {
            "ndcg@10": compute_ndcg(retrieved, relevant, k=10),
            "recall@5": compute_recall(retrieved, relevant, k=5),
            "precision@5": compute_precision(retrieved, relevant, k=5),
        }

    def evaluate_generation(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        ground_truths: list[str] | None = None
    ) -> GenerationMetrics:
        """Evaluate generation component."""
        # Use RAGAS or DeepEval based on config
        pass

    def evaluate_end_to_end(
        self,
        test_cases: list[TestCase]
    ) -> EndToEndMetrics:
        """Full pipeline evaluation."""
        pass
```

### Quality Gate Integration

```python
def pre_release_evaluation(model_version: str) -> bool:
    """Run evaluation suite before release."""
    evaluator = RAGEvaluator(config)

    # Load test dataset
    test_data = load_test_dataset("evaluation/golden_set.json")

    # Run evaluation
    results = evaluator.evaluate_end_to_end(test_data)

    # Check thresholds
    passed = all([
        results.faithfulness >= config.thresholds.faithfulness.minimum,
        results.answer_relevancy >= config.thresholds.answer_relevancy.minimum,
        results.ndcg_10 >= config.thresholds.ndcg_10.minimum,
    ])

    # Log results
    log_evaluation_results(model_version, results)

    return passed
```

---

## Creating Evaluation Datasets

### Golden Dataset Requirements

1. **Size:** Minimum 100-200 query-answer pairs
2. **Diversity:** Cover all expected query types
3. **Ground Truth:** Expert-validated correct answers
4. **Context Labels:** Which documents should be retrieved
5. **Difficulty Levels:** Easy, medium, hard queries

### Dataset Structure

```json
{
  "version": "1.0",
  "created": "2025-01-15",
  "test_cases": [
    {
      "id": "tc_001",
      "query": "What are the benefits of RAG?",
      "expected_answer": "RAG combines retrieval with generation...",
      "relevant_doc_ids": ["doc_042", "doc_187"],
      "difficulty": "easy",
      "category": "conceptual"
    }
  ]
}
```

### Synthetic Data Generation

For bootstrapping evaluation datasets:

```python
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

generator = TestsetGenerator.from_langchain(
    generator_llm=generator_model,
    critic_llm=critic_model,
    embeddings=embeddings
)

testset = generator.generate_with_langchain_docs(
    documents=your_docs,
    test_size=100,
    distributions={
        simple: 0.4,
        reasoning: 0.3,
        multi_context: 0.3
    }
)
```

---

## References

### Frameworks and Tools
- [RAGAS Documentation](https://docs.ragas.io/) - RAG Assessment framework
- [DeepEval GitHub](https://github.com/confident-ai/deepeval) - LLM evaluation framework
- [BEIR Benchmark](https://github.com/beir-cellar/beir) - Information retrieval benchmark
- [LangSmith](https://docs.langchain.com/langsmith/) - LangChain observability
- [Langfuse](https://langfuse.com/) - Open-source LLM observability

### Academic Papers
- [RAGAS: Automated Evaluation of RAG (EACL 2024)](https://aclanthology.org/2024.eacl-demo.16/)
- [BEIR: Heterogeneous Benchmark for Zero-shot IR (NeurIPS 2021)](https://arxiv.org/abs/2104.08663)
- [StructuredRAG: JSON Response Formatting](https://arxiv.org/html/2408.11061v1)

### Practical Guides
- [Pinecone RAG Evaluation Guide](https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/rag-evaluation/)
- [Evaluating RAG with RAGAS - Vectara](https://www.vectara.com/blog/evaluating-rag)
- [RAGAS + LangSmith Integration](https://blog.langchain.com/evaluating-rag-pipelines-with-ragas-langsmith/)
- [DeepEval vs RAGAS Comparison](https://deepeval.com/blog/deepeval-vs-ragas)

---

## Related Documentation

- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Embedding model selection
- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [F-013: RAGAS Evaluation](../features/planned/F-013-ragas-evaluation.md) - Feature specification
- [ADR-0008: Evaluation Framework](../decisions/adrs/0008-evaluation-framework.md) - Architecture decision

---

**Status:** Research complete
