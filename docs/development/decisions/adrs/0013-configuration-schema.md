# ADR-0013: Configuration Schema and Management

## Status

Accepted

## Context

ragd requires configuration for:
- Hardware detection results (backend, tier, memory)
- Storage paths (data directory, vector database)
- Model selection (embedding, LLM, reranker)
- Feature settings (watch folders, cache sizes)
- User preferences (output format, verbosity)

Without a clear configuration strategy:
- Settings scattered across environment variables, files, and CLI flags
- No persistence between sessions
- Difficult to share/replicate configurations
- Complex precedence rules

## Decision

Use a **single authoritative YAML configuration file** at `~/.ragd/config.yaml` with **schema versioning** for future migrations.

### Configuration Schema (v1)

```yaml
# ~/.ragd/config.yaml
version: 1

# Hardware detection (set by ragd init, can override)
hardware:
  backend: mps              # mps | cuda | cpu
  tier: extreme             # minimal | standard | high | extreme
  memory_gb: 128
  detected_at: 2025-01-15T10:30:00Z

# Storage paths
storage:
  data_dir: ~/.ragd
  chroma_db: ~/.ragd/chroma_db
  reader_views: ~/.ragd/reader_views

# Embedding model
embedding:
  model: nomic-embed-text-v1.5
  device: auto              # auto | cpu | mps | cuda

# LLM configuration
llm:
  provider: ollama
  model: qwen2.5:72b
  base_url: http://localhost:11434

# Retrieval settings
retrieval:
  top_k: 10
  rerank: true
  rerank_model: bge-reranker-base

# Cache settings (scaled by tier)
cache:
  enabled: true
  max_entries: 100000
  max_memory_gb: 5.0

# Watch folder daemon
watch:
  enabled: false
  directories: []
  patterns:
    - "*.pdf"
    - "*.md"
    - "*.txt"
    - "*.docx"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"
  debounce_seconds: 5
  max_file_size_mb: 100
```

### Configuration Precedence

1. **CLI flags** (highest) - Override for single command
2. **Environment variables** - `RAGD_*` prefix
3. **Config file** - `~/.ragd/config.yaml`
4. **Tier defaults** - Based on detected hardware
5. **Built-in defaults** (lowest)

### Environment Variable Mapping

```bash
RAGD_LLM_MODEL=llama3.1:8b          # llm.model
RAGD_RETRIEVAL_TOP_K=20             # retrieval.top_k
RAGD_CACHE_ENABLED=false            # cache.enabled
RAGD_STORAGE_DATA_DIR=/custom/path  # storage.data_dir
```

### Configuration Commands

```bash
# View current configuration
ragd config show

# Get specific value
ragd config get llm.model

# Set value (updates config file)
ragd config set llm.model llama3.1:8b

# Reset to tier defaults
ragd config reset

# Validate configuration
ragd config validate
```

### Schema Versioning

The `version` field enables future migrations:

```python
def migrate_config(config: dict) -> dict:
    """Migrate config to current schema version."""
    version = config.get("version", 0)

    if version < 1:
        # v0 -> v1: Add hardware section
        config["hardware"] = detect_hardware()
        config["version"] = 1

    if version < 2:
        # v1 -> v2: Future migration
        pass

    return config
```

### Pydantic Validation

```python
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum

class HardwareTier(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    EXTREME = "extreme"

class HardwareConfig(BaseModel):
    backend: str = "cpu"
    tier: HardwareTier = HardwareTier.STANDARD
    memory_gb: float = 16.0

class StorageConfig(BaseModel):
    data_dir: Path = Path("~/.ragd").expanduser()
    chroma_db: Path = Path("~/.ragd/chroma_db").expanduser()

class RagdConfig(BaseModel):
    version: int = 1
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    # ... additional sections
```

## Consequences

### Positive

- Single source of truth for all settings
- Human-readable and editable format (YAML)
- Versioned schema enables safe migrations
- CLI tools for configuration management
- Environment variable overrides for CI/containers
- Pydantic validation catches errors early

### Negative

- YAML parsing adds startup overhead (~10ms)
- Users may edit config incorrectly
- Schema migrations require careful handling
- Config file permissions need consideration

## Alternatives Considered

### Multiple Config Files

- **Pros:** Separation of concerns, smaller files
- **Cons:** Fragmentation, unclear precedence
- **Rejected:** Single file simpler for personal tool

### TOML Format

- **Pros:** Python standard (pyproject.toml), less ambiguous than YAML
- **Cons:** Less readable for nested structures, less familiar to users
- **Rejected:** YAML more common for application config

### Environment Variables Only

- **Pros:** Container-friendly, no file management
- **Cons:** Not persistent, verbose, hard to view all settings
- **Rejected:** Poor UX for desktop application

### JSON Format

- **Pros:** Standard, strict parsing
- **Cons:** No comments, verbose, less readable
- **Rejected:** Comments important for user-edited config

### SQLite Settings Store

- **Pros:** Queryable, atomic updates
- **Cons:** Not human-editable, overkill for config
- **Rejected:** Adds complexity without benefit

## Related Documentation

- [F-035: Health Check Command](../../features/planned/F-035-health-check.md)
- [F-036: Guided Setup](../../features/planned/F-036-guided-setup.md)
- [F-037: Watch Folder](../../features/planned/F-037-watch-folder.md)
- [ADR-0011: Hardware Detection](./0011-hardware-detection.md)
