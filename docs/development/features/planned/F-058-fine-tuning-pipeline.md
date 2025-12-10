# F-058: Domain-Specific Fine-Tuning Pipeline

## Overview

**Research**: [State-of-the-Art Fine-Tuning](../../research/state-of-the-art-fine-tuning.md)
**Milestone**: v0.9.0
**Priority**: P2

## Problem Statement

Users with specialised document corpora (legal contracts, medical records, technical documentation) experience suboptimal retrieval with general-purpose embedding models. Pre-trained models lack understanding of domain-specific terminology, document structures, and query patterns.

Fine-tuning enables 5-25% retrieval improvement for embedding models and 35-76% accuracy improvement for LLM generation, but the process is complex and requires ML expertise that most ragd users don't have.

## Design Approach

### Architecture

```
User's Documents (already indexed)
         |
         v
[ragd train generate-data]
         |
         +---> Synthetic queries via Ollama
         +---> Hard negative mining from index
         |
         v
Training Dataset (query, positive, negatives)
         |
         v
[ragd train embeddings/reranker/llm]
         |
         +---> Platform detection (MLX vs CUDA)
         +---> Backend selection (automatic)
         +---> Training with progress display
         |
         v
Fine-tuned Model (~/.ragd/models/)
         |
         v
[ragd train evaluate]
         |
         +---> A/B comparison with base model
         +---> RAGAS metrics
         |
         v
[ragd config set] to use fine-tuned model
```

### Technologies

- **Embedding Fine-Tuning**: sentence-transformers
- **LLM Fine-Tuning (Apple Silicon)**: MLX, mlx-lm
- **LLM Fine-Tuning (CUDA)**: Unsloth, Axolotl
- **Data Generation**: Ollama (existing integration)
- **Evaluation**: RAGAS (F-013)

### Platform Support

| Platform | Embedding | LLM (LoRA) | Reranker |
|----------|-----------|------------|----------|
| Apple Silicon | sentence-transformers | MLX | sentence-transformers |
| CUDA | sentence-transformers | Unsloth | sentence-transformers |
| CPU-only | sentence-transformers | N/A (guidance) | sentence-transformers |

## Implementation Tasks

### Phase 1: Synthetic Data Generation

- [ ] Create `ragd train generate-data` command
- [ ] Implement query generation from chunks via Ollama
- [ ] Add hard negative mining from existing index
- [ ] Support quality filtering with LLM-as-judge
- [ ] Output training data in standard formats (JSON, JSONL)
- [ ] Add progress display with Rich

### Phase 2: Embedding Fine-Tuning

- [ ] Create `ragd train embeddings` command
- [ ] Implement MultipleNegativesRankingLoss training
- [ ] Add Matryoshka loss support for flexible dimensions
- [ ] Integrate with existing `Embedder` protocol
- [ ] Save models to `~/.ragd/models/`
- [ ] Add training progress and metrics display

### Phase 3: Reranker Fine-Tuning

- [ ] Create `ragd train reranker` command
- [ ] Implement cross-encoder fine-tuning
- [ ] Support ColBERT training (optional)
- [ ] Integrate with search pipeline

### Phase 4: LLM Fine-Tuning (RAFT)

- [ ] Create `ragd train llm` command
- [ ] Implement platform detection (MLX vs CUDA)
- [ ] Add MLX backend for Apple Silicon
- [ ] Add Unsloth backend for CUDA
- [ ] Support RAFT-style training with distractors
- [ ] LoRA adapter management

### Phase 5: Evaluation and Integration

- [ ] Create `ragd train evaluate` command
- [ ] Implement A/B model comparison
- [ ] Add RAGAS-based evaluation (depends on F-013)
- [ ] Configuration for custom model paths
- [ ] CLI for model management (list, delete, export)

## Success Criteria

- [ ] Users can fine-tune embeddings with a single command
- [ ] Synthetic data generation works with existing Ollama setup
- [ ] Training completes on consumer hardware (8GB+ memory)
- [ ] Fine-tuned models integrate seamlessly via configuration
- [ ] A/B evaluation shows measurable improvement
- [ ] Documentation covers full workflow

## Dependencies

- F-004: Embedding Generation (existing embedder protocol)
- F-012: Hybrid Search (index for hard negative mining)
- F-020: Ollama LLM Integration (for data generation)
- F-013: RAGAS Evaluation (for model evaluation)
- Ollama (external, for synthetic data generation)

## Technical Notes

### Configuration

```yaml
# ~/.ragd/config.yaml
training:
  # Data generation
  queries_per_chunk: 2
  hard_negatives_per_query: 5
  quality_filter: true

  # Embedding training
  embedding_epochs: 3
  embedding_batch_size: 32
  embedding_learning_rate: 2e-5
  matryoshka_dims: [768, 512, 256, 128]

  # LLM training (RAFT)
  llm_backend: auto  # auto, mlx, unsloth
  lora_rank: 16
  lora_alpha: 32
  training_epochs: 3

embedding:
  # Use fine-tuned model
  model: custom
  custom_model_path: ~/.ragd/models/finetuned-embeddings
```

### Data Generation Output

```json
{
  "query": "What authentication methods are supported?",
  "positive": "The system supports OAuth 2.0, SAML, and API key authentication...",
  "positive_id": "chunk_abc123",
  "negatives": [
    {"id": "chunk_def456", "text": "Database connections use TLS 1.3..."},
    {"id": "chunk_ghi789", "text": "The API rate limit is 1000 requests per hour..."}
  ],
  "source_document": "security-guide.pdf"
}
```

### CLI Commands

```bash
# Generate training data from indexed documents
ragd train generate-data \
    --output ./training_data.json \
    --queries-per-chunk 2 \
    --negatives 5

# Fine-tune embedding model
ragd train embeddings \
    --data ./training_data.json \
    --base-model BAAI/bge-small-en-v1.5 \
    --output ~/.ragd/models/my-domain-embeddings \
    --epochs 3

# Fine-tune reranker
ragd train reranker \
    --data ./training_data.json \
    --output ~/.ragd/models/my-domain-reranker

# Fine-tune LLM with RAFT
ragd train llm \
    --data ./raft_training_data.json \
    --base-model llama3.2:3b \
    --output ~/.ragd/models/my-domain-llm \
    --backend auto

# Evaluate fine-tuned model
ragd train evaluate \
    --model ~/.ragd/models/my-domain-embeddings \
    --test-data ./test_data.json \
    --compare-to BAAI/bge-small-en-v1.5

# List trained models
ragd train list

# Use fine-tuned model
ragd config set embedding.custom_model_path ~/.ragd/models/my-domain-embeddings
```

### Model Storage

```
~/.ragd/
├── models/
│   ├── my-domain-embeddings/
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   └── training_metadata.json
│   ├── my-domain-reranker/
│   │   └── ...
│   └── my-domain-llm/
│       ├── adapters.safetensors  # LoRA weights only
│       └── training_metadata.json
└── training_data/
    ├── generated_queries.json
    └── hard_negatives.json
```

### Integration with Embedder Protocol

```python
# src/ragd/embedding/finetuned.py
from ragd.embedding.embedder import Embedder

class FineTunedEmbedder:
    """Embedder for user fine-tuned models."""

    def __init__(self, model_path: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_path)
        self._model_path = model_path

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return f"finetuned:{self._model_path}"
```

## Related Documentation

- [State-of-the-Art Fine-Tuning](../../research/state-of-the-art-fine-tuning.md) - Research basis
- [State-of-the-Art Embeddings](../../research/state-of-the-art-embeddings.md) - Model selection
- [ADR-0027: Fine-Tuning Strategy](../../decisions/adrs/0027-fine-tuning-strategy.md) - Architecture decision
- [F-013: RAGAS Evaluation](../completed/F-013-ragas-evaluation.md) - Evaluation framework
- [F-020: Ollama LLM Integration](../completed/F-020-ollama-llm-integration.md) - LLM for data generation

---
