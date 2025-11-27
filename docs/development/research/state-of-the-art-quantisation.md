# State-of-the-Art: LLM Quantisation for Apple Silicon

Research on quantisation methods, quality trade-offs, and optimal configurations for local LLM deployment on Apple Silicon with unified memory.

## Executive Summary

Quantisation reduces LLM memory requirements by using lower-precision number formats, enabling larger models to run on consumer hardware. For Apple Silicon with unified memory (particularly the M4 Max with 128GB), the optimal approach combines:

- **Weight quantisation**: Q4_K_M or Q5_K_M for excellent quality/size balance
- **KV cache quantisation**: Q8_0 to halve context memory requirements
- **Format**: GGUF with K-quants for native Metal optimisation

**Key finding**: Q4_K_M is the "sweet spot" - blind testing shows it's nearly indistinguishable from FP16 for most use cases, while reducing memory by 75%.

---

## Quantisation Methods Overview

### GGUF (Recommended for Apple Silicon)

GGUF (GPT-Generated Unified Format) is the native format for llama.cpp and Ollama, with first-class Metal support on Apple Silicon.

**K-Quants (Mixed Precision)**

K-quants use different precision for different layers based on their sensitivity:

| Quant | Description | Use Case |
|-------|-------------|----------|
| Q8_0 | 8-bit uniform | Maximum quality, ~2x smaller than FP16 |
| Q6_K | 6-bit K-quant | Near-lossless, minimal degradation |
| Q5_K_M | 5-bit K-quant medium | Excellent balance |
| Q4_K_M | 4-bit K-quant medium | **Sweet spot** - best quality/size ratio |
| Q4_K_S | 4-bit K-quant small | Smaller than Q4_K_M, slight quality loss |
| Q4_0 | 4-bit uniform | Legacy, prefer Q4_K variants |
| Q3_K | 3-bit K-quant | Noticeable degradation |
| Q2_K | 2-bit K-quant | Not recommended - significant quality loss |

**Quality Hierarchy** (best to worst):
```
Q8_0 > Q6_K > Q5_K_M > Q4_K_M > Q4_K_S > Q4_0 > Q3_K > Q2_K
```

### GPTQ (GPU-Optimised)

- 4-bit quantisation with calibration dataset
- Optimised for NVIDIA GPUs with CUDA
- Less efficient on Apple Silicon
- Use case: CUDA-based systems

### AWQ (Activation-Aware)

- Preserves important weights based on activation patterns
- Better quality than GPTQ at same bit-width
- Growing Metal support but less mature than GGUF
- Use case: When quality is paramount on CUDA systems

### EXL2 (ExLlama v2)

- Variable bit-width (2-8 bits per layer)
- Excellent quality retention
- CUDA-only, no Apple Silicon support
- Use case: NVIDIA GPUs with memory constraints

**Recommendation for Apple Silicon**: Use GGUF with K-quants for best performance and compatibility.

---

## Quality vs Size Trade-offs

### Perplexity Benchmarks (7B Models)

| Quant | Size | PPL Impact | Memory | Recommendation |
|-------|------|------------|--------|----------------|
| FP16 | ~14GB | Baseline | High | Reference only |
| Q8_0 | ~7GB | +0.01 | 50% | Maximum quality |
| Q6_K | ~5.5GB | +0.02 | 39% | Near-lossless |
| Q5_K_M | ~4.3GB | +0.035 | 31% | Excellent balance |
| Q4_K_M | ~3.8GB | +0.054 | 27% | **Sweet spot** |
| Q4_K_S | ~3.6GB | +0.115 | 26% | Space-constrained |
| Q3_K | ~3.0GB | +0.290 | 21% | Noticeable degradation |
| Q2_K | ~2.7GB | +0.870 | 19% | Not recommended |

### Blind Testing Results

Community blind testing (llama.cpp discussions) found:

- **Q6_K and Q5_K**: Nearly indistinguishable from FP16 in blind tests
- **Q4_K_M**: Extremely difficult to distinguish from higher quants
- **Q4_K_S**: Minor quality loss detectable in careful comparison
- **Q3_K and below**: Noticeable quality degradation

### Large Model Findings (70B+)

For models 70B parameters and above:
- Q4_K_M through Q8_0 achieve **identical benchmark scores**
- Larger models tolerate quantisation better
- Q4_K_M is optimal for 70B models on 128GB systems

---

## Apple Silicon Optimisations

### M4 Max 128GB Specifications

| Specification | Value |
|--------------|-------|
| Memory | 128GB unified (LPDDR5X) |
| Memory bandwidth | 546 GB/s (512-bit bus) |
| GPU cores | 40 |
| P-cores | 12 |
| E-cores | 4 |
| Neural Engine | 16-core |

### Performance Benchmarks

| Model | Quant | Size | Tokens/sec | Context |
|-------|-------|------|------------|---------|
| 104B | Q6_K | ~85GB | 4.5 t/s | 32K |
| 104B | Q4_K_M | ~60GB | 6.5 t/s | 32K |
| 70B | Q6_K | ~55GB | 8-10 t/s | 8K |
| 70B | Q4_K_M | ~40GB | 10-14 t/s | 8K |
| 70B | Q4_0 | ~40GB | 14 t/s | 8K |
| 32B | Q4_K_M | ~18GB | 25-30 t/s | 8K |
| 8B | Q4_K_M | ~5GB | 96-100 t/s | 8K |

**Practical model limits (128GB)**:
- Maximum: ~104B at Q6_K with 32K context
- Comfortable: 70B at Q4_K_M with 32K context + headroom
- Fast: 8B at Q4_K_M with 100+ t/s

### MLX vs llama.cpp

| Framework | Strengths | Weaknesses |
|-----------|-----------|------------|
| **MLX** | Apple-optimised, ~100 t/s for 8B, native Swift | Smaller ecosystem, fewer models |
| **llama.cpp** | Mature ecosystem, GGUF support, Ollama backend | Slightly less Apple-optimised |

**Recommendation**: Use Ollama (llama.cpp backend) for compatibility and ecosystem benefits. MLX for maximum Apple Silicon performance when models are available.

### CPU Thread Optimisation

```bash
# Use only performance cores for inference
# M4 Max has 12 P-cores
-t 12  # or OLLAMA_NUM_THREADS=12
```

Using efficiency cores for inference can reduce performance. Configure llama.cpp/Ollama to use only P-cores.

---

## Context Window & KV Cache Management

### KV Cache Memory Formula

The KV cache stores attention state and grows linearly with context length:

```
KV Cache Size ≈ 2 × num_layers × hidden_dim × context_length × bytes_per_value
```

**Simplified**: ~0.11 MB per token per 7B model (FP16)

### KV Cache Quantisation

| KV Cache | Memory vs FP16 | Quality Impact |
|----------|----------------|----------------|
| FP16 | 100% (baseline) | None |
| Q8_0 | 50% | Negligible |
| Q4_0 | 33% | Minor (avoid for complex reasoning) |

**Recommendation**: Q8_0 KV cache - halves context memory with negligible quality impact.

### Context vs Memory (8B Model)

| Context | KV Cache (FP16) | KV Cache (Q8_0) | Total (Q4_K_M + KV) |
|---------|-----------------|-----------------|---------------------|
| 4K | 0.44 GB | 0.22 GB | 5.2 GB |
| 8K | 0.88 GB | 0.44 GB | 5.4 GB |
| 16K | 1.75 GB | 0.88 GB | 5.9 GB |
| 32K | 3.5 GB | 1.75 GB | 6.75 GB |
| 64K | 7 GB | 3.5 GB | 8.5 GB |
| 128K | 14 GB | 7 GB | 12 GB |

### Context vs Memory (70B Model)

| Context | KV Cache (FP16) | KV Cache (Q8_0) | Total (Q4_K_M + KV) |
|---------|-----------------|-----------------|---------------------|
| 4K | 4.4 GB | 2.2 GB | 42.2 GB |
| 8K | 8.8 GB | 4.4 GB | 44.4 GB |
| 16K | 17.5 GB | 8.75 GB | 48.75 GB |
| 32K | 35 GB | 17.5 GB | 57.5 GB |
| 64K | 70 GB | 35 GB | 75 GB |

**Key insight**: Long contexts (64K+) on large models require Q8_0 KV cache quantisation to fit in 128GB.

---

## Multi-Model Memory Planning

### Ollama Configuration

```bash
# Multi-model settings for 128GB system
export OLLAMA_MAX_LOADED_MODELS=3       # Max concurrent models
export OLLAMA_NUM_PARALLEL=4            # Parallel requests per model
export OLLAMA_KV_CACHE_TYPE=q8_0        # Halves context memory
export OLLAMA_FLASH_ATTENTION=1         # Enable flash attention
export OLLAMA_KEEP_ALIVE="1h"           # Keep models loaded
```

### Multi-Model Configurations (128GB)

**Quality-Focused Configuration**
| Role | Model | Quant | Memory |
|------|-------|-------|--------|
| Primary generation | 70B | Q5_K_M | 50GB |
| Fast/simple queries | 8B | Q6_K | 6GB |
| Embedding | nomic-embed-text | - | 1GB |
| KV caches (32K) | - | Q8_0 | ~20GB |
| **Total** | | | **77GB** |
| **Headroom** | | | **51GB** |

**Balanced Configuration**
| Role | Model | Quant | Memory |
|------|-------|-------|--------|
| Primary generation | 70B | Q4_K_M | 40GB |
| Secondary generation | 14B | Q4_K_M | 8GB |
| Fast/simple queries | 8B | Q4_K_M | 5GB |
| Embedding | nomic-embed-text | - | 1GB |
| KV caches (32K) | - | Q8_0 | ~20GB |
| **Total** | | | **74GB** |
| **Headroom** | | | **54GB** |

**Multi-Model RAG Configuration**
| Role | Model | Quant | Memory |
|------|-------|-------|--------|
| Primary generation | 32B | Q4_K_M | 18GB |
| Classification/routing | 8B | Q4_K_M | 5GB |
| Specialised tasks (×3) | 3B | Q4_K_M | 5GB |
| Embedding | nomic-embed-text | - | 1GB |
| Reranker | - | - | 1GB |
| KV caches | - | Q8_0 | ~10GB |
| **Total** | | | **40GB** |
| **Headroom** | | | **88GB** |

### Memory Budget Template (128GB)

```
System reserve:              16 GB (macOS, apps)
────────────────────────────────────
Primary model (70B Q4_K_M):  40 GB
Primary KV (32K, Q8_0):       4 GB
Secondary model (8B Q4_K_M):  5 GB
Secondary KV (8K, Q8_0):      1 GB
Embedding model:              1 GB
────────────────────────────────────
Total used:                  67 GB
Headroom:                    61 GB
```

---

## Recommendations for ragd

### Default Quantisation Settings

| Setting | Default | Rationale |
|---------|---------|-----------|
| Weight quantisation | Q4_K_M | Best quality/size ratio |
| Quality mode | Q5_K_M or Q6_K | When memory permits |
| KV cache | Q8_0 | Halves context memory, negligible quality loss |
| Format | GGUF | Native Apple Silicon support |

### Recommended Model Sizes by Hardware

| RAM | Primary Model | Secondary Model | Context |
|-----|---------------|-----------------|---------|
| 8GB | 8B Q4_K_M | - | 4K |
| 16GB | 8B Q4_K_M | 3B Q4_K_M | 8K |
| 32GB | 14B Q4_K_M | 8B Q4_K_M | 16K |
| 64GB | 32B Q4_K_M | 8B Q4_K_M | 32K |
| 128GB | 70B Q4_K_M | 8B Q4_K_M | 32K+ |

### Implementation Guidance

**Ollama Integration**

```python
# Configuration for ragd
QUANTISATION_DEFAULTS = {
    "weight_quant": "Q4_K_M",
    "quality_weight_quant": "Q5_K_M",
    "kv_cache_quant": "q8_0",
    "flash_attention": True,
}

# Context window recommendations
def recommend_context(available_ram_gb: int, model_size_gb: float) -> int:
    """Recommend context window based on available memory."""
    headroom = available_ram_gb - model_size_gb - 16  # System reserve
    if headroom > 40:
        return 65536
    elif headroom > 20:
        return 32768
    elif headroom > 10:
        return 16384
    else:
        return 8192
```

**Model Selection Logic**

```python
def select_quantisation(
    model_params_b: float,
    available_ram_gb: int,
    priority: str = "balanced"
) -> str:
    """Select optimal quantisation based on model size and RAM."""
    if priority == "quality":
        quants = ["Q6_K", "Q5_K_M", "Q4_K_M"]
    else:
        quants = ["Q4_K_M", "Q5_K_M", "Q6_K"]

    for quant in quants:
        estimated_size = estimate_model_size(model_params_b, quant)
        if estimated_size < (available_ram_gb - 20):  # Leave headroom
            return quant

    return "Q4_K_S"  # Fallback for constrained systems
```

---

## References

### Quantisation Quality

- [Blind testing quants](https://github.com/ggml-org/llama.cpp/discussions/5962) - Community blind testing results
- [Demystifying LLM Quantisation](https://medium.com/@paul.ilvez/demystifying-llm-quantization-suffixes-what-q4-k-m-q8-0-and-q6-k-really-mean-0ec2770f17d3) - Quantisation suffix explanation
- [Practical Quantisation Guide](https://enclaveai.app/blog/2025/11/12/practical-quantization-guide-iphone-mac-gguf/) - iPhone/Mac GGUF guide

### Apple Silicon Performance

- [llama.cpp Apple Silicon Discussion](https://github.com/ggml-org/llama.cpp/discussions/4167) - Performance optimisation
- [M4 Max LLM Testing](https://forums.macrumors.com/threads/m4-max-studio-128gb-llm-testing.2453816/) - Community benchmarks
- [M4 Max 200B Parameter Performance](https://seanvosler.medium.com/the-200b-parameter-cruncher-macbook-pro-exploring-the-m4-max-llm-performance-8fd571a94783) - Large model testing

### Memory & Context

- [Context Kills VRAM](https://medium.com/@lyx_62906/context-kills-vram-how-to-run-llms-on-consumer-gpus-a785e8035632) - KV cache memory analysis
- [KV Cache Quantisation in Ollama](https://smcleod.net/2024/12/bringing-k/v-context-quantisation-to-ollama/) - Q8_0 KV cache implementation
- [LLM VRAM Requirements Explained](https://techtactician.com/llm-gpu-vram-requirements-explained/) - Memory calculation guide

### Format Comparison

- [GGUF vs GPTQ vs AWQ](https://newsletter.maartengrootendorst.com/p/which-quantization-method-is-right) - Format comparison
- [Quantisation Format Comparison](https://oobabooga.github.io/blog/posts/gptq-awq-exl2-llamacpp/) - Detailed benchmarks

---

## Related Documentation

- [ADR-0030: Model Quantisation Strategy](../decisions/adrs/0030-model-quantisation-strategy.md) - Default quantisation settings
- [State-of-the-Art Multi-Model RAG](./state-of-the-art-multi-model-rag.md) - Multi-model orchestration
- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Local deployment patterns
- [F-020: Ollama LLM Integration](../features/planned/F-020-ollama-llm-integration.md) - Ollama integration feature
- [F-055: Multi-Model Orchestration](../features/planned/F-055-multi-model-orchestration.md) - Multi-model memory planning

---

**Status**: Complete
