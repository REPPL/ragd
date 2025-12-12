# Contributing to ragd

## Development Setup

### Prerequisites

- Python 3.12
- [Ollama](https://ollama.ai/) (for LLM inference)
- Git

### Quick Start

```bash
git clone git@github.com:REPPL/ragd.git
cd ragd
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pip==24.0      # Required: see pip version note below
pip install -e ".[contrib]"
```

This installs dev tools, testing, and security auditing without system dependencies.

> **Note:** The pip downgrade is required due to a [breaking change in packaging 24.0](https://packaging.pypa.io/en/stable/changelog.html)
> (bundled with pip 24.1+) that causes `InvalidVersion` errors when evaluating optional dependency markers.

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=ragd --cov-report=term-missing
```

### Code Quality

```bash
ruff check src/
mypy src/
pre-commit run --all-files
```

## Optional Extras

### Database Encryption (F-015)

Requires SQLCipher system library:

**macOS:**

```bash
brew install sqlcipher
export LDFLAGS="-L$(brew --prefix sqlcipher)/lib"
export CPPFLAGS="-I$(brew --prefix sqlcipher)/include"
pip install -e ".[contrib,encryption]"
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt install sqlcipher libsqlcipher-dev
pip install -e ".[contrib,encryption]"
```

## All Extras Reference

| Extra | Purpose | System Deps |
|-------|---------|-------------|
| `contrib` | Dev + test + security tools | None |
| `encryption` | SQLCipher database encryption | SQLCipher |
| `all` | Everything (requires all system deps) | SQLCipher |

Note: FAISS is included in the default installation.

## Code Style

This project follows:

- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- [mypy](https://mypy.readthedocs.io/) for type checking
- British English for all documentation and user-facing text

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run tests and code quality checks
4. Submit a pull request

## Documentation

- [Development Documentation](docs/development/)
- [Feature Roadmap](docs/development/features/)
- [Architecture Decisions](docs/development/decisions/adrs/)
