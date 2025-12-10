# ADR-0027: Fine-Tuning Strategy for Local RAG

## Status

Proposed

## Context

ragd is a local-first RAG system that currently uses pre-trained embedding models and relies on Ollama for LLM generation. Users with domain-specific corpora (legal, medical, technical) may benefit from fine-tuned models that better understand their terminology and document structures.

Research shows:
- Embedding fine-tuning can improve retrieval by 5-25% for specialised domains
- RAFT (Retrieval Augmented Fine-Tuning) improves LLM accuracy by 35-76% on domain tasks
- Reranker fine-tuning improves precision by 10-20%

The challenge is enabling fine-tuning while:
1. Maintaining ragd's local-only principle
2. Supporting both Apple Silicon and CUDA platforms equally
3. Keeping the barrier to entry low for non-ML-experts
4. Integrating with existing abstractions (Embedder protocol, LLMClient)

## Decision

### 1. Prioritise Embedding Fine-Tuning First

**Rationale:**
- Lowest barrier to entry (smaller models, faster training)
- Works with existing Ollama LLM setup (no LLM fine-tuning required initially)
- Affects entire retrieval pipeline (high impact)
- Training data can be synthetically generated from existing documents

**Implementation:**
- Use sentence-transformers library for fine-tuning
- Support MultipleNegativesRankingLoss and Matryoshka loss
- Provide CLI commands for data generation and training

### 2. Use Synthetic Data Generation Over Manual Labelling

**Rationale:**
- Scales with corpus size automatically
- No domain expertise required from users
- Leverages existing Ollama LLM for query generation
- Quality filtering ensures useful training pairs

**Implementation:**
```
Documents → Chunks → [Ollama generates questions] → (query, chunk) pairs
                   → [Mine hard negatives] → Training dataset
```

### 3. Platform-Specific Fine-Tuning Backends

**Rationale:**
- Apple Silicon users are a primary audience (local-first philosophy)
- MLX provides native performance on M-series chips
- CUDA users have more framework options (Unsloth for efficiency)
- Graceful fallback to CPU or cloud suggestions

**Decision Matrix:**

| Platform | Primary Backend | Fallback |
|----------|-----------------|----------|
| Apple Silicon | MLX (mlx-lm) | sentence-transformers (CPU) |
| CUDA | Unsloth | Axolotl, Torchtune |
| CPU-only | sentence-transformers | Cloud/Colab guidance |

**Implementation:**
- Detect hardware via existing `hardware.py` module
- Automatically select appropriate backend
- Allow manual override via configuration

### 4. Integrate via Existing Embedder Protocol

**Rationale:**
- No breaking changes to existing codebase
- Fine-tuned models are drop-in replacements
- Configuration-based model selection
- Consistent API for all embedding sources

**Implementation:**
```python
# Configuration
embedding:
  model: "custom"
  custom_model_path: "~/.ragd/models/finetuned-embeddings"

# Or with adapters
embedding:
  model: "BAAI/bge-small-en-v1.5"
  adapter_path: "~/.ragd/adapters/domain-specific"
```

### 5. Phased Rollout of Fine-Tuning Capabilities

| Phase | Capability | Milestone |
|-------|------------|-----------|
| 1 | Embedding fine-tuning | v0.9.0 |
| 2 | Reranker fine-tuning | v0.9.x |
| 3 | LLM fine-tuning (RAFT) | v1.0+ |

## Consequences

### Positive

- Users can customise ragd for their specific domains
- Significant retrieval improvements for specialised use cases
- Platform-agnostic approach supports diverse user base
- Synthetic data generation lowers barrier to entry
- No breaking changes to existing functionality

### Negative

- Adds complexity to the codebase
- Fine-tuning requires additional dependencies (sentence-transformers, mlx-lm, unsloth)
- Training quality depends on corpus quality
- Users need sufficient hardware (8GB+ memory recommended)
- Model management adds storage overhead

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Poor fine-tuning results | A/B evaluation tools, rollback to base model |
| Dependency conflicts | Optional dependency groups (`pip install ragd[finetune]`) |
| Storage bloat | Model pruning, adapter-only storage |
| Platform fragmentation | Unified CLI, automatic backend selection |

## Alternatives Considered

### 1. Cloud-Only Fine-Tuning

**Rejected because:**
- Violates local-first principle
- Requires data upload (privacy concern)
- Adds external dependency and cost

### 2. Pre-Built Domain Models

**Rejected because:**
- Limited to pre-defined domains
- Cannot adapt to user's specific corpus
- Model distribution complexity

### 3. Full Fine-Tuning Only (No LoRA/QLoRA)

**Rejected because:**
- Prohibitive memory requirements (48GB+)
- Excludes consumer hardware users
- Longer training times discourage experimentation

### 4. Single Framework (Unsloth Only)

**Rejected because:**
- Excludes Apple Silicon users (MLX performs better)
- Single point of failure if framework changes
- Limits user choice

## Implementation Notes

### CLI Commands

```bash
# Generate synthetic training data
ragd train generate-data --output ./training_data.json

# Fine-tune embedding model
ragd train embeddings --data ./training_data.json --output ./models/finetuned

# Evaluate fine-tuned model
ragd train evaluate --model ./models/finetuned --test-data ./test_data.json

# Use fine-tuned model
ragd config set embedding.custom_model_path ./models/finetuned
```

### Dependencies

```toml
[project.optional-dependencies]
finetune = [
    "sentence-transformers>=3.0.0",
    "datasets>=2.14.0",
]
finetune-mlx = [
    "mlx>=0.10.0",
    "mlx-lm>=0.10.0",
]
finetune-cuda = [
    "unsloth>=2024.8",
    "bitsandbytes>=0.41.0",
]
```

## Related Documentation

- [State-of-the-Art Fine-Tuning](../../research/state-of-the-art-fine-tuning.md) - Research basis
- [State-of-the-Art Embeddings](../../research/state-of-the-art-embeddings.md) - Model selection
- [F-058: Fine-Tuning Pipeline](../../features/planned/F-058-fine-tuning-pipeline.md) - Feature specification
- [ADR-0007: Advanced Retrieval Techniques](./0007-advanced-retrieval-techniques.md) - Related decisions

---

**Status**: Proposed
