# F-055: Multi-Model Orchestration

## Overview

**Research**: [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md)
**ADR**: [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md)
**Milestone**: v0.5
**Priority**: P2

## Problem Statement

Running a single large model for all generation tasks is inefficient. Simple queries don't need 8B+ models, and resource-constrained environments may need smaller models. Users need the ability to:

1. Configure different models for different tasks
2. Override model selection per-query
3. See available and loaded models
4. Handle graceful degradation when preferred models are unavailable

## Design Approach

### Architecture

```
Configuration (config.yaml)
    |
    v
+------------------------------------------+
| ModelRegistry                             |
|   - List available models (Ollama)        |
|   - Track loaded models                   |
|   - Validate model availability           |
+------------------------------------------+
    |
    v
+------------------------------------------+
| ModelRouter                               |
|   - Route by task type                    |
|   - Apply manual overrides                |
|   - Fallback handling                     |
+------------------------------------------+
    |
    v
+------------------------------------------+
| OllamaClient (existing)                   |
|   - Generate with selected model          |
|   - On-demand model loading               |
+------------------------------------------+
```

### Configuration Schema

```yaml
# ~/.ragd/config.yaml

models:
  # Generation models
  generation:
    default: llama3.2:3b        # Used for all tasks if routing disabled
    complex: llama3.1:8b        # Optional: for complex queries
    fallback: null              # What to use if primary unavailable

  # Embedding (existing, for reference)
  embedding:
    model: all-MiniLM-L6-v2
    dimension: 384

  # Optional reranking
  reranking:
    enabled: false
    model: bge-reranker-base

# Routing configuration
routing:
  enabled: false                # Single model by default
  strategy: manual              # manual | task_type (future: complexity)

# Ollama settings
ollama:
  base_url: http://localhost:11434
  timeout_seconds: 60
  max_loaded_models: 3          # Maps to OLLAMA_MAX_LOADED_MODELS
  keep_alive: 5m                # Maps to OLLAMA_KEEP_ALIVE
```

### CLI Commands

```bash
# Model management
ragd config models list               # Show available/loaded models
ragd config models set default llama3.1:8b
ragd config models pull llama3.2:3b   # Download via Ollama

# Per-query model override
ragd ask "question" --model llama3.2:3b

# Check model status
ragd status                           # Shows loaded models in status
```

## Implementation Tasks

- [ ] Create ModelRegistry class for tracking available models
- [ ] Create ModelRouter class for task-based routing
- [ ] Extend LLMConfig with multi-model configuration
- [ ] Add `--model` flag to `ragd ask` command
- [ ] Implement `ragd config models list` command
- [ ] Implement `ragd config models set` command
- [ ] Add model status to `ragd status` output
- [ ] Implement fallback logic when model unavailable
- [ ] Add health checks for model availability
- [ ] Write unit tests for ModelRouter
- [ ] Write integration tests for multi-model config
- [ ] Update configuration documentation

## Success Criteria

- [ ] Users can configure different default models
- [ ] Per-query model override works via `--model` flag
- [ ] Model availability is checked before generation
- [ ] Graceful fallback when model unavailable
- [ ] Model status visible in `ragd status`
- [ ] Configuration validated on startup
- [ ] Documentation updated

## Dependencies

- F-020: Ollama LLM Integration (must be complete)
- Ollama installed with desired models

## Technical Notes

### ModelRegistry Implementation

```python
from dataclasses import dataclass

@dataclass
class ModelInfo:
    name: str
    size_gb: float
    quantisation: str | None
    loaded: bool
    last_used: datetime | None

class ModelRegistry:
    """Track and manage available models."""

    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        self._cache: dict[str, ModelInfo] = {}

    async def list_available(self) -> list[ModelInfo]:
        """List all models available in Ollama."""
        models = await self.ollama.list_models()
        return [self._parse_model_info(m) for m in models]

    async def list_loaded(self) -> list[ModelInfo]:
        """List currently loaded models."""
        # Uses ollama ps
        pass

    async def is_available(self, model: str) -> bool:
        """Check if model is available (downloaded)."""
        available = await self.list_available()
        return any(m.name == model for m in available)
```

### ModelRouter Implementation

```python
class ModelRouter:
    """Route requests to appropriate models."""

    def __init__(self, config: ModelsConfig, registry: ModelRegistry):
        self.config = config
        self.registry = registry

    async def get_model(
        self,
        task: str = "default",
        override: str | None = None
    ) -> str:
        """Get model for task, with optional override."""

        # Manual override takes precedence
        if override:
            if await self.registry.is_available(override):
                return override
            raise ModelNotAvailableError(override)

        # Task-specific model if routing enabled
        if self.config.routing.enabled:
            model = self._get_model_for_task(task)
        else:
            model = self.config.generation.default

        # Check availability, fall back if needed
        if not await self.registry.is_available(model):
            if self.config.generation.fallback:
                return self.config.generation.fallback
            raise ModelNotAvailableError(model)

        return model
```

### CLI Output Examples

```bash
$ ragd config models list

Available Models (Ollama)
-------------------------
llama3.2:3b          2.0 GB   Q4_K_M   loaded
llama3.1:8b          4.7 GB   Q4_K_M   -
qwen2.5:3b           1.9 GB   Q4_K_M   -

Configuration
-------------
Default:   llama3.2:3b
Complex:   llama3.1:8b (not loaded)
Fallback:  (none)
Routing:   disabled


$ ragd ask "What is RAG?" --model qwen2.5:3b

Loading model: qwen2.5:3b...

RAG (Retrieval-Augmented Generation) is a technique that...

[Model: qwen2.5:3b | Time: 1.2s | Tokens: 156]
```

## Related Documentation

- [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md) - Research basis
- [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md) - Decision
- [F-020: Ollama LLM Integration](./F-020-ollama-llm-integration.md) - Foundation feature
- [F-056: Specialised Task Models](../planned/F-056-specialised-task-models.md) - SLIM models
- [F-057: Model Comparison](./F-057-model-comparison.md) - Comparison mode

---
