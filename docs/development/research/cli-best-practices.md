# CLI Best Practices Research

Modern CLI design principles for non-expert users with progressive disclosure.

## Executive Summary

This research synthesises best practices from industry leaders (clig.dev, Atlassian) and proven patterns from ragged's 4-level documentation approach. The goal: enable complete control of functionality without overwhelming non-expert users.

---

## 1. Core Philosophy

### Human-First Design

Design CLIs for humans first, not machines. If a command is primarily used by humans, prioritise usability over traditional UNIX conventions.

**Source**: [Command Line Interface Guidelines](https://clig.dev/)

### Progressive Disclosure

Introduce complexity gradually:
- Essential features immediately accessible
- Advanced features discoverable but not overwhelming
- Power user features available but hidden by default

**Source**: [Atlassian: 10 Design Principles for Delightful CLIs](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

---

## 2. The Four-Layer Documentation Model

Based on ragged's proven approach:

```
Layer 1: ESSENTIALS (4-6 commands, 15 min to productivity)
    ↓ user gains confidence
Layer 2: INTERMEDIATE (task-specific workflows, 20 min additional)
    ↓ user needs more control
Layer 3: ADVANCED (power user features, configuration, debugging)
    ↓ reference
Layer 4: COMPLETE REFERENCE (all flags, all options, technical specs)
```

### Layer Characteristics

| Layer | Audience | Content | Learning Time |
|-------|----------|---------|---------------|
| Essentials | New users | Core commands only | 15 min |
| Intermediate | Regular users | Task workflows | 20 min |
| Advanced | Power users | Configuration, debugging | 15 min |
| Reference | All users | Complete technical specs | As needed |

---

## 3. Help System Design

### Lead with Examples

Show common use cases before listing options:

```bash
ragd search --help

USAGE: ragd search <query> [OPTIONS]

EXAMPLES:
    ragd search "machine learning"           # Basic search
    ragd search "neural networks" --limit 5  # Top 5 results
    ragd search "AI ethics" --format json    # JSON output

OPTIONS:
    --limit, -n <N>     Number of results (default: 10)
    --format <FORMAT>   Output format: rich|plain|json (default: rich)
```

**Principles:**
- Examples before options
- Most-used flags before rarely-used ones
- `--help` available after any command/subcommand
- Link to web documentation from help text
- Suggest corrections for typos

**Source**: [clig.dev - Help](https://clig.dev/#help)

---

## 4. Output Design

### Three Output Modes

| Mode | Flag | Use Case | Default |
|------|------|----------|---------|
| Rich | (default) | Interactive terminal, human reading | Yes (TTY) |
| Plain | `--plain` | Scripts, piping, accessibility | Yes (pipe) |
| JSON | `--json` | Programmatic integration | No |

### Output Principles

1. **Detect TTY vs pipe automatically** - Rich output for terminal, plain for pipes
2. **Respect NO_COLOR** - Disable colour when `NO_COLOR` is set or `TERM=dumb`
3. **Critical info at END** - Where eyes naturally look after command completes
4. **Progress for long operations** - Show indicators for operations > 100ms
5. **Symbols sparingly** - Use for distinction, not decoration

### Progress Feedback

```
Indexing document.pdf...
  ├─ Extracting text... done (1.2s)
  ├─ Creating chunks... 47 chunks
  ├─ Generating embeddings... ████████░░ 80%
  └─ Storing in database... done

✓ Indexed 1 document (47 chunks) in 3.4s
```

**Source**: [Atlassian Principles #3, #4, #7](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

---

## 5. Error Handling

### User-Centric Error Messages

Structure every error with:
1. **What went wrong** - Clear description
2. **Why it might have happened** - Context
3. **How to fix it** - Actionable suggestions
4. **Where to get help** - Documentation link

```
# Bad
Error: ENOENT

# Good
Error: Cannot find document "report.pdf"

Suggestions:
  • Check the file path is correct
  • Use 'ragd status' to see indexed documents
  • See: https://docs.ragd.io/troubleshooting#file-not-found
```

**Source**: [clig.dev - Errors](https://clig.dev/#errors)

---

## 6. Arguments and Flags

### Prefer Flags Over Positional Arguments

```bash
# Good: Self-documenting
ragd search --query "AI" --limit 5 --format json

# Acceptable: Single positional for primary argument
ragd search "AI" --limit 5

# Avoid: Multiple positional arguments
ragd search "AI" 5 json
```

### Standard Flag Conventions

| Flag | Short | Purpose |
|------|-------|---------|
| `--help` | `-h` | Display help |
| `--version` | `-v` | Display version |
| `--quiet` | `-q` | Minimal output |
| `--verbose` | | Detailed output |
| `--debug` | | Debug information |
| `--limit` | `-n` | Limit results |
| `--format` | | Output format |
| `--json` | | Shorthand for `--format json` |
| `--force` | `-f` | Skip confirmations |
| `--dry-run` | | Preview without executing |

**Source**: [Atlassian Principle #10](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

---

## 7. Interactivity and Prompting

### Prompt for Missing Information

Rather than failing with an error, prompt interactively:

```bash
$ ragd index
No path specified. What would you like to index?
> ~/Documents/papers/

Indexing ~/Documents/papers/...
```

### Always Provide Flag Alternatives

- Every prompt should be skippable via flag
- Support `--no-input` to disable all prompting
- Provide sensible defaults where possible

**Source**: [Atlassian Principle #8](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

---

## 8. Suggest Next Steps

After successful operations, guide users to logical next actions:

```
✓ Successfully indexed 5 documents

Next steps:
  • Search your knowledge: ragd search "your query"
  • View statistics: ragd status
  • See all commands: ragd --help
```

**Source**: [Atlassian Principle #7](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

---

## 9. Accessibility

### Theme Support

From ragged's accessibility patterns:
- **Default** - Auto-detect terminal capabilities
- **High-contrast** - Maximum readability
- **Colourblind-safe** - Avoid red/green distinctions
- **Monochrome** - No colour (text only)

### Requirements

1. **Don't rely solely on colour** - Use symbols/text alongside colour
2. **Support screen readers** - `--plain` mode outputs clean text
3. **Respect NO_COLOR** - Environment variable disables all colour
4. **Text alternatives** - Provide text for visual progress indicators

**Source**: [Best Practices for Inclusive CLIs](https://seirdy.one/posts/2022/06/10/cli-best-practices/)

---

## 10. ragd Implementation Recommendations

### Essential Commands (v0.1)

```bash
ragd health              # Verify setup works
ragd index <path>        # Add documents
ragd search "<query>"    # Find information
ragd status              # View statistics
```

### Command Structure

```
ragd [global-options] <command> [command-options] [arguments]
```

### Global Options

| Option | Purpose |
|--------|---------|
| `--help` | Show help for any command |
| `--version` | Show version |
| `--quiet` | Suppress non-essential output |
| `--verbose` | Show detailed output |
| `--format` | Output format (rich/plain/json) |
| `--no-color` | Disable colour output |
| `--config` | Specify config file path |

---

## Research Sources

| Source | Topic | URL |
|--------|-------|-----|
| clig.dev | CLI Guidelines | [clig.dev](https://clig.dev/) |
| Atlassian | 10 Design Principles | [atlassian.com](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis) |
| Seirdy | Inclusive CLI Best Practices | [seirdy.one](https://seirdy.one/posts/2022/06/10/cli-best-practices/) |
| ragged | 4-Level Documentation | Internal reference |

---

## Related Documentation

- [ADR-0005: CLI Design Principles](../decisions/adrs/0005-cli-design-principles.md)
- [CLI Essentials Guide](../../guides/cli/essentials.md)
- [CLI Reference](../../guides/cli/reference.md)

---

**Status:** Research complete
