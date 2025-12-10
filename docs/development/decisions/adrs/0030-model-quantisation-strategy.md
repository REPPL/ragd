# ADR-0030: Model Quantisation Strategy

## Status

Accepted

## Context

ragd targets Apple Silicon systems with unified memory (8GB to 128GB+). Users need guidance on optimal quantisation settings to balance model quality, memory usage, and inference speed.

Key considerations:
- GGUF format with K-quants provides native Metal optimisation
- Q4_K_M offers the best quality/size ratio in blind testing
- KV cache quantisation (Q8_0) halves context memory with negligible quality loss
- Multi-model scenarios require careful memory budgeting

Research findings from [State-of-the-Art Quantisation](../../research/state-of-the-art-quantisation.md) show:
- Q4_K_M through Q6_K are nearly indistinguishable from FP16 in blind tests
- 70B models at Q4_K_M achieve identical benchmark scores to higher quants
- Q8_0 KV cache reduces context memory by 50% with negligible quality impact

## Decision

ragd will use the following default quantisation strategy:

### Weight Quantisation Defaults

| Priority | Quantisation | Use Case |
|----------|--------------|----------|
| Default | Q4_K_M | Best quality/size balance |
| Quality | Q5_K_M | When memory permits |
| Maximum | Q6_K | Near-lossless quality |
| Constrained | Q4_K_S | Memory-limited systems |

### KV Cache Quantisation

- **Default**: Q8_0 (halves context memory)
- **Quality**: FP16 (when memory permits)
- **Constrained**: Q4_0 (not recommended for complex reasoning)

### Format

- **Required**: GGUF with K-quants
- **Rationale**: Native Metal support, mature ecosystem (Ollama, llama.cpp)

### Ollama Configuration Defaults

```bash
OLLAMA_KV_CACHE_TYPE=q8_0        # Enable KV cache quantisation
OLLAMA_FLASH_ATTENTION=1         # Enable flash attention
OLLAMA_MAX_LOADED_MODELS=3       # Multi-model support
```

### Hardware Tier Recommendations

| RAM | Primary Model | Secondary | Context |
|-----|---------------|-----------|---------|
| 8GB | 8B Q4_K_M | - | 4K |
| 16GB | 8B Q4_K_M | 3B Q4_K_M | 8K |
| 32GB | 14B Q4_K_M | 8B Q4_K_M | 16K |
| 64GB | 32B Q4_K_M | 8B Q4_K_M | 32K |
| 128GB | 70B Q4_K_M | 8B Q4_K_M | 32K+ |

## Consequences

### Positive

- **Consistent defaults**: Users get optimal settings out-of-the-box
- **Memory efficiency**: Q8_0 KV cache enables longer contexts
- **Quality preservation**: Q4_K_M maintains high quality with 75% memory reduction
- **Multi-model support**: Memory budgeting enables concurrent model loading

### Negative

- **Format lock-in**: GGUF-only limits model availability (mitigated by wide ecosystem adoption)
- **Complexity**: Multiple quantisation options may confuse users (mitigated by sensible defaults)

### Neutral

- Users can override defaults via configuration
- Future Apple Silicon improvements may shift optimal settings

## Alternatives Considered

### GPTQ/AWQ

- Better suited for NVIDIA CUDA systems
- Less mature Metal support
- Rejected: GGUF has better Apple Silicon optimisation

### FP16 Default

- Maximum quality
- Rejected: Requires 2-4x more memory with minimal perceptible quality benefit

### Q8_0 Default

- Higher quality than Q4_K_M
- Rejected: Q4_K_M achieves same benchmark scores at 50% memory cost

### No KV Cache Quantisation

- Maximum context quality
- Rejected: Q8_0 KV cache halves memory with negligible quality impact

---

## Related Documentation

- [State-of-the-Art Quantisation](../../research/state-of-the-art-quantisation.md) - Research informing this decision
- [ADR-0011: Hardware Detection](./0011-hardware-detection.md) - Hardware tier system
- [ADR-0026: Multi-Model Architecture](./0026-multi-model-architecture.md) - Multi-model memory planning
- [F-020: Ollama LLM Integration](../../features/completed/F-020-ollama-llm-integration.md) - Implementation feature
- [F-055: Multi-Model Orchestration](../../features/completed/F-055-multi-model-orchestration.md) - Multi-model memory requirements

---

**Status**: Accepted
