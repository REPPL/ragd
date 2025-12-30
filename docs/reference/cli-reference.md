# CLI Reference

Complete command reference for ragd v1.0.9.

## Synopsis

```
ragd [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version and exit |
| `--admin` | | Show administration commands (see [Admin Mode](#admin-mode)) |
| `--help` | | Show help and exit |

### Admin Mode

ragd has additional commands for advanced users that are hidden by default. To access them:

```bash
# Using the flag
ragd --admin --help

# Using environment variable
RAGD_ADMIN=1 ragd --help
```

Admin-only commands include: `config`, `doctor`, `lock`, `unlock`, `delete`, `compare`, `evaluate`, `quality`, and command groups: `tier`, `library`, `backend`, `models`, `password`, `session`, `watch`, `audit`, `profile`, `migrate`.

### Per-Command Options

Most commands support these common options:

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format: `rich`, `plain`, `json` | `rich` |
| `--no-color` | | Disable colour output | `false` |

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
| [`inspect`](#ragd-inspect) | Inspect the index for troubleshooting |
| [`list`](#ragd-list) | List documents in the knowledge base |
| [`delete`](#ragd-delete) | Delete documents from the knowledge base |

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

### Configuration

| Command | Description |
|---------|-------------|
| [`prompts`](#ragd-prompts) | Manage prompt templates |

### Administration (Admin Mode)

These commands require `--admin` flag or `RAGD_ADMIN=1` environment variable:

| Command | Description |
|---------|-------------|
| [`config`](#ragd-config) | Manage ragd configuration |
| [`doctor`](#ragd-doctor) | Run health checks on components |
| [`lock`](#ragd-lock) | Lock the encrypted database |
| [`unlock`](#ragd-unlock) | Unlock the encrypted database |
| [`compare`](#ragd-compare) | Compare search/retrieval methods |
| [`evaluate`](#ragd-evaluate) | Evaluate RAG performance |
| [`quality`](#ragd-quality) | Check document quality |
| [`watch`](#ragd-watch) | Watch folders for automatic indexing |
| [`models`](#ragd-models) | Manage LLM models |
| [`backend`](#ragd-backend) | Manage vector store backends |
| [`tier`](#ragd-tier) | Manage data sensitivity tiers |
| [`library`](#ragd-library) | Manage tag library |
| [`password`](#ragd-password) | Manage encryption password |
| [`session`](#ragd-session) | Manage encryption session |
| [`audit`](#ragd-audit) | View operation audit log |
| [`profile`](#ragd-profile) | Profile performance |
| [`migrate`](#ragd-migrate) | Migrate between backends |

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

### ragd doctor

Run health checks on ragd components.

> **Note:** This is an admin command. Use `ragd --admin doctor` or set `RAGD_ADMIN=1`.

```
ragd --admin doctor [OPTIONS]
```

**Description:**

Validates configuration, storage, embedding model, and dependencies. Use this command to diagnose issues with your ragd installation.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin doctor              # Run all health checks
ragd --admin doctor -f json      # JSON output for scripting
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

### ragd inspect

Inspect the index for troubleshooting.

```
ragd inspect [OPTIONS]
```

**Description:**

Use this command to understand what's in your index, find duplicates, or investigate why files are being skipped during indexing.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--hashes` | `-H` | Show content hashes | `false` |
| `--duplicates` | `-d` | Find duplicate content | `false` |
| `--explain` | `-e` | Explain why a file would be skipped | |
| `--limit` | `-n` | Maximum documents to show | `100` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd inspect                     # Show index overview
ragd inspect --hashes            # Include content hashes
ragd inspect --duplicates        # Find duplicate content
ragd inspect --explain file.pdf  # Why would this be skipped?
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

### ragd delete

Delete documents from the knowledge base.

```
ragd delete <DOCUMENT_ID> [OPTIONS]
```

**Description:**

Permanently removes a document and all its chunks from the knowledge base.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `DOCUMENT_ID` | Document ID to delete | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--force` | `-f` | Skip confirmation prompt | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd delete doc-123              # Delete with confirmation
ragd delete doc-123 --force      # Delete without confirmation
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

### ragd prompts

Manage prompt templates.

```
ragd prompts <COMMAND> [OPTIONS]
```

**Description:**

View, export, and customise the prompt templates used by ragd for RAG, agentic processing, metadata extraction, and evaluation.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | List available prompt templates |
| `export` | Export default prompts for customisation |
| `show` | Show content of a specific prompt |

**ragd prompts list:**

| Option | Short | Description |
|--------|-------|-------------|
| `--category` | `-c` | Filter by category (rag, agentic, metadata, evaluation) |
| `--status` | `-s` | Show customisation status |

**ragd prompts export:**

| Option | Short | Description |
|--------|-------|-------------|
| `--category` | `-c` | Export only this category |
| `--output` | `-o` | Output directory (default: `~/.ragd/prompts`) |
| `--overwrite` | `-f` | Overwrite existing files |

**ragd prompts show:**

| Argument | Description |
|----------|-------------|
| `NAME` | Prompt name (e.g., `rag/answer`, `agentic/relevance_eval`) |

**Examples:**

```bash
ragd prompts list                      # List all prompts
ragd prompts list --category rag       # List RAG prompts only
ragd prompts list --status             # Show customisation status
ragd prompts export                    # Export all prompts
ragd prompts export --category rag     # Export only RAG prompts
ragd prompts show rag/answer           # Show specific prompt content
```

---

### ragd watch

Watch folders for automatic indexing.

> **Note:** This is an admin command. Use `ragd --admin watch` or set `RAGD_ADMIN=1`.

```
ragd --admin watch <COMMAND> [OPTIONS]
```

**Description:**

Monitors directories for file changes and automatically indexes new or modified documents. Requires the `watchdog` package.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `start` | Start watching folders |
| `stop` | Stop the watch daemon |
| `status` | Show watch daemon status |

**ragd watch start:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--pattern` | `-p` | File patterns to watch (e.g., `*.pdf`) | `*.pdf,*.md,*.txt,*.html` |
| `--exclude` | `-e` | Patterns to exclude | `node_modules,.git,venv` |
| `--debounce` | `-d` | Seconds to wait before indexing | `5` |
| `--daemon` | | Run in background | `false` |

**Examples:**

```bash
ragd watch start ~/Documents              # Watch a directory
ragd watch start ~/PDFs --pattern "*.pdf" # Watch only PDFs
ragd watch start ~/Docs --daemon          # Run in background
ragd watch status                         # Check if running
ragd watch stop                           # Stop watching
```

---

### ragd models

Manage LLM models for chat and ask commands.

> **Note:** This is an admin command. Use `ragd --admin models` or set `RAGD_ADMIN=1`.

```
ragd --admin models <COMMAND> [OPTIONS]
```

**Description:**

View, configure, and discover LLM models available through Ollama.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | List available models |
| `show` | Show model details |
| `set` | Set the default model |
| `recommend` | Get model recommendations for your hardware |
| `discover` | Discover new models from Ollama |
| `cards` | View model cards |

**Examples:**

```bash
ragd models list                   # List available models
ragd models show llama3.2          # Show model details
ragd models set llama3.2:8b        # Set default model
ragd models recommend              # Get hardware-based recommendations
ragd models discover               # Find new models
```

---

### ragd config

Manage ragd configuration.

> **Note:** This is an admin command. Use `ragd --admin config` or set `RAGD_ADMIN=1`.

```
ragd --admin config [OPTIONS]
```

**Description:**

View, validate, and modify ragd configuration. Supports interactive wizard mode for guided configuration.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--show` | `-s` | Show current configuration | `false` |
| `--path` | `-p` | Show configuration file path | `false` |
| `--validate` | `-v` | Validate configuration and detect issues | `false` |
| `--effective` | `-e` | Show effective config with defaults | `false` |
| `--diff` | `-d` | Show only non-default values | `false` |
| `--source` | | Show config value sources | `false` |
| `--interactive` | `-i` | Interactive configuration wizard | `false` |
| `--migrate` | | Migrate config to current version | `false` |
| `--dry-run` | | Show migration changes without applying | `false` |
| `--rollback` | | Rollback to previous config backup | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin config --show                 # Show config
ragd --admin config --effective            # Show with defaults
ragd --admin config --diff                 # Show customisations
ragd --admin config --interactive          # Wizard mode
ragd --admin config --migrate --dry-run    # Preview migration
```

---

### ragd lock

Lock the encrypted database.

> **Note:** This is an admin command. Use `ragd --admin lock` or set `RAGD_ADMIN=1`.

```
ragd --admin lock [OPTIONS]
```

**Description:**

Locks the encrypted database, ending the current session. Requires re-authentication to access data.

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--no-color` | Disable colour output | |

**Examples:**

```bash
ragd --admin lock    # Lock the database
```

---

### ragd unlock

Unlock the encrypted database.

> **Note:** This is an admin command. Use `ragd --admin unlock` or set `RAGD_ADMIN=1`.

```
ragd --admin unlock [OPTIONS]
```

**Description:**

Unlocks the encrypted database with password authentication, starting a new session.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--timeout` | `-t` | Session timeout in minutes | Config |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin unlock              # Unlock with default timeout
ragd --admin unlock -t 60        # Unlock with 60-minute timeout
```

---

### ragd compare

Compare search and retrieval methods.

> **Note:** This is an admin command. Use `ragd --admin compare` or set `RAGD_ADMIN=1`.

```
ragd --admin compare <QUERY> [OPTIONS]
```

**Description:**

Compare results from different search modes, models, or configurations side-by-side.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `QUERY` | Query to compare | Yes |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--modes` | `-m` | Search modes to compare | `hybrid,semantic,keyword` |
| `--limit` | `-n` | Maximum results per mode | `5` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin compare "machine learning"              # Compare all modes
ragd --admin compare "AI" --modes hybrid,semantic    # Compare specific modes
```

---

### ragd evaluate

Evaluate RAG performance.

> **Note:** This is an admin command. Use `ragd --admin evaluate` or set `RAGD_ADMIN=1`.

```
ragd --admin evaluate [OPTIONS]
```

**Description:**

Run RAGAS evaluation metrics on your RAG system to measure answer quality, faithfulness, and relevance.

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--queries` | `-q` | Path to query file (one per line) | |
| `--limit` | `-n` | Number of queries to evaluate | `10` |
| `--verbose` | `-V` | Show detailed results | `false` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin evaluate                          # Quick evaluation
ragd --admin evaluate --queries test.txt       # Evaluate from file
ragd --admin evaluate --verbose                # Detailed results
```

---

### ragd quality

Check document quality.

> **Note:** This is an admin command. Use `ragd --admin quality` or set `RAGD_ADMIN=1`.

```
ragd --admin quality [DOCUMENT_ID] [OPTIONS]
```

**Description:**

Analyse extraction quality for documents, identifying potential issues with text extraction.

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `DOCUMENT_ID` | Specific document to check | No |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--all` | `-a` | Check all documents | `false` |
| `--type` | `-t` | Filter by file type | |
| `--threshold` | | Minimum quality score (0-1) | `0.7` |
| `--format` | `-f` | Output format | `rich` |
| `--no-color` | | Disable colour output | |

**Examples:**

```bash
ragd --admin quality                     # Quick quality check
ragd --admin quality --all               # Check all documents
ragd --admin quality doc-123             # Check specific document
ragd --admin quality --type pdf          # Check only PDFs
```

---

### ragd backend

Manage vector store backends.

> **Note:** This is an admin command. Use `ragd --admin backend` or set `RAGD_ADMIN=1`.

```
ragd --admin backend <COMMAND> [OPTIONS]
```

**Description:**

Switch between vector store backends (ChromaDB, FAISS), check health, and run benchmarks.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `show` | Show current backend |
| `list` | List available backends |
| `set` | Set the active backend |
| `health` | Check backend health |
| `benchmark` | Run performance benchmark |

**Examples:**

```bash
ragd --admin backend show                # Show current backend
ragd --admin backend list                # List available backends
ragd --admin backend set faiss           # Switch to FAISS
ragd --admin backend health              # Check health
ragd --admin backend benchmark           # Run benchmark
```

---

### ragd tier

Manage data sensitivity tiers.

> **Note:** This is an admin command. Use `ragd --admin tier` or set `RAGD_ADMIN=1`.

```
ragd --admin tier <COMMAND> [OPTIONS]
```

**Description:**

Assign and manage data sensitivity tiers for documents (public, internal, confidential, restricted).

**Subcommands:**

| Command | Description |
|---------|-------------|
| `show` | Show document tier |
| `set` | Set document tier |
| `list` | List documents by tier |
| `promote` | Promote to higher tier |
| `demote` | Demote to lower tier |
| `summary` | Show tier summary |

**Examples:**

```bash
ragd --admin tier show doc-123           # Show document tier
ragd --admin tier set doc-123 confidential  # Set tier
ragd --admin tier list --tier restricted # List restricted docs
ragd --admin tier summary                # Tier overview
```

---

### ragd library

Manage tag library.

> **Note:** This is an admin command. Use `ragd --admin library` or set `RAGD_ADMIN=1`.

```
ragd --admin library <COMMAND> [OPTIONS]
```

**Description:**

Manage the curated tag library for consistent tagging across documents.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `show` | Show library contents |
| `create` | Create a new tag |
| `add` | Add tag to library |
| `remove` | Remove tag from library |
| `rename` | Rename a tag |
| `delete` | Delete a tag |
| `hide` | Hide deprecated tag |
| `pending` | Show pending additions |
| `promote` | Promote suggestion to library |
| `validate` | Validate library integrity |
| `stats` | Show library statistics |

**Examples:**

```bash
ragd --admin library show                # View library
ragd --admin library create "topic:ai"   # Create new tag
ragd --admin library stats               # View statistics
```

---

### ragd password

Manage encryption password.

> **Note:** This is an admin command. Use `ragd --admin password` or set `RAGD_ADMIN=1`.

```
ragd --admin password <COMMAND> [OPTIONS]
```

**Description:**

Change or reset the encryption password for the secure database.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `change` | Change password |
| `reset` | Reset password (requires recovery key) |

**Examples:**

```bash
ragd --admin password change             # Change password
ragd --admin password reset              # Reset with recovery key
```

---

### ragd session

Manage encryption session.

> **Note:** This is an admin command. Use `ragd --admin session` or set `RAGD_ADMIN=1`.

```
ragd --admin session <COMMAND> [OPTIONS]
```

**Description:**

View and manage the current encryption session.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `status` | Show session status |

**Examples:**

```bash
ragd --admin session status              # View session info
```

---

### ragd audit

View operation audit log.

> **Note:** This is an admin command. Use `ragd --admin audit` or set `RAGD_ADMIN=1`.

```
ragd --admin audit <COMMAND> [OPTIONS]
```

**Description:**

View the audit trail of operations performed on the knowledge base.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | List audit entries |
| `show` | Show audit entry details |
| `stats` | Show audit statistics |
| `clear` | Clear old audit entries |

**Examples:**

```bash
ragd --admin audit list                  # List recent entries
ragd --admin audit list --limit 50       # More entries
ragd --admin audit stats                 # View statistics
ragd --admin audit clear --older-than 30 # Clear entries older than 30 days
```

---

### ragd profile

Profile performance.

> **Note:** This is an admin command. Use `ragd --admin profile` or set `RAGD_ADMIN=1`.

```
ragd --admin profile <COMMAND> [OPTIONS]
```

**Description:**

Profile ragd operations to identify performance bottlenecks.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `index` | Profile indexing |
| `search` | Profile search |
| `chat` | Profile chat |
| `startup` | Profile startup time |
| `all` | Run all profiles |
| `compare` | Compare profile results |

**Examples:**

```bash
ragd --admin profile search "test query" # Profile search
ragd --admin profile index ~/Documents   # Profile indexing
ragd --admin profile startup             # Profile startup
ragd --admin profile all                 # All profiles
```

---

### ragd migrate

Migrate between backends.

> **Note:** This is an admin command. Use `ragd --admin migrate` or set `RAGD_ADMIN=1`.

```
ragd --admin migrate <COMMAND> [OPTIONS]
```

**Description:**

Migrate data between vector store backends or schema versions.

**Subcommands:**

| Command | Description |
|---------|-------------|
| `status` | Show migration status |
| (default) | Run migration |

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--from` | | Source backend | Current |
| `--to` | | Target backend | |
| `--dry-run` | | Preview without migrating | `false` |
| `--force` | `-f` | Skip confirmation | `false` |

**Examples:**

```bash
ragd --admin migrate status              # Check status
ragd --admin migrate --to faiss          # Migrate to FAISS
ragd --admin migrate --dry-run           # Preview migration
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
| `RAGD_ADMIN` | Enable admin commands (`1`, `true`, or `yes`) | |
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

**Status**: Reference specification for v1.0.9
