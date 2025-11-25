# ADR-0001: Use Typer + Rich for CLI

## Status

Accepted

## Context

ragd needs a command-line interface as its primary user interaction method. The CLI must be:
- Easy to use for non-technical users
- Beautiful and informative in output
- Type-safe for maintainability
- Well-documented automatically

Several Python CLI frameworks exist with different trade-offs.

## Decision

Use **Typer** for command structure with **Rich** for terminal output.

### Typer

Typer provides:
- Type hints for argument/option validation
- Automatic help generation
- Intuitive command structure
- Click compatibility for advanced features

### Rich

Rich provides:
- Coloured and styled output
- Progress bars for long operations
- Tables for structured data
- Panels for information blocks

### Example Usage

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def search(query: str, limit: int = 10):
    """Search the knowledge base."""
    results = perform_search(query, limit)

    table = Table(title="Search Results")
    table.add_column("Score", style="green")
    table.add_column("Document")
    table.add_column("Content")

    for result in results:
        table.add_row(str(result.score), result.doc, result.content)

    console.print(table)
```

## Consequences

### Positive

- Beautiful, professional CLI output
- Type safety catches errors early
- Automatic documentation generation
- Familiar patterns (Click-based)
- Excellent learning resources available
- Proven in production (FastAPI ecosystem)

### Negative

- Requires Python 3.7+ (we require 3.12, so not an issue)
- Additional dependencies
- Learning curve for Rich's formatting API

## Alternatives Considered

### argparse (stdlib)

- **Pros:** No dependencies, well-known
- **Cons:** Verbose, limited output formatting, no type hints
- **Rejected:** Too basic for good UX

### Click

- **Pros:** Powerful, well-established
- **Cons:** More verbose than Typer, decorators feel dated
- **Rejected:** Typer provides better DX on top of Click

### Fire

- **Pros:** Minimal code, automatic CLI from functions
- **Cons:** Less control, magic behaviour, limited customisation
- **Rejected:** Too magical, limited output control

### Textual

- **Pros:** Full TUI capabilities
- **Cons:** Overkill for CLI, heavy dependency
- **Rejected:** CLI-first, TUI later if needed

## Related Documentation

- [Feature Specifications](../../features/)
- [ragged Analysis](../../lineage/ragged-analysis.md) - Lessons from predecessor

