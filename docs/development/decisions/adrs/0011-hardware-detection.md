# ADR-0011: Hardware Detection and Tier-Based Configuration

## Status

Accepted

## Context

ragd must run effectively across diverse hardware configurations:
- MacBook Air with 8GB unified memory
- Mac Studio with 128GB+ unified memory
- Linux workstations with NVIDIA GPUs (8-48GB VRAM)
- CPU-only servers

Without automatic hardware detection, users must manually configure model selection, memory limits, and performance parameters. This creates friction and leads to suboptimal configurations (too conservative on powerful hardware, crashes on limited hardware).

The Apple Silicon unified memory architecture fundamentally changes what's possible for local RAG:
- No PCIe bottleneck for model loading
- Models up to system memory limit (512GB on M3 Ultra)
- Different optimal configurations per memory tier

## Decision

Implement **automatic hardware detection** with a **four-tier classification system** that drives model selection, memory allocation, and performance tuning.

### Hardware Tiers

| Tier | Usable Memory | LLM Size | Models Loaded | Use Case |
|------|---------------|----------|---------------|----------|
| MINIMAL | <16GB | 1-3B | 1 | Basic laptops |
| STANDARD | 16-32GB | 3-8B | 2 | Professional laptops |
| HIGH | 32-96GB | 8-70B | 3 + reranker | Workstations |
| EXTREME | 96GB+ | 70B+ | Full pool | High-end workstations |

### Detection Strategy

```python
from enum import Enum, auto

class ComputeBackend(Enum):
    APPLE_SILICON = auto()  # MPS/Metal
    CUDA = auto()           # NVIDIA GPU
    CPU = auto()            # Fallback

class HardwareTier(Enum):
    MINIMAL = auto()
    STANDARD = auto()
    HIGH = auto()
    EXTREME = auto()

def detect_hardware() -> tuple[ComputeBackend, HardwareTier]:
    """Detect compute backend and memory tier."""
    import platform
    import psutil

    total_gb = psutil.virtual_memory().total / (1024**3)

    # Apple Silicon detection
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        usable_gb = total_gb * 0.8  # 80% of unified memory
        return ComputeBackend.APPLE_SILICON, _memory_to_tier(usable_gb)

    # CUDA detection
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return ComputeBackend.CUDA, _memory_to_tier(vram_gb)
    except ImportError:
        pass

    # CPU fallback
    usable_gb = total_gb * 0.5  # Conservative for CPU
    return ComputeBackend.CPU, _memory_to_tier(usable_gb)

def _memory_to_tier(memory_gb: float) -> HardwareTier:
    if memory_gb >= 96:
        return HardwareTier.EXTREME
    elif memory_gb >= 32:
        return HardwareTier.HIGH
    elif memory_gb >= 16:
        return HardwareTier.STANDARD
    return HardwareTier.MINIMAL
```

### Tier-Based Configuration

Each tier configures:

1. **Model Recommendations**
   - MINIMAL: `llama3.2:1b`
   - STANDARD: `llama3.2:3b`
   - HIGH: `llama3.1:8b` + reranker
   - EXTREME: `qwen2.5:72b` + reranker + fast model

2. **HNSW Parameters** (vector index quality vs memory)
   - MINIMAL: M=8, ef_construction=100, ef_search=50
   - STANDARD: M=16, ef_construction=200, ef_search=100
   - HIGH: M=24, ef_construction=300, ef_search=150
   - EXTREME: M=32, ef_construction=400, ef_search=200

3. **Semantic Cache Size**
   - MINIMAL: 1,000 entries, 100MB
   - STANDARD: 10,000 entries, 500MB
   - HIGH: 50,000 entries, 2GB
   - EXTREME: 100,000 entries, 5GB

4. **Context Window**
   - MINIMAL: 4,000 tokens
   - STANDARD: 16,000 tokens
   - HIGH: 32,000 tokens
   - EXTREME: 128,000 tokens

### Storage in Configuration

Detection results are stored in `~/.ragd/config.yaml`:

```yaml
hardware:
  backend: mps
  tier: extreme
  memory_gb: 128
  detected_at: 2025-01-15T10:30:00Z
```

This avoids re-detection on every command while allowing manual override.

## Consequences

### Positive

- Zero-configuration experience for most users
- Optimal performance without manual tuning
- Prevents crashes from over-allocation on limited hardware
- Leverages full capability of high-end hardware
- Clear upgrade path as users add memory

### Negative

- Detection adds ~100ms to first run
- May misdetect in virtualised/containerised environments
- Hardcoded tier boundaries may not suit all workloads
- Users with unusual configurations may need manual override

## Alternatives Considered

### Manual Configuration Only

- **Pros:** Full user control, no detection complexity
- **Cons:** Friction for new users, likely misconfiguration
- **Rejected:** Too much burden on non-technical users

### Dynamic Per-Command Detection

- **Pros:** Always accurate, no stale config
- **Cons:** Performance overhead on every command
- **Rejected:** Unnecessary latency for stable hardware

### Continuous Spectrum (No Tiers)

- **Pros:** Fine-grained configuration
- **Cons:** Complex to reason about, harder to test
- **Rejected:** Tiers provide clear mental model and testing boundaries

## Related Documentation

- [State-of-the-Art Apple Silicon](../../research/state-of-the-art-apple-silicon.md)
- [F-035: Health Check Command](../../features/completed/F-035-health-check.md)
- [F-036: Guided Setup](../../features/completed/F-036-guided-setup.md)
- [ADR-0013: Configuration Schema](./0013-configuration-schema.md)
