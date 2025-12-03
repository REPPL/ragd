"""Storage layer for ragd.

This module provides vector storage backends for ragd. The recommended way
to create a vector store is via the factory:

    from ragd.storage import create_vector_store, BackendType

    store = create_vector_store(BackendType.CHROMADB)

For backwards compatibility, ChromaStore is still available:

    from ragd.storage import ChromaStore  # Deprecated
"""

# New v0.6 API
from ragd.storage.factory import (
    BackendNotAvailableError,
    VectorStoreFactory,
    create_vector_store,
    get_factory,
)
from ragd.storage.protocols import MetadataProxy, VectorStore
from ragd.storage.types import (
    BackendHealth,
    BackendType,
    HealthStatus,
    MigrationProgress,
    StorageStats,
    VectorSearchResult,
)
from ragd.storage.profiler import (
    BenchmarkResult,
    OperationMetrics,
    StorageProfiler,
    compare_backends,
)

# Legacy API (deprecated but maintained for compatibility)
from ragd.storage.chromadb import ChromaStore, DocumentRecord
from ragd.storage.images import ImageRecord, ImageStore

__all__ = [
    # New v0.6 API
    "VectorStore",
    "MetadataProxy",
    "VectorStoreFactory",
    "create_vector_store",
    "get_factory",
    "BackendNotAvailableError",
    "BackendType",
    "BackendHealth",
    "HealthStatus",
    "StorageStats",
    "VectorSearchResult",
    "MigrationProgress",
    # Profiler
    "StorageProfiler",
    "BenchmarkResult",
    "OperationMetrics",
    "compare_backends",
    # Legacy API
    "ChromaStore",
    "DocumentRecord",
    "ImageStore",
    "ImageRecord",
]
