# ADR-0012: Package Distribution Strategy

## Status

Accepted

## Context

ragd needs a distribution strategy that serves diverse users:
- Non-technical users who want simple installation
- Developers who need reproducible environments
- Enterprises with specific deployment requirements

The predecessor project (ragged) used Docker with 4 services (API, UI, ChromaDB, Redis), which created significant complexity:
- Hybrid architecture (native Ollama + Docker) for GPU access
- Platform-specific networking workarounds
- 3-level environment configuration cascade
- Requires Docker knowledge for troubleshooting

This complexity is inappropriate for a personal knowledge tool targeting non-expert users.

## Decision

Use **`uv/pip install` as the primary distribution** with **ChromaDB in embedded mode**. Docker is repositioned as a secondary option for development/advanced deployment.

### Primary Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User's Machine                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Ollama    │    │    ragd     │    │  ChromaDB   │  │
│  │  (native)   │◄──►│   (CLI)     │◄──►│ (embedded)  │  │
│  │             │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│   Separate          pip/uv install      In-process      │
│   install                               (no service)    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Installation Methods

**1. Recommended: uv (fastest)**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install ragd
uv tool install ragd

# Run guided setup
ragd init
```

**2. Standard: pip**
```bash
pip install ragd
ragd init
```

**3. Development: editable install**
```bash
git clone <repo>
cd ragd
uv pip install -e ".[dev]"
```

**4. Advanced: Docker**
```bash
docker-compose up -d  # For development/CI
```

### Why uv Over pip

| Aspect | pip | uv |
|--------|-----|-----|
| Speed | Baseline | 10-100x faster |
| Resolver | Backtracking | Rust-based, parallel |
| Lock files | pip-tools | Native support |
| Tool install | pip + pipx | `uv tool install` |

### ChromaDB Embedded Mode

ChromaDB runs in-process, eliminating:
- Separate database service
- Network configuration
- Container orchestration
- Port conflicts

```python
import chromadb

# Embedded mode (recommended)
client = chromadb.PersistentClient(path="~/.ragd/chroma_db")

# vs Server mode (not recommended for personal use)
# client = chromadb.HttpClient(host="localhost", port=8000)
```

### Ollama as External Dependency

Ollama handles LLM complexity:
- Model downloading and management
- GPU acceleration
- Quantisation
- API server

ragd treats Ollama as an external service (like a database), not a bundled dependency:

```bash
# User installs Ollama separately
brew install ollama  # macOS
# or
curl -fsSL https://ollama.com/install.sh | sh  # Linux

# ragd doctor verifies Ollama is available
ragd doctor
```

## Consequences

### Positive

- Single-command installation for most users
- No Docker knowledge required
- 10-100x faster installation with uv
- Zero-configuration database (ChromaDB embedded)
- Works offline after initial setup
- Clear separation of concerns (ragd vs Ollama)

### Negative

- Users must install Ollama separately
- No web UI in default installation (CLI only)
- Embedded ChromaDB limits to single-process access
- Less isolation than containerised deployment

## Alternatives Considered

### Docker-First (ragged approach)

- **Pros:** Full isolation, reproducible
- **Cons:** Complex for non-experts, GPU passthrough issues
- **Rejected:** Too much friction for personal tool

### Single Binary (PyInstaller/Nuitka)

- **Pros:** Simplest distribution, no Python needed
- **Cons:** 200MB+ binary, platform-specific builds, hard to update
- **Rejected:** Maintenance burden outweighs simplicity

### Bundled Ollama

- **Pros:** True single-install experience
- **Cons:** Duplicate installations, update complexity, licensing
- **Rejected:** Ollama is better managed separately

### ChromaDB Server Mode

- **Pros:** Multi-process access, network separation
- **Cons:** Additional service to manage, port conflicts
- **Rejected:** Embedded mode sufficient for personal use

## Related Documentation

- [State-of-the-Art Setup UX](../../research/state-of-the-art-setup-ux.md)
- [F-035: Health Check Command](../../features/completed/F-035-health-check.md)
- [F-036: Guided Setup](../../features/completed/F-036-guided-setup.md)
- [ADR-0002: Use ChromaDB](./0002-chromadb-vector-store.md)
