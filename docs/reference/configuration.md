# Configuration Reference

Complete reference for ragd configuration options.

## Configuration File

Default location: `~/.ragd/config.yaml`

View path: `ragd config --path`

## Configuration Sections

### hardware

Hardware detection and optimisation.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backend` | string | `cpu` | Compute backend: `cpu`, `mps`, `cuda` |
| `tier` | string | `standard` | Hardware tier: `minimal`, `standard`, `high`, `extreme` |
| `memory_gb` | float | 8.0 | Available memory in GB |
| `detected_at` | string | null | Timestamp of hardware detection |

### storage

Storage paths and directories.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `data_dir` | path | `~/.ragd` | Root data directory |
| `chroma_dir` | string | `chroma` | ChromaDB subdirectory |
| `documents_dir` | string | `documents` | Document storage subdirectory |

### embedding

Embedding model configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `all-MiniLM-L6-v2` | Embedding model name |
| `dimension` | int | 384 | Embedding vector dimension |
| `batch_size` | int | 32 | Batch size for embedding |
| `device` | string | null | Device override: `cpu`, `mps`, `cuda` |
| `late_chunking` | bool | false | Enable late chunking for context |
| `late_chunking_model` | string | `jinaai/jina-embeddings-v2-small-en` | Model for late chunking |
| `max_context_tokens` | int | 8192 | Max tokens for late chunking context |

### llm

Large Language Model configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `provider` | string | `ollama` | LLM provider: `ollama`, `openai`, `anthropic` |
| `model` | string | `llama3.2:3b` | Model name |
| `base_url` | string | `http://localhost:11434` | Provider base URL |

### search

Search behaviour settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mode` | string | `hybrid` | Search mode: `hybrid`, `semantic`, `keyword` |
| `semantic_weight` | float | 0.7 | Weight for semantic search (0.0-1.0) |
| `keyword_weight` | float | 0.3 | Weight for keyword search (0.0-1.0) |
| `rrf_k` | int | 60 | Reciprocal Rank Fusion k parameter |
| `bm25_k1` | float | 1.2 | BM25 k1 parameter |
| `bm25_b` | float | 0.75 | BM25 b parameter |

### retrieval

Retrieval configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_limit` | int | 10 | Default number of results |
| `min_score` | float | 0.3 | Minimum similarity score (0.0-1.0) |
| `rerank` | bool | false | Enable reranking |

#### retrieval.contextual

Contextual retrieval settings (requires Ollama).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | false | Enable contextual retrieval |
| `provider` | string | `ollama` | Context generation provider |
| `model` | string | `llama3.2:3b` | Context generation model |
| `base_url` | string | `http://localhost:11434` | Provider URL |
| `timeout_seconds` | int | 60 | Request timeout |
| `batch_size` | int | 10 | Batch size for context generation |
| `prompt_template` | string | `` | Custom prompt template |

### chunking

Text chunking configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `strategy` | string | `sentence` | Strategy: `sentence`, `fixed`, `recursive` |
| `chunk_size` | int | 512 | Target chunk size in tokens |
| `overlap` | int | 50 | Overlap between chunks in tokens |
| `min_chunk_size` | int | 100 | Minimum chunk size |

### normalisation

Text normalisation configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | true | Enable text normalisation |
| `fix_spaced_letters` | bool | true | Fix `s p a c e d` letters |
| `fix_word_boundaries` | bool | true | Fix word boundaries |
| `fix_line_breaks` | bool | true | Fix line breaks |
| `fix_ocr_spelling` | bool | true | Fix common OCR errors |
| `remove_boilerplate` | bool | true | Remove boilerplate text |
| `boilerplate_mode` | string | `aggressive` | Mode: `conservative`, `moderate`, `aggressive` |

### cache

Caching configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | true | Enable caching |
| `max_size_mb` | int | 100 | Maximum cache size in MB |

### chat

Chat session configuration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `temperature` | float | 0.7 | Generation temperature (0.0-1.0) |
| `max_tokens` | int | 1024 | Maximum tokens in response |
| `context_window` | int | 4096 | Context window size |
| `history_turns` | int | 5 | Conversation turns to keep |
| `search_limit` | int | 15 | Documents to retrieve per query |
| `auto_save` | bool | true | Auto-save conversation |
| `default_cite_mode` | string | `numbered` | Citation style: `numbered`, `none`, `inline` |

### security

Security configuration.

#### security.encryption

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | false | Enable encryption |
| `algorithm` | string | `AES-256-GCM` | Encryption algorithm |
| `kdf` | string | `argon2id` | Key derivation function |
| `kdf_memory_mb` | int | 64 | KDF memory cost |
| `kdf_iterations` | int | 3 | KDF iteration count |
| `kdf_parallelism` | int | 4 | KDF parallelism |

#### security.session

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_lock_minutes` | int | 5 | Auto-lock timeout (0 = disabled) |
| `failed_attempts_lockout` | int | 5 | Failed attempts before lockout |
| `lockout_minutes` | int | 15 | Lockout duration |
| `activity_resets_timer` | bool | true | Reset timer on activity |

#### security.deletion

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_level` | string | `standard` | Level: `standard`, `secure`, `purge` |
| `require_confirmation` | bool | true | Require confirmation |
| `audit_log` | bool | true | Enable audit logging |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RAGD_OUTPUT_FORMAT` | Default output format: `rich`, `plain`, `json`, `csv` |
| `NO_COLOR` | Disable colour output when set |
| `RAGD_DATA_DIR` | Override data directory |
| `RAGD_CONFIG_PATH` | Override config file path |

## Example Configurations

### Minimal

```yaml
version: 2
embedding:
  model: all-MiniLM-L6-v2
llm:
  model: llama3.2:3b
```

### High Performance

```yaml
version: 2
hardware:
  backend: mps  # or cuda
embedding:
  model: all-mpnet-base-v2
  batch_size: 64
llm:
  model: llama3.2:8b
chunking:
  chunk_size: 1024
  overlap: 100
retrieval:
  contextual:
    enabled: true
```

---

## Related Documentation

- [Model Purposes Explained](../explanation/model-purposes.md) — Understanding chat, summary, embedding, contextual, and classification models
- [Troubleshooting Guide](../guides/troubleshooting.md)
- [Tutorials](../tutorials/)
