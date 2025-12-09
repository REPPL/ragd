"""ragd - Local RAG for personal knowledge management."""

from __future__ import annotations

import os

# Suppress HuggingFace tokenizers parallelism warning
# ragd uses single-threaded indexing; parallelism causes fork deadlocks with OCR
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

__version__ = "0.9.6"

# Vision module is available via `from ragd.vision import ...`
# Not imported here to avoid heavy chromadb/torch imports on every ragd command
