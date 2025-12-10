[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-green.svg)]()


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
pip install ragd
```

Then run the guided setup:

```bash
ragd init     # Detects hardware, recommends models
ragd doctor   # Verify installation
```

### Install from Source (for contributors)

```bash
git clone git@github.com:REPPL/ragd.git
cd ragd
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
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

