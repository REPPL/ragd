# State-of-the-Art Apple Silicon Optimisation for Local RAG

Strategies for leveraging Apple Silicon's unified memory architecture in local RAG systems.

## Executive Summary

Apple Silicon's unified memory architecture fundamentally changes what's possible for local RAG:

- **No PCIe bottleneck**: Models up to 600B+ parameters can run on a single machine
- **Memory tiers**: From 8GB MacBook Air to 512GB Mac Studio M3 Ultra
- **Automatic scaling**: ragd should detect hardware and optimise automatically

This research covers memory tier strategies, what ragd can do differently with high memory configurations (64GB+), and cross-platform compatibility approaches.

---

## The Unified Memory Advantage

### Architecture Comparison

| Architecture | Memory Access | Bandwidth | Model Loading |
|-------------|---------------|-----------|---------------|
| Discrete GPU (RTX 4090) | CPU → PCIe → GPU VRAM | ~1TB/s VRAM, but PCIe bottleneck | Must fit in VRAM (24GB) |
| Apple Silicon | Shared pool, no transfer | 800GB/s (M3 Ultra) | Up to 512GB unified |

**Key insight**: For models that exceed GPU VRAM, Apple Silicon outperforms discrete GPUs because there's no PCIe transfer bottleneck.

### Why This Matters for RAG

Traditional GPU deployments face a hard limit: if your model doesn't fit in VRAM (typically 24GB max for consumer GPUs), you must quantise aggressively or use CPU fallback. Apple Silicon with 128GB+ unified memory can run:

- 70B parameter models at Q4 quantisation (~45GB)
- 10M+ vectors in memory (~60GB with HNSW overhead)
- Multiple models loaded simultaneously (no swap penalty)
- 128K+ token context windows

---

## Memory Tier Strategies

### Tier 1: 8-16GB (MacBook Air, base MacBook Pro)

**Target Users**: Casual users, students, developers testing locally

```
Configuration:
├── LLM:        3B quantised (Llama-3.2-3B Q4_K_M) → ~2GB
├── Embeddings: nomic-embed-text-v1.5 (137M) → ~500MB
├── Vectors:    <100K in-memory → ~300MB
├── Cache:      100MB semantic cache
└── Total:      ~3GB peak usage
```

**ragd Optimisations:**
- Single model loaded at a time
- Aggressive cache eviction
- Disk-based vector persistence (ChromaDB default)
- Smaller batch sizes for embedding

### Tier 2: 32-64GB (MacBook Pro Max, Mac Studio base)

**Target Users**: Professional developers, researchers, small teams

```
Configuration:
├── LLM:        7-13B quantised (Llama-3.1-8B Q5_K_M) → ~6GB
├── Embeddings: nomic-embed-text-v1.5 (137M) → ~500MB
├── Vectors:    100K-1M in-memory → ~3GB
├── Cache:      500MB semantic cache
├── Reranker:   bge-reranker-base (278M) → ~1GB (optional)
└── Total:      ~10-15GB peak usage
```

**ragd Optimisations:**
- 2-3 models loaded (embedding + LLM + optional reranker)
- Moderate HNSW parameters (M=16, ef=100)
- In-memory vector index for collections under 1M
- Background model preloading

### Tier 3: 96-128GB (Mac Studio M2/M3 Max)

**Target Users**: Power users, AI researchers, enterprise single-user

```
Configuration:
├── LLM:        30B-70B quantised (Qwen2.5-72B Q4_K_M) → ~45GB
├── Embeddings: Large model (1B+ params) → ~4GB
├── Vectors:    1M-10M in-memory → ~30GB
├── Cache:      2GB+ semantic cache
├── Context:    32K+ token windows → ~1GB
└── Total:      ~80GB peak usage
```

**ragd Optimisations:**
- Multiple models loaded without swapping
- High-quality HNSW parameters (M=24, ef=150)
- Large semantic cache (100K+ queries)
- Extended context windows for complex queries
- Background batch processing

### Tier 4: 192-512GB (Mac Studio M3 Ultra)

**Target Users**: Research labs, enterprise deployments, AI developers

```
Configuration:
├── LLM:        70B-600B+ quantised models → ~50-300GB
├── Embeddings: Multiple embedding models → ~10GB
├── Vectors:    10M-100M in-memory → ~60-120GB
├── Cache:      10GB+ semantic cache
├── Context:    128K+ token contexts
├── GraphRAG:   In-memory knowledge graphs → ~10GB
└── Total:      ~150-400GB peak usage
```

**ragd Optimisations:**
- Full model zoo loaded (route by task complexity)
- Maximum HNSW quality (M=32, ef=200)
- Entire corpus in memory
- In-memory knowledge graphs (NetworkX/Kuzu)
- Speculative retrieval and caching

---

## What ragd Should Do Differently with 128GB+

### 1. Automatic Model Size Selection

```python
def recommend_model(available_memory_gb: float) -> str:
    """Recommend LLM model based on available memory."""
    if available_memory_gb >= 128:
        return "qwen2.5:72b-instruct-q4_K_M"  # ~45GB
    elif available_memory_gb >= 64:
        return "llama3.1:70b-instruct-q4_K_M"  # ~40GB
    elif available_memory_gb >= 32:
        return "llama3.1:8b-instruct-q5_K_M"   # ~6GB
    elif available_memory_gb >= 16:
        return "llama3.2:3b-instruct-q5_K_M"   # ~3GB
    else:
        return "llama3.2:1b-instruct-q4_K_M"   # ~1GB
```

### 2. In-Memory Vector Index Configuration

```python
def get_hnsw_settings(available_memory_gb: float, vector_count: int) -> dict:
    """Configure HNSW parameters based on memory and corpus size."""

    # Memory required: vectors × dims × 4 bytes × 2 (HNSW overhead)
    # 10M vectors × 768 dims × 4 bytes × 2 = ~60GB

    if available_memory_gb >= 128:
        return {
            "hnsw:M": 32,                # Maximum connections
            "hnsw:ef_construction": 400,  # High index quality
            "hnsw:ef_search": 200,        # High recall
            "hnsw:space": "cosine"
        }
    elif available_memory_gb >= 64:
        return {
            "hnsw:M": 24,
            "hnsw:ef_construction": 300,
            "hnsw:ef_search": 150,
            "hnsw:space": "cosine"
        }
    elif available_memory_gb >= 32:
        return {
            "hnsw:M": 16,
            "hnsw:ef_construction": 200,
            "hnsw:ef_search": 100,
            "hnsw:space": "cosine"
        }
    else:
        return {
            "hnsw:M": 8,
            "hnsw:ef_construction": 100,
            "hnsw:ef_search": 50,
            "hnsw:space": "cosine"
        }
```

### 3. Multi-Model Pool (No Swap Penalty)

```python
class HighMemoryModelPool:
    """Load multiple models simultaneously when memory permits."""

    def __init__(self, available_memory_gb: float):
        self.models = {}

        if available_memory_gb >= 128:
            self.models = {
                "embed": "nomic-embed-text-v1.5",    # ~500MB
                "rerank": "bge-reranker-base",       # ~1GB
                "fast": "llama3.2:3b-instruct",      # ~2GB
                "quality": "qwen2.5:72b-instruct",   # ~45GB
            }
        elif available_memory_gb >= 64:
            self.models = {
                "embed": "nomic-embed-text-v1.5",
                "rerank": "bge-reranker-base",
                "quality": "llama3.1:8b-instruct",
            }
        else:
            self.models = {
                "embed": "nomic-embed-text-v1.5",
                "quality": "llama3.2:3b-instruct",
            }

    def route(self, query_complexity: str) -> str:
        """Route query to appropriate model based on complexity."""
        if query_complexity == "simple" and "fast" in self.models:
            return self.models["fast"]
        return self.models["quality"]
```

### 4. Aggressive Semantic Caching

```python
class TieredSemanticCache:
    """Size cache based on available memory."""

    def __init__(self, available_memory_gb: float):
        if available_memory_gb >= 128:
            self.max_entries = 100_000      # 100K queries
            self.max_memory_gb = 5.0        # 5GB cache
        elif available_memory_gb >= 64:
            self.max_entries = 50_000
            self.max_memory_gb = 2.0
        elif available_memory_gb >= 32:
            self.max_entries = 10_000
            self.max_memory_gb = 0.5
        else:
            self.max_entries = 1_000
            self.max_memory_gb = 0.1
```

### 5. Extended Context Windows

```python
def get_max_context_tokens(available_memory_gb: float) -> int:
    """Determine maximum context window based on memory."""
    # Rule of thumb: 128K tokens ≈ 1GB memory overhead

    if available_memory_gb >= 128:
        return 128_000  # Full Qwen/Llama context
    elif available_memory_gb >= 64:
        return 64_000
    elif available_memory_gb >= 32:
        return 32_000
    elif available_memory_gb >= 16:
        return 16_000
    else:
        return 4_000    # Conservative for low memory
```

### 6. In-Memory Knowledge Graph (Future)

```python
def should_use_memory_graph(available_memory_gb: float, node_count: int) -> bool:
    """Determine if knowledge graph can fit in memory."""
    # Rule: ~1KB per node for NetworkX DiGraph
    estimated_memory_gb = (node_count * 1024) / (1024**3)

    return (
        available_memory_gb >= 128 and
        estimated_memory_gb < available_memory_gb * 0.1  # Max 10% for graph
    )
```

---

## Cross-Platform Compatibility

### Hardware Detection Strategy

```python
from enum import Enum, auto
from dataclasses import dataclass

class ComputeBackend(Enum):
    APPLE_SILICON = auto()  # MPS/Metal
    CUDA = auto()           # NVIDIA GPU
    CPU = auto()            # Fallback

class HardwareTier(Enum):
    MINIMAL = auto()        # <16GB usable
    STANDARD = auto()       # 16-32GB usable
    HIGH = auto()           # 32-96GB usable
    EXTREME = auto()        # 96GB+ usable

@dataclass
class HardwareProfile:
    backend: ComputeBackend
    tier: HardwareTier
    usable_memory_gb: float
    device_name: str

def detect_hardware() -> HardwareProfile:
    """Detect hardware and determine optimal configuration."""
    import platform
    import psutil

    total_gb = psutil.virtual_memory().total / (1024**3)

    # Check for Apple Silicon
    if platform.system() == "Darwin" and platform.processor() == "arm":
        try:
            import torch
            if torch.backends.mps.is_available():
                usable_gb = total_gb * 0.8  # 80% of unified memory
                return HardwareProfile(
                    backend=ComputeBackend.APPLE_SILICON,
                    tier=_memory_to_tier(usable_gb),
                    usable_memory_gb=usable_gb,
                    device_name=f"Apple {platform.processor()}"
                )
        except ImportError:
            pass

    # Check for CUDA
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return HardwareProfile(
                backend=ComputeBackend.CUDA,
                tier=_memory_to_tier(vram_gb),
                usable_memory_gb=vram_gb,
                device_name=torch.cuda.get_device_name(0)
            )
    except ImportError:
        pass

    # CPU fallback
    usable_gb = total_gb * 0.5  # Conservative for CPU
    return HardwareProfile(
        backend=ComputeBackend.CPU,
        tier=_memory_to_tier(usable_gb),
        usable_memory_gb=usable_gb,
        device_name="CPU"
    )

def _memory_to_tier(memory_gb: float) -> HardwareTier:
    if memory_gb >= 96:
        return HardwareTier.EXTREME
    elif memory_gb >= 32:
        return HardwareTier.HIGH
    elif memory_gb >= 16:
        return HardwareTier.STANDARD
    return HardwareTier.MINIMAL
```

### Platform-Specific Defaults

| Feature | Apple Silicon (128GB) | CUDA (24GB) | CPU Only |
|---------|----------------------|-------------|----------|
| LLM Size | 70B Q4 | 13B Q4 | 7B Q4 |
| Vectors In-Memory | 10M+ | 1M | 500K |
| Models Loaded | 4-5 | 2 | 1 |
| Context Window | 128K | 32K | 8K |
| Semantic Cache | 5GB | 500MB | 100MB |
| HNSW M | 32 | 16 | 8 |

---

## Implementation Roadmap

### v0.1 (Foundation)

- Hardware detection via `ragd doctor`
- Memory tier display and recommendations
- Basic MPS/Metal detection via PyTorch
- Conservative defaults that work on all tiers

### v0.2 (Memory-Aware)

- Automatic model size selection
- ChromaDB HNSW tuning by tier
- Semantic cache sizing
- Memory usage monitoring

### v0.3+ (Advanced)

- Multi-model routing
- In-memory GraphRAG option
- MLX inference backend (optional)
- Speculative retrieval

---

## Performance Benchmarks (Expected)

### Query Latency by Tier

| Tier | Embedding | Retrieval | Generation | Total |
|------|-----------|-----------|------------|-------|
| Tier 1 (8GB) | 50ms | 100ms | 3000ms | ~3.2s |
| Tier 2 (32GB) | 30ms | 50ms | 1500ms | ~1.6s |
| Tier 3 (128GB) | 20ms | 30ms | 800ms | ~0.9s |
| Tier 4 (512GB) | 10ms | 20ms | 500ms | ~0.5s |

### Throughput by Tier

| Tier | Docs/Hour (Indexing) | Queries/Minute |
|------|---------------------|----------------|
| Tier 1 | ~500 | ~20 |
| Tier 2 | ~2,000 | ~40 |
| Tier 3 | ~10,000 | ~70 |
| Tier 4 | ~50,000 | ~120 |

---

## References

- [Training LLMs on Apple Silicon: M3 Ultra Guide](https://markaicode.com/training-llms-apple-silicon-m3-ultra-guide/)
- [Best Local LLMs for Apple Silicon](https://apxml.com/posts/best-local-llm-apple-silicon-mac)
- [Mac Studio M3 Ultra AI Workstation Review](https://creativestrategies.com/mac-studio-m3-ultra-ai-workstation-review/)
- [Thoughts on Apple Silicon Performance for Local LLMs](https://medium.com/@andreask_75652/thoughts-on-apple-silicon-performance-for-local-llms-3ef0a50e08bd)
- [llama.cpp Apple Silicon Performance Discussion](https://github.com/ggml-org/llama.cpp/discussions/4167)
- [Local LLM Hardware Guide 2025](https://introl.com/blog/local-llm-hardware-pricing-guide-2025)
- [Apple M3 Ultra Announcement](https://www.apple.com/newsroom/2025/03/apple-reveals-m3-ultra-taking-apple-silicon-to-a-new-extreme/)

---

## Related Documentation

- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Model selection
- [State-of-the-Art Setup UX](./state-of-the-art-setup-ux.md) - Installation and detection
- [F-035: Health Check](../features/completed/F-035-health-check.md) - ragd doctor implementation

---

**Status**: Research complete
