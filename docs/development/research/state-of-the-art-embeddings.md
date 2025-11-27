# State-of-the-Art Embedding Model Selection

## Executive Summary

**Key Recommendations for ragd:**

1. **Default Local Model:** Use `nomic-embed-text-v1.5` (137M params) - best balance of quality, speed, and 8192 context length for local deployment
2. **High-Quality Local:** Use `BAAI/bge-m3` for multilingual or hybrid retrieval (dense + sparse + multi-vector)
3. **Budget API Option:** Voyage-3-lite outperforms OpenAI at 6x lower cost
4. **Premium API Option:** Voyage-3-large for maximum retrieval quality
5. **Always Benchmark:** MTEB scores are indicative but evaluate on your own data before production

---

## Model Categories

### Local vs API-Based Models

| Aspect | Local Models | API Models |
|--------|--------------|------------|
| **Latency** | 5-50ms typical | 100-500ms+ (network) |
| **Cost** | One-time compute | Per-token pricing |
| **Privacy** | Data stays local | Data sent to provider |
| **Scalability** | Hardware-limited | Highly scalable |
| **Offline** | Full capability | Requires internet |
| **Best For** | Privacy-first, high-volume | Low-volume, maximum quality |

### Model Size Classes

| Class | Parameters | Memory (FP16) | Typical Use Case |
|-------|------------|---------------|------------------|
| **Tiny** | 22-33M | ~50-100MB | Edge devices, high throughput |
| **Small** | 100-150M | ~300-500MB | Balanced local deployment |
| **Medium** | 300-500M | ~1-2GB | Quality-focused local |
| **Large** | 1-8B | 2-16GB | Maximum quality, GPU required |

---

## Top Models by Category (2024-2025)

### Local Deployment (Recommended for ragd)

| Model | Params | Dims | Context | MTEB Avg | Best For |
|-------|--------|------|---------|----------|----------|
| **nomic-embed-text-v1.5** | 137M | 768 | 8192 | 62.3 | General RAG, long docs |
| **BAAI/bge-m3** | 568M | 1024 | 8192 | 64.5 | Multilingual, hybrid retrieval |
| **all-MiniLM-L6-v2** | 22M | 384 | 512 | 56.3 | Speed-critical, short text |
| **all-mpnet-base-v2** | 109M | 768 | 384 | 57.8 | Balanced, semantic search |
| **Alibaba-NLP/gte-large-en-v1.5** | 434M | 1024 | 8192 | 65.4 | English-only, high quality |
| **Qwen3-Embedding-0.6B** | 600M | 1024 | 32K | 66.1 | Long context, multilingual |

### API-Based Models

| Model | Provider | Dims | Context | Cost/1M tokens | Notes |
|-------|----------|------|---------|----------------|-------|
| **voyage-3-large** | Voyage AI | 1024 | 32K | $0.18 | Best retrieval quality |
| **voyage-3** | Voyage AI | 1024 | 32K | $0.06 | Best value premium |
| **voyage-3-lite** | Voyage AI | 512 | 32K | $0.02 | Budget with quality |
| **text-embedding-3-large** | OpenAI | 3072 | 8K | $0.13 | Widely integrated |
| **text-embedding-3-small** | OpenAI | 1536 | 8K | $0.02 | Budget option |
| **embed-v4** | Cohere | 1024 | - | $0.10 | Good multilingual |

### Domain-Specific Models

| Domain | Recommended Model | Improvement vs General |
|--------|-------------------|----------------------|
| **Code** | voyage-code-3 | +15-20% on code retrieval |
| **Legal** | voyage-law-2 | +20% on legal docs |
| **Finance** | voyage-finance-2 | +15% on SEC filings |
| **Medical** | Fine-tuned BGE/Nomic | Requires custom training |

---

## MTEB Benchmark Guidance

### Understanding MTEB

The Massive Text Embedding Benchmark (MTEB) evaluates embedding models across 56 tasks in 8 categories:
- **Retrieval** - Most relevant for RAG
- **Semantic Textual Similarity (STS)** - Query-document matching
- **Classification** - Less relevant for RAG
- **Clustering** - Document organisation
- **Reranking** - Second-stage retrieval
- **Pair Classification** - Relationship detection
- **Summarisation** - Content similarity
- **Bitext Mining** - Cross-lingual matching

### RAG-Specific Evaluation

**Focus on these MTEB categories for RAG:**

1. **Retrieval (NDCG@10)** - Primary metric for RAG performance
2. **STS** - Query understanding quality
3. **Reranking** - If using two-stage retrieval

**Key Insight:** A model with high average MTEB score but poor retrieval performance is worse for RAG than a model with moderate average but excellent retrieval scores.

### Benchmark Caveats

1. **Self-reported scores** - Some may be inflated
2. **Training contamination** - Models may have trained on MTEB data
3. **Task mismatch** - Your domain may differ from benchmarks
4. **Always validate** - Test on representative sample of your data

---

## Local Model Deep Dive

### Nomic Embed (Recommended Default)

**Why nomic-embed-text-v1.5:**
- 8192 token context (handles long documents)
- Outperforms OpenAI ada-002 and Jina v2
- Fully open weights (Apache 2.0)
- 137M parameters - runs on CPU efficiently
- Native sentence-transformers integration

**Usage Pattern:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)

# For documents
doc_embeddings = model.encode(
    ["search_document: " + doc for doc in documents]
)

# For queries
query_embedding = model.encode("search_query: What is RAG?")
```

**Performance Characteristics:**
- ~500-800 docs/sec on modern CPU
- ~50-100MB memory footprint
- 768-dimensional embeddings

### BGE-M3 (Multilingual/Hybrid)

**Why BGE-M3:**
- Supports 100+ languages
- Triple retrieval: dense + sparse + multi-vector
- 8192 token context
- Excellent with reranker (bge-reranker-v2-m3)

**Hybrid Retrieval Pattern:**
```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

# Returns dense, sparse, and colbert vectors
output = model.encode(
    documents,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True
)
```

**Best Practice:** Combine BGE-M3 dense retrieval with BM25 for hybrid search, then rerank with bge-reranker for maximum quality.

### MiniLM (Speed-Critical)

**Why all-MiniLM-L6-v2:**
- 22M parameters - extremely fast
- 5-14k sentences/sec on CPU
- 4-5x faster than mpnet
- Good enough for many use cases

**Trade-offs:**
- 512 token context limit (truncates long text)
- Lower quality on complex queries
- 384 dimensions (smaller index size)

---

## Quantisation for Local Deployment

### GGUF Format for Embeddings

While less common than for LLMs, quantised embedding models offer significant memory savings:

| Quantisation | Memory Reduction | Quality Impact |
|--------------|------------------|----------------|
| **FP16** | 50% vs FP32 | Negligible |
| **Q8_0** | 75% vs FP32 | Minimal (~1% degradation) |
| **Q6_K** | ~81% vs FP32 | Small (~2-3% degradation) |
| **Q4_K_M** | ~87% vs FP32 | Moderate (~5% degradation) |

### Recommendations

1. **Start with FP16** - Best quality/memory balance for most cases
2. **Q8_0 for constrained memory** - Nearly indistinguishable from FP16
3. **Avoid Q4 for embeddings** - Quality degradation more noticeable than for LLMs
4. **Test retrieval quality** - Small perplexity changes can significantly impact retrieval

### Qwen3-Embedding GGUF Example

```bash
# Download quantised model
huggingface-cli download Mungert/Qwen3-Embedding-4B-GGUF

# Use with llama.cpp or compatible runtime
```

---

## Fine-Tuning Considerations

### When to Fine-Tune

**Fine-tune when:**
- Working with specialised domains (legal, medical, finance)
- General models underperform on your data
- You have representative query-document pairs
- Retrieval accuracy is critical to application success

**Don't fine-tune when:**
- General-purpose retrieval is sufficient
- Limited training data (<1000 pairs)
- Rapid iteration is needed
- Domain vocabulary is standard

### Expected Improvements

| Scenario | Typical Improvement |
|----------|---------------------|
| Domain-specific terminology | 5-10% |
| Specialised document formats | 10-15% |
| Legal/medical with training data | 15-25% |
| Code retrieval | 10-20% |

### Fine-Tuning Approach

1. **Collect Data:** Query-document pairs from your domain
2. **Hard Negatives:** Include challenging negative examples
3. **Loss Function:** MultipleNegativesRankingLoss recommended
4. **Validation:** Hold out test set from same distribution
5. **Avoid Overfitting:** Early stopping, diverse training data

**Minimum Viable Dataset:** ~5,000-10,000 query-document pairs

### LM-Cocktail for Domain Adaptation

BAAI's LM-Cocktail technique allows mixing fine-tuned and base model weights to maintain general capability while adding domain expertise:

```python
# Blend domain fine-tuned with base model
final_weights = 0.7 * finetuned_weights + 0.3 * base_weights
```

---

## Recommended Architecture for ragd

### Default Configuration (v0.1)

```yaml
embedding:
  # Primary model for all embedding tasks
  model: "nomic-ai/nomic-embed-text-v1.5"

  # Query/document prefixes (required for nomic)
  query_prefix: "search_query: "
  document_prefix: "search_document: "

  # Dimensions and context
  dimensions: 768
  max_tokens: 8192

  # Performance settings
  batch_size: 32
  use_fp16: true
```

### Fallback Strategy

```yaml
embedding:
  primary: "nomic-ai/nomic-embed-text-v1.5"

  fallbacks:
    - model: "sentence-transformers/all-MiniLM-L6-v2"
      reason: "Low memory environments"

    - model: "BAAI/bge-m3"
      reason: "Multilingual documents"
```

### API Integration (Optional)

```yaml
embedding:
  api_models:
    voyage:
      enabled: false
      model: "voyage-3"
      api_key_env: "VOYAGE_API_KEY"

    openai:
      enabled: false
      model: "text-embedding-3-small"
      api_key_env: "OPENAI_API_KEY"
```

### Hybrid Retrieval (v0.3+)

```yaml
retrieval:
  strategy: "hybrid"

  dense:
    model: "BAAI/bge-m3"
    weight: 0.7

  sparse:
    method: "bm25"  # or "splade" or "bge-m3-sparse"
    weight: 0.3

  reranker:
    enabled: true
    model: "BAAI/bge-reranker-v2-m3"
    top_k: 10  # Rerank top 10 results
```

---

## Performance Benchmarks

### Throughput Comparison (CPU - Apple M2)

| Model | Docs/sec | Memory | Batch Size |
|-------|----------|--------|------------|
| all-MiniLM-L6-v2 | 2,500 | 120MB | 64 |
| nomic-embed-text-v1.5 | 450 | 380MB | 32 |
| bge-m3 (dense only) | 180 | 1.2GB | 16 |
| bge-m3 (full hybrid) | 85 | 1.8GB | 8 |

### Throughput Comparison (GPU - RTX 3080)

| Model | Docs/sec | VRAM | Batch Size |
|-------|----------|------|------------|
| all-MiniLM-L6-v2 | 12,000 | 0.5GB | 256 |
| nomic-embed-text-v1.5 | 3,500 | 0.8GB | 128 |
| bge-m3 (dense only) | 1,200 | 2.5GB | 64 |

### Latency (Single Query)

| Model | CPU (M2) | GPU (3080) |
|-------|----------|------------|
| MiniLM | 2-5ms | <1ms |
| Nomic | 8-15ms | 2-3ms |
| BGE-M3 | 25-40ms | 5-8ms |

---

## Decision Matrix

### Choosing Your Embedding Model

```
START
  │
  ├─ Need offline/privacy-first?
  │   ├─ YES → Local model
  │   │   ├─ Multilingual documents?
  │   │   │   ├─ YES → BGE-M3
  │   │   │   └─ NO → Continue
  │   │   ├─ Memory constrained (<500MB)?
  │   │   │   ├─ YES → all-MiniLM-L6-v2
  │   │   │   └─ NO → nomic-embed-text-v1.5
  │   │   └─ Maximum local quality needed?
  │   │       └─ YES → gte-large-en-v1.5 or Qwen3-Embedding
  │   │
  │   └─ NO → API model
  │       ├─ Budget priority?
  │       │   ├─ YES → voyage-3-lite ($0.02/1M)
  │       │   └─ NO → Continue
  │       ├─ Maximum quality?
  │       │   └─ YES → voyage-3-large
  │       └─ OpenAI ecosystem?
  │           └─ YES → text-embedding-3-small
  │
  └─ Domain-specific (legal/finance/code)?
      ├─ YES → Voyage domain models or fine-tune
      └─ NO → General-purpose model
```

---

## References

### Benchmarks and Leaderboards
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - Massive Text Embedding Benchmark
- [Modal MTEB Analysis](https://modal.com/blog/mteb-leaderboard-article) - Top embedding models breakdown
- [Pinecone Embedding Models Rundown](https://www.pinecone.io/learn/series/rag/embedding-models-rundown/)

### Model Documentation
- [Nomic Embed Technical Report](https://static.nomic.ai/reports/2024_Nomic_Embed_Text_Technical_Report.pdf)
- [BGE-M3 on Hugging Face](https://huggingface.co/BAAI/bge-m3)
- [Voyage AI Blog](https://blog.voyageai.com/)
- [FlagEmbedding GitHub](https://github.com/FlagOpen/FlagEmbedding)

### Fine-Tuning Resources
- [Fine-tune Embedding Models for RAG](https://www.philschmid.de/fine-tune-embedding-model-for-rag) - Phil Schmid
- [Databricks: Improving RAG with Finetuning](https://www.databricks.com/blog/improving-retrieval-and-rag-embedding-model-finetuning)
- [Weaviate: When to Fine-Tune](https://weaviate.io/blog/fine-tune-embedding-model)

### Quantisation
- [GGUF Quantized Models Guide](https://apatero.com/blog/gguf-quantized-models-complete-guide-2025)
- [Choosing GGUF Quants](https://kaitchup.substack.com/p/choosing-a-gguf-model-k-quants-i)

---

## Related Documentation

- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [State-of-the-Art Evaluation](./state-of-the-art-evaluation.md) - Measuring retrieval quality
- [ADR-0002: ChromaDB Vector Store](../decisions/adrs/0002-chromadb-vector-store.md) - Storage for embeddings
- [F-004: Embedding Generation](../features/completed/F-004-embedding-generation.md) - Feature specification

---

**Status:** Research complete
