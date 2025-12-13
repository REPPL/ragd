"""ragd - Your Private Intelligent Document Assistant."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, metadata, version

# Suppress HuggingFace tokenizers parallelism warning
# ragd uses single-threaded indexing; parallelism causes fork deadlocks with OCR
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Single source of truth: version and description come from pyproject.toml
try:
    __version__ = version("ragd")
    __description__ = metadata("ragd")["Summary"]
except PackageNotFoundError:
    # Package not installed (e.g., running from source without pip install -e)
    __version__ = "0.0.0.dev0"
    __description__ = "Your Private Intelligent Document Assistant"

# Vision module is available via `from ragd.vision import ...`
# Not imported here to avoid heavy chromadb/torch imports on every ragd command
