# CLI Reference

Complete command specifications for ragd.

---

## Global Options

Options available for all commands:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | `-h` | flag | | Show help message |
| `--version` | `-v` | flag | | Show version |
| `--quiet` | `-q` | flag | | Suppress non-essential output |
| `--verbose` | | flag | | Show detailed output |
| `--debug` | | flag | | Show debug information |
| `--format` | | string | `rich` | Output format: `rich`, `plain`, `json` |
| `--json` | | flag | | Shorthand for `--format json` |
| `--plain` | | flag | | Shorthand for `--format plain` |
| `--no-color` | | flag | | Disable colour output |
| `--theme` | | string | `default` | Colour theme |
| `--config` | `-c` | path | `~/.ragd/config.yaml` | Config file path |
| `--no-input` | | flag | | Disable interactive prompts |

---

## ragd doctor

Run health checks on ragd components.

### Synopsis

```
ragd doctor [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose` | flag | | Show detailed diagnostics |
| `--format` | string | `rich` | Output format |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |

### Examples

```bash
# Basic health check
ragd doctor

# Detailed diagnostics
ragd doctor --verbose

# JSON for monitoring
ragd doctor --format json
```

### JSON Output Schema

```json
{
  "status": "healthy",
  "checks": [
    {
      "name": "Storage",
      "status": "healthy",
      "message": "ChromaDB accessible",
      "duration_ms": 12
    }
  ],
  "total_duration_ms": 253
}
```

---

## ragd index

Add documents to the knowledge base.

### Synopsis

```
ragd index <PATH> [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `PATH` | Yes | File or directory to index |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--recursive` | flag | `true` | Process subdirectories |
| `--include` | string | | Glob pattern to include |
| `--exclude` | string | | Glob pattern to exclude |
| `--verbose` | flag | | Show detailed progress |
| `--force` | flag | | Re-index existing files |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 3 | File not found |

### Examples

```bash
# Index a file
ragd index document.pdf

# Index a directory
ragd index ~/Documents/

# Index only PDFs
ragd index ~/Documents/ --include "*.pdf"

# Force re-index
ragd index report.pdf --force

# Verbose output
ragd index ~/Notes/ --verbose
```

### JSON Output Schema

```json
{
  "indexed": 5,
  "chunks": 247,
  "skipped": 2,
  "errors": [],
  "duration_ms": 3420
}
```

---

## ragd search

Search the knowledge base.

### Synopsis

```
ragd search <QUERY> [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `QUERY` | Yes | Natural language search query |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--limit` | `-n` | int | `10` | Maximum results |
| `--format` | | string | `rich` | Output format |
| `--quotes` | | flag | | Include direct quotes |
| `--cite-style` | | string | `plain` | Citation style |
| `--bibliography` | | string | | Export format (bibtex, ris) |

### Citation Styles

| Style | Format |
|-------|--------|
| `plain` | `file.pdf, p.5` |
| `apa` | `Smith, J. (2024). Title. Publisher.` |
| `ieee` | `[1] J. Smith, "Title," Publisher, 2024.` |
| `acm` | `John Smith. 2024. Title. Publisher.` |
| `chicago` | `Smith, John. Title. Publisher, 2024.` |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Results found |
| 0 | No results (not an error) |
| 1 | Search error |

### Examples

```bash
# Basic search
ragd search "machine learning"

# Limited results
ragd search "neural networks" --limit 5

# JSON output
ragd search "authentication" --format json

# With citations
ragd search "privacy" --cite-style apa

# Export bibliography
ragd search "AI ethics" --bibliography bibtex > refs.bib
```

### JSON Output Schema

```json
{
  "query": "machine learning",
  "results": [
    {
      "content": "Machine learning is...",
      "score": 0.89,
      "source": {
        "file": "paper.pdf",
        "page": 5,
        "link": "file:///path/paper.pdf#page=5"
      }
    }
  ],
  "total": 10,
  "duration_ms": 142
}
```

---

## ragd status

View knowledge base statistics.

### Synopsis

```
ragd status [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose` | flag | | Show detailed statistics |
| `--format` | string | `rich` | Output format |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error accessing storage |

### Examples

```bash
# Basic status
ragd status

# Detailed statistics
ragd status --verbose

# JSON for monitoring
ragd status --format json
```

### JSON Output Schema

```json
{
  "status": "ready",
  "index": {
    "documents": 42,
    "chunks": 1247,
    "embeddings": 1247
  },
  "storage": {
    "index_size_bytes": 163887104,
    "available_bytes": 48523837440,
    "data_path": "~/.ragd"
  },
  "config": {
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 512,
    "config_file": "~/.ragd/config.yaml"
  }
}
```

---

## ragd config

Manage configuration settings.

### Synopsis

```
ragd config <COMMAND> [OPTIONS]
```

### Subcommands

| Command | Description |
|---------|-------------|
| `show` | Display current configuration |
| `set` | Set a configuration value |
| `reset` | Reset to defaults |

### Examples

```bash
# Show configuration
ragd config show

# Set a value
ragd config set embedding.model all-MiniLM-L6-v2
ragd config set output.theme high-contrast

# Reset to defaults
ragd config reset
```

---

## ragd unlock

Unlock the encrypted database.

### Synopsis

```
ragd unlock [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--extend` | flag | | Extend current session instead of re-authenticating |

### Examples

```bash
# Unlock database
ragd unlock
Enter password: ********
✓ Session unlocked for 5 minutes

# Extend current session
ragd unlock --extend
✓ Session extended by 5 minutes
```

---

## ragd lock

Lock the session immediately.

### Synopsis

```
ragd lock
```

### Examples

```bash
ragd lock
✓ Session locked
```

---

## ragd password

Manage encryption password.

### Subcommands

| Command | Description |
|---------|-------------|
| `change` | Change encryption password |
| `reset` | Reset encryption (deletes all data) |

### ragd password change

```bash
ragd password change
Current password: ********
New password: ********
Confirm password: ********
✓ Password changed
```

### ragd password reset

```bash
ragd password reset --confirm-data-loss
⚠️  This will DELETE ALL DATA and reset encryption.
Type 'DELETE' to confirm: DELETE
✓ Encryption reset
```

---

## ragd session

View session status.

### Synopsis

```
ragd session status
```

### Examples

```bash
ragd session status
Session: Unlocked (4:32 remaining)

ragd session status
Session: Locked
```

---

## ragd delete

Delete documents from the knowledge base.

### Synopsis

```
ragd delete <DOC_IDS> [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `DOC_IDS` | Yes | Document IDs to delete |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--secure` | flag | | Securely overwrite storage |
| `--purge` | flag | | Cryptographic erasure with key rotation |
| `--force` | flag | | Skip confirmation prompts |

### Subcommands

| Command | Description |
|---------|-------------|
| `audit` | View deletion audit log |

### Examples

```bash
# Standard deletion
ragd delete doc123
Delete "doc123" from index? [y/N] y
✓ Removed from index

# Secure deletion
ragd delete doc123 --secure
Secure delete "doc123"? This cannot be undone. [y/N] y
✓ Securely deleted

# Cryptographic erasure
ragd delete doc123 --purge
Enter password to confirm: ********
✓ Purged with key rotation

# View audit log
ragd delete audit
ragd delete audit --all
ragd delete audit -n 10
```

---

## ragd ask

Ask a question with citation support.

### Synopsis

```
ragd ask <QUERY> [OPTIONS]
```

### Citation Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cite` | string | `numbered` | Citation style: `none`, `numbered`, `inline` |

### Examples

```bash
# Default numbered citations
ragd ask "What authentication methods are recommended?"

Sources:
  [1] security-guide.pdf, p. 5
  [2] best-practices.md

# Disable citations
ragd ask "Summarise the policy" --cite none

# Inline citations
ragd ask "Compare approaches" --cite inline
```

---

## ragd chat

Interactive chat with citation support.

### Synopsis

```
ragd chat [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--cite` | `-c` | string | from config | Citation style: `none`, `numbered` |
| `--session` | `-s` | string | | Resume previous session |
| `--model` | `-m` | string | from config | LLM model to use |

### Examples

```bash
# Start chat with default citation mode
ragd chat

# Disable citations
ragd chat --cite none

# Resume previous session
ragd chat --session abc123

# Use different model
ragd chat --model llama3.2:8b
```

### Built-in Commands

| Command | Description |
|---------|-------------|
| `/exit`, `/quit`, `/q` | Exit chat |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/help` | Show help |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAGD_CONFIG` | Configuration file path | `~/.ragd/config.yaml` |
| `RAGD_DATA_PATH` | Data directory path | `~/.ragd/data` |
| `RAGD_THEME` | Output colour theme | `default` |
| `RAGD_LOG_LEVEL` | Logging level | `INFO` |
| `NO_COLOR` | Disable colour output | unset |

---

## Configuration File

### Location

```
~/.ragd/config.yaml
```

### Full Schema

```yaml
# Embedding configuration
embedding:
  model: all-MiniLM-L6-v2    # Embedding model name

# Chunking configuration
chunking:
  size: 512                   # Tokens per chunk
  overlap: 50                 # Token overlap between chunks

# Output configuration
output:
  theme: default              # default | high-contrast | colourblind-safe | monochrome
  format: rich                # rich | plain | json

# Citation configuration
citations:
  style: plain                # plain | apa | ieee | acm | chicago
  inline_format: numeric      # numeric | author-date
  show_page: true
  link_to_source: true
  max_quote_length: 200

# Storage configuration
storage:
  path: ~/.ragd/data

# Logging configuration
logging:
  level: INFO                 # DEBUG | INFO | WARNING | ERROR
  file: ~/.ragd/logs/ragd.log
```

---

## Related Documentation

- [CLI Essentials](./essentials.md) - Quick start guide
- [CLI Intermediate](./intermediate.md) - Task workflows
- [CLI Advanced](./advanced.md) - Configuration and debugging
- [Troubleshooting](../troubleshooting.md) - Common issues

---
