# ragd Documentation

Welcome to the ragd documentation hub.

## Documentation Structure

This documentation follows the [Diátaxis](https://diataxis.fr/) framework:

| Section | Purpose | Audience |
|---------|---------|----------|
| [Tutorials](./tutorials/) | Learning-oriented guides | New users |
| [Guides](./guides/) | Task-oriented how-tos | All users |
| [Reference](./reference/) | Technical specifications | Developers |
| [Explanation](./explanation/) | Conceptual understanding | All audiences |
| [Development](./development/) | Developer documentation | Contributors |

## Quick Start

```bash
# Clone and set up
git clone <repository-url>
cd ragd
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run the CLI
ragd --help
```

## For Users

- **New to ragd?** Start with [Tutorials](./tutorials/)
- **Need to accomplish a task?** Check [Guides](./guides/)
- **Looking for API details?** See [Reference](./reference/)
- **Want to understand concepts?** Read [Explanation](./explanation/)

## For Contributors

- [Development Documentation](./development/)
- [Feature Roadmap](./development/features/)
- [Architecture Decisions](./development/decisions/adrs/)

## AI Transparency

This project is developed with AI assistance. See [AI Contributions](./development/ai-contributions.md) for details.

---

## Related Documentation

- [Project README](../README.md)
- [.claude/ Configuration](../.claude/README.md)
