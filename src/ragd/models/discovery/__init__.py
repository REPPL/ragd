"""Model card auto-discovery system.

Provides automatic discovery and caching of model metadata from external
sources (Ollama API, HuggingFace Hub) with offline-first architecture.
"""

from ragd.models.discovery.service import AutoDiscoveryService

__all__ = [
    "AutoDiscoveryService",
]
