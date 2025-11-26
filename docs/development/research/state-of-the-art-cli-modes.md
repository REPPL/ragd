# State-of-the-Art CLI Design: User & Expert Modes

## Executive Summary

**Key Recommendations for ragd:**

1. **Porcelain + Plumbing Pattern** - High-level user commands with stable output, low-level scriptable commands for experts
2. **Progressive Disclosure** - Reveal complexity gradually; defaults that "just work" with full control available
3. **Configuration Hierarchy** - Flags > Environment > Config file > Defaults (standard precedence)
4. **Graduated Verbosity** - `-q` (quiet) → default → `-v` → `-vv` → `-vvv` (debug)
5. **Smart Defaults with Override** - Detect context automatically, always allow explicit control

---

## The Dual-Interface Challenge

### User Personas

| Persona | Goals | Preferred Interface |
|---------|-------|---------------------|
| **Beginner** | Quick results, minimal learning | Simple commands, sensible defaults |
| **Regular User** | Efficient workflows, some customisation | Core commands with common options |
| **Power User** | Full control, automation | All options, scripting support |
| **Developer/Integrator** | Programmatic access, stable API | Plumbing commands, JSON output |

### The Git Model

Git pioneered the **porcelain/plumbing** dual-interface pattern:

**Porcelain** (user-facing):
- Human-readable output
- Sensible defaults
- Output format may change between versions
- Examples: `git status`, `git log`, `git commit`

**Plumbing** (script-facing):
- Machine-parseable output
- Stable interface across versions
- Full control over behaviour
- Examples: `git rev-parse`, `git update-index`, `git cat-file`

**Key Insight:** The same data is accessible through both interfaces, but the presentation and stability guarantees differ.

**Source:** [Git - Plumbing and Porcelain](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)

---

## Progressive Disclosure Patterns

### The Principle

> "Show people the basics first, and once they understand that, allow them to get to the expert features." - Jakob Nielsen

### Implementation Levels

```
Level 0: Zero Configuration
├─ Works out of the box
├─ Intelligent defaults
└─ No required setup

Level 1: Essential Commands (4-6 commands)
├─ Core functionality
├─ Learn in 15 minutes
└─ Covers 80% of use cases

Level 2: Common Options
├─ Frequently-used flags
├─ Output customisation
└─ Basic filtering

Level 3: Advanced Features
├─ Full configuration
├─ Debugging tools
└─ Performance tuning

Level 4: Plumbing/Scripting
├─ Machine-readable output
├─ Low-level operations
└─ Stable API contract
```

### Practical Example

```bash
# Level 0: Just works
ragd search "What is machine learning?"

# Level 1: Essential option
ragd search "What is ML?" --sources

# Level 2: Common customisation
ragd search "What is ML?" --sources --limit 5 --format markdown

# Level 3: Advanced control
ragd search "What is ML?" \
  --model llama3:8b \
  --temperature 0.7 \
  --retriever hybrid \
  --rerank true

# Level 4: Plumbing for scripts
ragd retrieve --query "machine learning" --format json | \
  jq '.chunks[].text' | \
  ragd generate --stdin --format json
```

**Source:** [Command Line Interface Guidelines](https://clig.dev/)

---

## Porcelain vs Plumbing Architecture

### Command Categories

| Category | Audience | Output Stability | Features |
|----------|----------|------------------|----------|
| **Porcelain** | Humans | May change | Colour, progress, hints |
| **Porcelain --porcelain** | Scripts | Stable subset | Parseable, no decoration |
| **Plumbing** | Integrators | Stable API | JSON, minimal, raw |

### Implementation Pattern

```python
import typer
from enum import Enum
from rich.console import Console

class OutputMode(Enum):
    RICH = "rich"       # Human-friendly, colours, progress
    PORCELAIN = "porcelain"  # Stable, parseable, no decoration
    JSON = "json"       # Machine-readable

app = typer.Typer()
console = Console()

@app.command()
def status(
    porcelain: bool = typer.Option(False, "--porcelain", help="Machine-readable output"),
    json_output: bool = typer.Option(False, "--json", help="JSON output")
):
    """Show ragd status (porcelain command)."""

    # Determine output mode
    if json_output:
        mode = OutputMode.JSON
    elif porcelain:
        mode = OutputMode.PORCELAIN
    else:
        mode = OutputMode.RICH

    # Get data (same regardless of mode)
    stats = get_status_data()

    # Render based on mode
    if mode == OutputMode.JSON:
        print(json.dumps(stats, indent=2))
    elif mode == OutputMode.PORCELAIN:
        # Stable, parseable format
        print(f"documents\t{stats['document_count']}")
        print(f"chunks\t{stats['chunk_count']}")
        print(f"index_size\t{stats['index_size_bytes']}")
    else:
        # Rich human output
        console.print(f"[bold]Documents:[/bold] {stats['document_count']}")
        console.print(f"[bold]Chunks:[/bold] {stats['chunk_count']}")
        console.print(f"[bold]Index Size:[/bold] {humanize_bytes(stats['index_size_bytes'])}")
```

### Separate Plumbing Commands

```python
# Plumbing commands in separate module
plumbing = typer.Typer(name="plumbing", hidden=True)

@plumbing.command()
def hash_document(
    path: Path,
    algorithm: str = "sha256"
) -> None:
    """Compute document hash (plumbing command)."""
    # Always outputs raw hash, no decoration
    print(compute_hash(path, algorithm))

@plumbing.command()
def embed_text(
    text: str = typer.Option(..., "--text"),
    model: str = typer.Option("nomic-embed-text-v1.5", "--model")
) -> None:
    """Generate embedding for text (plumbing command)."""
    embedding = generate_embedding(text, model)
    print(json.dumps({"embedding": embedding.tolist()}))

# Mount plumbing under main app
app.add_typer(plumbing, name="plumbing")
```

**Source:** [What does the term "porcelain" mean in Git?](https://stackoverflow.com/questions/6976473/what-does-the-term-porcelain-mean-in-git)

---

## Verbosity Control

### Standard Verbosity Levels

| Level | Flags | Use Case | Output |
|-------|-------|----------|--------|
| **Silent** | `--silent` | Cron jobs, CI | Nothing (even errors) |
| **Quiet** | `-q`, `--quiet` | Scripts | Errors only |
| **Normal** | (default) | Interactive | Essential info |
| **Verbose** | `-v` | Debugging | Detailed progress |
| **Very Verbose** | `-vv` | Troubleshooting | Debug messages |
| **Debug** | `-vvv`, `--debug` | Development | All internal state |

### Implementation

```python
import logging
from enum import IntEnum

class Verbosity(IntEnum):
    SILENT = -2
    QUIET = -1
    NORMAL = 0
    VERBOSE = 1
    VERY_VERBOSE = 2
    DEBUG = 3

def configure_verbosity(verbose: int = 0, quiet: bool = False, debug: bool = False):
    """Map CLI flags to logging level."""
    if debug:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        # Map -v, -vv, -vvv to INFO, DEBUG levels
        base_level = logging.WARNING  # 30
        level = max(logging.DEBUG, base_level - (verbose * 10))

    logging.basicConfig(level=level)

# Usage with Typer
@app.callback()
def main(
    verbose: int = typer.Option(0, "-v", "--verbose", count=True,
                                help="Increase verbosity (-v, -vv, -vvv)"),
    quiet: bool = typer.Option(False, "-q", "--quiet",
                               help="Suppress non-error output"),
    debug: bool = typer.Option(False, "--debug",
                               help="Enable debug output")
):
    """ragd - Your personal RAG assistant."""
    configure_verbosity(verbose, quiet, debug)
```

### Output Separation

```python
import sys
from rich.console import Console

# Create separate consoles for different output streams
console = Console()  # stdout - results
err_console = Console(stderr=True)  # stderr - progress, status

def run_pipeline(query: str):
    # Progress goes to stderr (doesn't interfere with piping)
    err_console.print("[dim]Retrieving documents...[/dim]")

    results = retrieve(query)

    err_console.print(f"[dim]Found {len(results)} results[/dim]")

    # Results go to stdout (can be piped)
    for result in results:
        console.print(result)
```

**Source:** [CLI Verbosity Levels - Ubuntu Guidelines](https://discourse.ubuntu.com/t/cli-verbosity-levels/26973)

---

## Configuration Hierarchy

### Standard Precedence (Highest to Lowest)

```
1. Command-line flags          (--model llama3:8b)
   ↓
2. Environment variables       (RAGD_MODEL=llama3:8b)
   ↓
3. Project config file        (./.ragd/config.yaml)
   ↓
4. User config file           (~/.ragd/config.yaml)
   ↓
5. System config file         (/etc/ragd/config.yaml)
   ↓
6. Built-in defaults          (hardcoded in application)
```

### Implementation

```python
from pathlib import Path
from dataclasses import dataclass, field
import os
import yaml

@dataclass
class Config:
    model: str = "llama3.2:3b"
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    top_k: int = 10
    temperature: float = 0.7

    @classmethod
    def load(cls, cli_overrides: dict | None = None) -> "Config":
        """Load configuration with proper precedence."""
        config = cls()  # Start with defaults

        # Load from config files (lowest to highest priority)
        for path in [
            Path("/etc/ragd/config.yaml"),
            Path.home() / ".ragd" / "config.yaml",
            Path(".ragd/config.yaml"),
        ]:
            if path.exists():
                config = cls._merge(config, cls._load_yaml(path))

        # Apply environment variables
        config = cls._apply_env(config)

        # Apply CLI overrides (highest priority)
        if cli_overrides:
            config = cls._merge(config, cli_overrides)

        return config

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def _apply_env(cls, config: "Config") -> "Config":
        """Apply RAGD_* environment variables."""
        env_mapping = {
            "RAGD_MODEL": "model",
            "RAGD_EMBEDDING_MODEL": "embedding_model",
            "RAGD_TOP_K": ("top_k", int),
            "RAGD_TEMPERATURE": ("temperature", float),
        }

        for env_var, target in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                if isinstance(target, tuple):
                    attr, converter = target
                    setattr(config, attr, converter(value))
                else:
                    setattr(config, target, value)

        return config
```

### Showing Configuration Sources

```bash
$ ragd config show --sources

Configuration:
  model: llama3:8b
    └─ source: CLI flag (--model)

  embedding_model: nomic-ai/nomic-embed-text-v1.5
    └─ source: ~/.ragd/config.yaml

  top_k: 10
    └─ source: default

  temperature: 0.8
    └─ source: environment (RAGD_TEMPERATURE)
```

**Source:** [Configuration Precedence Rules](https://app.studyraid.com/en/read/11421/357759/configuration-precedence-rules)

---

## Command Aliasing & Shortcuts

### Short Form Patterns

| Full Command | Short Alias | Purpose |
|--------------|-------------|---------|
| `ragd search` | `ragd s` | Frequent command |
| `ragd index` | `ragd i` | Frequent command |
| `ragd --verbose` | `ragd -v` | Standard flag |
| `ragd status --all` | `ragd st -a` | Combined short form |

### Resource Type Aliases (kubectl pattern)

```python
RESOURCE_ALIASES = {
    "documents": ["doc", "docs", "d"],
    "collections": ["col", "cols", "c"],
    "embeddings": ["emb", "e"],
}

def resolve_resource(name: str) -> str:
    """Resolve alias to canonical resource name."""
    for canonical, aliases in RESOURCE_ALIASES.items():
        if name == canonical or name in aliases:
            return canonical
    return name

# Usage: ragd list docs == ragd list documents
```

### Command Suggestion

```python
from difflib import get_close_matches

COMMANDS = ["search", "add", "remove", "status", "config", "doctor"]

def suggest_command(typo: str) -> str | None:
    """Suggest correction for mistyped command."""
    matches = get_close_matches(typo, COMMANDS, n=1, cutoff=0.6)
    return matches[0] if matches else None

# Output:
# $ ragd serach "query"
# Unknown command: serach
# Did you mean: search?
```

**Source:** [kubectl Aliases and Shortcuts](https://kubernetes.io/docs/reference/kubectl/)

---

## Interactive vs Batch Mode

### Mode Detection

```python
import sys

def is_interactive() -> bool:
    """Detect if running in interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()

def is_piped() -> bool:
    """Detect if output is being piped."""
    return not sys.stdout.isatty()
```

### Behaviour Adaptation

| Context | Behaviour |
|---------|-----------|
| **Interactive terminal** | Colours, progress bars, prompts |
| **Piped output** | Plain text, no colours, no prompts |
| **CI environment** | No prompts, exit codes for status |
| **--no-input flag** | Never prompt, use defaults or fail |

### Implementation

```python
@app.command()
def add(
    path: Path,
    no_input: bool = typer.Option(False, "--no-input", "-y",
                                   help="Don't prompt for confirmation"),
    force: bool = typer.Option(False, "--force", "-f",
                               help="Overwrite existing documents")
):
    """Add documents to the index."""

    existing = find_existing_documents(path)

    if existing and not force:
        if no_input or not is_interactive():
            # Non-interactive: fail with clear message
            console.print(f"[red]Error:[/red] {len(existing)} documents already exist")
            console.print("Use --force to overwrite")
            raise typer.Exit(1)
        else:
            # Interactive: prompt
            if not Confirm.ask(f"{len(existing)} documents exist. Overwrite?"):
                raise typer.Abort()

    # Proceed with add operation
    do_add(path, overwrite=force or bool(existing))
```

### Progress Indicators

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

def with_progress(operation_name: str):
    """Show progress only in interactive mode."""
    if is_interactive():
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        )
    else:
        # Return a no-op context manager for non-interactive
        from contextlib import nullcontext
        return nullcontext()

# Usage
with with_progress("Processing"):
    # Long operation
    pass
```

---

## Help System Design

### Tiered Help

```
ragd --help              # Overview of all commands
ragd search --help       # Detailed help for search command
ragd search --help-all   # Full reference including advanced options
ragd help search         # Alternative syntax
ragd help topics         # List all help topics
ragd help tutorial       # Interactive tutorial
```

### Examples-First Help

```
$ ragd search --help

Search your documents with natural language queries.

EXAMPLES:
    ragd search "machine learning"
        Search for documents about machine learning

    ragd search "neural networks" --limit 5
        Get top 5 results only

    ragd search "AI" --format json | jq '.results'
        Output as JSON for scripting

USAGE:
    ragd search <QUERY> [OPTIONS]

COMMON OPTIONS:
    --limit, -n <N>        Number of results (default: 10)
    --format <FORMAT>      Output format: rich|plain|json
    --sources, -s          Show source documents

ADVANCED OPTIONS (use --help-all for details):
    --retriever            Retrieval method
    --rerank               Enable reranking
    --threshold            Similarity threshold

MORE HELP:
    ragd search --help-all     Full option reference
    ragd help search-tips      Search query tips
    https://ragd.io/docs/search
```

### Context-Aware Suggestions

```python
@app.command()
def search(query: str = typer.Argument(None)):
    """Search documents."""

    if query is None:
        # No query provided - guide the user
        console.print("[bold]ragd search[/bold] - Search your documents\n")

        if is_interactive():
            # Interactive: prompt for query
            query = Prompt.ask("What would you like to search for?")
        else:
            # Non-interactive: show usage
            console.print("Usage: ragd search <QUERY>")
            console.print("\nExamples:")
            console.print("  ragd search 'machine learning'")
            console.print("  ragd search 'how does X work?'")
            raise typer.Exit(1)

    # Execute search
    results = do_search(query)

    # Show results and next steps
    display_results(results)

    if is_interactive():
        console.print("\n[dim]Tip: Use --sources to see source documents[/dim]")
```

**Source:** [Top 3 Design Principles for CLI UX](https://relay.sh/blog/command-line-ux-in-2020/)

---

## Recommended Architecture for ragd

### Command Structure

```
ragd
├── search <query>        # Porcelain: Search and answer questions (primary command)
├── index <path>          # Porcelain: Index documents
├── remove <path>         # Porcelain: Remove from index
├── status                # Porcelain: Show system status
├── config                # Configuration management
│   ├── show              # Display current config
│   ├── set <key> <value> # Set config value
│   └── reset             # Reset to defaults
├── doctor                # Health check
├── models                # Model management
│   ├── list              # List available models
│   ├── pull <model>      # Download model
│   └── remove <model>    # Remove model
└── plumbing              # Low-level commands (hidden by default)
    ├── embed <text>      # Generate embedding
    ├── retrieve <query>  # Raw retrieval
    ├── generate          # Raw generation
    └── hash <path>       # Document hash
```

### Mode Configurations

```yaml
# Default mode (beginner-friendly)
defaults:
  output_format: rich
  verbosity: normal
  prompts: auto  # Prompt in interactive, fail in non-interactive
  suggestions: true
  colours: auto

# Expert mode (full control)
expert:
  output_format: json
  verbosity: quiet
  prompts: never
  suggestions: false
  colours: false
```

### CLI Flag Reference

```python
# Global options (available on all commands)
@app.callback()
def main(
    # Output control
    format: OutputFormat = typer.Option(OutputFormat.RICH, "--format",
        help="Output format: rich|plain|json"),
    no_color: bool = typer.Option(False, "--no-color",
        help="Disable colour output"),

    # Verbosity
    verbose: int = typer.Option(0, "-v", "--verbose", count=True,
        help="Increase verbosity"),
    quiet: bool = typer.Option(False, "-q", "--quiet",
        help="Minimal output"),
    debug: bool = typer.Option(False, "--debug",
        help="Debug output"),

    # Interaction
    no_input: bool = typer.Option(False, "--no-input", "-y",
        help="Never prompt, use defaults"),

    # Configuration
    config_file: Path = typer.Option(None, "--config",
        help="Config file path"),

    # Mode shortcuts
    porcelain: bool = typer.Option(False, "--porcelain",
        help="Machine-readable output"),
):
    """ragd - Your personal RAG assistant."""
    pass
```

---

## Case Studies: CLI Complexity Management

### kubectl

**What works:**
- Verb-resource pattern (`kubectl get pods`, `kubectl delete service`)
- Resource aliases (`pods` → `po`, `services` → `svc`)
- Output formats (`-o json`, `-o yaml`, `-o wide`)
- Context/namespace management

**Lessons for ragd:**
- Consistent command structure
- Meaningful aliases for power users
- Multiple output formats for different use cases

### Docker

**What works:**
- Simple commands for common tasks (`docker run`, `docker ps`)
- Compose for complex configurations
- Image/container model is intuitive

**What to avoid:**
- Some commands have become overloaded
- Legacy syntax alongside new syntax

### git

**What works:**
- Porcelain/plumbing separation
- Powerful but learnable
- Excellent documentation

**What to avoid:**
- Some commands are confusing (`git checkout` doing too many things)
- Steep learning curve for advanced features

---

## References

### CLI Design Guidelines
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/)
- [Better CLI Guide](https://bettercli.org/)
- [Relay: Command Line UX Principles](https://relay.sh/blog/command-line-ux-in-2020/)

### Progressive Disclosure
- [Nielsen Norman: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [Interaction Design Foundation: Progressive Disclosure](https://www.interaction-design.org/literature/book/the-glossary-of-human-computer-interaction/progressive-disclosure)

### Technical References
- [Git Internals: Plumbing and Porcelain](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- [Symfony Console: Verbosity Levels](https://symfony.com/doc/current/console/verbosity.html)
- [Ubuntu CLI Guidelines: Verbosity](https://discourse.ubuntu.com/t/cli-verbosity-levels/26973)

---

## Related Documentation

- [CLI Best Practices](./cli-best-practices.md) - General CLI design principles
- [State-of-the-Art Setup UX](./state-of-the-art-setup-ux.md) - Installation experience
- [ADR-0005: CLI Design Principles](../decisions/adrs/0005-cli-design-principles.md) - Architecture decision
- [F-001: CLI Framework](../features/planned/F-001-cli-framework.md) - Feature specification

---

**Status:** Research complete
