"""Factory for creating vector store instances.

This module provides the VectorStoreFactory which creates appropriate
backend instances based on configuration. It also handles feature
detection for optional backends like FAISS.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ragd.storage.types import BackendType

if TYPE_CHECKING:
    from ragd.storage.protocols import VectorStore

logger = logging.getLogger(__name__)


class BackendNotAvailableError(Exception):
    """Raised when a requested backend is not available."""

    def __init__(self, backend: BackendType, reason: str) -> None:
        self.backend = backend
        self.reason = reason
        super().__init__(f"Backend '{backend.value}' not available: {reason}")


class VectorStoreFactory:
    """Factory for creating vector store instances.

    This factory creates the appropriate backend adapter based on
    configuration and available dependencies. It handles:

    1. Backend selection (chromadb, faiss)
    2. Feature detection (is faiss installed?)
    3. Fallback to default backend
    4. Consistent configuration passing

    Usage:
        factory = VectorStoreFactory()
        store = factory.create(BackendType.CHROMADB, path=Path("~/.ragd/data"))

        # Or with auto-detection from config
        store = factory.create_from_config(config)
    """

    _instance: VectorStoreFactory | None = None

    def __new__(cls) -> VectorStoreFactory:
        """Singleton pattern for factory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self) -> None:
        """Initialise factory with backend availability detection."""
        if getattr(self, "_initialised", False):
            return

        self._available_backends: dict[BackendType, bool] = {}
        self._detect_backends()
        self._initialised = True

    def _detect_backends(self) -> None:
        """Detect which backends are available."""
        # ChromaDB is always available (core dependency)
        self._available_backends[BackendType.CHROMADB] = True

        # Check for FAISS
        try:
            import faiss  # noqa: F401

            self._available_backends[BackendType.FAISS] = True
            logger.debug("FAISS backend available")
        except ImportError:
            self._available_backends[BackendType.FAISS] = False
            logger.debug("FAISS not installed, backend unavailable")

    def is_available(self, backend: BackendType) -> bool:
        """Check if a backend is available.

        Args:
            backend: Backend type to check

        Returns:
            True if backend is installed and available
        """
        return self._available_backends.get(backend, False)

    def list_available(self) -> list[BackendType]:
        """List all available backends.

        Returns:
            List of available backend types
        """
        return [b for b, available in self._available_backends.items() if available]

    def create(
        self,
        backend: BackendType,
        persist_directory: Path,
        dimension: int = 384,
        **kwargs: object,
    ) -> VectorStore:
        """Create a vector store instance.

        Args:
            backend: Backend type to create
            persist_directory: Directory for persistent storage
            dimension: Embedding dimension (default 384 for MiniLM)
            **kwargs: Additional backend-specific options

        Returns:
            VectorStore instance

        Raises:
            BackendNotAvailableError: If backend is not installed
            ValueError: If invalid backend type
        """
        if not self.is_available(backend):
            raise BackendNotAvailableError(
                backend,
                f"Install with: pip install ragd[{backend.value}]",
            )

        if backend == BackendType.CHROMADB:
            return self._create_chromadb(persist_directory, dimension, **kwargs)
        elif backend == BackendType.FAISS:
            return self._create_faiss(persist_directory, dimension, **kwargs)
        else:
            raise ValueError(f"Unknown backend type: {backend}")

    def _create_chromadb(
        self,
        persist_directory: Path,
        dimension: int,
        **kwargs: object,
    ) -> VectorStore:
        """Create ChromaDB adapter.

        Args:
            persist_directory: Storage directory
            dimension: Embedding dimension
            **kwargs: Additional options

        Returns:
            ChromaDBAdapter instance
        """
        from ragd.storage.adapters.chromadb import ChromaDBAdapter

        return ChromaDBAdapter(
            persist_directory=persist_directory,
            dimension=dimension,
            **kwargs,
        )

    def _create_faiss(
        self,
        persist_directory: Path,
        dimension: int,
        **kwargs: object,
    ) -> VectorStore:
        """Create FAISS adapter.

        Args:
            persist_directory: Storage directory
            dimension: Embedding dimension
            **kwargs: Additional options (index_type, nlist, nprobe)

        Returns:
            FAISSAdapter instance
        """
        from ragd.storage.adapters.faiss import FAISSAdapter

        return FAISSAdapter(
            persist_directory=persist_directory,
            dimension=dimension,
            **kwargs,
        )

    def get_default_backend(self) -> BackendType:
        """Get the default backend.

        Returns ChromaDB as default, as it's always available.

        Returns:
            Default backend type
        """
        return BackendType.CHROMADB


# Global factory instance
_factory: VectorStoreFactory | None = None


def get_factory() -> VectorStoreFactory:
    """Get the global factory instance.

    Returns:
        VectorStoreFactory singleton
    """
    global _factory
    if _factory is None:
        _factory = VectorStoreFactory()
    return _factory


def create_vector_store(
    backend: BackendType | str | None = None,
    persist_directory: Path | str | None = None,
    dimension: int = 384,
    **kwargs: object,
) -> VectorStore:
    """Convenience function to create a vector store.

    Args:
        backend: Backend type (or string name). None for default.
        persist_directory: Storage directory. None for default ~/.ragd/data
        dimension: Embedding dimension
        **kwargs: Backend-specific options

    Returns:
        VectorStore instance
    """
    factory = get_factory()

    # Handle backend type
    if backend is None:
        backend_type = factory.get_default_backend()
    elif isinstance(backend, str):
        backend_type = BackendType(backend)
    else:
        backend_type = backend

    # Handle persist directory
    if persist_directory is None:
        persist_directory = Path.home() / ".ragd" / "data"
    elif isinstance(persist_directory, str):
        persist_directory = Path(persist_directory)

    return factory.create(
        backend=backend_type,
        persist_directory=persist_directory,
        dimension=dimension,
        **kwargs,
    )
