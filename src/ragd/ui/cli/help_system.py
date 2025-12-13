"""Enhanced help system for ragd (F-089).

Provides detailed help with examples and extended documentation.
"""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Extended help content for commands
EXTENDED_HELP: dict[str, str] = {
    "search": """
# ragd search

Search your indexed documents using natural language queries.

## Usage

```
ragd search QUERY [OPTIONS]
```

## Examples

**Basic search:**
```
ragd search "machine learning basics"
```

**Search with more results:**
```
ragd search "python errors" --limit 20
```

**JSON output for scripting:**
```
ragd search "API documentation" --format json | jq '.results[0]'
```

**Keyword-only search:**
```
ragd search "exact error message" --mode keyword
```

**Search with citations:**
```
ragd search "climate change" --cite apa
```

## Search Modes

- **hybrid** (default): Combines semantic understanding with keyword matching
- **semantic**: Pure vector similarity, best for conceptual queries
- **keyword**: Pure BM25 matching, best for exact phrases

## Tips

- Use quotes for exact phrases: `"error code 500"`
- Try different modes if results aren't relevant
- Lower `--min-score` for broader results
""",

    "index": """
# ragd index

Index documents into your knowledge base.

## Usage

```
ragd index PATH [OPTIONS]
```

## Examples

**Index a single file:**
```
ragd index document.pdf
```

**Index a directory recursively:**
```
ragd index ~/Documents/research
```

**Index with contextual embeddings:**
```
ragd index papers/ --contextual
```

**Non-recursive indexing:**
```
ragd index notes/ --no-recursive
```

## Supported Formats

- PDF (including scanned with OCR)
- Markdown (.md)
- Plain text (.txt)
- HTML (.html, .htm)

## Tips

- Use `--verbose` to see per-file progress
- Enable `--contextual` for better search quality (requires Ollama)
- Already-indexed files are skipped by default
""",

    "ask": """
# ragd ask

Get AI-generated answers from your knowledge base.

## Usage

```
ragd ask QUESTION [OPTIONS]
```

## How It Works

1. Retrieves relevant document chunks (like `search`)
2. Sends chunks + your question to an Ollama LLM
3. Generates an answer grounded in your documents
4. Returns the answer with source citations

## Examples

**Basic question:**
```
ragd ask "What are the main findings?"
```

**With a specific model:**
```
ragd ask "Summarise the methodology" --model llama3.2:8b
```

**Enable agentic mode for complex questions:**
```
ragd ask "What security measures are recommended?" --agentic
```

**Show confidence score:**
```
ragd ask "What is the conclusion?" --show-confidence
```

**Without citations:**
```
ragd ask "Brief summary" --cite none
```

## Agentic Mode

With `--agentic`, ragd uses advanced techniques:

- **CRAG (Corrective RAG)**: Evaluates if retrieved documents are relevant.
  If not, rewrites the query and retrieves again.
- **Self-RAG**: Assesses if the answer is faithful to the sources.
  If confidence is low, refines the answer.

Use agentic mode when:
- The question is complex or ambiguous
- You need high confidence in accuracy
- Initial results seem poor

## Difference from search and chat

| Command | Returns | Multi-turn | LLM Required |
|---------|---------|------------|--------------|
| `search` | Raw document excerpts | No | No |
| `ask` | AI-generated answer | No | Yes |
| `chat` | Conversation | Yes | Yes |

## Tips

- Use `--cite numbered` for source references
- Use `--verbose` to see retrieval progress
- Try `--agentic` for complex questions
- Adjust `--temperature` for more/less creative answers
""",

    "chat": """
# ragd chat

Start an interactive chat session with your knowledge base.

## Usage

```
ragd chat [OPTIONS]
```

## Examples

**Start a chat:**
```
ragd chat
```

**Chat with citations:**
```
ragd chat --cite numbered
```

## Chat Commands

While in chat mode:
- Type your question and press Enter
- Use `/help` for available commands
- Use `/clear` to clear history
- Use `/quit` or Ctrl+C to exit

## Tips

- The chat maintains conversation history for context
- Citations help verify information sources
- Use specific questions for better answers
""",

    "config": """
# ragd config

Manage ragd configuration.

## Usage

```
ragd config [OPTIONS]
```

## Examples

**Show current configuration:**
```
ragd config --show
```

**Show config file path:**
```
ragd config --path
```

**Validate configuration:**
```
ragd config --validate
```

**Show effective config with defaults:**
```
ragd config show --effective
```

**Show only changed values:**
```
ragd config show --diff
```

**Interactive configuration:**
```
ragd config --interactive
```

**Migrate configuration:**
```
ragd config migrate --dry-run
ragd config migrate
```

## Tips

- Use `--effective` to see all values including defaults
- Use `--diff` to see only your customisations
- Run `migrate --dry-run` before actual migration
""",

    "status": """
# ragd status

Show ragd status and basic statistics.

## Usage

```
ragd status [OPTIONS]
```

## Examples

**Quick status check:**
```
ragd status
```

**JSON output:**
```
ragd status --format json
```

## Information Shown

- Number of indexed documents
- Number of chunks
- Storage location
- Configuration file path
- Encryption status

## Related Commands

- `ragd stats` - Detailed statistics
- `ragd doctor` - Health checks
""",

    "doctor": """
# ragd doctor

Run health checks on ragd components.

## Usage

```
ragd doctor [OPTIONS]
```

## Examples

**Run all checks:**
```
ragd doctor
```

**JSON report:**
```
ragd doctor --format json
```

## Checks Performed

- Configuration validity
- Data directory accessibility
- Database integrity
- Embedding model availability
- Ollama connectivity (if configured)

## Tips

- Run after installation to verify setup
- Run if experiencing issues
- Check output for specific fix suggestions
""",
}


def show_extended_help(command: str, console: Console | None = None) -> bool:
    """Show extended help for a command.

    Args:
        command: Command name
        console: Rich console for output

    Returns:
        True if help was found and displayed
    """
    con = console or Console()

    help_text = EXTENDED_HELP.get(command.lower())

    if not help_text:
        con.print(f"[yellow]No extended help available for '{command}'[/yellow]")
        con.print("\nAvailable topics:")
        for cmd in sorted(EXTENDED_HELP.keys()):
            con.print(f"  ragd help {cmd}")
        return False

    con.print(Markdown(help_text.strip()))
    return True


def show_examples(command: str, console: Console | None = None) -> bool:
    """Show only examples for a command.

    Args:
        command: Command name
        console: Rich console for output

    Returns:
        True if examples were found and displayed
    """
    con = console or Console()

    help_text = EXTENDED_HELP.get(command.lower())

    if not help_text:
        con.print(f"[yellow]No examples available for '{command}'[/yellow]")
        return False

    # Extract examples section
    lines = help_text.strip().split("\n")
    in_examples = False
    examples: list[str] = []

    for line in lines:
        if line.startswith("## Examples"):
            in_examples = True
            examples.append(f"# {command} Examples\n")
        elif in_examples:
            if line.startswith("## ") and "Example" not in line:
                break
            examples.append(line)

    if examples:
        con.print(Markdown("\n".join(examples)))
        return True

    con.print(f"[yellow]No examples section found for '{command}'[/yellow]")
    return False


def list_help_topics(console: Console | None = None) -> None:
    """List all available help topics.

    Args:
        console: Rich console for output
    """
    con = console or Console()

    con.print(Panel("[bold]ragd Help Topics[/bold]", border_style="blue"))
    con.print()

    for command in sorted(EXTENDED_HELP.keys()):
        # Get first line of description
        help_text = EXTENDED_HELP[command].strip()
        first_line = ""
        for line in help_text.split("\n"):
            if line and not line.startswith("#"):
                first_line = line.strip()
                break

        con.print(f"  [cyan]{command}[/cyan] - {first_line}")

    con.print()
    con.print("Use [bold]ragd help <topic>[/bold] for detailed information")
    con.print("Use [bold]ragd <command> --help[/bold] for command options")
