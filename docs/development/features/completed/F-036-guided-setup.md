# F-036: Guided Setup

## Overview

**Use Case**: First-run experience and configuration
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

New users face friction during initial setup: choosing embedding models, configuring Ollama, understanding hardware capabilities. Without guided setup, users must read documentation and manually edit configuration files, leading to suboptimal configurations or abandonment.

## Design Approach

Implement a `ragd init` command that guides users through initial configuration with sensible defaults based on detected hardware.

**Command Interface:**

```bash
ragd init                # Interactive guided setup
ragd init --defaults     # Accept all defaults (non-interactive)
ragd init --force        # Reconfigure even if already initialised
```

**Interactive Flow:**

```
ragd init

Welcome to ragd! Let's set up your private document assistant.

Hardware Detection
───────────────────────────────────────────────────────

Detected: Apple Silicon (M3 Max) with 128 GB unified memory
Hardware tier: EXTREME

This system can run large language models (70B+) and store
millions of documents in memory.

Configuration
───────────────────────────────────────────────────────

? Where should ragd store data? (~/.ragd)
  > ~/.ragd
  > Custom location...

? Which LLM would you like to use?
  > qwen2.5:72b (recommended for your hardware)
    llama3.1:8b (faster, lower quality)
    Custom...

? Download recommended models now? (Y/n)
  Downloading nomic-embed-text... ✓
  Downloading qwen2.5:72b... ━━━━━━━━━━ 45% (23.4 GB / 52.1 GB)

Setup Complete!
───────────────────────────────────────────────────────

Configuration saved to ~/.ragd/config.yaml

Next steps:
  ragd index ~/Documents    Index your documents
  ragd search "query"       Search indexed content
  ragd doctor               Verify installation

```

## Implementation Tasks

- [ ] Create `ragd init` command in CLI
- [ ] Implement hardware detection and tier display
- [ ] Implement data directory selection
- [ ] Implement model recommendation based on hardware tier
- [ ] Implement interactive model selection
- [ ] Implement model download with progress
- [ ] Generate configuration file
- [ ] Add `--defaults` flag for non-interactive setup
- [ ] Add `--force` flag to reconfigure
- [ ] Display next steps after completion

## Success Criteria

- [ ] First-time setup completes in <5 minutes (excluding downloads)
- [ ] Hardware tier correctly influences recommendations
- [ ] Configuration file generated and valid
- [ ] Model downloads show progress
- [ ] Non-interactive mode works for CI/scripting

## Dependencies

- [F-035: Health Check](./F-035-health-check.md) - Hardware detection logic

## Technical Notes

**Configuration Schema:**

```yaml
# ~/.ragd/config.yaml
version: 1

hardware:
  backend: mps              # mps | cuda | cpu
  tier: extreme             # minimal | standard | high | extreme
  memory_gb: 128

storage:
  data_dir: ~/.ragd
  chroma_db: ~/.ragd/chroma_db

embedding:
  model: nomic-embed-text-v1.5
  device: auto

llm:
  provider: ollama
  model: qwen2.5:72b
  base_url: http://localhost:11434

retrieval:
  top_k: 10
  rerank: true
  rerank_model: bge-reranker-base

cache:
  enabled: true
  max_entries: 100000       # Tier-dependent
  max_memory_gb: 5.0        # Tier-dependent
```

**Model Recommendations by Tier:**

```python
MODEL_RECOMMENDATIONS = {
    HardwareTier.MINIMAL: {
        "llm": "llama3.2:1b",
        "embed": "nomic-embed-text-v1.5",
        "rerank": None,
    },
    HardwareTier.STANDARD: {
        "llm": "llama3.2:3b",
        "embed": "nomic-embed-text-v1.5",
        "rerank": None,
    },
    HardwareTier.HIGH: {
        "llm": "llama3.1:8b",
        "embed": "nomic-embed-text-v1.5",
        "rerank": "bge-reranker-base",
    },
    HardwareTier.EXTREME: {
        "llm": "qwen2.5:72b",
        "embed": "nomic-embed-text-v1.5",
        "rerank": "bge-reranker-base",
    },
}
```

**Non-Interactive Setup:**

```bash
# For CI/scripting
ragd init --defaults

# Output:
# Using detected hardware: Apple Silicon (128 GB)
# Configuration saved to ~/.ragd/config.yaml
# Run 'ragd doctor' to verify setup
```

## Related Documentation

- [State-of-the-Art Setup UX](../../research/state-of-the-art-setup-ux.md)
- [State-of-the-Art Apple Silicon](../../research/state-of-the-art-apple-silicon.md)
- [F-035: Health Check](./F-035-health-check.md)

---

**Status**: Planned
