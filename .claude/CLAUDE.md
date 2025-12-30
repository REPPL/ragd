# ragd Project Standards

**Scope:** Project-specific standards for ragd (RAG reference implementation)

**Inherits from:**
- `~/.claude/CLAUDE.md` - Global essentials
- `~/Development/.claude/CLAUDE.md` - Development standards
- `~/Development/Sandboxed/.claude/CLAUDE.md` - Sandboxed project standards

---

## Project Overview

**ragd** is a reference implementation for Retrieval-Augmented Generation (RAG) systems, designed to validate and demonstrate best practices for:
- Python 3.12 development
- CLI-first applications using Typer + Rich
- Docker-based development environments
- Feature-centric documentation

---

## Python Standards

### Version
- **Required:** Python 3.12 (NOT 3.9 or earlier)

### Virtual Environment (CRITICAL for Agents)

**All agents MUST use `.venv/` with full dependencies:**

```bash
# Activate environment
source .venv/bin/activate

# Verify Python version
python --version  # Must show 3.12+

# Install all dependencies (dev, test, security)
pip install -e ".[all]"
```

**Environment rules:**
- **Always use `.venv/`** - the canonical development environment
- **Never create alternative venvs** - consistency is critical
- **Verify before running commands** - ensure correct Python and deps
- If `.venv/` doesn't exist: `python3.12 -m venv .venv`

### Package Management
- Use `pyproject.toml` for all dependencies
- Dependency groups: `dev`, `test`, `security`, `all`
- Install with `pip install -e ".[all]"` to get everything

### CLI Framework
- **Primary:** Typer with Rich for output formatting
- All user-facing functionality must be accessible via CLI
- Design for non-technical users where applicable

---

## AI Transparency

This project uses **Full AI Transparency**:

### Commit Attribution
All AI-assisted commits include:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Documentation
- AI contributions documented in `docs/development/ai-contributions.md`
- Significant AI decisions noted in ADRs
- Milestone retrospectives committed to `docs/development/process/retrospectives/`

---

## Version Numbering Policy

### Semantic Versioning (MAJOR.MINOR.PATCH)

| Version | When to Use | Example |
|---------|-------------|---------|
| **0.X.0** | Milestone release (planned features) | v0.1.0, v0.2.0 |
| **0.X.Y** | Bug fixes after milestone | v0.1.1, v0.1.2 |
| **X.0.0** | Breaking changes or major milestone | v1.0.0 |

### Rules

1. **pyproject.toml** version = next planned version during development
2. **Git tag** = version at release moment
3. **After release**: Bump pyproject.toml to next patch (0.1.0 → 0.1.1)
4. **Milestone tags**: Use pre-release suffixes during development
   - `vX.Y.Z-alpha.1` - Foundation complete
   - `vX.Y.Z-beta.1` - Features complete
   - `vX.Y.Z` - Release

### Current Status

| Version | Status | Notes |
|---------|--------|-------|
| v0.1.0 | ✅ Released | Core RAG pipeline |
| v0.2.0 | ✅ Released | Messy PDFs (killer feature) |
| v0.2.5 | ✅ Released | HTML Enhancement |
| v0.3.0 | 📋 Planned | Advanced Search |
| v1.0.0 | 📋 Planned | Personal Platform + WebUI |

### Version Location

ragd uses a **single source of truth** for version:

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata - the canonical version |

The `__version__` in `src/ragd/__init__.py` is derived automatically from package metadata via `importlib.metadata`. When updating version, only edit `pyproject.toml`:

```bash
# 1. Update pyproject.toml
#    version = "X.Y.Z"

# 2. Reinstall package to update metadata
pip install -e ".[all]"

# 3. Verify
ragd --version
```

---

## Implementation Checklists

### Pre-Implementation (Before Starting)

- [ ] `pyproject.toml` version matches target milestone
- [ ] `ragd --version` displays expected version
- [ ] `.venv/` activated with Python 3.12+
- [ ] All dependencies installed (`pip install -e ".[all]"`)
- [ ] All existing tests pass (`pytest tests/`)
- [ ] Feature spec exists in `docs/development/features/`
- [ ] Session file created in `.work/agents/session.yaml` (if tracking)

### Post-Implementation (Before Completing)

- [ ] `ragd --version` shows correct version
- [ ] `pip show ragd` shows correct version
- [ ] All unit tests pass: `pytest tests/`
- [ ] Manual test script runs: `python tests/manual_vX.py`
- [ ] Coverage target met (≥80%)
- [ ] Feature spec marked as implemented
- [ ] Milestone status updated
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`

---

## Working Files

### .work/ Directory
**Purpose:** Temporary files that should NEVER be committed

**Use for:**
- Progress trackers
- Draft documents
- Scratch files
- Personal notes

**Structure:**
```
.work/
├── README.md        # Explains .work/ purpose
├── v0.1/            # Version-specific working files
└── scratch/         # General scratch space
```

**Enforcement:** Pre-commit hook blocks `.work/` commits

---

## British English Exceptions

### --no-color Flag

**Exception:** The `--no-color` CLI flag uses American English spelling.

**Rationale:** Compliance with the [NO_COLOR](https://no-color.org/) environment variable standard, which is universally adopted across CLI tools using American spelling.

**Implementation:**
- Flag name: `--no-color` (American, for ecosystem compatibility)
- Descriptions: "colour" (British, for documentation consistency)
- Environment variable: `NO_COLOR` (standard, American)

---

## Privacy Requirements

### Never Commit
- Hardcoded user paths (e.g., `/Users/username/`)
- Real email addresses (use @example.com)
- API keys, tokens, passwords
- Personal identifying information

### Safe Alternatives
- Use `$PROJECT_ROOT` or relative paths
- Use example.com domain for sample emails
- Use environment variables for secrets

---

## Documentation Structure

This project uses **Feature-Centric Roadmap** documentation:

```
docs/
├── README.md                    # Documentation hub
├── tutorials/                   # User-focused learning
├── guides/                      # Task-oriented how-tos
├── reference/                   # Technical specifications
├── explanation/                 # Conceptual understanding
└── development/
    ├── README.md
    ├── features/                # Feature-centric roadmap
    │   ├── active/              # Currently implementing
    │   ├── planned/             # Next up
    │   └── completed/           # Done
    ├── milestones/              # Release planning
    ├── implementation/          # What was built
    ├── process/                 # How it was built
    └── decisions/               # Architecture decisions
        └── adrs/
```

---

## Docker Development

### Container Usage
- Use `docker-compose.yml` for multi-container setups
- Document ports in project README
- Include health checks

### Quick Commands
```bash
docker-compose up -d      # Start services
docker-compose logs -f    # View logs
docker-compose down       # Stop services
```

---

## Related Documentation

- Global Standards: `~/.claude/CLAUDE.md`
- Development Standards: `~/Development/.claude/CLAUDE.md`
- Sandboxed Standards: `~/Development/Sandboxed/.claude/CLAUDE.md`

---

**Status**: Active development
