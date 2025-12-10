"""Metadata fetchers for model card discovery.

Each fetcher retrieves model metadata from a specific source:
- OllamaMetadataFetcher: Local Ollama installation
- HuggingFaceMetadataFetcher: HuggingFace Hub API
- HeuristicInferrer: Name pattern inference (offline)
"""

from ragd.models.discovery.fetchers.base import FetchedMetadata, MetadataFetcher
from ragd.models.discovery.fetchers.heuristics import HeuristicInferrer
from ragd.models.discovery.fetchers.huggingface import HuggingFaceMetadataFetcher
from ragd.models.discovery.fetchers.ollama import OllamaMetadataFetcher

__all__ = [
    "FetchedMetadata",
    "MetadataFetcher",
    "HeuristicInferrer",
    "HuggingFaceMetadataFetcher",
    "OllamaMetadataFetcher",
]
