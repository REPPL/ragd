# F-059: Embedding Privacy Protection

## Overview

**Research**: [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)
**ADR**: [ADR-0029: Privacy-Preserving Embedding Strategy](../../decisions/adrs/0029-embedding-privacy-strategy.md)
**Milestone**: v0.8
**Priority**: P2

## Problem Statement

Text embeddings can leak sensitive information through embedding inversion attacks:

- Research demonstrates 92% exact text recovery from embeddings
- Attackers can reconstruct names, health diagnoses, and other PII
- Even with text-level redaction, semantic patterns remain in embeddings
- Embeddings must be treated with the same security as raw text

This creates a gap: even when PII is redacted from text (F-023), residual information may persist in vector representations.

## Design Approach

### Defence-in-Depth Architecture

```
Text Input
    ↓
┌─────────────────────────────────────┐
│ Layer 1: Pre-Vectorisation          │
│ PII Detection & Redaction (F-023)   │
└─────────────────────────────────────┘
    ↓
Sanitised Text
    ↓
┌─────────────────────────────────────┐
│ Layer 2: Embedding Generation       │
│ sentence-transformers               │
└─────────────────────────────────────┘
    ↓
Raw Embedding
    ↓
┌─────────────────────────────────────┐
│ Layer 3: Embedding Protection       │
│ (Optional) Eguard Transformation    │
└─────────────────────────────────────┘
    ↓
Protected Embedding
    ↓
┌─────────────────────────────────────┐
│ Layer 4: Storage Encryption         │
│ SQLCipher (F-015)                   │
└─────────────────────────────────────┘
```

### Protection Methods

| Method | Description | Performance | Protection |
|--------|-------------|-------------|------------|
| **None** | Raw embeddings, encrypted at rest | Baseline | Low |
| **Eguard** | Transformer-based projection | ~20% overhead | High (95% tokens protected) |
| **Differential Privacy** | Add calibrated noise | Variable | Configurable |

### Eguard Integration

[Eguard](https://arxiv.org/abs/2411.05034) uses mutual information optimisation to protect embeddings while preserving utility:

```
Raw Embedding (768-dim)
    ↓
┌─────────────────────────────────────┐
│ Eguard Transformation               │
│  ├─ Sensitive Feature Detachment    │
│  ├─ Autoencoder Projection          │
│  └─ Functionality Preservation      │
└─────────────────────────────────────┘
    ↓
Protected Embedding (768-dim)
    ↓
Storage (ChromaDB)
```

**Key Properties:**
- Output dimensions match input (no schema changes)
- 98% consistency with original for downstream tasks
- 95%+ protection against inversion attacks

## Implementation Tasks

- [ ] Research and evaluate Eguard implementation options
- [ ] Implement embedding transformation module
- [ ] Create configuration schema for protection levels
- [ ] Add `--protect-embeddings` flag to index command
- [ ] Implement protection bypass for performance-critical scenarios
- [ ] Add metrics for protection effectiveness
- [ ] Create benchmarks comparing protected vs unprotected retrieval
- [ ] Write unit tests for transformation correctness
- [ ] Write integration tests for end-to-end flow
- [ ] Document trade-offs in user guide

## Success Criteria

- [ ] Protected embeddings resist inversion attacks (>90% token protection)
- [ ] Retrieval quality degrades <5% with protection enabled
- [ ] Processing overhead documented and configurable
- [ ] Works with existing sentence-transformers models
- [ ] Optional—does not impact users who don't enable it
- [ ] Clear documentation on when to use

## Dependencies

- F-004: Embedding Generation (integration point)
- F-023: PII Detection (complementary protection)
- F-015: Database Encryption (storage layer)
- PyTorch (for Eguard transformation)

## Technical Notes

### Configuration

```yaml
embedding:
  model: all-MiniLM-L6-v2

  protection:
    enabled: false  # Default: off for performance
    method: eguard  # eguard | differential_privacy | none

    eguard:
      model_path: ~/.ragd/models/eguard/  # Pre-trained weights
      batch_size: 32
      device: auto  # cpu | cuda | mps | auto

    differential_privacy:
      epsilon: 1.0  # Privacy budget
      delta: 1e-5
      mechanism: laplace  # laplace | gaussian
```

### CLI Integration

```bash
# Index with embedding protection
ragd index ~/Documents/ --protect-embeddings
# Embeddings will be transformed before storage

# Check protection status
ragd status --embeddings
# Embedding protection: enabled (eguard)
# Protected documents: 1,234
# Unprotected documents: 0

# Disable for specific high-trust documents
ragd index ~/trusted-docs/ --no-protect-embeddings
```

### Embedding Transformation

```python
from ragd.privacy import EguardTransformer

class EmbeddingProtector:
    """Protect embeddings against inversion attacks."""

    def __init__(self, config: EmbeddingProtectionConfig):
        self.transformer = EguardTransformer(
            model_path=config.eguard.model_path,
            device=config.eguard.device
        )
        self.enabled = config.enabled

    def protect(self, embeddings: np.ndarray) -> np.ndarray:
        """Transform embeddings for privacy protection."""
        if not self.enabled:
            return embeddings

        return self.transformer.transform(embeddings)

    def get_metrics(self) -> dict:
        """Return protection effectiveness metrics."""
        return {
            "method": "eguard",
            "token_protection_rate": 0.95,
            "utility_preservation": 0.98
        }
```

### Performance Considerations

| Scenario | Overhead | Recommendation |
|----------|----------|----------------|
| Personal notes | ~20% | Enable if paranoid |
| Medical/financial | ~20% | Recommended |
| General documents | ~20% | Optional |
| High-volume indexing | ~20% | Consider batch later |

**Note:** Primary protection should be pre-vectorisation PII removal (F-023). Embedding protection is a secondary defence for high-security scenarios.

## Related Documentation

- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md) - Research basis
- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md) - Threat model
- [ADR-0029: Privacy-Preserving Embedding Strategy](../../decisions/adrs/0029-embedding-privacy-strategy.md)
- [F-023: PII Detection](../completed/F-023-pii-detection.md) - Primary protection layer
- [F-015: Database Encryption](../completed/F-015-database-encryption.md) - Storage encryption
- [F-004: Embedding Generation](../completed/F-004-embedding-generation.md) - Base capability

---
