"""ragd - Local RAG for personal knowledge management."""

from __future__ import annotations

import os
from importlib.metadata import version, PackageNotFoundError

# Suppress HuggingFace tokenizers parallelism warning
# ragd uses single-threaded indexing; parallelism causes fork deadlocks with OCR
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Single source of truth: version comes from pyproject.toml via package metadata
try:
    __version__ = version("ragd")
except PackageNotFoundError:
    # Package not installed (e.g., running from source without pip install -e)
    __version__ = "0.0.0.dev0"

# Vision module is available via `from ragd.vision import ...`
# Not imported here to avoid heavy chromadb/torch imports on every ragd command
