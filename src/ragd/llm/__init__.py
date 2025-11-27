"""LLM client module for ragd.

Provides LLM integration for contextual retrieval and other features.
Primary support is for Ollama (local, free), with potential for other providers.
"""

from ragd.llm.client import LLMClient, LLMResponse
from ragd.llm.metadata import (
    EnhancedMetadata,
    LLMMetadataEnhancer,
    create_metadata_enhancer,
)
from ragd.llm.ollama import OllamaClient, OllamaError

__all__ = [
    "LLMClient",
    "LLMResponse",
    "OllamaClient",
    "OllamaError",
    # Metadata enhancement
    "LLMMetadataEnhancer",
    "EnhancedMetadata",
    "create_metadata_enhancer",
]
