# CLI Documentation

Command-line interface guides for ragd.

## Documentation Levels

ragd's CLI documentation follows a **progressive disclosure** model. Start with Essentials, then explore deeper levels as needed.

| Level | Audience | Time | Content |
|-------|----------|------|---------|
| [Essentials](./essentials.md) | New users | 15 min | Core commands to get productive |
| [Intermediate](./intermediate.md) | Regular users | 20 min | Task-specific workflows |
| [Advanced](./advanced.md) | Power users | 15 min | Configuration, debugging |
| [Reference](./reference.md) | All users | As needed | Complete command specifications |

## Quick Start

If you're new to ragd, start here:

```bash
# 1. Check everything works
ragd doctor

# 2. Index some documents
ragd index ~/Documents/notes/

# 3. Search your knowledge
ragd search "your question here"

# 4. Check your index
ragd status
```

That's it! You now know the 4 essential commands.

## Choosing the Right Guide

**I'm brand new to ragd**
→ Start with [Essentials](./essentials.md)

**I want to do something specific**
→ Check [Intermediate](./intermediate.md) for task workflows

**I need to customise ragd**
→ See [Advanced](./advanced.md) for configuration

**I need exact flag syntax**
→ Use [Reference](./reference.md) for complete specs

## Related Documentation

- [Getting Started Tutorial](../../tutorials/getting-started.md) - Hands-on learning
- [ADR-0005: CLI Design Principles](../../development/decisions/adrs/0005-cli-design-principles.md) - Design rationale
- [CLI Best Practices Research](../../development/research/cli-best-practices.md) - Background research

---
