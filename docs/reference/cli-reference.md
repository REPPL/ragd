# CLI Reference

Complete command reference for ragd v0.7.0.

## Synopsis

```
ragd [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format: `rich`, `plain`, `json` | `rich` (auto-detects pipe) |
| `--verbose` | `-v` | Enable verbose output | `false` |
| `--quiet` | `-q` | Minimal output (errors only) | `false` |
| `--config` | `-c` | Path to config file | `~/.config/ragd/config.yaml` |
| `--help` | `-h` | Show help and exit | |
| `--version` | `-V` | Show version and exit | |

### Output Formats

| Format | When to Use | Example |
|--------|-------------|---------|
| `rich` | Interactive terminal (default) | Colours, tables, progress bars |
| `plain` | Pipes, scripts, screen readers | Simple text, no formatting |
| `json` | Programmatic integration | Machine-readable structured data |

**Auto-detection:** ragd automatically uses `plain` when output is piped to another command.

```bash
# Rich output (terminal)
ragd search "machine learning"

# Auto-plain (piped)
ragd search "machine learning" | grep "neural"

# Explicit JSON (scripting)
ragd search "machine learning" --json | jq '.results[0]'
```

---

## Commands

### ragd init

Guided setup wizard to initialise ragd configuration.

#### Synopsis

```
ragd init [OPTIONS]
```

#### Description

Initialises ragd by:
1. Detecting hardware capabilities (CPU, GPU, memory)
2. Creating configuration directory (`~/.config/ragd/`)
3. Generating `config.yaml` with appropriate defaults
4. Creating data directory (`~/.local/share/ragd/`)
5. Initialising ChromaDB collection
6. Running health checks

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--force` | Overwrite existing configuration | `false` |
| `--non-interactive` | Skip prompts, use defaults | `false` |

#### Examples

```bash
# Interactive setup (recommended for first-time users)
ragd init

# Non-interactive setup (CI/CD, scripting)
ragd init --non-interactive

# Reset configuration
ragd init --force
```

#### Output

```
ragd init

Detecting hardware...
  CPU: Apple M2 Pro (12 cores)
  Memory: 32 GB
  GPU: Apple Silicon (MPS)
  Tier: high

Creating configuration...
  Config: ~/.config/ragd/config.yaml
  Data: ~/.local/share/ragd/
  Cache: ~/.cache/ragd/

Initialising database...
  ChromaDB: ~/.local/share/ragd/chroma_db/

Running health checks...
  [OK] Configuration valid
  [OK] Database accessible
  [OK] Embedding model available

Setup complete! Try: ragd index ~/Documents/example.pdf
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 78 | Configuration error (EX_CONFIG) |

---

### ragd index

Index documents for search.

#### Synopsis

```
ragd index <PATH>... [OPTIONS]
```

#### Description

Indexes one or more files or directories:
1. Discovers documents matching supported formats
2. Extracts text content (PDF, TXT, Markdown)
3. Chunks text using configured strategy
4. Generates embeddings
5. Stores in ChromaDB for search

**Supported formats:** PDF (`.pdf`), Text (`.txt`), Markdown (`.md`)

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `PATH` | File or directory to index | Yes (1 or more) |

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--recursive` | `-r` | Recursively index directories | `true` |
| `--pattern` | `-p` | Glob pattern for file matching | `*.pdf,*.txt,*.md` |
| `--reindex` | | Force re-indexing of existing files | `false` |
| `--dry-run` | | Show what would be indexed without indexing | `false` |

#### Examples

```bash
# Index a single file
ragd index ~/Documents/report.pdf

# Index a directory (recursive by default)
ragd index ~/Documents/

# Index multiple paths
ragd index ~/Documents/ ~/Downloads/papers/

# Index only PDFs
ragd index ~/Documents/ --pattern "*.pdf"

# Preview without indexing
ragd index ~/Documents/ --dry-run

# Force re-index existing documents
ragd index ~/Documents/report.pdf --reindex
```

#### Output

```
ragd index ~/Documents/reports/

Discovering documents...
  Found 15 files (12 PDF, 2 TXT, 1 MD)

Indexing [========================================] 15/15

Summary:
  Indexed: 15 documents
  Chunks: 423
  New: 12
  Updated: 3
  Skipped: 0
  Errors: 0

Total time: 12.3s
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (all files indexed) |
| 1 | Partial success (some files failed) |
| 66 | No input files found (EX_NOINPUT) |
| 74 | I/O error during indexing (EX_IOERR) |

---

### ragd search

Search the indexed knowledge base.

#### Synopsis

```
ragd search <QUERY> [OPTIONS]
```

#### Description

Searches indexed documents using semantic similarity:
1. Embeds the query using the configured model
2. Searches ChromaDB for similar chunks
3. Returns ranked results with citations

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `QUERY` | Natural language search query | Yes |

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--limit` | `-n` | Maximum number of results | `10` |
| `--threshold` | `-t` | Minimum similarity score (0.0-1.0) | `0.0` |
| `--filter` | | Metadata filter (key=value) | |

#### Examples

```bash
# Basic search
ragd search "machine learning algorithms"

# Limit results
ragd search "neural networks" --limit 5

# Filter by tag
ragd search "revenue analysis" --filter "tags=finance"

# JSON output for scripting
ragd search "AI ethics" --json | jq '.results[].citation'

# With minimum score threshold
ragd search "quantum computing" --threshold 0.7
```

#### Output (Rich Format)

```
ragd search "machine learning"

Found 8 results (0.42s)

[1] report.pdf, p. 12, "Introduction to ML"
    Score: 94.2%
    Machine learning is a subset of artificial intelligence
    that enables systems to learn from data...

[2] notes.md, "Chapter 3"
    Score: 87.5%
    The fundamental concepts of machine learning include
    supervised and unsupervised learning...

[3] paper.pdf, pp. 5-6, "Methodology"
    Score: 82.1%
    We applied machine learning techniques to analyse
    the dataset, specifically using...
```

#### Output (JSON Format)

```json
{
  "query": "machine learning",
  "total_results": 8,
  "search_time_ms": 420,
  "results": [
    {
      "rank": 1,
      "score": 0.942,
      "chunk_id": "chunk_abc123",
      "doc_id": "doc_xyz789",
      "citation": {
        "filename": "report.pdf",
        "title": null,
        "page_numbers": [12],
        "section_header": "Introduction to ML"
      },
      "excerpt": "Machine learning is a subset of artificial intelligence..."
    }
  ]
}
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (results found) |
| 0 | Success (no results - not an error) |
| 1 | General error |
| 69 | Database not initialised (EX_UNAVAILABLE) |

---

### ragd status

Show index statistics and system status.

#### Synopsis

```
ragd status [OPTIONS]
```

#### Description

Displays information about:
- Number of indexed documents and chunks
- Database size and location
- Configuration summary
- System health indicators

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--detailed` | Show detailed statistics | `false` |

#### Examples

```bash
# Basic status
ragd status

# Detailed statistics
ragd status --detailed

# JSON output
ragd status --json
```

#### Output

```
ragd status

Database Status
  Documents: 156
  Chunks: 4,892
  Database size: 125 MB

Configuration
  Config file: ~/.config/ragd/config.yaml
  Data directory: ~/.local/share/ragd/
  Embedding model: BAAI/bge-base-en-v1.5

System
  Hardware tier: high
  Device: mps (Apple Silicon)
  Last indexed: 2025-01-26 10:30:00
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 69 | Database not initialised (EX_UNAVAILABLE) |

---

### ragd doctor

Run health checks and diagnostics.

#### Synopsis

```
ragd doctor [OPTIONS]
```

#### Description

Performs comprehensive health checks:
1. **Configuration** - Validates config file syntax and values
2. **Database** - Tests ChromaDB connectivity and integrity
3. **Embedding Model** - Verifies model availability and loading
4. **Storage** - Checks disk space and permissions
5. **Dependencies** - Validates required packages

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--fix` | Attempt to fix detected issues | `false` |
| `--check` | Specific check to run | All checks |

#### Examples

```bash
# Run all health checks
ragd doctor

# Run specific check
ragd doctor --check database

# Attempt to fix issues
ragd doctor --fix
```

#### Output

```
ragd doctor

Running health checks...

Configuration
  [OK] Config file exists
  [OK] Config syntax valid
  [OK] All required fields present

Database
  [OK] ChromaDB accessible
  [OK] Collection exists
  [OK] Data integrity verified

Embedding Model
  [OK] Model available
  [OK] Model loads successfully
  [WARN] Using CPU (GPU recommended)

Storage
  [OK] Data directory writable
  [OK] Sufficient disk space (45 GB free)

Dependencies
  [OK] All required packages installed

Summary: 10 passed, 1 warning, 0 failed

Suggestions:
  - Consider enabling GPU acceleration for faster embeddings
    See: ragd config set embedding.device mps
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 78 | Configuration error (EX_CONFIG) |

---

### ragd ask

Ask a question and get an AI-generated answer from your knowledge base.

#### Synopsis

```
ragd ask <QUERY> [OPTIONS]
```

#### Description

Combines retrieval with LLM generation:
1. Retrieves relevant chunks from the knowledge base
2. Sends context and query to local LLM (Ollama)
3. Returns AI-generated answer with citations

Requires Ollama to be running with a compatible model.

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `QUERY` | Natural language question | Yes |

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--model` | `-m` | Override LLM model | Config value |
| `--temperature` | `-t` | Sampling temperature (0.0-2.0) | `0.7` |
| `--agentic` | | Enable agentic RAG (CRAG + Self-RAG) | Auto |
| `--no-agentic` | | Disable agentic RAG | |
| `--show-confidence` | | Display confidence scores | `false` |
| `--cite` | `-c` | Citation style: `none`, `numbered`, `inline` | `numbered` |
| `--limit` | `-n` | Max context chunks | `5` |

#### Examples

```bash
# Basic question
ragd ask "What authentication methods are used?"

# Use specific model
ragd ask "Summarise the security policy" --model llama3.2:8b

# Enable agentic mode with confidence
ragd ask "Explain the architecture" --agentic --show-confidence

# Disable citations
ragd ask "What is the conclusion?" --cite none
```

#### Output

```
ragd ask "What authentication methods are used?"

Searching knowledge base...

Based on your documents, the main authentication methods are:

1. **OAuth 2.0** - Used for third-party integrations
2. **JWT tokens** - For API authentication
3. **Session cookies** - For web application state

[Sources: security-policy.pdf:12, api-docs.md:45]
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | LLM error or generation failed |
| 69 | Ollama unavailable |

---

### ragd chat

Start an interactive chat session with your knowledge base.

#### Synopsis

```
ragd chat [OPTIONS]
```

#### Description

Opens an interactive REPL for conversational queries:
- Maintains conversation history across turns
- Context-aware follow-up questions
- Streaming response output
- Chat commands for session management

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--model` | `-m` | Override LLM model | Config value |
| `--session` | `-s` | Session name to resume | New session |
| `--cite` | `-c` | Citation style: `none`, `numbered` | Config value |
| `--agentic` | | Force agentic mode | Auto |

#### Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/sources` | Show sources from last response |
| `/model <name>` | Switch to different model |
| `/exit` or `/quit` | Exit chat session |

#### Examples

```bash
# Start new chat session
ragd chat

# Use specific model
ragd chat --model qwen2.5:7b

# Resume named session
ragd chat --session project-research
```

#### Interactive Session

```
ragd chat

Welcome to ragd chat! Type /help for commands, /exit to quit.
Model: llama3.2:3b

> What is the main topic of my documents?

Based on your indexed documents, the main topics are software
architecture and API design...

> Tell me more about the API design

The API design follows REST principles with these key patterns...

> /sources
[1] api-design.pdf:5-8
[2] architecture.md:12

> /exit
Session saved. Goodbye!
```

---

### ragd evaluate

Evaluate retrieval and response quality.

#### Synopsis

```
ragd evaluate [OPTIONS]
```

#### Description

Runs evaluation metrics on queries:
- Context Precision - How relevant are retrieved chunks
- Context Recall - Ground truth comparison
- Relevance Score - Position-weighted ranking
- NDCG - Normalised discounted cumulative gain

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Single query to evaluate | |
| `--test-file` | `-f` | YAML/JSON file with test queries | |
| `--expected` | `-e` | Expected document(s) for recall | |
| `--limit` | `-n` | Number of results to evaluate | `10` |
| `--threshold` | | Relevance threshold | `0.3` |
| `--no-save` | | Don't save results | `false` |

#### Examples

```bash
# Evaluate single query
ragd evaluate --query "What is machine learning?"

# With expected documents
ragd evaluate --query "security policy" --expected policy.pdf

# Batch evaluation from file
ragd evaluate --test-file tests/golden_queries.yaml
```

#### Test File Format

```yaml
# tests/golden_queries.yaml
queries:
  - query: "What is machine learning?"
    expected_docs:
      - intro.pdf
      - ml-chapter.md
  - query: "Authentication methods"
    expected_docs:
      - security.pdf
```

#### Output

```
ragd evaluate --query "What is machine learning?"

Evaluating query...

Query: "What is machine learning?"

Metrics:
  Context Precision: 0.85
  Relevance Score: 0.78
  NDCG@10: 0.82
  Reciprocal Rank: 1.0

Top Results:
  [1] intro.pdf:12 (0.94) ✓
  [2] ml-chapter.md:5 (0.87) ✓
  [3] notes.txt:3 (0.72)
```

---

### ragd models

Manage LLM models via Ollama.

#### Synopsis

```
ragd models <COMMAND> [OPTIONS]
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `list` | List available models |
| `status` | Show loaded models and memory |
| `pull <model>` | Download a model |
| `set <key> <value>` | Set model configuration |

#### Examples

```bash
# List available models
ragd models list

# Show what's loaded
ragd models status

# Pull a new model
ragd models pull qwen2.5:3b

# Set default model
ragd models set default llama3.2:8b
```

#### Output (list)

```
ragd models list

Available Models:
  llama3.2:3b     2.0 GB  ✓ Loaded
  llama3.2:8b     4.7 GB
  qwen2.5:3b      1.9 GB  ✓ Loaded
  qwen2.5:7b      4.4 GB

Default: llama3.2:3b
```

---

### ragd unlock

Unlock the encrypted database.

#### Synopsis

```
ragd unlock [OPTIONS]
```

#### Description

Unlocks the encrypted database for a session:
1. Prompts for password
2. Derives encryption key using Argon2id
3. Starts session timer

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--extend` | Extend current session instead of re-authenticating | `false` |

#### Examples

```bash
# Unlock database
ragd unlock

# Extend current session
ragd unlock --extend
```

---

### ragd lock

Lock the session immediately.

#### Synopsis

```
ragd lock
```

#### Description

Locks the session and clears encryption keys from memory.

#### Examples

```bash
ragd lock
```

---

### ragd password

Manage encryption password.

#### Synopsis

```
ragd password <COMMAND>
```

#### Subcommands

| Command | Description |
|---------|-------------|
| `change` | Change encryption password |
| `reset` | Reset encryption (deletes all data) |
| `rotate-key` | Rotate encryption key |

#### Examples

```bash
# Change password
ragd password change

# Reset encryption (warning: deletes data)
ragd password reset --confirm-data-loss

# Rotate encryption key
ragd password rotate-key
```

---

### ragd session

View session status.

#### Synopsis

```
ragd session status
```

#### Description

Shows current session state, remaining time, and failed attempt count.

#### Examples

```bash
ragd session status
```

#### Output

```
Session: Unlocked (4:32 remaining)
Failed attempts: 0
```

---

### ragd delete

Delete documents from the knowledge base.

#### Synopsis

```
ragd delete <DOC_IDS>... [OPTIONS]
```

#### Description

Removes documents from the index with three deletion levels:
- **Standard** - Remove from index only
- **Secure** - Overwrite storage locations
- **Cryptographic** - Rotate encryption key (maximum security)

#### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `DOC_IDS` | Document IDs to delete | Yes (1 or more) |

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--secure` | Securely overwrite storage | `false` |
| `--purge` | Cryptographic erasure with key rotation | `false` |
| `--force` | Skip confirmation prompts | `false` |

#### Subcommands

| Command | Description |
|---------|-------------|
| `audit` | View deletion audit log |

#### Examples

```bash
# Standard deletion
ragd delete doc123

# Secure deletion
ragd delete doc123 --secure

# Cryptographic erasure
ragd delete doc123 --purge

# View audit log
ragd delete audit
ragd delete audit -n 10
```

---

## Exit Codes Reference

ragd uses standard sysexits.h codes where applicable:

| Code | Name | Meaning |
|------|------|---------|
| 0 | `EX_OK` | Success |
| 1 | `EX_GENERAL` | General/unspecified error |
| 2 | `EX_USAGE` | Incorrect command usage |
| 64 | `EX_USAGE` | Command line usage error |
| 66 | `EX_NOINPUT` | Cannot open input file |
| 69 | `EX_UNAVAILABLE` | Service unavailable (database) |
| 70 | `EX_SOFTWARE` | Internal software error |
| 74 | `EX_IOERR` | Input/output error |
| 78 | `EX_CONFIG` | Configuration error |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAGD_CONFIG` | Path to config file | `~/.config/ragd/config.yaml` |
| `RAGD_DATA_DIR` | Data directory path | `~/.local/share/ragd/` |
| `RAGD_EMBEDDING__MODEL` | Override embedding model | Config value |
| `RAGD_EMBEDDING__DEVICE` | Override device (cpu/cuda/mps) | Config value |
| `NO_COLOR` | Disable coloured output | |

Environment variables use double underscore (`__`) for nested config keys.

---

## Configuration

See [Configuration Reference](./config.example.yaml) for full configuration options.

Quick configuration commands:

```bash
# Show current configuration
ragd config show

# Get specific value
ragd config get embedding.model

# Set value
ragd config set embedding.device mps

# Validate configuration
ragd config validate
```

---

## Related Documentation

- [CLI Documentation Standards](../development/research/cli-documentation-standards.md) - Research findings
- [ADR-0005: CLI Design Principles](../development/decisions/adrs/0005-cli-design-principles.md)
- [Configuration Reference](./config.example.yaml)
- [Data Schema Reference](./data-schema.md)

---

**Status**: Reference specification for v0.7.0
