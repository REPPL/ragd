# State-of-the-Art Configuration Management for RAG/ML Applications

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

## Executive Summary

This research surveys configuration management patterns for RAG and ML applications in 2024-2025, providing recommendations for ragd's configuration architecture defined in ADR-0013.

### Key Recommendations

1. **Default Embedding Model**: Use `BAAI/bge-base-en-v1.5` (768 dimensions) for general-purpose RAG
   - Superior accuracy (84.7%) with reasonable speed (79-82ms latency)
   - Strong performance across diverse domains (legal, scientific, business)
   - Requires query prefix: "Represent this sentence for searching relevant passages:"

2. **Optimal Chunking Defaults**: 400-512 tokens with 10-20% overlap
   - Start with `RecursiveCharacterTextSplitter` at 400 tokens with 15% overlap
   - Consider semantic chunking for production if metrics justify cost/complexity
   - Page-level chunking shows best consistency (0.648 accuracy, lowest variance)

3. **Configuration Location**: Follow XDG Base Directory Specification
   - Config: `$XDG_CONFIG_HOME/ragd/config.yaml` (default: `~/.config/ragd/config.yaml`)
   - Data: `$XDG_DATA_HOME/ragd/` (default: `~/.local/share/ragd/`)
   - Cache: `$XDG_CACHE_HOME/ragd/` (default: `~/.cache/ragd/`)
   - State: `$XDG_STATE_HOME/ragd/` (default: `~/.local/state/ragd/`)

4. **Configuration Precedence**: CLI flags > Environment variables > Config file > Defaults
   - Use `RAGD_*` prefix for environment variables
   - Support nested config via `RAGD_SECTION__SUBSECTION__KEY` pattern
   - Implement `env_nested_delimiter="__"` in Pydantic BaseSettings

5. **Schema Versioning**: Include explicit `version` field with migration strategy
   - Use idempotent migrations that check existing state
   - Track migrations in dedicated version table
   - Validate after each migration step

## RAG Framework Configuration Patterns

### Framework Comparison (2024-2025 Benchmarks)

A comprehensive benchmark tested LangChain, LangGraph, LlamaIndex, Haystack, and DSPy using identical components (GPT-4.1-mini, BGE-small embeddings, Qdrant retriever) across 100 queries × 100 runs.

| Framework | Overhead (ms) | Token Usage | Configuration Approach |
|-----------|--------------|-------------|----------------------|
| DSPy | 3.53 | ~2,030 | Declarative signatures + Python driver |
| Haystack | 5.9 | ~1,570 | Typed components with @component decorator |
| LlamaIndex | 6.0 | ~1,600 | Procedural with high-level API |
| LangChain | 10.0 | ~2,400 | Imperative with composable chains |
| LangGraph | 14.0 | ~2,030 | State graphs with declarative flow |

**Key Finding**: Haystack and LlamaIndex offer the best balance of low overhead and token efficiency for production RAG systems.

### LangChain Configuration Pattern

```python
# Composable chains with | operator
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama
from langchain.output_parsers import StrOutputParser

# State as flexible dict
chain = prompt | llm | parser

# Configuration via constructor params
llm = Ollama(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0.7
)
```

**Strengths**:
- Large ecosystem with many integrations
- Rapid prototyping with composable components
- Flexible for complex multi-step workflows

**Weaknesses**:
- Highest framework overhead (10ms)
- Most token usage (2.4k)
- Configuration scattered across components

### LlamaIndex Configuration Pattern

```python
# High-level API with sensible defaults
from llama_index import VectorStoreIndex, SimpleDirectoryReader

# Config via Settings singleton
from llama_index import Settings

Settings.llm = Ollama(model="llama3.1:8b")
Settings.embed_model = "local:BAAI/bge-base-en-v1.5"
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Then use throughout application
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
```

**Strengths**:
- Gentle learning curve
- Global Settings object for consistency
- Strong data ingestion and indexing
- Low framework overhead (6ms)

**Weaknesses**:
- Global state can cause issues in concurrent scenarios
- Less explicit than component-based approaches

### Haystack Configuration Pattern

```python
# Typed components with explicit I/O
from haystack import component, Pipeline

@component
class MyRetriever:
    @component.output_types(documents=List[Document])
    def run(self, query: str) -> Dict[str, List[Document]]:
        return {"documents": [...]}

# Build pipeline with clear data flow
pipeline = Pipeline()
pipeline.add_component("retriever", MyRetriever())
pipeline.add_component("prompt_builder", PromptBuilder(template=template))
pipeline.add_component("llm", OllamaGenerator(model="llama3.1:8b"))

# Connect with explicit contracts
pipeline.connect("retriever.documents", "prompt_builder.documents")
pipeline.connect("prompt_builder", "llm")

# Run with typed inputs
result = pipeline.run({"retriever": {"query": "What is RAG?"}})
```

**Strengths**:
- Lowest token usage (1.57k)
- Explicit, testable components
- Easy to swap implementations
- Production-ready architecture

**Weaknesses**:
- More verbose than LlamaIndex
- Steeper learning curve

### Framework Selection Guide

| Use Case | Recommended Framework | Rationale |
|----------|---------------------|-----------|
| Production RAG pipeline | **Haystack** | Lowest tokens, explicit components, testable |
| Data-heavy Q&A | **LlamaIndex** | Best indexing, simple API, good performance |
| Complex agent workflows | LangChain/LangGraph | Mature ecosystem for multi-step reasoning |
| Research/experimentation | DSPy | Lowest overhead, optimizer-driven approach |

## Embedding Model Recommendations

### Top General-Purpose Models (2024-2025)

Based on MTEB leaderboard and practical benchmarks:

| Model | Dimensions | Speed | Accuracy | Best For |
|-------|-----------|-------|----------|----------|
| **BAAI/bge-base-en-v1.5** | 768 | 79-82ms | 84.7% | **General-purpose RAG (recommended)** |
| intfloat/e5-base-v2 | 768 | ~75ms | 83-85% | Simple integration (no prefix) |
| all-MiniLM-L6-v2 | 384 | 14.7ms | ~80% | High-throughput, latency-critical |
| nomic-embed-text-v1.5 | 768 | ~100ms | 86.2% | Precision-critical (legal, medical) |
| bge-m3 | 1024 | ~90ms | 85%+ | Multilingual, hybrid dense/sparse |

### BGE-Base-en-v1.5: Recommended Default

**Why BGE over alternatives**:
- **Superior accuracy**: 84.7% top-5 accuracy across diverse domains
- **Balanced performance**: 79-82ms latency suitable for interactive use
- **Production-proven**: Consistent reliability in legal, scientific, and business tasks
- **Open source**: Apache 2.0 licence, active development

**Critical requirement**: Must prefix queries with instruction:
```python
query = "Represent this sentence for searching relevant passages: " + user_query
```

**Model card**: `BAAI/bge-base-en-v1.5` on Hugging Face

### E5-Base-v2: Alternative for Simplicity

**When to choose E5**:
- Want simpler integration (no query prefix required)
- Slightly faster embedding time (~75ms vs 79-82ms)
- Similar accuracy (83-85%) acceptable for use case

**Trade-offs**:
- 1-2% lower retrieval accuracy
- Smaller community than BGE
- Less fine-tuning resources

### MiniLM-L6-v2: High-Throughput Alternative

**When to choose MiniLM**:
- Latency is critical (<20ms requirement)
- High request volume (>1000 qps)
- Mobile or resource-constrained deployment
- Accuracy drop (5-8%) acceptable

**Trade-offs**:
- Smaller dimensions (384 vs 768) = less semantic capacity
- Lower accuracy (~80% vs 84.7%)
- Less suitable for precision-critical domains

### Device Configuration

Following Hugging Face Transformers patterns:

```python
from sentence_transformers import SentenceTransformer

# Auto-detect best device
model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5",
    device="auto"  # Selects: MPS > CUDA > CPU
)

# Or explicit device
model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5",
    device="mps"  # Options: cpu, cuda, mps, cuda:0
)

# Normalize embeddings (critical for BGE/E5)
embeddings = model.encode(
    texts,
    normalize_embeddings=True  # Required for cosine similarity
)
```

**Configuration recommendation for ragd**:
```yaml
embedding:
  model: BAAI/bge-base-en-v1.5
  device: auto              # mps | cuda | cpu | auto
  normalize: true           # Required for BGE/E5 models
  batch_size: 32           # Scale by hardware tier
  query_prefix: "Represent this sentence for searching relevant passages: "
```

## Chunking Strategy Defaults

### Optimal Chunk Size Research (2024)

Multiple benchmarks converge on **400-512 tokens with 10-20% overlap** as optimal starting point:

| Study | Recommended Size | Overlap | Strategy |
|-------|-----------------|---------|----------|
| NVIDIA 2024 | Page-level (variable) | N/A | 0.648 accuracy, lowest variance |
| Chroma Research | 400 tokens | 15-20% | 88.1-89.5% recall |
| Unstructured.io | 256-512 tokens | 10-20% | Use case dependent |
| LlamaIndex Evaluation | 512 tokens | 20% | Balanced context/precision |

### Strategy Selection by Content Type

| Content Type | Chunk Size | Strategy | Rationale |
|-------------|-----------|----------|-----------|
| Technical docs | 400-500 tokens | Page-level or semantic | Preserve complete API examples |
| General text | 256-512 tokens | RecursiveCharacterTextSplitter | Balance context and retrieval |
| Conversational | 128-256 tokens | Smaller chunks | Dense with keywords |
| Legal/medical | 512+ tokens | Larger chunks | Context critical for accuracy |

### RecursiveCharacterTextSplitter: Default Recommendation

**Why this strategy**:
- **Works well out-of-box**: 88.1-89.5% recall at 400 tokens in Chroma benchmarks
- **Predictable behaviour**: Splits on `\n\n`, then `\n`, then ` `, then character
- **Handles varied content**: Adapts to document structure naturally
- **Framework support**: Available in LangChain, LlamaIndex, Haystack

**Implementation**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,           # Target size in tokens
    chunk_overlap=60,         # 15% overlap (400 * 0.15)
    length_function=len,      # Or tiktoken for token-accurate
    separators=["\n\n", "\n", " ", ""],
    is_separator_regex=False
)

chunks = splitter.split_text(text)
```

### Semantic Chunking: Production Upgrade

**When to upgrade** from RecursiveCharacterTextSplitter:
- Metrics show poor retrieval (hit rate <80%)
- Content has complex semantic structure
- Budget allows for embedding-based chunking cost

**Performance**: LLMSemanticChunker achieved 0.919 recall (vs 0.885 for recursive)

**Trade-offs**:
- Requires embeddings for chunking = slower ingestion
- Variable chunk sizes = harder to predict storage
- More complex to debug

**Recommendation**: Start with RecursiveCharacterTextSplitter, upgrade only if metrics justify.

### Configuration Recommendation

```yaml
chunking:
  strategy: recursive          # recursive | semantic | page_level
  target_size: 400            # tokens
  overlap_percent: 15         # 15% = 60 tokens
  min_chunk_size: 100         # Avoid tiny chunks
  max_chunk_size: 800         # Hard limit

  # Separators for recursive strategy
  separators:
    - "\n\n"                  # Paragraphs first
    - "\n"                    # Then lines
    - ". "                    # Then sentences
    - " "                     # Then words
    - ""                      # Finally chars

  # Semantic chunking (if enabled)
  semantic:
    breakpoint_threshold: 95  # Percentile for splits
    buffer_size: 1           # Sentences to merge
```

## Configuration Location Standards

### XDG Base Directory Specification

Modern CLI tools follow XDG standards for configuration, even on macOS:

| Directory | Purpose | Default | ragd Use |
|-----------|---------|---------|----------|
| `$XDG_CONFIG_HOME` | User configuration | `~/.config` | `config.yaml`, `presets/` |
| `$XDG_DATA_HOME` | User data | `~/.local/share` | Vector DB, document store |
| `$XDG_STATE_HOME` | State/history | `~/.local/state` | Query history, session logs |
| `$XDG_CACHE_HOME` | Cache | `~/.cache` | Embedding cache, temp files |

### Cross-Platform Implementation

```python
from pathlib import Path
import os

def get_config_dir() -> Path:
    """Get config directory following XDG spec."""
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "ragd"
    return Path.home() / ".config" / "ragd"

def get_data_dir() -> Path:
    """Get data directory following XDG spec."""
    xdg_data = os.getenv("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "ragd"
    return Path.home() / ".local" / "share" / "ragd"

def get_cache_dir() -> Path:
    """Get cache directory following XDG spec."""
    xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "ragd"
    return Path.home() / ".cache" / "ragd"

def get_state_dir() -> Path:
    """Get state directory following XDG spec."""
    xdg_state = os.getenv("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state) / "ragd"
    return Path.home() / ".local" / "state" / "ragd"
```

### Directory Structure Recommendation

```
~/.config/ragd/
├── config.yaml              # Main configuration
├── presets/                 # Named presets (legal, academic, etc)
│   ├── legal.yaml
│   └── academic.yaml
└── profiles/                # Hardware profiles
    └── macbook-m2.yaml

~/.local/share/ragd/
├── chroma_db/              # Vector database
├── documents/              # Document metadata DB
└── models/                 # Downloaded model cache

~/.cache/ragd/
├── embeddings/             # Embedding cache
├── chunks/                 # Chunking cache
└── downloads/              # Temporary downloads

~/.local/state/ragd/
├── history.db              # Query history
├── sessions/               # Session logs
└── metrics.db              # Performance metrics
```

### Migration from Legacy Locations

Many users have existing `~/.ragd/` installations. Support graceful migration:

```python
def migrate_legacy_config() -> None:
    """Migrate from ~/.ragd to XDG locations."""
    legacy_dir = Path.home() / ".ragd"
    if not legacy_dir.exists():
        return

    xdg_config = get_config_dir()
    xdg_data = get_data_dir()

    # Migrate config.yaml
    legacy_config = legacy_dir / "config.yaml"
    if legacy_config.exists() and not (xdg_config / "config.yaml").exists():
        xdg_config.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_config, xdg_config / "config.yaml")

    # Migrate vector DB
    legacy_chroma = legacy_dir / "chroma_db"
    if legacy_chroma.exists():
        xdg_data.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy_chroma), str(xdg_data / "chroma_db"))

    # Leave legacy directory with README explaining migration
    (legacy_dir / "MIGRATED.txt").write_text(
        f"Configuration migrated to XDG directories:\n"
        f"Config: {xdg_config}\n"
        f"Data: {xdg_data}\n"
    )
```

## Configuration Precedence and Overrides

### Precedence Order (12-Factor App Principles)

Following 12-factor app methodology adapted for CLI tools:

1. **CLI flags** (highest priority) - Single-command overrides
2. **Environment variables** - Session or deployment overrides
3. **Configuration file** - Persistent user preferences
4. **Tier defaults** - Hardware-appropriate defaults
5. **Built-in defaults** (lowest priority) - Fallback values

### Environment Variable Mapping

**Naming convention**: `RAGD_SECTION__SUBSECTION__KEY`

```bash
# Flat keys
export RAGD_EMBEDDING_MODEL="intfloat/e5-base-v2"
export RAGD_RETRIEVAL_TOP_K=20

# Nested keys (double underscore)
export RAGD_LLM__PROVIDER="ollama"
export RAGD_LLM__MODEL="llama3.1:8b"
export RAGD_LLM__BASE_URL="http://localhost:11434"

# Array values (comma-separated)
export RAGD_WATCH__DIRECTORIES="~/Documents,~/Downloads"
export RAGD_WATCH__PATTERNS="*.pdf,*.md,*.txt"
```

### Pydantic BaseSettings Implementation

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Optional, List

class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    provider: str = "ollama"
    model: str = "llama3.1:8b"
    base_url: str = "http://localhost:11434"
    timeout: int = 60

class EmbeddingConfig(BaseSettings):
    """Embedding model configuration."""
    model: str = "BAAI/bge-base-en-v1.5"
    device: str = "auto"
    normalize: bool = True
    batch_size: int = 32
    query_prefix: str = "Represent this sentence for searching relevant passages: "

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        allowed = {"auto", "cpu", "cuda", "mps"}
        if v not in allowed and not v.startswith("cuda:"):
            raise ValueError(f"device must be one of {allowed} or cuda:N")
        return v

class RagdConfig(BaseSettings):
    """Main ragd configuration."""
    model_config = SettingsConfigDict(
        env_prefix="RAGD_",
        env_nested_delimiter="__",
        case_sensitive=False,
        validate_default=True,
    )

    version: int = 1
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "RagdConfig":
        """Load config from file with env var overrides."""
        if config_path and config_path.exists():
            import yaml
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return cls(**data)
        return cls()  # Uses env vars and defaults
```

**Usage**:
```python
# Load with precedence: env vars > file > defaults
config = RagdConfig.load(Path("~/.config/ragd/config.yaml").expanduser())

# CLI flag override
if args.model:
    config.embedding.model = args.model
```

### Secrets Management

**Never store secrets in config file**. Use environment variables or secret management tools.

> Cloud LLM provider configuration (OpenAI, etc.) is not supported until v2.0+.
> See [Future Cloud Support](../planning/future-cloud-support.md) for planned API key patterns.

## Schema Versioning and Migration

### Version Field Requirement

Every configuration must include explicit version:

```yaml
version: 1  # REQUIRED - enables migrations

# Rest of config...
```

### Migration Strategy

Following database migration best practices adapted for config files:

```python
from typing import Dict, Any, Callable
from pathlib import Path
import yaml

# Migration registry
MIGRATIONS: Dict[int, Callable[[Dict], Dict]] = {}

def migration(from_version: int):
    """Decorator to register migrations."""
    def decorator(func: Callable[[Dict], Dict]) -> Callable:
        MIGRATIONS[from_version] = func
        return func
    return decorator

@migration(from_version=0)
def migrate_v0_to_v1(config: Dict[str, Any]) -> Dict[str, Any]:
    """Add hardware section from legacy environment."""
    config["version"] = 1
    config["hardware"] = {
        "backend": "cpu",
        "tier": "standard",
        "memory_gb": 16.0,
        "detected_at": None,
    }
    return config

@migration(from_version=1)
def migrate_v1_to_v2(config: Dict[str, Any]) -> Dict[str, Any]:
    """Move to XDG directories."""
    config["version"] = 2

    # Update storage paths
    old_data_dir = Path(config["storage"]["data_dir"]).expanduser()
    if str(old_data_dir) == str(Path.home() / ".ragd"):
        # Only migrate if using default legacy path
        xdg_data = Path.home() / ".local" / "share" / "ragd"
        config["storage"]["data_dir"] = str(xdg_data)
        config["storage"]["chroma_db"] = str(xdg_data / "chroma_db")

    return config

def migrate_config(config: Dict[str, Any], target_version: int = 2) -> Dict[str, Any]:
    """Migrate config to target version."""
    current_version = config.get("version", 0)

    if current_version == target_version:
        return config

    if current_version > target_version:
        raise ValueError(
            f"Cannot downgrade from v{current_version} to v{target_version}"
        )

    # Apply migrations sequentially
    for version in range(current_version, target_version):
        migration_func = MIGRATIONS.get(version)
        if not migration_func:
            raise ValueError(f"No migration defined for v{version} -> v{version + 1}")

        logger.info(f"Migrating config from v{version} to v{version + 1}")
        config = migration_func(config)

        # Validate after each migration
        try:
            RagdConfig(**config)
        except Exception as e:
            raise ValueError(f"Migration to v{version + 1} produced invalid config: {e}")

    return config

def load_and_migrate_config(config_path: Path) -> Dict[str, Any]:
    """Load config and migrate to current version."""
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    # Migrate to current version
    config = migrate_config(config, target_version=2)

    # Backup before writing
    backup_path = config_path.with_suffix(".yaml.backup")
    shutil.copy2(config_path, backup_path)

    # Write migrated config
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Config migrated successfully (backup: {backup_path})")
    return config
```

### Idempotent Migrations

Each migration should check state before making changes:

```python
@migration(from_version=2)
def migrate_v2_to_v3(config: Dict[str, Any]) -> Dict[str, Any]:
    """Add query prefix to embedding config."""
    config["version"] = 3

    embedding = config.get("embedding", {})

    # Check if already present (idempotent)
    if "query_prefix" not in embedding:
        model = embedding.get("model", "")
        if "bge" in model.lower():
            embedding["query_prefix"] = "Represent this sentence for searching relevant passages: "
        elif "e5" in model.lower():
            embedding["query_prefix"] = "query: "
        else:
            embedding["query_prefix"] = ""

        config["embedding"] = embedding

    return config
```

### User-Friendly Validation Errors

Pydantic v2 provides excellent error messages, but customise for users:

```python
from pydantic import ValidationError

def load_config_with_friendly_errors(config_path: Path) -> RagdConfig:
    """Load config with user-friendly error messages."""
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)

        return RagdConfig(**data)

    except ValidationError as e:
        # Transform Pydantic errors to user-friendly messages
        friendly_errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            value = error.get("input")

            if error["type"] == "enum":
                allowed = error["ctx"]["expected"]
                friendly_errors.append(
                    f"❌ {field}: '{value}' is not valid. Choose from: {allowed}"
                )
            elif error["type"] == "missing":
                friendly_errors.append(
                    f"❌ {field}: Required field is missing"
                )
            else:
                friendly_errors.append(
                    f"❌ {field}: {msg} (got: {value})"
                )

        error_msg = "\n".join(friendly_errors)
        raise ValueError(
            f"Configuration validation failed:\n\n{error_msg}\n\n"
            f"Config file: {config_path}"
        )

    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML syntax in config file:\n{e}\n\n"
            f"Config file: {config_path}"
        )
```

## ML/AI Configuration Patterns

### Hugging Face Transformers Configuration

Transformers uses a consistent configuration pattern:

```python
from transformers import AutoConfig, AutoModel

# Load config separately
config = AutoConfig.from_pretrained(
    "BAAI/bge-base-en-v1.5",
    revision="main",           # Git branch/tag/commit
    trust_remote_code=False,  # Security: only run trusted code
)

# Inspect config
print(config.hidden_size)          # 768
print(config.num_attention_heads)  # 12

# Load model with config
model = AutoModel.from_pretrained(
    "BAAI/bge-base-en-v1.5",
    config=config,
    device_map="auto",              # Automatic device placement
    torch_dtype="auto",             # Automatic precision selection
)
```

### Model Selection Configuration

```yaml
embedding:
  # Hugging Face model identifier
  model: BAAI/bge-base-en-v1.5

  # Model revision (git branch/tag/commit)
  revision: main

  # Device placement
  device: auto                    # auto | cpu | cuda | mps | cuda:0

  # Memory optimisation
  torch_dtype: auto              # auto | float32 | float16 | bfloat16

  # Trust remote code (security risk)
  trust_remote_code: false

  # Local model cache
  cache_dir: ~/.cache/ragd/models
```

### Device Configuration by Hardware Tier

```python
from enum import Enum

class HardwareTier(str, Enum):
    MINIMAL = "minimal"      # <8GB RAM, CPU only
    STANDARD = "standard"    # 8-16GB RAM, integrated GPU
    HIGH = "high"           # 16-64GB RAM, dedicated GPU
    EXTREME = "extreme"     # 64GB+ RAM, high-end GPU

def get_device_config(tier: HardwareTier) -> dict:
    """Get device config by hardware tier."""
    configs = {
        HardwareTier.MINIMAL: {
            "device": "cpu",
            "batch_size": 8,
            "torch_dtype": "float32",
        },
        HardwareTier.STANDARD: {
            "device": "auto",        # MPS on Mac, CUDA if available
            "batch_size": 16,
            "torch_dtype": "float32",
        },
        HardwareTier.HIGH: {
            "device": "auto",
            "batch_size": 32,
            "torch_dtype": "float16",  # FP16 for speed
        },
        HardwareTier.EXTREME: {
            "device": "auto",
            "batch_size": 64,
            "torch_dtype": "bfloat16",  # BF16 for precision + speed
        },
    }
    return configs[tier]
```

### Cache Configuration

```yaml
cache:
  enabled: true

  # Embedding cache (LRU)
  embeddings:
    max_entries: 100000        # ~768MB for BGE-base (768 dims × 4 bytes × 100k)
    max_memory_gb: 1.0
    ttl_seconds: 86400        # 24 hours

  # Chunk cache (for deduplication)
  chunks:
    max_entries: 50000
    max_memory_gb: 0.5

  # Model cache (Hugging Face downloads)
  models:
    cache_dir: ~/.cache/ragd/models
    max_size_gb: 10.0         # Limit total model storage
```

## Complete Configuration Example

### Recommended Default Configuration

```yaml
# ~/.config/ragd/config.yaml
version: 2

# Hardware detection (auto-populated by ragd init)
hardware:
  backend: mps                 # cpu | cuda | mps
  tier: high                  # minimal | standard | high | extreme
  memory_gb: 64.0
  detected_at: 2025-01-26T10:30:00Z

# Storage paths (XDG-compliant)
storage:
  config_dir: ~/.config/ragd
  data_dir: ~/.local/share/ragd
  cache_dir: ~/.cache/ragd
  state_dir: ~/.local/state/ragd

  # Specific data locations
  chroma_db: ~/.local/share/ragd/chroma_db
  documents: ~/.local/share/ragd/documents
  models: ~/.cache/ragd/models

# Embedding configuration
embedding:
  model: BAAI/bge-base-en-v1.5
  revision: main
  device: auto                 # auto | cpu | cuda | mps
  normalize: true             # Required for cosine similarity
  batch_size: 32              # Scale by hardware tier
  torch_dtype: float16        # float32 | float16 | bfloat16
  trust_remote_code: false    # Security: only trusted models

  # Model-specific settings
  query_prefix: "Represent this sentence for searching relevant passages: "

# LLM configuration
llm:
  provider: ollama
  model: llama3.1:8b
  base_url: http://localhost:11434
  timeout: 60
  temperature: 0.7
  max_tokens: 2048

# Chunking strategy
chunking:
  strategy: recursive          # recursive | semantic | page_level
  target_size: 400            # tokens
  overlap_percent: 15         # 60 tokens overlap
  min_chunk_size: 100
  max_chunk_size: 800

  separators:
    - "\n\n"                  # Paragraphs
    - "\n"                    # Lines
    - ". "                    # Sentences
    - " "                     # Words
    - ""                      # Characters

# Retrieval settings
retrieval:
  top_k: 10                   # Initial retrieval
  rerank: true
  rerank_model: BAAI/bge-reranker-base
  rerank_top_k: 5            # After reranking
  similarity_threshold: 0.7   # Minimum similarity score

# Cache configuration
cache:
  enabled: true

  embeddings:
    max_entries: 100000
    max_memory_gb: 1.0
    ttl_seconds: 86400        # 24 hours

  chunks:
    max_entries: 50000
    max_memory_gb: 0.5

  models:
    cache_dir: ~/.cache/ragd/models
    max_size_gb: 10.0

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
    - "**/.venv/**"
  debounce_seconds: 5
  max_file_size_mb: 100

# Logging configuration
logging:
  level: INFO                 # DEBUG | INFO | WARNING | ERROR
  file: ~/.local/state/ragd/logs/ragd.log
  max_size_mb: 10
  backup_count: 5

# Performance tuning
performance:
  max_workers: 4              # Parallel processing
  prefetch_count: 100        # Documents to prefetch
  connection_pool_size: 10   # DB connections
```

### Hardware-Specific Presets

**Minimal tier** (`~/.config/ragd/presets/minimal.yaml`):
```yaml
hardware:
  tier: minimal
  backend: cpu

embedding:
  model: sentence-transformers/all-MiniLM-L6-v2  # Faster, smaller
  batch_size: 8
  device: cpu
  torch_dtype: float32

chunking:
  target_size: 256           # Smaller chunks for faster processing

retrieval:
  top_k: 5                   # Fewer retrievals
  rerank: false             # Skip reranking for speed

cache:
  embeddings:
    max_entries: 10000      # Smaller cache
    max_memory_gb: 0.1
```

**Extreme tier** (`~/.config/ragd/presets/extreme.yaml`):
```yaml
hardware:
  tier: extreme
  backend: cuda

embedding:
  model: nomic-ai/nomic-embed-text-v1.5  # Most accurate
  batch_size: 64
  device: cuda:0
  torch_dtype: bfloat16

chunking:
  strategy: semantic         # Best quality
  target_size: 512

retrieval:
  top_k: 20                  # More candidates
  rerank: true
  rerank_top_k: 10          # More results

cache:
  embeddings:
    max_entries: 500000     # Large cache
    max_memory_gb: 5.0

performance:
  max_workers: 16           # More parallelism
```

## Related Frameworks and Tools

### Similar Tools' Configuration Approaches

| Tool | Config Location | Format | Key Features |
|------|----------------|--------|--------------|
| **PrivateGPT** | `~/.privategpt/` | YAML | Single file, profiles support |
| **AnythingLLM** | `~/.anythingllm/` | JSON | API-first, UI-driven config |
| **Khoj** | `~/.khoj/` | YAML | Separate model and app config |
| **Ollama** | `~/.ollama/` | N/A | No config file (env vars only) |

### Ollama Configuration Pattern

Ollama uses **environment variables only** for configuration:

```bash
# No config file - all via env vars
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_MODELS="/custom/path/models"
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=3

ollama serve
```

**Lesson**: Environment-only works for services, but desktop apps need file-based config.

### PrivateGPT Configuration Approach

PrivateGPT uses profiles for different scenarios:

```yaml
# ~/.privategpt/config.yaml
profile: default  # Switch profiles easily

profiles:
  default:
    embedding:
      mode: huggingface
      model: BAAI/bge-small-en-v1.5

  high-quality:
    embedding:
      mode: huggingface
      model: BAAI/bge-large-en-v1.5
    llm:
      model: llama3.1:70b

  fast:
    embedding:
      mode: huggingface
      model: all-MiniLM-L6-v2
    llm:
      model: llama3.1:8b
```

**Lesson**: Profiles enable easy switching between quality/speed trade-offs.

## Implementation Recommendations for ragd

### Priority 1: Core Configuration

1. **Use Pydantic BaseSettings** with `env_nested_delimiter="__"`
2. **Support XDG directories** with fallback to `~/.ragd/` for migration
3. **Default to BGE-base-en-v1.5** embedding model
4. **Default to 400 tokens, 15% overlap** for chunking
5. **Implement config commands**: `show`, `get`, `set`, `validate`, `reset`

### Priority 2: Versioning and Migration

1. **Require `version` field** in all configs
2. **Implement idempotent migrations** with validation
3. **Backup before migration** (`.yaml.backup` files)
4. **User-friendly validation errors** with suggestions

### Priority 3: Advanced Features

1. **Hardware-specific presets** (minimal/standard/high/extreme)
2. **Profile system** (legal, academic, code, general)
3. **Configuration validation on startup** with suggestions
4. **Config file watching** for hot-reload in daemon mode

### Priority 4: Security and Secrets

1. **Never store secrets in config files**
2. **Document env var approach** for API keys
3. **Validate file permissions** on sensitive configs
4. **Support secret management tools** (future: Keychain, Vault)

## References

### RAG Frameworks

- [RAG Frameworks: LangChain vs LlamaIndex vs Haystack (2025)](https://research.aimultiple.com/rag-frameworks/)
- [LangChain vs Haystack vs LlamaIndex: RAG Showdown 2025](https://mayur-ds.medium.com/langchain-vs-haystack-vs-llamaindex-rag-showdown-2025-28c222d34b0a)
- [Compare the Top 7 RAG Frameworks in 2025 | Pathway](https://pathway.com/rag-frameworks/)

### Chunking and Embeddings

- [Chunking for RAG: Best Practices | Unstructured](https://unstructured.io/blog/chunking-for-rag-best-practices)
- [What is the optimal chunk size for RAG applications? | Milvus](https://milvus.io/ai-quick-reference/what-is-the-optimal-chunk-size-for-rag-applications)
- [Best Chunking Strategies for RAG in 2025 | Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [Evaluating the Ideal Chunk Size for a RAG System using LlamaIndex](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)

### Embedding Models

- [Best Open Source Sentence Embedding Models in August 2024 | Codesphere](https://codesphere.com/articles/best-open-source-sentence-embedding-models)
- [Best Open-Source Embedding Models Benchmarked and Ranked | Supermemory](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/)
- [5 Best Embedding Models for RAG | Greennode](https://greennode.ai/blog/best-embedding-models-for-rag)
- [Top Embedding Models for RAG | Modal Blog](https://modal.com/blog/embedding-models-article)

### Configuration Standards

- [The Twelve-Factor App: Config](https://12factor.net/config)
- [Twelve-Factor Config: Misunderstandings and Advice](https://blog.doismellburning.co.uk/twelve-factor-config-misunderstandings-and-advice/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)
- [XDG Base Directory | ArchWiki](https://wiki.archlinux.org/title/XDG_Base_Directory)
- [Use the XDG Base Directory Specification!](https://xdgbasedirectoryspecification.com/)

### Pydantic Configuration

- [Settings Management - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Configuration - Pydantic Validation](https://docs.pydantic.dev/latest/api/config/)
- [Best Practices for Using Pydantic in Python | DEV](https://dev.to/devasservice/best-practices-for-using-pydantic-in-python-2021)

### Schema Versioning

- [Schema Versioning and Migration Strategies for Scalable Databases | JusDB](https://www.jusdb.com/blog/schema-versioning-and-migration-strategies-for-scalable-databases)
- [Database Migration and Version Control: The Ultimate Guide | XCubeLabs](https://www.xcubelabs.com/blog/database-migration-and-version-control-the-ultimate-guide-for-beginners/)
- [Best Schema Migration Tools for Developers in 2024 | Debugg.ai](https://debugg.ai/resources/best-schema-migration-tools-2024)

### Hugging Face Configuration

- [Configuration - Transformers Documentation](https://huggingface.co/docs/transformers/en/main_classes/configuration)
- [Models - Transformers Documentation](https://huggingface.co/docs/transformers/en/main_classes/model)
- [Loading Models - Transformers Documentation](https://huggingface.co/docs/transformers/en/models)

---

## Related Documentation

- [ADR-0013: Configuration Schema and Management](../decisions/adrs/0013-configuration-schema.md)
- [ADR-0011: Hardware Detection](../decisions/adrs/0011-hardware-detection.md)
- [F-035: Health Check Command](../features/completed/F-035-health-check.md)
- [F-036: Guided Setup](../features/completed/F-036-guided-setup.md)
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md)
- [State-of-the-Art Chunking](./state-of-the-art-chunking.md)
- [State-of-the-Art Setup UX](./state-of-the-art-setup-ux.md)
