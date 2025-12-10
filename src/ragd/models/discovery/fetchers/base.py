"""Base classes for metadata fetchers.

Defines the FetchedMetadata dataclass and MetadataFetcher protocol
that all fetchers must implement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class FetchedMetadata:
    """Raw metadata from an external source.

    Attributes:
        source: Source identifier ("ollama", "huggingface", "heuristic")
        model_id: Original model identifier requested
        name: Human-readable name
        model_type: Type string ("llm", "embedding", "reranker", "vision")
        family: Model family (e.g., "llama", "qwen")
        parameters: Model size in billions of parameters
        context_length: Maximum context length in tokens
        quantisation: Quantisation level (e.g., "Q4_K_M")
        description: Brief description
        capabilities: List of capability strings
        licence: Model licence
        hardware_min_ram_gb: Minimum RAM in GB
        raw_data: Original response data for debugging
    """

    source: str
    model_id: str
    name: str | None = None
    model_type: str | None = None
    family: str | None = None
    parameters: float | None = None
    context_length: int | None = None
    quantisation: str | None = None
    description: str | None = None
    capabilities: list[str] = field(default_factory=list)
    licence: str | None = None
    hardware_min_ram_gb: float | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def merge_from(self, other: FetchedMetadata) -> None:
        """Merge non-None values from another FetchedMetadata.

        Updates this instance with non-None values from other.
        Does not overwrite existing non-None values.

        Args:
            other: FetchedMetadata to merge from
        """
        if self.name is None and other.name is not None:
            self.name = other.name
        if self.model_type is None and other.model_type is not None:
            self.model_type = other.model_type
        if self.family is None and other.family is not None:
            self.family = other.family
        if self.parameters is None and other.parameters is not None:
            self.parameters = other.parameters
        if self.context_length is None and other.context_length is not None:
            self.context_length = other.context_length
        if self.quantisation is None and other.quantisation is not None:
            self.quantisation = other.quantisation
        if self.description is None and other.description is not None:
            self.description = other.description
        if not self.capabilities and other.capabilities:
            self.capabilities = other.capabilities.copy()
        if self.licence is None and other.licence is not None:
            self.licence = other.licence
        if self.hardware_min_ram_gb is None and other.hardware_min_ram_gb is not None:
            self.hardware_min_ram_gb = other.hardware_min_ram_gb


@runtime_checkable
class MetadataFetcher(Protocol):
    """Protocol for metadata fetchers.

    All fetchers must implement fetch() and is_available() methods.
    """

    def fetch(self, model_id: str) -> FetchedMetadata | None:
        """Fetch metadata for a model.

        Args:
            model_id: Model identifier (e.g., 'llama3.2:3b')

        Returns:
            FetchedMetadata if found, None otherwise
        """
        ...

    def is_available(self) -> bool:
        """Check if this fetcher is available.

        Returns:
            True if fetcher can be used (e.g., network available)
        """
        ...
