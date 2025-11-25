# ADR-0005: CLI Design Principles

## Status

Accepted

## Context

ragd targets non-expert users who need a powerful knowledge management tool without CLI expertise. The challenge: enable complete control of functionality without overwhelming new users.

Research from [clig.dev](https://clig.dev/) and [Atlassian's CLI principles](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis) provides industry best practices. ragged's 4-level documentation approach proves effective for progressive disclosure.

## Decision

Adopt the following CLI design principles for ragd:

### 1. Four-Layer Documentation

```
Layer 1: ESSENTIALS (4 commands, 15 min)
Layer 2: INTERMEDIATE (task workflows, 20 min)
Layer 3: ADVANCED (configuration, debugging)
Layer 4: REFERENCE (complete technical specs)
```

### 2. Three Output Modes

| Mode | Trigger | Use Case |
|------|---------|----------|
| Rich | TTY detected | Human terminal use |
| Plain | Pipe detected or `--plain` | Scripts, accessibility |
| JSON | `--json` flag | Programmatic integration |

### 3. Examples-First Help

Help text leads with examples before listing options:

```bash
EXAMPLES:
    ragd search "machine learning"
    ragd search "AI" --limit 5

OPTIONS:
    --limit, -n <N>  Number of results
```

### 4. Structured Error Messages

Every error includes:
1. What went wrong
2. Why it might have happened
3. How to fix it
4. Where to get help

### 5. Progressive Prompting

Prompt for missing required information instead of failing:

```bash
$ ragd index
No path specified. What would you like to index?
> ~/Documents/
```

### 6. Standard Flags

| Flag | Short | Purpose |
|------|-------|---------|
| `--help` | `-h` | Show help |
| `--version` | `-v` | Show version |
| `--quiet` | `-q` | Minimal output |
| `--verbose` | | Detailed output |
| `--format` | | Output format |
| `--json` | | Shorthand for `--format json` |
| `--no-color` | | Disable colour |

### 7. Accessibility

- Respect `NO_COLOR` environment variable
- Support `--plain` for screen readers
- Don't rely solely on colour for meaning
- Provide theme options (default, high-contrast, monochrome)

## Consequences

### Positive

- New users productive in 15 minutes
- Power users have full control
- Consistent experience across commands
- Accessible to users with visual impairments
- Script-friendly output modes

### Negative

- More complex help system to maintain
- Multiple output formatters to implement
- Interactive prompts need `--no-input` escape hatch

## Related Documentation

- [CLI Best Practices Research](../../research/cli-best-practices.md)
- [CLI Essentials Guide](../../../guides/cli/essentials.md)
- [ADR-0001: Use Typer + Rich](./0001-use-typer-rich-cli.md)

---
