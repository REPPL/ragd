# CLI Reference

Complete command reference for ragd v1.0.0a5.

## Synopsis

```
ragd [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version and exit |
| `--install-completion` | | Install shell completion |
| `--show-completion` | | Show completion script |
| `--help` | | Show help and exit |

### Per-Command Options

Most commands support these common options:

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format: `rich`, `plain`, `json` | `rich` |
| `--no-color` | | Disable coloured output | `false` |

### Output Formats

| Format | When to Use |
|--------|-------------|
| `rich` | Interactive terminal (default) - colours, tables, progress bars |
| `plain` | Pipes, scripts, screen readers - simple text |
| `json` | Programmatic integration - machine-readable |

**Auto-detection:** ragd automatically uses `plain` when output is piped.

---

## Command Categories

### Setup & Help

| Command | Description |
|---------|-------------|
| [`init`](#ragd-init) | Initialise ragd with guided setup |
| [`info`](#ragd-info) | Show ragd status and statistics |
| [`help`](#ragd-help) | Show extended help for commands |

### Document Management

| Command | Description |
|---------|-------------|
| [`index`](#ragd-index) | Index documents from a file or directory |
| [`reindex`](#ragd-reindex) | Re-index documents with improved extraction |
| [`list`](#ragd-list) | List documents in the knowledge base |

### Core Commands

| Command | Description |
|---------|-------------|
| [`search`](#ragd-search) | Search indexed documents |
| [`ask`](#ragd-ask) | Ask a question (LLM-powered) |
| [`chat`](#ragd-chat) | Interactive chat mode |

### Knowledge Base

| Command | Description |
|---------|-------------|
| [`export`](#ragd-export) | Export knowledge base to archive |
| [`import`](#ragd-import) | Import knowledge base from archive |

### Organisation

| Command | Description |
|---------|-------------|
| [`collection`](#ragd-collection) | Manage smart collections |
| [`meta`](#ragd-meta) | Manage document metadata |
| [`tag`](#ragd-tag) | Manage document tags |

---

## Commands

### ragd init

Initialise ragd with guided setup.

```
ragd init [OPTIONS]
```

**Description:**

Detects hardware capabilities and creates optimal configuration:
1. Detects CPU, GPU, and memory
2. Creates configuration directory (`~/.config/ragd/`)
3. Generates `config.yaml` with appropriate defaults
4. Creates data directory (`~/.local/share/ragd/`)
5. Initialises ChromaDB collection
6. Runs health checks

**Options:**

| Option | Description |
|--------|-------------|
| `--no-color` | Disable colour output |
| `--help` | Show help and exit |

**Examples:**

```bash
ragd init
```

---

### ragd index

Index documents from a file or directory.

```
ragd index <PATH> [OPTIONS]
```

**Description:**

Indexes documents with these steps:
1. Discovers files matching supported formats
2. Extracts text content
3. Chunks text using configured strategy
4. Generates embeddings
5. Stores in vector database

**Supported formats:** PDF, TXT, MD, HTML

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `PATH` | File or directory to index | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--recursive` | `-r` | Search directories recursively | `true` |
| `--no-recursive` | | Do not recurse into directories | |
| `--skip-duplicates` | | Skip already-indexed documents | `true` |
| `--no-skip-duplicates` | | Re-index all documents | |
| `--contextual` | `-c` | Enable contextual retrieval (requires Ollama) | Config |
| `--no-contextual` | | Disable contextual retrieval | |
| `--late-chunking` | `-l` | Enable late chunking | Config |
| `--no-late-chunking` | | Disable late chunking | |
| `--verbose` | `-V` | Show per-file progress | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
# Index a single file
ragd index ~/Documents/report.pdf

# Index a directory (recursive by default)
ragd index ~/Documents/

# Disable recursive, show per-file progress
ragd index ~/Documents/ --no-recursive --verbose

# Enable contextual retrieval
ragd index ~/Documents/ --contextual
```

---

### ragd search

Search indexed documents with natural language.

```
ragd search <QUERY> [OPTIONS]
```

**Description:**

Returns relevant document chunks using hybrid search. By default, opens an interactive navigator (use j/k or arrows to navigate, q to quit).

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `QUERY` | Search query | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--limit` | `-n` | Maximum results | `10` |
| `--min-score` | | Minimum similarity score (0-1) | `0.3` |
| `--mode` | `-m` | Search mode: `hybrid`, `semantic`, `keyword` | `hybrid` |
| `--cite` | | Citation style | `none` |
| `--tag` | `-t` | Filter by tag (repeatable) | |
| `--no-interactive` | | Print results directly | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Search Modes:**

| Mode | Description |
|------|-------------|
| `hybrid` | Combines semantic and keyword search (default) |
| `semantic` | Pure vector similarity search |
| `keyword` | Pure BM25 keyword search |

**Citation Styles:**

| Style | Description |
|-------|-------------|
| `none` | No citations (default) |
| `inline` | Simple (filename, p. X) format |
| `apa` | APA 7th edition |
| `mla` | MLA 9th edition |
| `chicago` | Chicago notes-bibliography |
| `bibtex` | BibTeX for LaTeX |
| `markdown` | Markdown link format |

**Examples:**

```bash
# Basic search
ragd search "machine learning algorithms"

# Limit results
ragd search "neural networks" --limit 5

# Semantic-only search
ragd search "AI ethics" --mode semantic

# With citations
ragd search "revenue analysis" --cite apa

# JSON output for scripting
ragd search "quantum computing" --format json --no-interactive

# Filter by tag
ragd search "neural networks" --tag "topic:ml"

# Multiple tags (all must match)
ragd search "requirements" --tag "project:alpha" --tag "status:reviewed"
```

---

### ragd info

Show ragd status and statistics.

```
ragd info [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--detailed` | `-d` | Show comprehensive statistics | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd info              # Quick status
ragd info --detailed   # Full statistics
ragd info -d           # Short form
```

---

### ragd help

Show extended help for commands.

```
ragd help [TOPIC] [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `TOPIC` | Help topic (command name) | No |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--examples` | `-e` | Show only examples |

**Examples:**

```bash
ragd help                    # List all help topics
ragd help search             # Extended search help
ragd help search --examples  # Just examples
```

---

### ragd reindex

Re-index documents with improved text extraction.

```
ragd reindex [DOCUMENT_ID] [OPTIONS]
```

**Description:**

Use after upgrading ragd to apply text quality improvements to existing documents.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `DOCUMENT_ID` | Specific document ID | No |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--all` | `-a` | Re-index all documents | `false` |
| `--type` | `-t` | Filter by file type (pdf, html) | |
| `--force` | `-F` | Skip confirmation prompt | `false` |
| `--verbose` | `-V` | Show per-file progress | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd reindex --all              # Re-index all documents
ragd reindex --type pdf         # Re-index only PDFs
ragd reindex doc-123            # Re-index specific document
ragd reindex --all --force      # Without confirmation
```

---

### ragd list

List documents in the knowledge base.

```
ragd list [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--tag` | `-t` | Filter by tag | |
| `--project` | `-p` | Filter by project | |
| `--limit` | `-n` | Maximum results | |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd list                      # All documents
ragd list --tag important      # Documents with tag
ragd list --project Research   # Documents in project
ragd list -n 10                # First 10 documents
```

---

### ragd ask

Ask a question using your knowledge base.

```
ragd ask <QUESTION> [OPTIONS]
```

**Description:**

Retrieves relevant documents and generates an answer using Ollama LLM. Requires Ollama to be running locally.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `QUESTION` | Question to ask | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--model` | `-m` | LLM model to use | Config |
| `--temperature` | `-t` | Sampling temperature (0.0-1.0) | `0.7` |
| `--limit` | `-n` | Maximum search results for context | `5` |
| `--min-relevance` | `-r` | Minimum relevance score (0.0-1.0) | Config |
| `--no-stream` | | Disable streaming output | `false` |
| `--agentic` | | Enable agentic RAG (CRAG + Self-RAG) | |
| `--no-agentic` | | Disable agentic RAG | |
| `--show-confidence` | `-c` | Show confidence score | `false` |
| `--cite` | | Citation style: `none`, `numbered`, `inline` | `numbered` |
| `--verbose` | `-V` | Show detailed progress | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd ask "What authentication methods are recommended?"
ragd ask "Summarise the security policy" --model llama3.2:8b
ragd ask "Compare the approaches" --agentic --show-confidence
ragd ask "What is the conclusion?" --cite none
```

---

### ragd chat

Start an interactive chat with your knowledge base.

```
ragd chat [OPTIONS]
```

**Description:**

Multi-turn conversation with RAG-powered responses. Requires Ollama to be running locally.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--model` | `-m` | LLM model to use | Config |
| `--temperature` | `-t` | Sampling temperature (0.0-1.0) | `0.7` |
| `--limit` | `-n` | Maximum search results per query | `5` |
| `--min-relevance` | `-r` | Minimum relevance score (0.0-1.0) | Config |
| `--session` | `-s` | Resume a previous chat session | |
| `--cite` | `-c` | Citation style: `none`, `numbered` | Config |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Chat Commands:**

| Command | Description |
|---------|-------------|
| `/exit`, `/quit`, `/q` | Exit chat |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/help` | Show available commands |

**Examples:**

```bash
ragd chat
ragd chat --model llama3.2:8b
ragd chat --cite none            # Disable citations
ragd chat --session abc123       # Resume previous session
```

---

### ragd export

Export knowledge base to an archive.

```
ragd export <OUTPUT_PATH> [OPTIONS]
```

**Description:**

Creates a portable tar.gz archive containing documents, chunks, embeddings, and metadata.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `OUTPUT_PATH` | Path for output archive (.tar.gz) | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--no-embeddings` | | Exclude embeddings (smaller archive) | `false` |
| `--tag` | `-t` | Only export documents with tag | |
| `--project` | `-p` | Only export documents in project | |
| `--verbose` | `-V` | Show detailed progress | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd export ~/backup.tar.gz               # Full export
ragd export ~/backup.tar.gz --no-embeddings  # Smaller archive
ragd export ~/ml.tar.gz --tag "topic:ml"  # Export by tag
```

---

### ragd import

Import knowledge base from an archive.

```
ragd import <ARCHIVE_PATH> [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `ARCHIVE_PATH` | Path to archive (.tar.gz) | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--skip-conflicts` | | Skip documents that already exist | `false` |
| `--overwrite` | | Overwrite existing documents | `false` |
| `--dry-run` | | Validate without importing | `false` |
| `--verbose` | `-V` | Show detailed progress | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd import ~/backup.tar.gz               # Import with defaults
ragd import ~/backup.tar.gz --dry-run     # Validate only
ragd import ~/backup.tar.gz --overwrite   # Replace existing
```

---

### ragd collection

Manage smart collections.

```
ragd collection <COMMAND> [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `create` | Create a new smart collection |
| `list` | List all collections |
| `show` | Show collection details and contents |
| `update` | Update a collection's query or description |
| `delete` | Delete a collection |
| `export` | Export collection members |

**Examples:**

```bash
ragd collection create "Q3 Finance" --include-all finance q3-2024 --exclude draft
ragd collection list
ragd collection show "Q3 Finance"
ragd collection delete "Old Projects" --force
```

---

### ragd meta

Manage document metadata.

```
ragd meta <COMMAND> [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `show` | Show metadata for a document |
| `edit` | Edit metadata for a document |

**Examples:**

```bash
ragd meta show doc-123
ragd meta edit doc-123 --title "My Document"
ragd meta edit doc-123 --creator "Smith, J.; Doe, J."
```

---

### ragd tag

Manage document tags.

```
ragd tag <COMMAND> [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `add` | Add tags to a document |
| `remove` | Remove tags from a document |
| `list` | List tags |
| `suggestions` | Show tag suggestions for a document |
| `pending` | Show documents with pending suggestions |
| `confirm` | Confirm tag suggestions |
| `reject` | Reject tag suggestions |
| `stats` | Show tag suggestion statistics |

**Examples:**

```bash
ragd tag add doc-123 important "topic:ml"
ragd tag remove doc-123 draft
ragd tag list --counts
ragd tag suggestions doc-123
ragd tag confirm doc-123 finance quarterly
```

---

## Exit Codes

ragd uses standard sysexits.h codes:

| Code | Name | Meaning |
|------|------|---------|
| 0 | `EX_OK` | Success |
| 1 | `EX_GENERAL` | General/unspecified error |
| 2 | `EX_USAGE` | Incorrect command usage |
| 66 | `EX_NOINPUT` | Cannot open input file |
| 69 | `EX_UNAVAILABLE` | Service unavailable (database, Ollama) |
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

## Related Documentation

- [Getting Started Tutorial](../tutorials/01-getting-started.md) - Hands-on introduction
- [Configuration Reference](./configuration.md) - Full configuration options
- [CLI Guides](../guides/cli/README.md) - Learning path for CLI usage

---

**Status**: Reference specification for v1.0.0a5
