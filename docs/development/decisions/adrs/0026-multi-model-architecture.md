# ADR-0026: Multi-Model Architecture

## Status

Accepted

## Context

ragd currently uses a single LLM (via Ollama) for all generation tasks. Research shows significant benefits from task-specific model assignment:

- **85% cost reduction** with complexity-based routing (RouteLLM)
- **2-5x faster inference** using SLMs for simple queries
- **Better accuracy** for structured tasks using fine-tuned models (SLIM)
- **Resource efficiency** from loading multiple smaller models vs one large model

The key question: How should ragd support multiple models without adding unnecessary complexity?

### Use Cases

1. **Simple queries** (e.g., "What is X?") don't need 8B+ models
2. **Structured extraction** (NER, classification) benefits from specialised models
3. **Model comparison** helps users evaluate different models for their use case
4. **Hardware constraints** may require smaller models on some machines

## Decision

Implement **configurable task-to-model mapping** with sensible single-model defaults.

### Architecture

```
Configuration
    |
    v
+------------------------------------------+
| Model Registry                            |
|   - Available models (from Ollama)        |
|   - Task assignments                      |
|   - Health status                         |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Model Router                              |
|   - Default: single model for all        |
|   - Optional: task-based routing         |
|   - Optional: complexity routing         |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Ollama Client (existing)                  |
|   - Multi-model via OLLAMA_MAX_LOADED    |
|   - On-demand model loading              |
+------------------------------------------+
```

### Configuration Schema

```yaml
# ~/.ragd/config.yaml

models:
  generation:
    default: llama3.2:3b        # Used for all tasks by default
    complex: llama3.1:8b        # Optional: for complex queries
  embedding: all-MiniLM-L6-v2   # Fixed embedding model
  reranking: null               # Optional reranker

routing:
  enabled: false                # Single model by default
  strategy: manual              # manual | complexity | task_type
```

### Options Considered

#### Option 1: Single Model (Current Default)

- One generation model for all tasks
- Simplest configuration
- No routing overhead
- Limited optimisation potential

**Chosen as default** for simplicity.

#### Option 2: Configurable Task-Model Mapping (Recommended)

- User configures which model for which task
- Explicit control
- No magic routing
- Backward compatible

**Chosen as the implementation approach.**

#### Option 3: Automatic Complexity Routing

- Classifier determines query complexity
- Routes to appropriate model automatically
- Requires training/tuning
- More complex to implement

**Deferred to future release.**

## Consequences

### Positive

- Users can optimise for their hardware and use case
- Backward compatible (single model default)
- Explicit configuration avoids magic
- Foundation for future automatic routing
- Enables specialised models for extraction tasks

### Negative

- Additional configuration complexity (optional)
- Multiple models require more VRAM
- Model switching adds ~100ms latency
- Users must understand model trade-offs

### Migration

No migration required. Existing single-model configurations continue to work. Multi-model features are opt-in.

## Implementation Strategy

| Phase | Milestone | Features |
|-------|-----------|----------|
| 1 | v0.5 (F-020) | Single model generation, model selection |
| 2 | v0.5 (F-055) | Multi-model config, manual routing, CLI model override |
| 3 | v1.0 (F-056) | Specialised task models (NER, classification) |
| 4 | v1.0+ (F-057) | Model comparison mode, judge evaluation |
| 5 | Future | Automatic complexity routing |

## Related Documentation

- [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md)
- [State-of-the-Art Local RAG](../../research/state-of-the-art-local-rag.md)
- [F-020: Ollama LLM Integration](../../features/completed/F-020-ollama-llm-integration.md)
- [F-055: Multi-Model Orchestration](../../features/completed/F-055-multi-model-orchestration.md)
- [F-056: Specialised Task Models](../../features/planned/F-056-specialised-task-models.md)
- [F-057: Model Comparison](../../features/planned/F-057-model-comparison.md)

---
