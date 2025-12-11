[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0a4-green.svg)](https://github.com/REPPL/ragd/releases)
[![Requires Ollama](https://img.shields.io/badge/requires-Ollama-purple.svg)](https://ollama.ai/)
[![macOS](https://img.shields.io/badge/macOS-supported-brightgreen.svg)]()
[![Linux](https://img.shields.io/badge/Linux-supported-brightgreen.svg)]()
[![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-orange.svg)](https://claude.ai/code)


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
# Create a virtual environment (recommended)
python3.12 -m venv ~/.ragd-env
source ~/.ragd-env/bin/activate  # On Windows: .ragd-env\Scripts\activate

# Install ragd
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

