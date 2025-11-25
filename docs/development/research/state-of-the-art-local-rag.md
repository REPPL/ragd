# State-of-the-Art Local RAG: Performance, Models & Storage

Advanced techniques for optimising local RAG implementations.

## Executive Summary

Local RAG systems face unique challenges compared to cloud-based deployments: limited compute resources, memory constraints, and the need to orchestrate multiple models efficiently. This research covers four critical areas:

1. **Performance Enhancement** - Caching, quantisation, and inference optimisation
2. **Multi-Model Orchestration** - Task-specific routing and model management
3. **Vector Storage Best Practices** - Indexing, persistence, and scaling
4. **Graph Databases for RAG** - Knowledge graphs and hybrid approaches

The key insight: **local RAG is not just "cloud RAG on a laptop"**—it requires fundamentally different architectural choices that prioritise efficiency over raw capability.

---

## Part 1: Performance Enhancement for Local RAG

### The Latency Challenge

From [Systems Trade-offs in RAG](https://arxiv.org/html/2412.11854v1):

> "RAG stages nearly double the TTFT (Time To First Token) latency, from 495ms to 965ms, compared to baseline LLM inference. The retrieval stage accounts for nearly 35% of the total TTFT latency."

### Caching Strategies

Caching is the highest-impact optimisation for local RAG. Three levels of caching apply:

| Cache Type | What It Stores | Latency Savings | Trade-offs |
|------------|----------------|-----------------|------------|
| **Embedding Cache** | Vector representations of queries | Eliminates embedding API calls | Low risk, always use |
| **Retrieval Cache** | Retrieved document chunks | Eliminates vector search | Moderate risk if docs change |
| **Answer Cache** | Full LLM responses | Eliminates all LLM calls | High risk, needs invalidation |

**Source:** [Lesson 15: Cost Optimization & Latency Reduction](https://medium.com/@noumannawaz/lesson-15-cost-optimization-latency-reduction-89cc00c36669)

#### Semantic Caching

Traditional caching uses exact key matching. **Semantic caching** uses embedding similarity:

```python
# Traditional: cache["what is Python"] != cache["tell me about Python"]
# Semantic: embed("what is Python") ≈ embed("tell me about Python") → cache hit

class SemanticCache:
    def __init__(self, similarity_threshold=0.95):
        self.cache = {}  # query_embedding -> response
        self.threshold = similarity_threshold

    def get(self, query_embedding):
        for cached_emb, response in self.cache.items():
            if cosine_similarity(query_embedding, cached_emb) > self.threshold:
                return response  # Cache hit
        return None  # Cache miss
```

**Performance Impact:**
- Up to 68.8% reduction in API calls
- 40-50% reduction in query latency
- 97%+ positive hit rate accuracy

**Notable Frameworks:**
- **GPTCache** - Redis-backed semantic cache
- **RAGCache** - GPU/host memory hierarchy with LLM-aware replacement policy
- **Proximity** - Approximate caching with similarity thresholds

**Source:** [GPT Semantic Cache](https://arxiv.org/html/2411.05276v2), [RAGCache](https://arxiv.org/html/2404.12457v2)

### Quantisation Techniques

Quantisation reduces model precision to improve speed and memory:

| Precision | Memory | Speed Gain | Quality Impact |
|-----------|--------|------------|----------------|
| FP32 | 4 bytes/param | Baseline | Baseline |
| FP16 | 2 bytes/param | ~1.5x | Negligible |
| INT8 | 1 byte/param | ~2x | Minor |
| INT4 | 0.5 bytes/param | ~3-4x | Noticeable on complex tasks |
| FP8 | 1 byte/param | ~2x | Better than INT8 quality |

**Local RAG Application:**
- **Embedding models:** INT8 quantisation works well (minimal quality loss)
- **Rerankers:** FP16 or INT8 (preserve ranking quality)
- **Generators:** INT4/GPTQ for 7B models, INT8 for larger models

**Source:** [RAG Performance Optimization with TensorRT](https://www.codespace.blog/performance-optimization-with-nvidia-tensorrt-and-quantization/)

### Vector Database Optimisation

| Optimisation | Technique | Latency Impact |
|--------------|-----------|----------------|
| Indexing | HNSW vs IVF-PQ | 10-50ms difference |
| Filtering | Pre-filter metadata | 2-3x faster for filtered queries |
| Quantisation | Scalar/Product Quantisation | 4-16x memory reduction |
| Batching | Batch embedding generation | 5-10x throughput improvement |

**Combined Optimisations Example:**

```
Initial pipeline: 3000ms (1000ms retrieval + 2000ms generation)

After optimisations:
├── HNSW index + metadata filtering → 200ms retrieval
├── INT8 quantised LLM → 1000ms generation
├── TensorRT compilation → 500ms generation
├── Semantic cache (50% hit rate) → 50% queries instant
└── Result: <700ms average, <50ms for cache hits
```

---

## Part 2: Multi-Model Orchestration

### The Model Routing Problem

Different tasks have different compute requirements:

| Task | Complexity | Suitable Model Size |
|------|------------|---------------------|
| Query embedding | Low | 100-400M params (sentence-transformers) |
| Document classification | Low-Medium | 1-3B params |
| Reranking | Medium | 400M-7B params |
| Simple Q&A | Medium | 7-13B params |
| Complex reasoning | High | 30B+ params or API |

**Insight:** Running a 70B model for simple queries wastes 90% of compute.

### LLM Routers

[RouteLLM](https://github.com/lm-sys/RouteLLM) (LMSYS, 2024) provides intelligent query routing:

```python
from routellm import Controller

# Route between expensive (GPT-4) and cheap (Llama-3 8B) models
controller = Controller(
    routers=["bert"],  # Trained routing classifier
    strong_model="gpt-4",
    weak_model="ollama/llama3:8b"
)

# Simple query → routes to Llama-3 8B (local)
response = controller.chat.completions.create(
    model="router-bert-0.5",  # Threshold controls routing
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

# Complex query → routes to GPT-4 (API)
response = controller.chat.completions.create(
    model="router-bert-0.5",
    messages=[{"role": "user", "content": "Explain quantum entanglement in the context of Bell's theorem"}]
)
```

**Performance:**
- Up to 85% cost reduction while maintaining 95% GPT-4 quality
- 40% cheaper than commercial routing offerings

**Source:** [RouteLLM Blog](https://lmsys.org/blog/2024-07-01-routellm/), [GitHub](https://github.com/lm-sys/RouteLLM)

### Ollama Model Management

[Ollama 0.2](https://medium.com/@simeon.emanuilov/ollama-0-2-revolutionizing-local-model-management-with-concurrency-2318115ce961) introduced key concurrency features:

| Setting | Purpose | Default |
|---------|---------|---------|
| `OLLAMA_MAX_LOADED_MODELS` | Max models in memory | 3 × GPU count |
| `OLLAMA_NUM_PARALLEL` | Parallel requests per model | 1 |
| `OLLAMA_MAX_QUEUE` | Request queue depth | 512 |

**Multi-Model Architecture for RAG:**

```
Query Input
    ↓
┌─────────────────────────────────────────────────────┐
│ Semantic Router (lightweight classifier)            │
│   → Identifies task type from query                 │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Task-Specific Models (Ollama)                       │
│                                                     │
│   Embedding    → nomic-embed-text (137M)            │
│   Reranking    → bge-reranker-base (278M)           │
│   Simple Q&A   → llama3.2:3b                        │
│   Complex Q&A  → llama3.1:8b or qwen2.5:14b         │
│   Summarisation → mistral:7b-instruct               │
└─────────────────────────────────────────────────────┘
```

### Small Language Models (SLMs) for RAG

SLMs (< 7B parameters) excel at specific RAG tasks:

| Model | Size | Best For |
|-------|------|----------|
| **Qwen2.5-0.5B/1.5B/3B** | 0.5-3B | Fast classification, simple extraction |
| **Gemma-2-2B** | 2B | Code, instruction following |
| **Phi-3-mini** | 3.8B | Reasoning, math |
| **Llama-3.2-3B** | 3B | General tasks, tool use |
| **SmolLM2** | 135M-1.7B | Ultra-fast inference, edge deployment |

**SLM for Embedding/Reranking:**
- SLMs can generate embeddings for retrieval
- Can replace expensive reranker API calls
- Trade-off: slightly lower quality for major speed gains

**Source:** [Evaluating RAG Capabilities of SLMs](https://medium.com/data-science-at-microsoft/evaluating-rag-capabilities-of-small-language-models-e7531b3a5061)

### Inference Engine Comparison

| Engine | Best For | Throughput | Ease of Use |
|--------|----------|------------|-------------|
| **vLLM** | Production, high concurrency | 35x llama.cpp | Medium |
| **llama.cpp** | CPU/GPU hybrid, portability | Baseline | High |
| **Ollama** | Development, model switching | ~llama.cpp | Highest |
| **TensorRT-LLM** | NVIDIA GPUs, maximum speed | Highest | Low |

**Recommendations:**
- **Development:** Ollama (easy model management)
- **Production single-user:** llama.cpp (low memory, fast startup)
- **Production multi-user:** vLLM (batching, PagedAttention)

**Source:** [vLLM vs Ollama Benchmark](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)

---

## Part 3: Vector Storage Best Practices

### Indexing Methods

#### HNSW (Hierarchical Navigable Small World)

```
Layer 3:   A ─────────── B           (sparse, fast navigation)
           │             │
Layer 2:   A ─── C ───── B           (medium density)
           │     │       │
Layer 1:   A ─ D ─ C ─ E ─ B         (dense, precise)
           │   │   │   │   │
Layer 0:   A D F C G E H B I         (all vectors)
```

**Characteristics:**
- O(log n) search complexity
- High recall (95-99%)
- Memory-intensive
- Excellent for dynamic updates

**Tuning Parameters:**
- `M` (connections per layer): Higher = better recall, more memory
- `ef_construction`: Higher = better index quality, slower build
- `ef_search`: Higher = better recall, slower queries

#### IVF (Inverted File Index)

```
Centroids:     C1        C2        C3        C4
               │         │         │         │
Clusters:   [v1,v2,v3] [v4,v5] [v6,v7,v8,v9] [v10,v11]
```

**Characteristics:**
- Partitions vectors into clusters
- Memory-efficient
- Not suited for frequent updates
- Best for static, large datasets

**Tuning Parameters:**
- `nlist`: Number of clusters
- `nprobe`: Clusters to search (higher = better recall, slower)

#### Composite Indexes (HNSW-PQ)

Combine HNSW navigation with Product Quantisation compression:

| Approach | Memory | Speed | Recall |
|----------|--------|-------|--------|
| HNSW only | 100% | Fast | 99% |
| HNSW-PQ | 25-50% | Medium | 95-98% |
| HNSW-SQ (Scalar) | 50% | Fast | 97-99% |

**Source:** [Vector Database Indexing Guide](https://dev.to/foxgem/vector-database-indexing-a-comprehensive-guide-3an1)

### Local Vector Database Comparison

| Database | Architecture | Best For | Limitations |
|----------|-------------|----------|-------------|
| **ChromaDB** | Embedded (SQLite) | Prototyping, <1M vectors | Concurrency bottlenecks |
| **Qdrant** | Client-server | Production, filtering | Requires separate process |
| **Milvus Lite** | Embedded | Large datasets | Complex setup |
| **FAISS** | Library | Custom implementations | No persistence by default |
| **sqlite-vss** | SQLite extension | SQL integration | Limited features |
| **LanceDB** | Embedded, columnar | Multi-modal, versioning | Newer, less mature |

**ChromaDB Specifics:**
- Uses HNSW internally
- SQLite backend (file-level locking limits concurrency)
- Excellent for single-user local RAG
- Configure `ef` and `M` for quality/speed trade-off

**Source:** [SQLite vs Chroma Analysis](https://stephencollins.tech/posts/sqlite-vs-chroma-comparative-analysis)

### Memory Optimisation

| Technique | Memory Saving | Trade-off |
|-----------|---------------|-----------|
| Scalar Quantisation (SQ) | 4x | ~1% recall loss |
| Product Quantisation (PQ) | 8-16x | 2-5% recall loss |
| Binary Quantisation | 32x | Significant recall loss |
| Disk-based storage | N/A (offload) | Higher latency |
| Memory-mapped files | OS-managed | I/O dependent |

**Practical Guidance:**

```python
# ChromaDB with memory optimisation
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
)

# For large collections, consider HNSW tuning
collection = client.create_collection(
    name="documents",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # Higher = better quality
        "hnsw:M": 16,  # Lower = less memory
        "hnsw:search_ef": 100  # Query-time recall/speed trade-off
    }
)
```

### Scaling Strategies

| Scale | Vectors | Strategy |
|-------|---------|----------|
| Small | <100K | Single ChromaDB, in-memory |
| Medium | 100K-10M | ChromaDB with disk persistence |
| Large | 10M-100M | Qdrant/Milvus, consider sharding |
| Massive | >100M | Distributed cluster, tiered storage |

**Source:** [Scaling Vector Databases](https://stevescargall.com/blog/2024/08/how-much-ram-could-a-vector-database-use-if-a-vector-database-could-use-ram/)

---

## Part 4: Graph Databases for RAG Knowledge Graphs

### Why Knowledge Graphs for RAG?

Vector search excels at **similarity** but struggles with **relationships**:

| Query Type | Vector RAG | Graph RAG |
|------------|------------|-----------|
| "Documents about Python" | Excellent | Good |
| "Who wrote documents citing Smith's work?" | Poor | Excellent |
| "What topics connect AI and biology?" | Poor | Excellent |
| "Show me the chain of references" | Impossible | Native |

### Microsoft GraphRAG

[Microsoft GraphRAG](https://github.com/microsoft/graphrag) (2024) introduced a paradigm shift:

**Architecture:**

```
Documents
    ↓
┌─────────────────────────────────────────────────────┐
│ Entity Extraction (LLM)                             │
│   → Extract entities: people, places, concepts      │
│   → Extract relationships between entities          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Community Detection (Leiden Algorithm)              │
│   → Cluster related entities into communities       │
│   → Hierarchical structure (communities within      │
│     communities)                                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Community Summarisation (LLM)                       │
│   → Generate summary for each community             │
│   → Enables "global" queries over entire corpus     │
└─────────────────────────────────────────────────────┘
    ↓
Knowledge Graph + Community Summaries
```

**Query Types:**
- **Local search:** Entity-centric, follows relationships
- **Global search:** Uses community summaries for corpus-wide questions

**Limitations:**
- High indexing cost (LLM calls for extraction + summarisation)
- Complex setup
- Overkill for simple document collections

### LlamaIndex Property Graph Index

[LlamaIndex PropertyGraphIndex](https://docs.llamaindex.ai/en/stable/examples/property_graph/property_graph_neo4j/) provides simpler graph RAG:

```python
from llama_index.core import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

# Create graph store
graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="password",
    url="bolt://localhost:7687"
)

# Build index (extracts entities/relations)
index = PropertyGraphIndex.from_documents(
    documents,
    property_graph_store=graph_store,
    embed_kg_nodes=True  # Also embed for vector search
)

# Query with graph + vector
retriever = index.as_retriever(
    include_text=True,
    similarity_top_k=5
)
```

**Benefits:**
- Hybrid retrieval (graph traversal + vector similarity)
- Customisable extraction (define your own entity types)
- Production-ready with Neo4j backend

**Source:** [LlamaIndex Property Graph](https://docs.llamaindex.ai/en/stable/examples/property_graph/property_graph_neo4j/)

### Lightweight Graph Options

For local RAG without heavy infrastructure:

| Option | Storage | Query Language | Best For |
|--------|---------|----------------|----------|
| **NetworkX** | In-memory | Python API | Prototyping, small graphs |
| **SQLite + JSON** | File | SQL | Simple relationships |
| **DuckDB** | File | SQL | Analytical queries |
| **Kuzu** | Embedded | Cypher | Local graph DB |
| **FalkorDB** | Redis-based | Cypher | Fast, Redis ecosystem |
| **Neo4j Desktop** | Local server | Cypher | Full-featured, free tier |

### Hybrid Vector + Graph Architecture

```
Query: "What papers by Smith influenced the transformer architecture?"
                ↓
┌─────────────────────────────────────────────────────┐
│ Query Analysis                                      │
│   → Entities: ["Smith", "transformer architecture"] │
│   → Intent: Influence chain / citation tracking     │
└─────────────────────────────────────────────────────┘
                ↓
        ┌───────┴───────┐
        ↓               ↓
┌──────────────┐  ┌──────────────┐
│ Graph Query  │  │ Vector Query │
│ (Neo4j)      │  │ (ChromaDB)   │
│              │  │              │
│ MATCH        │  │ Semantic     │
│ (a:Author    │  │ search for   │
│  {name:      │  │ "transformer │
│  'Smith'})   │  │ architecture"│
│ -[:WROTE]->  │  │              │
│ (p:Paper)    │  │              │
│ -[:CITED_BY]→│  │              │
│ (t:Paper)    │  │              │
│ WHERE t.topic│  │              │
│ = 'transform'│  │              │
└──────────────┘  └──────────────┘
        │               │
        └───────┬───────┘
                ↓
┌─────────────────────────────────────────────────────┐
│ Result Fusion                                       │
│   → Combine graph paths with semantic matches       │
│   → Rerank by relevance                             │
└─────────────────────────────────────────────────────┘
```

### When to Use Graph RAG

| Use Case | Vector RAG | Graph RAG | Hybrid |
|----------|------------|-----------|--------|
| Simple Q&A over documents | ✅ | ❌ | Optional |
| Multi-hop reasoning | ❌ | ✅ | ✅ |
| Citation/reference tracking | ❌ | ✅ | ✅ |
| Entity-centric queries | ⚠️ | ✅ | ✅ |
| Corpus-wide themes | ❌ | ✅ | ✅ |
| Real-time updates | ✅ | ⚠️ | ⚠️ |
| Low-resource environments | ✅ | ❌ | ❌ |

**Recommendation for ragd:**
- v0.1-v0.5: Vector-only (ChromaDB) - simpler, sufficient for most use cases
- v0.8+: Consider hybrid graph+vector for advanced knowledge management

---

## Recommended Architecture for ragd

### Performance-Optimised Local RAG Pipeline

```
Query Input
    ↓
┌─────────────────────────────────────────────────────┐
│ Semantic Cache Check                                │
│   Hit? → Return cached response                     │
│   Miss? → Continue                                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Query Embedding (cached)                            │
│   Model: nomic-embed-text or bge-small              │
│   Quantisation: INT8                                │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Vector Retrieval (ChromaDB)                         │
│   Index: HNSW (M=16, ef_search=100)                 │
│   Metadata pre-filtering                            │
│   Top-K: 20                                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Reranking (optional, for quality)                   │
│   Model: bge-reranker-base (local) or Cohere API    │
│   Output: Top-5                                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Model Router                                        │
│   Simple query → Llama-3.2-3B (Ollama)              │
│   Complex query → Llama-3.1-8B or API               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Generation (Ollama)                                 │
│   Quantisation: Q4_K_M or Q5_K_M                    │
│   Context: Retrieved chunks + query                 │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Cache Update                                        │
│   Store: query embedding → response                 │
└─────────────────────────────────────────────────────┘
    ↓
Response Output
```

### Proposed Features by Version

**v0.3 (Advanced Retrieval):**
- F-010: Contextual Retrieval (chunk context enhancement)
- F-011: Late Chunking (document-level embeddings)
- F-012: Hybrid Search (vector + BM25)

**v0.5 (Performance):**
- Semantic caching (query → response)
- Embedding caching (query → vector)
- Reranking integration

**v0.8 (Advanced):**
- Model routing (complexity-based)
- Multi-model orchestration via Ollama
- Optional: Graph-enhanced retrieval

---

## Key Takeaways

1. **Caching is the highest-ROI optimisation.** Semantic caching alone can reduce latency by 40-50% and API costs by 68%.

2. **Use task-specific models.** Route simple queries to 3B models, complex queries to 8B+. RouteLLM makes this easy.

3. **HNSW is the right default for local RAG.** Tune M and ef_search for your recall/speed requirements.

4. **ChromaDB is sufficient for most local use cases.** Only graduate to Qdrant/Milvus at >1M vectors or high concurrency.

5. **Graph RAG is powerful but expensive.** Consider only for multi-hop reasoning or entity-relationship queries. Vector RAG handles 90% of use cases.

6. **Quantisation enables local deployment.** INT4/INT8 models run on consumer hardware with acceptable quality loss.

---

## References

### Performance & Caching
- [RAGCache: Knowledge Caching](https://arxiv.org/html/2404.12457v2)
- [GPT Semantic Cache](https://arxiv.org/html/2411.05276v2)
- [Systems Trade-offs in RAG](https://arxiv.org/html/2412.11854v1)

### Model Orchestration
- [RouteLLM](https://github.com/lm-sys/RouteLLM) - LMSYS
- [Ollama Concurrency](https://medium.com/@simeon.emanuilov/ollama-0-2-revolutionizing-local-model-management-with-concurrency-2318115ce961)
- [vLLM vs Ollama Benchmark](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)

### Vector Storage
- [Vector Database Indexing Guide](https://dev.to/foxgem/vector-database-indexing-a-comprehensive-guide-3an1)
- [Scaling Vector Databases](https://stevescargall.com/blog/2024/08/how-much-ram-could-a-vector-database-use-if-a-vector-database-could-use-ram/)
- [SQLite vs Chroma](https://stephencollins.tech/posts/sqlite-vs-chroma-comparative-analysis)

### Graph RAG
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [LlamaIndex Property Graph](https://docs.llamaindex.ai/en/stable/examples/property_graph/property_graph_neo4j/)
- [Neo4j + LlamaIndex](https://neo4j.com/labs/genai-ecosystem/llamaindex/)

---

## Related Documentation

- [State-of-the-Art RAG](./state-of-the-art-rag.md) - Retrieval techniques
- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Document extraction
- [State-of-the-Art Metadata](./state-of-the-art-metadata.md) - Metadata management
- [ADR-0002: ChromaDB Vector Store](../decisions/adrs/0002-chromadb-vector-store.md) - Why ChromaDB

---

**Status**: Research complete, informs v0.3+ roadmap

