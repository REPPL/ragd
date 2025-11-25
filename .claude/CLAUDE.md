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
- **Virtual environments:**
  - `.venv/` - Development/release environment
  - `.venv-testing/` - Test isolation

### Package Management
- Use `pyproject.toml` for all dependencies
- Group dependencies: `[project.dependencies]`, `[project.optional-dependencies.dev]`, `[project.optional-dependencies.test]`
- Pin versions for reproducibility

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

- [Global Standards](~/.claude/CLAUDE.md)
- [Development Standards](~/Development/.claude/CLAUDE.md)
- [Sandboxed Standards](~/Development/Sandboxed/.claude/CLAUDE.md)

---

**Status**: Active development
