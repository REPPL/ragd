# F-074: Model Recommendation System

## Overview

**Milestone**: v0.6.0
**Priority**: P2
**Depends On**: [F-055](../completed/F-055-multi-model-orchestration.md)

## Problem Statement

Users don't know which Ollama models to use for different tasks (chat, contextual retrieval, embedding). ragd should recommend models based on task requirements and available hardware, and allow downloading models directly via CLI.

## Design Approach

### CLI Commands

```bash
ragd models list                     # Current: list installed
ragd models recommend --task chat    # NEW: suggest models
ragd models pull llama3.2:7b         # NEW: download with progress
ragd models info llama3.2:7b         # NEW: show model details
ragd models set-default llama3.2:7b  # NEW: set default
ragd models status                   # NEW: health/availability
```

### Model Cards Database

One YAML file per model for maintainability:

```
src/ragd/llm/model_cards/
├── __init__.py           # Card loader + merge logic
├── llama3.2-3b.yaml
├── llama3.3-70b.yaml
├── qwen2.5-7b.yaml
├── mistral-7b.yaml
├── nomic-embed-text.yaml
└── fallback_chains.yaml  # Task → model priority lists
```

### Model Card Schema

```yaml
name: llama3.2:3b
family: llama
model_type: chat  # chat | embedding | code | vision
quality_tier: good  # excellent | good | basic
speed_tier: fast    # fast | medium | slow
memory_required_gb: 4
gpu_recommended: false
context_window: 8192

strengths:
  - "fast inference"
  - "low memory footprint"

weaknesses:
  - "none significant for size class"

limitations:
  - "complex multi-step reasoning"
  - "very long documents (>4K tokens)"

recommended_tasks:
  - contextual_retrieval
  - metadata_extraction
  - simple_qa
```

### Fallback Chains

```yaml
# fallback_chains.yaml
# Filtered to INSTALLED models at runtime

chat:
  - llama3.3:70b-instruct-q4_K_M
  - qwen2.5:7b
  - llama3.2:3b
  - mistral:7b

contextual_retrieval:
  - llama3.2:3b
  - mistral:7b
  - qwen2.5:7b

embedding:
  - nomic-embed-text
  - all-MiniLM-L6-v2  # Built-in fallback
```

### Recommendation Output

```
ragd models recommend --task chat

Recommended models for chat (based on your hardware):
─────────────────────────────────────────────────────
  ✓ qwen2.5:7b        (installed, excellent, 8GB)
  ↓ llama3.2:3b       (installed, good, 4GB) - faster fallback
  ⬇ llama3.3:70b      (not installed, excellent, 48GB)
                      Run: ragd models pull llama3.3:70b

Your hardware: 32GB RAM, Apple M2 Pro
```

### Pull with Progress

```
ragd models pull llama3.3:70b

Pulling llama3.3:70b...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━ 82% (38.2/46.5 GB)
```

## Implementation Tasks

- [ ] Create `src/ragd/llm/model_cards/` directory
- [ ] Create ~10 model card YAML files
- [ ] Create `fallback_chains.yaml`
- [ ] Create `ModelRecommender` class
- [ ] Implement hardware detection (RAM, GPU)
- [ ] Add `pull_model_stream()` to OllamaClient
- [ ] Add `ragd models pull` with Rich progress
- [ ] Add `ragd models recommend` command
- [ ] Add `ragd models info` command
- [ ] Add `ragd models set-default` command
- [ ] Add `ragd models status` command
- [ ] Integrate fallback into ModelRouter
- [ ] Enhance `ragd init` with recommendations
- [ ] Write unit tests

## Success Criteria

- [ ] Model cards bundled with ragd
- [ ] User can override with ~/.config/ragd/model_cards/
- [ ] Fallback chains filter to installed models
- [ ] Pull command shows streaming progress
- [ ] Recommendations hardware-aware
- [ ] `ragd init` suggests optimal models

## Related Documentation

- [F-055: Multi-Model Orchestration](../completed/F-055-multi-model-orchestration.md)
- [F-020: Ollama LLM Integration](../completed/F-020-ollama-llm-integration.md)

---
