# F-089: Help System Enhancement

**Status:** Planned
**Milestone:** v0.8.7

## Problem Statement

Default Typer help is functional but lacks examples and detailed explanations. Users need contextual help with practical examples.

## Design Approach

Enhance `--help` output with examples and add a dedicated `ragd help` command for extended documentation.

### Enhanced Help Format
```
$ ragd search --help
Usage: ragd search [OPTIONS] QUERY

Search indexed documents with natural language.

Examples:
  ragd search "machine learning basics"
  ragd search "python errors" --limit 20
  ragd search "API documentation" --format json

Options:
  --limit, -l    Maximum results [default: 10]
  --format, -f   Output format (rich/plain/json)
  ...
```

### Extended Help Command
```
$ ragd help search
# Detailed documentation with:
# - Full description
# - All options explained
# - Multiple examples
# - Common workflows
# - Related commands
```

## Implementation Tasks

- [ ] Add epilog with examples to each command
- [ ] Create `ragd help` subcommand
- [ ] Write extended help content for major commands
- [ ] Add `--examples` flag to show only examples
- [ ] Create man page generation script
- [ ] Document help system usage

## Success Criteria

- [ ] Each command shows at least 2 examples in --help
- [ ] `ragd help <command>` shows detailed documentation
- [ ] Man pages can be generated

## Dependencies

- Typer (existing)
- v0.8.6 (Security Focus)

---

## Related Documentation

- [v0.8.7 Milestone](../../milestones/v0.8.7.md)
- [F-091 Tutorial Suite](./F-091-tutorial-suite.md)

---

**Status**: Planned
