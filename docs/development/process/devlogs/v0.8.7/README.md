# Devlog: v0.8.7 CLI Polish & Documentation

**Date:** 2025-12-04
**Version:** 0.8.7
**Theme:** Learn & Use ragd

## The Story

v0.8.7 transforms ragd from a capable tool into a learnable one. New users can now discover features through interactive wizards, comprehensive tutorials, and extended help.

## What We Built

### Interactive Configuration (F-088)

Created `src/ragd/ui/cli/config_wizard.py`:

```python
from ragd.ui.cli import run_config_wizard

# Launch wizard
ragd config --interactive
```

The wizard guides through:
- Model settings (embedding, LLM)
- Search behaviour (mode, weights)
- Storage settings (paths, chunking)
- Security options (encryption, sessions)

### Configuration Debugging (F-097)

Created `src/ragd/ui/cli/config_debug.py`:

```bash
# Show config with all defaults
ragd config --effective

# Show only customisations
ragd config --diff

# Show where values come from
ragd config --source
```

### Configuration Migration (F-096)

Created `src/ragd/ui/cli/config_migration.py`:

```bash
# Preview migration
ragd config --migrate --dry-run

# Apply migration
ragd config --migrate

# Rollback if needed
ragd config --rollback
```

Features:
- Version detection in configs
- Automatic backup before migration
- Rollback to previous versions
- Dry-run preview

### Extended Help System (F-089)

Created `src/ragd/ui/cli/help_system.py`:

```bash
# List topics
ragd help

# Extended help
ragd help search

# Just examples
ragd help search --examples
```

### Output Mode Consistency (F-090)

Created `src/ragd/ui/output.py`:

```python
from ragd.ui.output import OutputWriter, OutputFormat

writer = OutputWriter(format=OutputFormat.JSON)
writer.print(data)
writer.success("Done!")
```

Supports:
- `rich` - Coloured terminal output
- `plain` - Plain text
- `json` - Machine-readable
- `csv` - Spreadsheet export

### Tutorial Suite (F-091)

Six progressive tutorials:
1. Getting Started (15 min)
2. Searching (20 min)
3. Chat Interface (15 min)
4. Organisation (25 min)
5. Advanced Search (30 min)
6. Automation (20 min)

### Documentation

- Configuration Reference: Complete config.yaml documentation
- Troubleshooting Guide: Common issues and solutions
- Use Case Gallery: Notes, research, code documentation

## What We Didn't Build

### Full Video/GIF Recordings
Demo specs are written but actual recordings require additional tooling (asciinema, vhs). Deferred for future.

### Additional Use Cases
Only 3 use cases documented. Legal, recipes, meeting notes deferred.

## The Documentation Mindset

This release establishes a documentation-first approach:

1. **Tutorials guide learning** - Progressive skill building
2. **Reference documents details** - Complete technical info
3. **Troubleshooting prevents frustration** - Common solutions
4. **Use cases inspire adoption** - Real-world applications

These patterns make ragd accessible to newcomers.

---

*Documentation is code for humans.*
