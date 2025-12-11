# CLI Documentation

Command-line interface guides for ragd.

## Documentation Levels

ragd's CLI documentation follows a **progressive disclosure** model. Start with Essentials, then explore deeper levels as needed.

| Level | Audience | Time | Content |
|-------|----------|------|---------|
| [Essentials](./essentials.md) | New users | 20 min | 6 core commands to get productive |
| [Command Comparison](./command-comparison.md) | All users | 5 min | When to use search vs ask vs chat |
| [Intermediate](./intermediate.md) | Regular users | 20 min | Task-specific workflows |
| [Advanced](./advanced.md) | Power users | 15 min | Configuration, debugging, admin mode |
| [Reference](./reference.md) | All users | As needed | Complete command specifications |

## Quick Start

If you're new to ragd, start here:

```bash
# 1. Check everything works
ragd doctor

# 2. Index some documents
ragd index ~/Documents/notes/

# 3. Search your knowledge (retrieval only)
ragd search "your question here"

# 4. Get AI answers (requires Ollama)
ragd ask "What are the main points?"

# 5. Have a conversation
ragd chat

# 6. Check your index
ragd info
```

**Not sure when to use search, ask, or chat?** See [Command Comparison](./command-comparison.md).

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

- [What is RAG?](../../explanation/what-is-rag.md) - Understanding retrieval-augmented generation
- [Getting Started Tutorial](../../tutorials/01-getting-started.md) - Hands-on learning
- [CLI Reference](../../reference/cli-reference.md) - Complete command specifications

---
