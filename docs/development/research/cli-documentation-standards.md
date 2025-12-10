# CLI Documentation Standards Research

State-of-the-art CLI reference documentation patterns for Typer + Rich applications.

## Executive Summary

This research synthesises best practices for CLI reference documentation from leading tools (git, kubectl, docker, GitHub CLI) and modern frameworks (Typer, Rich, MkDocs). Key findings:

1. **Progressive Disclosure**: Documentation at multiple levels (--help, man pages, web docs)
2. **Format Conventions**: Standardised syntax notation for arguments, options, and commands
3. **Output Mode Documentation**: Clear guidance for multiple formats (rich/plain/JSON)
4. **Error Documentation**: Exit codes, error patterns, and recovery guidance
5. **Auto-Generation**: Tools exist for generating docs from Typer code

**Recommended Approach**: Three-tier documentation (inline --help, man page format, web reference) with auto-generation where possible.

---

## 1. Reference Documentation Architecture

### Three-Tier Documentation Model

Modern CLIs provide documentation at three levels:

| Tier | Access Method | Content | Target User |
|------|---------------|---------|-------------|
| **Quick Reference** | `--help` | Usage, common options, examples | Active terminal users |
| **Man Page** | `man command` or `command --help-all` | Complete syntax, all options, detailed descriptions | Power users, scripters |
| **Web Reference** | Documentation site | Searchable, cross-linked, tutorials + reference | All users, learners |

**Sources**:
- [Command Line Interface Guidelines](https://clig.dev/)
- [kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/)
- [git man pages](https://man7.org/linux/man-pages/man1/git.1.html)

### Progressive Disclosure Pattern

Documentation reveals complexity gradually:

```
--help           → 5-10 most common options, 2-3 examples
--help-all       → Complete option list, all flags
man page         → Detailed descriptions, exit codes, examples
web reference    → Tutorials, troubleshooting, cross-references
```

**Source**: [Progressive Disclosure - NN/g](https://www.nngroup.com/articles/progressive-disclosure/)

---

## 2. Man Page Conventions

### Standard Section Structure

Man pages follow a predictable structure defined in IEEE Std 1003.1 (POSIX):

| Section | Required | Content |
|---------|----------|---------|
| **NAME** | ✅ | Command name and one-line description |
| **SYNOPSIS** | ✅ | Command syntax with all argument patterns |
| **DESCRIPTION** | ✅ | Detailed explanation of functionality |
| **OPTIONS** | ✅ | All flags and arguments with descriptions |
| **EXIT STATUS** | Recommended | Exit codes and their meanings |
| **EXAMPLES** | Recommended | Common use cases with sample commands |
| **ENVIRONMENT** | Optional | Environment variables affecting behaviour |
| **FILES** | Optional | Configuration files and their locations |
| **SEE ALSO** | Optional | Related commands and documentation |
| **BUGS** | Optional | Known limitations or how to report issues |

**Sources**:
- [man-pages(7) - Linux manual page](https://man7.org/linux/man-pages/man7/man-pages.7.html)
- [Ubuntu Manpage conventions](https://manpages.ubuntu.com/manpages/bionic/man7/man-pages.7.html)

### Synopsis Syntax Conventions

Standard notation for command syntax:

| Convention | Meaning | Example |
|------------|---------|---------|
| **bold text** | Type exactly as shown | `ragd search` |
| *italic text* | Replace with appropriate value | `ragd search <query>` |
| `[...]` | Optional element | `ragd search [--limit N]` |
| `<...>` | Required placeholder | `ragd index <path>` |
| `...` | Repeatable element | `ragd index <path>...` |
| `a\|b` | Mutually exclusive alternatives | `--format rich\|plain\|json` |
| `{a\|b}` | Required choice | `{create\|update\|delete}` |

**Sources**:
- [Google Developer Documentation Style Guide](https://developers.google.com/style/code-syntax)
- [Stack Overflow: man page syntax conventions](https://stackoverflow.com/questions/23242493/linux-unix-man-page-syntax-conventions)

### Font and Formatting Conventions

For terminal and man page output:

- **Bold**: Command names, option names, literal text
- *Italic*: Placeholders, variable names, filenames
- Plain: Explanatory text

```
NAME
    ragd-search - search the indexed knowledge base

SYNOPSIS
    ragd search <query> [OPTIONS]

OPTIONS
    --limit, -n <N>
        Maximum number of results to return (default: 10)
```

**Source**: [man-pages(7) - font conventions](https://man7.org/linux/man-pages/man7/man-pages.7.html)

---

## 3. --help Output Best Practices

### Structure and Layout

Recommended help text structure:

```
USAGE:
    ragd search <query> [OPTIONS]

ARGUMENTS:
    <query>    Search query (natural language)

OPTIONS:
    -n, --limit <N>      Number of results [default: 10]
    -f, --format <FMT>   Output format [rich|plain|json] [default: rich]
    -h, --help           Print help
    -V, --version        Print version

EXAMPLES:
    ragd search "machine learning"
    ragd search "AI ethics" --limit 5 --format json

For more information, see: https://docs.ragd.io/cli/search
```

**Key Principles**:
1. Usage first, then arguments, then options
2. Group related options together
3. Show defaults for options
4. Align descriptions at consistent column
5. Examples section with 2-3 common patterns
6. Link to web documentation

**Sources**:
- [CLI Help pages - BetterCLI.org](https://bettercli.org/design/cli-help-page/)
- [Stack Overflow: Standard format for help text](https://stackoverflow.com/questions/9725675/is-there-a-standard-format-for-command-line-shell-help-text)

### Content Guidelines

**Do**:
- ✅ Use consistent indentation (2 spaces for content)
- ✅ Wrap text at 80 columns
- ✅ Put most common options first
- ✅ Include 2-3 practical examples
- ✅ Show default values explicitly
- ✅ Use spaces for alignment (not tabs)

**Don't**:
- ❌ Include giant walls of text
- ❌ Document every edge case
- ❌ Use inconsistent formatting
- ❌ Put advanced options in main --help
- ❌ Assume users know related commands

**Sources**:
- [Software Engineering SE: help output best practices](https://softwareengineering.stackexchange.com/questions/137451/what-is-considered-best-practice-for-printing-usage-help-help)
- [CLI tool help requirements - Fuchsia](https://fuchsia.dev/fuchsia-src/development/api/cli_help)

### Where to Output Help

**Always use stdout** (not stderr):
- Help is not an error condition
- Enables piping help through pagers or grep
- Consistent with UNIX conventions

```bash
# Good: Users can pipe help
ragd --help | grep format

# Bad: Would fail if help went to stderr
```

**Source**: [Stack Overflow: Proper formatting for --help output](https://stackoverflow.com/questions/6488026/proper-formatting-for-help-output)

---

## 4. Exemplar CLI Documentation Analysis

### Git: The Gold Standard

**Strengths**:
- Multi-level help (`git help`, `git help -a`, `git help -g`)
- Command categories (porcelain vs plumbing)
- Consistent man page structure across 150+ commands
- Cross-references between related commands
- Git-specific concepts explained in gitcli(7)

**Man Page Pattern**:
```
NAME
SYNOPSIS
DESCRIPTION
OPTIONS
    (grouped by category)
GIT
    (links to core git commands)
EXAMPLES
ENVIRONMENT VARIABLES
EXIT STATUS
SEE ALSO
```

**Key Innovation**: Command categorisation
- High-level "porcelain" commands for users
- Low-level "plumbing" commands for scripts
- Each documented separately

**Sources**:
- [git(1) manual page](https://man7.org/linux/man-pages/man1/git.1.html)
- [Git Documentation](https://git-scm.com/docs/git)

### kubectl: Hierarchical Commands

**Strengths**:
- Clear command hierarchy (verb-noun pattern)
- Auto-generated docs from source code
- Consistent format across all subcommands
- Examples for every command
- Separate reference vs tutorial documentation

**Command Structure**:
```
kubectl [flags] <command> <subcommand> [arguments]
kubectl get pods                    # verb noun
kubectl describe pod <name>         # verb noun target
```

**Documentation Architecture**:
- Generated reference docs in Markdown
- Task-oriented guides separate from reference
- Integration with web documentation
- Version-specific documentation

**Sources**:
- [kubectl Documentation](https://kubernetes.io/docs/reference/kubectl/)
- [Generating kubectl Reference Documentation](https://kubernetes.io/docs/contribute/generate-ref-docs/kubectl/)

### Docker: Clear Command Categories

**Strengths**:
- Logical command grouping (container, image, network, volume)
- Consistent option naming across commands
- Rich examples for complex commands
- Environment variable documentation
- Clear security guidance

**Documentation Pattern**:
```
docker [OPTIONS] COMMAND

Management Commands:
  container   Manage containers
  image       Manage images
  network     Manage networks

Commands:
  run         Create and run a container
  ps          List containers
```

**Key Features**:
- Options vs Management Commands distinction
- Consistent flag names (--detach, --interactive, --tty)
- JSON configuration file documentation
- Security best practices integrated

**Sources**:
- [Docker CLI Reference](https://docs.docker.com/reference/)
- [Docker command line documentation](https://docs.docker.com/reference/cli/docker/)

### GitHub CLI (gh): Modern Patterns

**Strengths**:
- Context-aware (detects current repo)
- Interactive prompts with flag alternatives
- Consistent output formats (--json flag)
- Built-in authentication flow
- Help topics beyond commands (gh help environment)

**Command Structure**:
```
gh <command> <subcommand> [flags]

Core commands:
  issue       Manage issues
  pr          Manage pull requests
  repo        Manage repositories

Additional commands:
  alias       Create command shortcuts
  api         Make API requests
```

**Innovations**:
- Help topics (exit-codes, formatting, environment)
- Extension system documented in reference
- JSON output consistently available
- Context awareness documented

**Sources**:
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub CLI Reference](https://docs.github.com/en/github-cli/github-cli/github-cli-reference)

---

## 5. Output Format Documentation

### Multi-Format Output Patterns

Modern CLIs support multiple output formats for different use cases:

| Format | Use Case | Trigger | Content |
|--------|----------|---------|---------|
| **Rich** | Interactive terminal, human reading | Default (TTY detected) | Colours, symbols, tables, progress bars |
| **Plain** | Scripts, pipes, screen readers | Auto (pipe) or `--plain` | No colour, simple text, easy to parse |
| **JSON** | Programmatic integration | `--json` or `--format json` | Machine-readable, structured data |
| **YAML** | Config-style output | `--yaml` or `--format yaml` | Human-readable structured data |
| **Table** | Dense information display | `--format table` | Aligned columns, borders |

**Sources**:
- [AWS CLI Output Formats](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html)
- [Azure CLI Output Formats](https://learn.microsoft.com/en-us/cli/azure/format-output-azure-cli)

### Documenting Format Options

**In --help text**:
```
OPTIONS:
    --format <FMT>    Output format [possible values: rich, plain, json]
                      [default: rich when TTY, plain when piped]
    --json            Shorthand for --format json
```

**In man page**:
```
OUTPUT FORMATS
    ragd supports multiple output formats to suit different use cases:

    rich (default)
        Terminal-optimised output with colour, symbols, and tables.
        Used automatically when output is to a terminal (TTY).

    plain
        Simple text output without colour or special formatting.
        Used automatically when output is piped to another command.
        Suitable for screen readers and accessibility tools.

    json
        Machine-readable JSON format for programmatic integration.
        All data included, structured for parsing by other tools.
```

**Sources**:
- [GitHub CLI help formatting](https://cli.github.com/manual/gh_help_formatting)
- [Command Line Interface Guidelines](https://clig.dev/)

### JSON Output Standards

**Format Versioning**: Include a format version for backward compatibility

```json
{
  "format_version": "1.0",
  "results": [...]
}
```

**Semantic Versioning for JSON Output**:
- Increment **minor** version for backward-compatible additions
- Increment **major** version for breaking changes
- Clients should ignore unknown fields (forward compatibility)

**Source**: [OpenTofu JSON Format](https://opentofu.org/docs/internals/json-format/)

### Automatic Format Detection

Best practice: Detect TTY and adjust output automatically

```python
import sys

if sys.stdout.isatty():
    # Rich output with colour
    use_rich_output()
else:
    # Plain text for pipes
    use_plain_output()
```

Respect environment variables:
- `NO_COLOR`: Disable colour when set
- `TERM=dumb`: Use plain output
- `CLICOLOR_FORCE`: Force colour even in pipes

**Source**: [Command Line Interface Guidelines - Output](https://clig.dev/#output)

---

## 6. Error Documentation Standards

### Exit Codes

Standard exit code conventions from sysexits.h and POSIX:

| Code | Name | Meaning | Use Case |
|------|------|---------|----------|
| 0 | `EX_OK` | Success | Command completed successfully |
| 1 | `EX_GENERAL` | General error | Default failure, unspecified error |
| 2 | `EX_USAGE` | Incorrect usage | Invalid arguments, missing required options |
| 64 | `EX_USAGE` | Command line usage error | Bad command syntax (sysexits.h) |
| 65 | `EX_DATAERR` | Data format error | Invalid input data |
| 66 | `EX_NOINPUT` | Cannot open input | Input file not found or unreadable |
| 69 | `EX_UNAVAILABLE` | Service unavailable | Required service not available |
| 70 | `EX_SOFTWARE` | Internal software error | Unexpected failure, bug |
| 73 | `EX_CANTCREAT` | Can't create output | Output file creation failed |
| 74 | `EX_IOERR` | Input/output error | I/O error during operation |
| 75 | `EX_TEMPFAIL` | Temp failure; retry | Transient failure, might succeed if retried |
| 77 | `EX_NOPERM` | Permission denied | Insufficient permissions |
| 78 | `EX_CONFIG` | Configuration error | Config file error or missing |

**Best Practices**:
1. Always return 0 for success, non-zero for failure
2. Use exit code 1 for general errors (most common)
3. Consider sysexits.h codes (64-78) for specific failures
4. Document exit codes in man page EXIT STATUS section
5. Distinguish permanent vs transient failures (for retry logic)

**Sources**:
- [Exit code best practices](https://chrisdown.name/2013/11/03/exit-code-best-practises.html)
- [Standard exit status codes in Linux](https://stackoverflow.com/questions/1101957/are-there-any-standard-exit-status-codes-in-linux)
- [gh exit-codes](https://cli.github.com/manual/gh_help_exit-codes)

### Exit Code Documentation Example

From GitHub CLI man page:

```
EXIT CODES
    0: Successful execution
    1: General error
    2: Command cancelled by user (e.g., when prompted)
    4: Authentication required or failed
```

### Error Message Best Practices

Structure every error with actionable information:

```
Error: Cannot find document "report.pdf"

Possible causes:
  • File path is incorrect
  • File not yet indexed
  • File was deleted

Suggestions:
  • Check file path: ragd index --list | grep report
  • Re-index directory: ragd index ~/Documents
  • See troubleshooting: https://docs.ragd.io/errors/file-not-found

Exit code: 66 (EX_NOINPUT)
```

**Error Message Components**:
1. **What**: Clear description of the error
2. **Why**: Possible causes
3. **How**: Actionable remediation steps
4. **Where**: Link to documentation
5. **Exit code**: (optional, helpful for debugging)

**Sources**:
- [Error Handling in CLI Tools](https://medium.com/@czhoudev/error-handling-in-cli-tools-a-practical-pattern-thats-worked-for-me-6c658a9141a9)
- [Command Line Interface Guidelines - Errors](https://clig.dev/#errors)

### Logging Error Details

- **stdout**: Success messages, normal output
- **stderr**: Error messages, warnings, diagnostics
- **exit code**: Machine-readable error category

```bash
# Good separation
ragd search "test" > results.txt 2> errors.txt
echo $?  # Check exit code
```

**Source**: [Better CLI - Exit codes](https://bettercli.org/design/exit-codes/)

---

## 7. Typer + Rich Integration Patterns

### Typer Auto-Documentation Features

Typer extracts documentation from:
- Function docstrings → Command descriptions
- Parameter type hints → Argument types
- Default values → Option defaults
- `help=` parameters → Option descriptions

```python
@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
    format: str = typer.Option("rich", "--format", help="Output format")
):
    """
    Search the indexed knowledge base.

    Searches through indexed documents using semantic similarity
    to find relevant information matching the query.
    """
    pass
```

Auto-generates:
```
Usage: ragd search [OPTIONS] QUERY

  Search the indexed knowledge base.

  Searches through indexed documents using semantic similarity to find
  relevant information matching the query.

Arguments:
  QUERY  Search query  [required]

Options:
  -n, --limit INTEGER    Max results  [default: 10]
  --format TEXT          Output format  [default: rich]
  --help                 Show this message and exit.
```

**Sources**:
- [Typer Documentation](https://typer.tiangolo.com/)
- [Command Help - Typer](https://typer.tiangolo.com/tutorial/commands/help/)

### Rich Markup Mode

Enable Rich console markup for formatted help text:

```python
app = typer.Typer(rich_markup_mode="rich")

@app.command()
def search(query: str):
    """
    Search the [bold cyan]indexed knowledge base[/].

    Supports [bold]natural language queries[/] with semantic search.
    """
    pass
```

**Rich Markup Elements**:
- `[bold]text[/]` - Bold text
- `[italic]text[/]` - Italic text
- `[cyan]text[/]` - Coloured text
- `[code]text[/]` - Code formatting
- `[link=url]text[/]` - Hyperlinks (terminal-dependent)

**Source**: [Rich Markup Mode - Typer](https://typer.tiangolo.com/tutorial/commands/help/)

### Rich Help Panels

Organise help output into collapsible panels:

```python
@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(
        10,
        help="Number of results",
        rich_help_panel="Search Options"
    ),
    format: str = typer.Option(
        "rich",
        help="Output format",
        rich_help_panel="Output Options"
    )
):
    pass
```

Results in grouped help output:

```
Search Options:
  -n, --limit INTEGER    Number of results  [default: 10]

Output Options:
  --format TEXT          Output format  [default: rich]
```

**Source**: [Rich Help Panels - Typer](https://typer.tiangolo.com/tutorial/options/help/)

### Rich Console Output

Rich provides automatic styling:

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Automatic colour, tables, progress
console.print("[green]✓[/] Search complete")

table = Table(title="Search Results")
table.add_column("Document", style="cyan")
table.add_column("Score", justify="right")
console.print(table)
```

**Rich Components for CLI Output**:
- **Console**: Styled text output
- **Table**: Formatted tables
- **Progress**: Progress bars
- **Syntax**: Code highlighting
- **Tree**: Hierarchical data
- **Panel**: Boxed content

**Sources**:
- [Rich Introduction](https://rich.readthedocs.io/en/stable/introduction.html)
- [Rich Console Features](https://github.com/Textualize/rich)

---

## 8. Auto-Generating Reference Documentation

### MkDocs Plugins for Typer

Two primary plugins for auto-generating Typer documentation:

#### 1. mkdocs-typer

```yaml
# mkdocs.yml
plugins:
  - mkdocs-typer

# In docs/cli-reference.md
::: mkdocs-typer
    :module: ragd.cli
    :command: app
    :prog_name: ragd
    :depth: 2
```

**Features**:
- Generates Markdown from Typer commands
- Supports nested subcommands
- Configurable header depth
- Integrates with MkDocs site navigation

**Source**: [mkdocs-typer on PyPI](https://pypi.org/project/mkdocs-typer/)

#### 2. mkdocs-typer2

```yaml
# mkdocs.yml
plugins:
  - mkdocs-typer2:
      pretty: true

# In docs/reference.md
::: mkdocs-typer
    :module: ragd.cli
    :name: ragd
    :pretty: true
```

**Features**:
- Uses `typer utils docs` command internally
- Pretty mode with Markdown tables
- Per-directive formatting control
- Cleaner table-based option formatting

**Source**: [mkdocs-typer2 documentation](https://syn54x.github.io/mkdocs-typer2/)

### Manual vs Auto-Generated Documentation

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Manual** | Full control, custom formatting, contextual examples | Out of sync risk, maintenance burden | Tutorial docs, conceptual guides |
| **Auto-generated** | Always up-to-date, consistent formatting, less work | Less flexibility, generic content | CLI reference, option lists |
| **Hybrid** | Up-to-date reference + rich examples | Requires tooling setup | Production documentation |

**Recommendation**: Use auto-generation for CLI reference, manual docs for tutorials and guides.

---

## 9. Documentation Site Architecture

### Recommended Structure

Based on Diátaxis framework and exemplar CLIs:

```
docs/
├── index.md                    # Overview and quick links
├── getting-started/
│   ├── installation.md
│   └── first-steps.md
├── tutorials/                  # Learning-oriented
│   ├── basic-usage.md
│   └── advanced-workflows.md
├── guides/                     # Task-oriented
│   ├── searching.md
│   ├── indexing.md
│   └── troubleshooting.md
├── reference/                  # Information-oriented
│   ├── cli/
│   │   ├── ragd.md            # Root command
│   │   ├── ragd-search.md     # Subcommands
│   │   ├── ragd-index.md
│   │   └── exit-codes.md
│   ├── api/
│   └── configuration.md
└── explanation/                # Understanding-oriented
    ├── how-rag-works.md
    └── architecture.md
```

### CLI Reference Page Template

Each command gets a dedicated page:

```markdown
# ragd search

Search the indexed knowledge base using semantic similarity.

## Synopsis

```bash
ragd search <query> [OPTIONS]
```

## Description

The `search` command queries the vector database to find documents
semantically similar to the provided query. Results are ranked by
relevance score.

## Arguments

**`<query>`**
: Natural language search query (required)

## Options

**`-n, --limit <N>`**
: Maximum number of results to return
: Default: `10`

**`--format <FMT>`**
: Output format: `rich`, `plain`, or `json`
: Default: `rich` (auto-detects pipe for `plain`)

**`-h, --help`**
: Display help information

## Examples

Basic search:
```bash
ragd search "machine learning"
```

Limit results:
```bash
ragd search "AI ethics" --limit 5
```

JSON output for scripting:
```bash
ragd search "neural networks" --json | jq '.results[0]'
```

## Exit Codes

- `0`: Success
- `1`: General error
- `66`: Database not initialised (run `ragd init` first)

## See Also

- [ragd-index(1)](./ragd-index.md) - Index documents
- [ragd-status(1)](./ragd-status.md) - View database status
```

---

## 10. Implementation Recommendations for ragd

### Documentation Tiers for ragd

| Tier | Implementation | Content | Completion Target |
|------|----------------|---------|-------------------|
| **1. Inline Help** | Typer docstrings + help parameters | Usage, common options, 2-3 examples | v0.1 MVP |
| **2. Man Pages** | Generated Markdown in man(1) format | Complete syntax, all options, exit codes | v0.2 |
| **3. Web Reference** | MkDocs + mkdocs-typer2 | Auto-generated reference + tutorials | v0.3 |

### v0.1 Minimum Documentation

For MVP release, implement:

1. **Comprehensive --help for every command**
   - Clear usage line
   - Argument descriptions
   - 2-3 practical examples
   - Link to web docs

2. **README with quick reference**
   - Installation instructions
   - Essential commands table
   - Link to full documentation

3. **Error messages with exit codes**
   - Actionable error messages
   - Consistent exit codes
   - Link to troubleshooting guide

### v0.2 Enhanced Documentation

Add:

1. **Man page format documentation**
   - Complete option reference
   - EXIT STATUS section
   - ENVIRONMENT section
   - SEE ALSO cross-references

2. **Troubleshooting guide**
   - Common errors and solutions
   - Exit code reference
   - Diagnostic commands

### v0.3 Full Documentation Site

Implement:

1. **Auto-generated CLI reference**
   - mkdocs-typer2 integration
   - One page per command
   - Searchable, cross-linked

2. **Tutorial documentation**
   - Getting started guide
   - Common workflows
   - Advanced techniques

3. **Integration examples**
   - Using JSON output in scripts
   - CI/CD integration patterns
   - API integration examples

### Output Format Documentation Strategy

Document the three output modes clearly:

**In --help**:
```
--format rich|plain|json    Output format [default: auto-detect]
--json                      Shorthand for --format json
```

**In man page**:
```
OUTPUT FORMATS
    rich    Terminal-optimised with colour and formatting
    plain   Simple text, automatically used when piping
    json    Machine-readable for scripting (with format_version)
```

**In web docs**:
- Separate page explaining each format
- Examples of processing JSON output
- Guidance on when to use each format

### Accessibility Considerations

Ensure documentation addresses:

1. **Screen reader compatibility**
   - `--plain` mode documented for accessibility
   - Alt text for any visual elements in web docs
   - Keyboard navigation in web documentation

2. **Colour blindness**
   - Document that output doesn't rely solely on colour
   - Explain symbol usage (✓ ✗ ▶ etc.)

3. **Environment variables**
   - `NO_COLOR` support documented
   - `CLICOLOR_FORCE` for CI environments

---

## 11. Quality Checklist

Before releasing CLI documentation:

### Inline Help (--help)
- [ ] Every command has --help
- [ ] Usage line is clear and accurate
- [ ] Required vs optional arguments are clear
- [ ] Defaults are shown for all options
- [ ] 2-3 practical examples included
- [ ] Link to web documentation provided
- [ ] Text wraps at 80 columns
- [ ] Consistent formatting across all commands

### Man Page Format
- [ ] NAME section: one-line description
- [ ] SYNOPSIS: complete syntax with notation
- [ ] DESCRIPTION: detailed explanation
- [ ] OPTIONS: all flags documented
- [ ] EXIT STATUS: exit codes explained
- [ ] EXAMPLES: 5+ realistic examples
- [ ] SEE ALSO: cross-references to related commands
- [ ] Consistent formatting (bold/italic)

### Web Reference
- [ ] Auto-generated from source code
- [ ] One page per command
- [ ] Searchable
- [ ] Cross-linked to related pages
- [ ] Includes output format examples
- [ ] Tutorial vs reference clearly separated
- [ ] Version-specific documentation

### Output Format Documentation
- [ ] All three formats documented (rich/plain/json)
- [ ] Auto-detection behaviour explained
- [ ] JSON schema or example provided
- [ ] Format versioning strategy documented
- [ ] Examples of processing each format

### Error Documentation
- [ ] Exit codes documented
- [ ] Common errors listed with solutions
- [ ] Error messages include actionable advice
- [ ] Links to troubleshooting guide
- [ ] Transient vs permanent errors distinguished

---

## 12. Research Sources

### Primary Sources

| Source | Focus | URL |
|--------|-------|-----|
| Command Line Interface Guidelines | Comprehensive CLI design principles | [clig.dev](https://clig.dev/) |
| Google Developer Style Guide | Command-line syntax standards | [Google Style Guide](https://developers.google.com/style/code-syntax) |
| man-pages(7) | Linux manual page conventions | [man7.org](https://man7.org/linux/man-pages/man7/man-pages.7.html) |
| BetterCLI.org | Modern CLI best practices | [bettercli.org](https://bettercli.org/design/cli-help-page/) |

### Exemplar CLIs

| Tool | Documentation Strengths | Reference |
|------|------------------------|-----------|
| **git** | Multi-level help, command categorisation, comprehensive man pages | [git-scm.com/docs](https://git-scm.com/docs/git) |
| **kubectl** | Auto-generated docs, clear hierarchy, task-oriented guides | [kubernetes.io/docs/reference/kubectl](https://kubernetes.io/docs/reference/kubectl/) |
| **docker** | Command grouping, consistent options, security documentation | [docs.docker.com/reference](https://docs.docker.com/reference/) |
| **gh** | Context awareness, help topics, modern patterns | [cli.github.com/manual](https://cli.github.com/manual/) |

### Framework Documentation

| Framework | Documentation Feature | Reference |
|-----------|----------------------|-----------|
| **Typer** | Auto-help generation, Rich integration, type-based docs | [typer.tiangolo.com](https://typer.tiangolo.com/) |
| **Rich** | Terminal styling, progress bars, tables | [rich.readthedocs.io](https://rich.readthedocs.io/en/stable/introduction.html) |
| **mkdocs-typer2** | Auto-generate CLI reference for MkDocs | [syn54x.github.io/mkdocs-typer2](https://syn54x.github.io/mkdocs-typer2/) |

### Standards Documents

| Standard | Specification | Reference |
|----------|--------------|-----------|
| IEEE Std 1003.1 | POSIX utility conventions | Referenced in man pages |
| sysexits.h | Standard exit codes (64-78) | Unix standard header |
| NO_COLOR | Environment variable for colour suppression | Community standard |

### Additional Resources

| Topic | Source | URL |
|-------|--------|-----|
| Exit code best practices | Chris Down | [chrisdown.name](https://chrisdown.name/2013/11/03/exit-code-best-practises.html) |
| Error handling patterns | Medium article | [Error Handling in CLI Tools](https://medium.com/@czhoudev/error-handling-in-cli-tools-a-practical-pattern-thats-worked-for-me-6c658a9141a9) |
| Progressive disclosure | NN/g | [nngroup.com](https://www.nngroup.com/articles/progressive-disclosure/) |
| JSON output formats | AWS CLI | [AWS CLI Output Formats](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html) |
| Man page formatting | Ubuntu | [Ubuntu Manpages](https://manpages.ubuntu.com/manpages/bionic/man7/man-pages.7.html) |

---

## Related Documentation

- [CLI Best Practices](./cli-best-practices.md) - Overall CLI design principles
- [ADR-0005: CLI Design Principles](../decisions/adrs/0005-cli-design-principles.md) - ragd CLI design decisions
- [CLI Reference Guide](../../guides/cli/reference.md) - Current CLI reference implementation

---

**Status**: Research complete
