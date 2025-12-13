# ragd Documentation

Welcome to the ragd documentation hub.

## What is ragd?

ragd is a **privacy-first personal knowledge system**. Index your documents and search them using natural language - all running locally on your machine.

**Key Features:**
- Index PDF, TXT, Markdown, and HTML files
- Semantic search with natural language queries
- Beautiful CLI with Rich output and interactive TUI
- 100% local processing (no cloud APIs)

## Documentation Structure

This documentation follows the [Diátaxis](https://diataxis.fr/) framework:

| Section | Purpose | Audience |
|---------|---------|----------|
| [Tutorials](./tutorials/) | Learning-oriented guides | New users |
| [Guides](./guides/) | Task-oriented how-tos | All users |
| [Reference](./reference/) | Technical specifications | Developers |
| [Explanation](./explanation/) | Conceptual understanding | All audiences |
| [Use Cases](./use-cases/) | What users want to accomplish | Product/Dev |
| [Development](./development/) | Developer documentation | Contributors |

## Quick Start

```bash
# Install ragd from GitHub
pip install git+https://github.com/REPPL/ragd.git

# Index your documents
ragd index ~/Documents/notes/

# Search your knowledge
ragd search "how does authentication work"

# Check status
ragd info
```

## For Users

- **New to ragd?** Start with [Getting Started Tutorial](./tutorials/01-getting-started.md)
- **Need to accomplish a task?** Check [Guides](./guides/)
- **Looking for API details?** See [Reference](./reference/)
- **Want to understand concepts?** Read [Explanation](./explanation/)

## For Contributors

- [Development Documentation](./development/)
- [Use Cases](./use-cases/) - What we're building
- [Feature Roadmap](./development/features/)
- [Architecture Decisions](./development/decisions/adrs/)
- [ragged Analysis](./development/lineage/ragged-analysis.md) - Knowledge transfer

## Roadmap Overview

| Version | Focus | Status |
|---------|-------|--------|
| v0.1.0 | Core RAG (index, search, status) | ✅ Released |
| v0.2.0 | Messy PDFs (killer feature) | ✅ Released |
| v0.3.0 | Advanced Search | ✅ Released |
| v0.4.0 | Multi-Modal (vision embeddings) | ✅ Released |
| v0.5.0 | Chat (LLM integration, agentic RAG) | ✅ Released |
| v0.6.0 | Storage Abstraction (FAISS, backends) | ✅ Released |
| v0.6.5 | Polish & Stability | ✅ Released |
| v0.7.0 | Privacy & Security (encryption, PII) | ✅ Released |
| v0.8.x | Metadata & Organisation | ✅ Released |
| v0.9.0 | Enhanced Indexing | ✅ Released |
| v0.9.5 | Stability & Logging | ✅ Released |
| v0.9.6 | Alpha Testing Release | ✅ Released |
| v1.0.0 | Performance & Polish | ✅ Released |

See [Milestones](./development/milestones/) for details.

## AI Transparency

This project is developed with AI assistance. See [AI Contributions](./development/ai-contributions.md) for details.

---

## Related Documentation

- [Project README](../README.md)

