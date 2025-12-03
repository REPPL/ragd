"""Vector store adapters for ragd.

This package contains adapter implementations for various vector store backends.
Each adapter implements the VectorStore protocol defined in ragd.storage.protocols.

Available adapters:
- ChromaDBAdapter: Default backend, always available
- FAISSAdapter: High-performance backend, requires faiss-cpu

Usage:
    from ragd.storage import create_vector_store, BackendType

    # Create via factory (recommended)
    store = create_vector_store(BackendType.CHROMADB)

    # Or import adapter directly
    from ragd.storage.adapters import ChromaDBAdapter
"""

from __future__ import annotations

from ragd.storage.adapters.chromadb import ChromaDBAdapter

__all__ = ["ChromaDBAdapter"]

# FAISSAdapter is optional - only import if faiss is installed
try:
    from ragd.storage.adapters.faiss import FAISSAdapter

    __all__.append("FAISSAdapter")
except ImportError:
    pass
