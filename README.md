<p align="center">
  <img src="docs/assets/img/ragd-logo.png" alt="ragd logo" width="200">
</p>

# ragd

Local RAG (Retrieval-Augmented Generation) for personal knowledge management.

## Overview

ragd is a reference implementation demonstrating best practices for:
- Python 3.12 development
- CLI-first applications with Typer + Rich
- Docker-based development environments
- Feature-centric documentation

## Quick Start

### Prerequisites
- Python 3.12
- Docker and Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ragd

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Verify installation
ragd --help
```

### Docker Setup

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Usage

```bash
# Show available commands
ragd --help

# Example commands (when implemented)
ragd index <path>      # Index documents
ragd search <query>    # Search indexed documents
ragd chat              # Interactive chat with context
```

## Documentation

- [Documentation Hub](docs/README.md)
- [Tutorials](docs/tutorials/)
- [Guides](docs/guides/)
- [Reference](docs/reference/)

## Development

- [Development Documentation](docs/development/)
- [Feature Roadmap](docs/development/features/)
- [Architecture Decisions](docs/development/decisions/adrs/)

## AI Transparency

This project is developed with AI assistance. See [AI Contributions](docs/development/ai-contributions.md) for transparency documentation.

## Licence

[Licence information to be added]

---

**Status**: Early development
