[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0a6-green.svg)](https://github.com/REPPL/ragd/releases)
[![Requires Ollama](https://img.shields.io/badge/requires-Ollama-purple.svg)](https://ollama.ai/)
[![macOS](https://img.shields.io/badge/macOS-supported-brightgreen.svg)]()
[![Linux](https://img.shields.io/badge/Linux-supported-brightgreen.svg)]()
[![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-orange.svg)](https://claude.ai/code)


![ragged logo](docs/assets/img/ragd-logo.png)


## Your Private Intelligent Document Assistant

`ragd` is a local RAG *(Retrieval-Augmented Generation)* system that lets you ask questions about your documents and get accurate answers with citations -- all while keeping your data completely private and local.

![Getting Started with ragd](docs/assets/img/getting-started-comic1.png)

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

# Downgrade pip (required due to bug in pip 24.2+)
pip install pip==24.1.2

# Install ragd (includes all runtime features)
pip install ragd
```

> **Note:** The pip downgrade is required due to a [bug in pip 24.2+](https://github.com/pypa/pip/issues)
> that causes `InvalidVersion` errors when evaluating optional dependency markers.

Then run the guided setup:

```bash
ragd init     # Detects hardware, recommends models
ragd doctor   # Verify installation and show feature status
```

#### Expert Installation (Minimal)

For CI pipelines or resource-constrained environments:

```bash
# Install core features only (smaller footprint)
RAGD_MINIMAL=1 pip install ragd
```

#### System-Dependent Extras

Some features require system-level dependencies:

```bash
# Database encryption (requires SQLCipher)
# macOS: brew install sqlcipher
# Linux: apt install sqlcipher libsqlcipher-dev
pip install 'ragd[encryption]'

# FAISS vector store (alternative backend)
pip install 'ragd[faiss]'
```

### Install from Source (for contributors)

```bash
git clone git@github.com:REPPL/ragd.git
cd ragd
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install pip==24.1.2    # Required: downgrade pip first (see note above)
pip install -e ".[all]"    # Includes dev, test, and security tools
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

