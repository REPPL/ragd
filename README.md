[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-red.svg)]()


![ragged logo](docs/assets/img/ragd-logo.png)


## Your Private Intelligent Document Assistant

`ragd` is a local RAG *(Retrieval-Augmented Generation)* system that lets you ask questions about your documents and get accurate answers with citations -- all while keeping your data completely private and local.

## Overview

ragd is a reference implementation demonstrating best practices for:
- **Local-first, privacy-preserving AI** - All processing happens on your machine
- **Hardware-aware optimisation** - Automatic tuning for Apple Silicon, CUDA, or CPU
- **CLI-first applications** with Typer + Rich
- **Feature-centric documentation**

## Quick Start

### Prerequisites
- Python 3.12
- [Ollama](https://ollama.ai/) (for LLM inference)

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

# Run guided setup (detects hardware, recommends models)
ragd init

# Verify installation
ragd doctor
```

### Docker Setup (Alternative)

For containerised deployment:

```bash
docker-compose up -d        # Start services
docker-compose logs -f      # View logs
docker-compose down         # Stop services
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

