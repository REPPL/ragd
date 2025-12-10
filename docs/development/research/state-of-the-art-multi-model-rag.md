# State-of-the-Art Multi-Model RAG: Orchestration, SLMs & Ensembles

> **Note:** This document surveys state-of-the-art techniques for multi-model local RAG
> systems. ragd implements **local-only** processing with Ollama as the primary LLM backend.

Advanced techniques for orchestrating multiple language models in local RAG implementations.

## Executive Summary

The emerging paradigm in local RAG systems is **task-specific model assignment**—using different models optimised for each stage of the pipeline rather than a single monolithic model for everything. This approach delivers:

- **2-5x performance improvement** through smaller, faster models for simple tasks
- **Better accuracy** via specialised models fine-tuned for specific functions
- **Resource efficiency** allowing multiple models to coexist in memory
- **Graceful degradation** when hardware constraints require model switching

Key insights from this research:

1. **Model routing** can reduce compute costs by 85% while maintaining 95% quality
2. **Small Language Models (SLMs)** under 3B parameters excel at classification, extraction, and structured output tasks
3. **Ollama natively supports multi-model orchestration** via environment variables
4. **LLM-as-Judge ensembles** outperform single-model evaluation for output comparison
5. **SLIM-style function-calling models** enable structured outputs for enterprise automation

---

## Part 1: Multi-Model Architecture Patterns

### The Case for Multiple Models

Traditional RAG pipelines use a single LLM for all generation tasks. This is inefficient:

| Query Type | Actual Need | Typical Model Used | Waste |
|------------|-------------|-------------------|-------|
| "What is X?" | 3B model sufficient | 8B+ model | ~60% compute |
| Entity extraction | Specialised NER | General chat model | Lower accuracy |
| Yes/no classification | 1B classifier | 8B+ model | ~85% compute |
| Complex reasoning | 8B+ model needed | 8B+ model | None |

**Insight:** Running a 70B model for simple queries wastes 90% of available compute.

### Task-Specific Model Assignment

Different RAG tasks have different optimal model sizes:

| Task | Complexity | Recommended Size | Example Models |
|------|------------|------------------|----------------|
| Query embedding | Low | 100-400M | nomic-embed, all-MiniLM |
| Document classification | Low-Medium | 0.5-3B | SLIM-intent, Qwen2.5-0.5B |
| Reranking | Medium | 400M-7B | bge-reranker, ColBERT |
| Simple Q&A | Medium | 3-7B | Llama 3.2:3B, Gemma 2:2B |
| Multi-hop reasoning | High | 8-14B | Llama 3.1:8B, Qwen2.5:14B |
| Complex analysis | Very High | 30B+ | Mixtral 8x7B, Llama 3.1:70B |

### Model Routing Strategies

#### Strategy 1: Complexity-Based Routing

Route queries based on estimated complexity using lightweight classifiers.

**RouteLLM** (LMSYS, 2024) implements this pattern:

```python
from routellm import Controller

controller = Controller(
    routers=["bert"],  # Trained routing classifier (~10ms inference)
    strong_model="ollama/llama3.1:8b",
    weak_model="ollama/llama3.2:3b"
)

# Simple query -> routes to 3B model
response = controller.chat.completions.create(
    model="router-bert-0.5",  # Threshold controls routing
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

# Complex query -> routes to 8B model
response = controller.chat.completions.create(
    model="router-bert-0.5",
    messages=[{"role": "user", "content": "Explain the implications of Bell's theorem"}]
)
```

**Performance:**
- Up to 85% cost reduction while maintaining 95% GPT-4 quality
- 40% cheaper than commercial routing offerings
- Routing overhead: ~10ms per query

**Source:** [RouteLLM Blog](https://lmsys.org/blog/2024-07-01-routellm/), [GitHub](https://github.com/lm-sys/RouteLLM)

#### Strategy 2: Task-Type Routing

Route based on detected task type (classification, extraction, generation, etc.):

```python
class TaskRouter:
    """Route queries to task-appropriate models."""

    TASK_MODELS = {
        "classification": "slim-intent-tool",      # 1B
        "extraction": "slim-ner-tool",             # 1B
        "summarisation": "llama3.2:3b",            # 3B
        "question_answering": "llama3.2:3b",       # 3B
        "complex_reasoning": "llama3.1:8b",        # 8B
        "comparison": "qwen2.5:7b",                # 7B
    }

    def route(self, query: str, task_type: str) -> str:
        """Return appropriate model for task."""
        return self.TASK_MODELS.get(task_type, "llama3.2:3b")
```

#### Strategy 3: Domain-Expert Routing

**ZOOTER** (NAACL 2024) routes to domain-expert models:

> "Off-the-shelf LLMs have heterogeneous expertise in a wide range of domains and
> tasks so that an ensemble of LLMs can achieve consistently better performance."

- Evaluated on 26 subsets across different domains
- Outperformed best single model on average
- Ranked first on 44% of tasks

**Source:** [Routing to the Expert](https://aclanthology.org/2024.naacl-long.109/)

### Architecture Diagram: Multi-Model RAG Pipeline

```
Query Input
    |
    v
+------------------------------------------+
| Query Analyser                            |
|   - Detect task type                      |
|   - Estimate complexity                   |
|   - Extract entities (if needed)          |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Model Router                              |
|                                          |
|   complexity < 0.3 ──> SLM (1-3B)        |
|   complexity < 0.7 ──> Medium (3-7B)     |
|   complexity >= 0.7 ──> Large (8B+)      |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Retrieval                                 |
|   - Embedding model (fixed, 384M)         |
|   - Vector search                         |
|   - Optional: Reranker (400M-7B)          |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Generation (model selected by router)     |
|                                          |
|   Embedding:    nomic-embed-text (137M)  |
|   Simple:       llama3.2:3b              |
|   Standard:     llama3.1:8b              |
|   Complex:      qwen2.5:14b              |
+------------------------------------------+
    |
    v
Response Output
```

---

## Part 2: Small Language Models (SLMs) for RAG

### Definition and Landscape

**Small Language Models (SLMs)** are models with fewer than 10 billion parameters, typically 0.5B-7B, optimised for specific tasks or efficient deployment.

> "The era of scaling is coming to a close... up to 99% of use cases could be
> addressed using SLMs." — Clem Delangue, CEO of Hugging Face (NeurIPS 2024)

**Key Characteristics:**
- Require significantly less compute, memory, and storage
- Train and fine-tune much faster than LLMs
- Suitable for real-time applications and edge deployment
- Can run on consumer hardware without GPUs
- Often fine-tuned for specific domains = better task accuracy

### SLM Landscape (2024-2025)

| Model Family | Sizes | Key Strengths | Best For |
|-------------|-------|---------------|----------|
| **Qwen2.5** | 0.5B, 1.5B, 3B, 7B | Fastest inference, excellent at RAG/tools | Classification, extraction |
| **Phi-3/3.5** | 3.8B | Reasoning, math (perfect benchmark scores) | Logic, analysis |
| **Gemma 2** | 2B, 9B | Code, instruction following | Code generation |
| **Llama 3.2** | 1B, 3B | General tasks, tool use | Balanced performance |
| **SmolLM2** | 135M, 360M, 1.7B | Ultra-fast, edge deployment | Mobile, IoT |
| **TinyLlama** | 1.1B | Commonsense reasoning | Lightweight RAG |

**Benchmark Performance:**

| Model | MMLU | HumanEval | Speed (tok/s) |
|-------|------|-----------|---------------|
| Qwen2.5-0.5B | 45.4 | 31.6 | 180+ |
| Qwen2.5-1.5B | 60.9 | 37.2 | 120+ |
| Phi-3-mini (3.8B) | 68.8 | 59.1 | 80+ |
| Llama-3.2-3B | 63.4 | 54.3 | 90+ |
| Gemma-2-2B | 51.3 | 41.5 | 100+ |

**Source:** [Best Small Language Models Benchmark](https://medium.com/@darrenoberst/best-small-language-models-for-accuracy-and-enterprise-use-cases-benchmark-results-cf71964759c8)

### LLMWare SLIM Models: Function-Calling SLMs

**SLIM (Structured Language Instruction Models)** are 1-3B parameter models fine-tuned to generate structured outputs (JSON, Python dicts, SQL):

> "SLIMs are small, specialized decoder-based, function-calling LLMs, fine-tuned
> on a specific task to generate structured outputs that can be handled
> programmatically."

**Available SLIM Models (18 as of 2024):**

| Model | Task | Output Format |
|-------|------|---------------|
| `slim-sentiment` | Sentiment analysis | `{"sentiment": "positive"}` |
| `slim-ner` | Named entity recognition | `{"entities": [...]}` |
| `slim-sa-ner` | Combined sentiment + NER | `{"sentiment": ..., "entities": [...]}` |
| `slim-boolean` | Yes/no with explanation | `{"answer": true, "reason": "..."}` |
| `slim-ratings` | 1-5 rating | `{"rating": 4, "explanation": "..."}` |
| `slim-emotions` | Emotion detection | `{"emotions": ["joy", "surprise"]}` |
| `slim-tags` | Auto-generate tags | `{"tags": ["python", "ml", "rag"]}` |
| `slim-intent` | Intent classification | `{"intent": "question", "confidence": 0.95}` |
| `slim-category` | Category classification | `{"category": "technical"}` |
| `slim-sql` | Text-to-SQL | `SELECT * FROM...` |
| `slim-extract` | Custom key extraction | `{"key1": "value1", ...}` |
| `slim-summary` | Summarisation | `{"summary": "..."}` |
| `slim-xsum` | Title/headline generation | `{"headline": "..."}` |
| `slim-nli` | Natural language inference | `{"entailment": true}` |

**Enterprise RAG Application:**

```python
from llmware.models import ModelCatalog

# Load SLIM model for NER
ner_model = ModelCatalog().load_model("slim-ner-tool")

# Extract entities from retrieved chunks
for chunk in retrieved_chunks:
    entities = ner_model.function_call(chunk.text)
    # Returns: {"entities": [{"text": "OpenAI", "type": "ORG"}, ...]}
```

**Key Benefits:**
- Run entirely on CPU with quantised "tool" versions
- Structured outputs enable programmatic handling
- Stack multiple SLIMs in multi-step agent workflows
- 10-100x faster than general LLMs for specific tasks

**Source:** [LLMWare SLIM Models](https://llmware.ai/resources/slims-small-specialized-models-function-calling-and-multi-model-agents), [GitHub](https://github.com/llmware-ai/llmware)

### SLMs with RAG: Performance Considerations

Research on SLMs for RAG on embedded devices (DeepSense.ai):

> "SLMs integrated with a RAG framework can deliver performance comparable to
> LLMs in many scenarios. By offloading knowledge storage and retrieval to
> external systems, SLMs can punch above their weight."

**Mobile RAG Pipeline Results:**

| Model | Size | Tokens/sec (Android) | Quality |
|-------|------|---------------------|---------|
| TinyLlama | 1.1B | 2.1 | Good |
| Phi-2 | 2.7B | 1.4 | Better |
| Gemma | 2B | 1.6 | Better |
| Qwen-0.5B | 0.5B | 7.2 | Acceptable |

**Practical Guidance:**
- SLMs work best with high-quality retrieval
- Combine SLM generation with strong embedding models
- Use larger models only for complex multi-hop queries
- Edge deployment viable with 1-3B models

**Source:** [SLMs with RAG on Embedded Devices](https://deepsense.ai/blog/implementing-small-language-models-slms-with-rag-on-embedded-devices-leading-to-cost-reduction-data-privacy-and-offline-use/)

---

## Part 3: Memory Management for Multiple Models

### Ollama Multi-Model Configuration

Ollama natively supports loading multiple models simultaneously:

```bash
# Key environment variables for multi-model support
export OLLAMA_MAX_LOADED_MODELS=3      # Max models in memory at once
export OLLAMA_NUM_PARALLEL=1           # Parallel requests per model
export OLLAMA_KEEP_ALIVE=5m            # How long models stay loaded after last use
```

**Commands for Multi-Model Management:**

```bash
# See currently loaded models
ollama ps

# Load specific models
ollama run llama3.2:3b
ollama run qwen2.5:3b

# Check available models
ollama list

# Set high GPU layer count for multi-GPU distribution
# (999 = use all available GPUs)
OLLAMA_NUM_GPU=999 ollama serve
```

**Multi-GPU Behaviour:**
- Ollama distributes model layers across available GPUs
- Two identical GPUs: ~50% layers on each
- Automatic layer distribution (not tensor parallelism)

**Source:** [Ollama Multi-Model Guide](https://www.byteplus.com/en/topic/516162)

### VRAM Requirements and Planning

**Rule of Thumb:** ~2GB VRAM per billion parameters (unquantised)

| Model Size | FP16 | Q8 | Q4_K_M |
|------------|------|-----|--------|
| 1B | 2GB | 1GB | 0.6GB |
| 3B | 6GB | 3GB | 1.8GB |
| 7B | 14GB | 7GB | 4GB |
| 8B | 16GB | 8GB | 5GB |
| 14B | 28GB | 14GB | 8GB |
| 70B | 140GB | 70GB | 40GB |

**Multi-Model VRAM Planning (32GB example):**

```
Option A: Single large model
  - 1x Llama 3.1:70B Q4 (40GB) ❌ Won't fit

Option B: Large + small
  - 1x Llama 3.1:8B Q4 (5GB)
  - 1x Llama 3.2:3B Q4 (1.8GB)
  - Headroom: ~25GB ✅

Option C: Multiple small models
  - 1x Embedding model (1GB)
  - 1x Reranker (2GB)
  - 3x SLIM models (0.6GB each = 1.8GB)
  - 1x Generation model 8B (5GB)
  - Headroom: ~22GB ✅
```

**Context Window Impact:**

> "Context kills VRAM" — Recent advances in Ollama now extend quantisation
> to the KV cache, storing keys and values in lower-precision formats.

- 8K context: ~1GB additional VRAM
- 32K context: ~4GB additional VRAM
- 128K context: ~16GB additional VRAM

**Source:** [Context & VRAM](https://medium.com/@lyx_62906/context-kills-vram-how-to-run-llms-on-consumer-gpus-a785e8035632)

### Inference Engine Comparison for Multi-Model

| Engine | Multi-Model | Tensor Parallel | Best For |
|--------|-------------|-----------------|----------|
| **Ollama** | Excellent | No | Development, model switching |
| **vLLM** | Limited | Yes | Production, high throughput |
| **llama.cpp** | Manual | No | CPU offloading, portability |
| **ExLlamaV2** | Limited | Yes | Quantised multi-GPU |

**When to Use Each:**

- **Ollama**: Best for local RAG development
  - Easy model switching
  - Native multi-model support
  - Simple API

- **vLLM**: Best for production multi-user
  - Tensor parallelism for speed
  - PagedAttention for efficiency
  - Batch inference support

- **llama.cpp**: Best for resource-constrained
  - CPU offloading when VRAM insufficient
  - Portable across platforms
  - Fine-grained control

**Source:** [vLLM vs Ollama vs llama.cpp](https://www.arsturn.com/blog/multi-gpu-showdown-benchmarking-vllm-llama-cpp-ollama-for-maximum-performance)

---

## Part 4: Model Comparison and Ensembling

### LLM-as-Judge Pattern

Use one LLM to evaluate outputs from another:

```python
JUDGE_PROMPT = """You are evaluating two responses to the same question.

Question: {question}
Context: {context}

Response A:
{response_a}

Response B:
{response_b}

Which response better answers the question based on the context?
Consider: accuracy, completeness, citation of sources, clarity.

Output JSON: {"winner": "A" or "B", "reason": "brief explanation"}
"""
```

**Common Judge Model Choices:**
- Same model family, larger size (8B judges 3B outputs)
- Different model family (Qwen judges Llama outputs)
- Ensemble of judges (multiple models vote)

**Source:** [LLM-as-a-Judge Guide](https://www.evidentlyai.com/llm-guide/llm-as-a-judge)

### Panel of LLMs (PoLL)

Instead of a single judge, use an ensemble:

> "PoLL uses an ensemble of three smaller LLM-evaluators to independently
> score model outputs. The final evaluation is determined by max voting
> or average pooling."

**Implementation:**

```python
class PanelOfLLMs:
    """Ensemble evaluation using multiple models."""

    def __init__(self, judges: list[str]):
        self.judges = judges  # e.g., ["llama3.2:3b", "qwen2.5:3b", "gemma2:2b"]

    async def evaluate(self, question: str, response_a: str, response_b: str) -> dict:
        """Get consensus from panel of judges."""
        votes = []

        for judge_model in self.judges:
            vote = await self._get_judgment(judge_model, question, response_a, response_b)
            votes.append(vote)

        # Majority voting
        winner = max(set(votes), key=votes.count)
        confidence = votes.count(winner) / len(votes)

        return {"winner": winner, "confidence": confidence, "votes": votes}
```

**Benefits:**
- Reduces single-model bias
- More robust evaluation
- Can detect edge cases where models disagree
- Mitigates position and verbosity biases

### Mixture of Agents (MoA)

**Research Finding:** Ensemble of weaker models can outperform single strong model:

> "An ensemble of open-source models in a MoA framework achieved a win rate
> of 65.1% on AlpacaEval 2.0, substantially surpassing GPT-4's 57.5%."

**Architecture:**

```
Query
  |
  v
+------------------+------------------+------------------+
|    Model A       |    Model B       |    Model C       |
|   (Llama 3B)     |   (Qwen 3B)      |   (Gemma 2B)     |
+------------------+------------------+------------------+
  |                  |                  |
  v                  v                  v
+----------------------------------------------------+
|              Aggregator Model                       |
|  (Synthesises best elements from each response)    |
+----------------------------------------------------+
  |
  v
Final Response
```

**Source:** [LLMs-as-Judges Survey](https://arxiv.org/html/2412.05579v2)

### Dynamic Arbitration Patterns

**DAFE (Dynamic Arbitration for Free-Form Evaluation):**
- Routes to expert models based on query domain
- Uses lightweight classifier for routing decisions
- Arbitrator resolves conflicts between experts

**Consensus Mechanisms:**

| Method | How It Works | Best For |
|--------|--------------|----------|
| **Majority Vote** | Most common answer wins | Classification tasks |
| **Weighted Vote** | Model confidence weights | When model quality varies |
| **Aggregation** | Synthesise best elements | Generation tasks |
| **Arbitration** | Third model decides | When models disagree |

---

## Part 5: Implementation Recommendations for ragd

### Recommended Multi-Model Configuration

```yaml
# ~/.ragd/config.yaml

models:
  # Embedding (always loaded)
  embedding:
    model: nomic-embed-text
    # Alternative: all-MiniLM-L6-v2 (local)

  # Generation models (loaded on demand)
  generation:
    default: llama3.2:3b      # Fast, good for simple queries
    complex: llama3.1:8b      # For multi-hop, long responses
    fallback: null            # Graceful degradation

  # Optional: Reranking
  reranking:
    enabled: false
    model: bge-reranker-base

# Model routing configuration
routing:
  enabled: false              # Start with single model
  strategy: complexity        # complexity | task_type | manual
  complexity_threshold: 0.7   # When to use complex model

# Ollama settings
ollama:
  base_url: http://localhost:11434
  max_loaded_models: 3
  keep_alive: 5m
```

### Phased Implementation Strategy

**Phase 1: Single Model (Current, F-020)**
- Single generation model for all queries
- Configuration for model selection
- Graceful fallback when Ollama unavailable

**Phase 2: Task-Specific Models (F-055)**
- Separate embedding/generation/reranking models
- Manual model override via CLI
- Model health checking

**Phase 3: Automatic Routing (Future)**
- Complexity-based routing
- RouteLLM integration
- Performance monitoring

**Phase 4: Specialised Models (F-056)**
- SLIM-style models for structured tasks
- Auto-classification on ingest
- Entity extraction pipelines

**Phase 5: Model Comparison (F-057)**
- Side-by-side comparison mode
- Judge model evaluation
- A/B testing infrastructure

### CLI Integration

```bash
# Model management
ragd config models list              # Show available/loaded models
ragd config models set generation llama3.1:8b
ragd config models pull llama3.2:3b  # Download via Ollama

# Per-query model override
ragd ask "question" --model llama3.2:3b

# Model comparison (F-057)
ragd ask "question" --compare llama3.2:3b,qwen2.5:3b
ragd ask "question" --compare all --judge llama3.1:8b

# Specialised extraction (F-056)
ragd ingest doc.pdf --auto-classify
ragd extract entities doc.pdf
```

### Performance Targets

| Metric | Single Model | Multi-Model | Target |
|--------|--------------|-------------|--------|
| Simple query latency | 2-5s | 0.5-2s | <2s |
| Complex query latency | 5-15s | 5-10s | <10s |
| Model switch time | N/A | <100ms | <200ms |
| Memory efficiency | Baseline | 40% reduction | 30%+ |
| Quality retention | 100% | 95%+ | 95%+ |

---

## Key Takeaways

1. **Task-specific models are the future of local RAG.** Running 8B+ models for simple queries wastes resources.

2. **SLMs (1-3B) excel at structured tasks.** SLIM-style models provide better accuracy than general LLMs for NER, classification, and extraction.

3. **Ollama supports multi-model out of the box.** Use `OLLAMA_MAX_LOADED_MODELS` and `OLLAMA_KEEP_ALIVE` for efficient orchestration.

4. **LLM-as-Judge enables model comparison.** Ensemble judges (PoLL) outperform single-model evaluation.

5. **Start simple, add complexity gradually.** Begin with single-model, add routing and specialised models based on actual needs.

6. **VRAM planning is critical.** Account for model size + context window + multiple loaded models.

---

## References

### Model Routing
- [RouteLLM](https://github.com/lm-sys/RouteLLM) - LMSYS model routing framework
- [RouteLLM Blog](https://lmsys.org/blog/2024-07-01-routellm/) - Performance analysis
- [Routing to the Expert](https://aclanthology.org/2024.naacl-long.109/) - NAACL 2024 paper

### Small Language Models
- [LLMWare SLIM Models](https://llmware.ai/resources/slims-small-specialized-models-function-calling-and-multi-model-agents) - Enterprise SLMs
- [LLMWare GitHub](https://github.com/llmware-ai/llmware) - Open source framework
- [Best SLMs Benchmark](https://medium.com/@darrenoberst/best-small-language-models-for-accuracy-and-enterprise-use-cases-benchmark-results-cf71964759c8)
- [SLMs on Embedded Devices](https://deepsense.ai/blog/implementing-small-language-models-slms-with-rag-on-embedded-devices-leading-to-cost-reduction-data-privacy-and-offline-use/)
- [Top SLMs 2025](https://www.datacamp.com/blog/top-small-language-models) - DataCamp overview

### LLM-as-Judge & Ensembles
- [LLMs-as-Judges Survey](https://arxiv.org/html/2412.05579v2) - Comprehensive survey
- [Awesome-LLMs-as-Judges](https://github.com/CSHaitao/Awesome-LLMs-as-Judges) - Paper collection
- [Evaluating LLM-Evaluators](https://eugeneyan.com/writing/llm-evaluators/) - Practical guide
- [LLM-as-a-Judge Guide](https://www.evidentlyai.com/llm-guide/llm-as-a-judge) - Evidently AI

### Memory & Performance
- [vLLM vs Ollama Benchmark](https://www.arsturn.com/blog/multi-gpu-showdown-benchmarking-vllm-llama-cpp-ollama-for-maximum-performance)
- [Context & VRAM](https://medium.com/@lyx_62906/context-kills-vram-how-to-run-llms-on-consumer-gpus-a785e8035632)
- [Ollama Multi-Model Guide](https://www.byteplus.com/en/topic/516162)
- [Multi-GPU LLM Setup](https://medium.com/@samanch70/goodbye-vram-limits-how-to-run-massive-llms-across-your-gpus-b2636f6ae6cf)

### RAG Architecture
- [RAG Best Practices](https://www.promptingguide.ai/research/rag) - Prompt Engineering Guide
- [Building RAG with Open Source](https://www.bentoml.com/blog/building-rag-with-open-source-and-custom-ai-models) - BentoML
- [RAG Architecture 2025](https://futureagi.com/blogs/rag-architecture-llm-2025) - FutureAGI

---

## Related Documentation

- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance, caching, vector storage
- [State-of-the-Art RAG](./state-of-the-art-rag.md) - General retrieval techniques
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Embedding model selection
- [F-020: Ollama LLM Integration](../features/completed/F-020-ollama-llm-integration.md) - Generation feature
- [F-055: Multi-Model Orchestration](../features/completed/F-055-multi-model-orchestration.md) - Routing feature
- [F-056: Specialised Task Models](../features/planned/F-056-specialised-task-models.md) - SLIM models
- [F-057: Model Comparison](../features/planned/F-057-model-comparison.md) - LLM-as-Judge
- [ADR-0026: Multi-Model Architecture](../decisions/adrs/0026-multi-model-architecture.md) - Decision record

---

**Status**: Research complete, informs v0.5+ roadmap
