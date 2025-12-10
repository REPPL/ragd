"""HuggingFace Hub metadata fetcher.

Fetches model metadata from the HuggingFace Hub API for models
that have corresponding HuggingFace model cards.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from ragd.models.discovery.connectivity import is_internet_available
from ragd.models.discovery.fetchers.base import FetchedMetadata

logger = logging.getLogger(__name__)


class HuggingFaceMetadataFetcher:
    """Fetch metadata from HuggingFace Hub API.

    Maps Ollama model names to their HuggingFace counterparts and
    fetches rich metadata including context length and capabilities.
    """

    HF_API_BASE = "https://huggingface.co/api/models"

    # Ollama model name -> HuggingFace model ID mappings
    # {size} is replaced with parameter count
    MODEL_MAPPINGS: dict[str, str] = {
        # Meta Llama models
        "llama3.2": "meta-llama/Llama-3.2-{size}B-Instruct",
        "llama3.1": "meta-llama/Llama-3.1-{size}B-Instruct",
        "llama3": "meta-llama/Meta-Llama-3-{size}B-Instruct",
        "llama2": "meta-llama/Llama-2-{size}b-chat-hf",
        "codellama": "codellama/CodeLlama-{size}b-Instruct-hf",
        # Qwen models
        "qwen2.5": "Qwen/Qwen2.5-{size}B-Instruct",
        "qwen2": "Qwen/Qwen2-{size}B-Instruct",
        "qwen": "Qwen/Qwen-{size}B-Chat",
        # Mistral models
        "mistral": "mistralai/Mistral-{size}B-Instruct-v0.3",
        "mixtral": "mistralai/Mixtral-8x{size}B-Instruct-v0.1",
        # Google models
        "gemma2": "google/gemma-2-{size}b-it",
        "gemma": "google/gemma-{size}b-it",
        # Microsoft models
        "phi3": "microsoft/Phi-3-mini-4k-instruct",
        "phi": "microsoft/phi-2",
        # Embedding models
        "nomic-embed-text": "nomic-ai/nomic-embed-text-v1.5",
        "all-minilm": "sentence-transformers/all-MiniLM-L6-v2",
        "bge": "BAAI/bge-{size}-en-v1.5",
        "e5": "intfloat/e5-{size}-v2",
        # DeepSeek models
        "deepseek": "deepseek-ai/deepseek-llm-{size}b-chat",
        "deepseek-coder": "deepseek-ai/deepseek-coder-{size}b-instruct",
    }

    # Known context lengths for models (fallback)
    KNOWN_CONTEXT_LENGTHS: dict[str, int] = {
        "meta-llama/Llama-3.2": 8192,
        "meta-llama/Llama-3.1": 131072,
        "Qwen/Qwen2.5": 32768,
        "mistralai/Mistral": 8192,
        "google/gemma-2": 8192,
    }

    def __init__(self, timeout_seconds: int = 10) -> None:
        """Initialise HuggingFace fetcher.

        Args:
            timeout_seconds: HTTP request timeout
        """
        self.timeout = timeout_seconds
        self._cache: dict[str, FetchedMetadata] = {}

    def fetch(self, model_id: str) -> FetchedMetadata | None:
        """Fetch metadata for a model from HuggingFace Hub.

        Args:
            model_id: Ollama model identifier (e.g., 'llama3.2:3b')

        Returns:
            FetchedMetadata if found, None otherwise
        """
        if not self.is_available():
            return None

        # Check cache
        if model_id in self._cache:
            return self._cache[model_id]

        # Map Ollama model to HuggingFace
        hf_model_id = self._map_to_huggingface(model_id)
        if not hf_model_id:
            logger.debug("No HuggingFace mapping for %s", model_id)
            return None

        # Fetch from API
        data = self._fetch_model_data(hf_model_id)
        if not data:
            return None

        # Parse response
        metadata = self._parse_response(model_id, hf_model_id, data)
        if metadata:
            self._cache[model_id] = metadata

        return metadata

    def is_available(self) -> bool:
        """Check if HuggingFace API is reachable.

        Returns:
            True if internet is available
        """
        return is_internet_available()

    def _map_to_huggingface(self, model_id: str) -> str | None:
        """Map Ollama model ID to HuggingFace model ID.

        Args:
            model_id: Ollama model identifier

        Returns:
            HuggingFace model ID or None
        """
        # Extract base name and size
        name_lower = model_id.lower()

        # Extract size parameter
        size = None
        size_match = re.search(r":?(\d+\.?\d*)b", name_lower)
        if size_match:
            size = size_match.group(1)

        # Try each mapping
        for ollama_pattern, hf_template in self.MODEL_MAPPINGS.items():
            if ollama_pattern in name_lower:
                if "{size}" in hf_template:
                    if size:
                        return hf_template.replace("{size}", size)
                    # Try without size for some models
                    continue
                return hf_template

        return None

    def _fetch_model_data(self, hf_model_id: str) -> dict[str, Any] | None:
        """Fetch model data from HuggingFace API.

        Args:
            hf_model_id: HuggingFace model identifier

        Returns:
            API response data or None
        """
        try:
            url = f"{self.HF_API_BASE}/{hf_model_id}"
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug("HuggingFace model not found: %s", hf_model_id)
            else:
                logger.debug("HuggingFace API error: %s", e)
        except Exception as e:
            logger.debug("Failed to fetch from HuggingFace: %s", e)

        return None

    def _parse_response(
        self,
        model_id: str,
        hf_model_id: str,
        data: dict[str, Any],
    ) -> FetchedMetadata | None:
        """Parse HuggingFace API response.

        Args:
            model_id: Original Ollama model ID
            hf_model_id: HuggingFace model ID
            data: API response data

        Returns:
            FetchedMetadata or None
        """
        # Determine model type from pipeline_tag
        pipeline_tag = data.get("pipeline_tag", "")
        model_type = self._infer_type_from_pipeline(pipeline_tag)

        # Extract from cardData if available
        card_data = data.get("cardData", {})

        # Get context length
        context_length = self._extract_context_length(hf_model_id, card_data)

        # Get licence
        licence = card_data.get("license") or data.get("license")

        # Get description from card
        description = None
        if "model-index" in card_data:
            model_index = card_data["model-index"]
            if model_index and isinstance(model_index, list):
                description = model_index[0].get("name")

        # Build capabilities list
        capabilities = self._infer_capabilities(pipeline_tag, card_data)

        # Extract parameter count if in model ID
        parameters = self._extract_parameters(hf_model_id)

        return FetchedMetadata(
            source="huggingface",
            model_id=model_id,
            name=data.get("id", "").split("/")[-1],
            model_type=model_type,
            parameters=parameters,
            context_length=context_length,
            description=description,
            capabilities=capabilities,
            licence=licence,
            raw_data=data,
        )

    def _infer_type_from_pipeline(self, pipeline_tag: str) -> str:
        """Infer model type from HuggingFace pipeline tag.

        Args:
            pipeline_tag: HuggingFace pipeline tag

        Returns:
            Model type string
        """
        if pipeline_tag in ["text-generation", "text2text-generation"]:
            return "llm"
        if pipeline_tag in ["feature-extraction", "sentence-similarity"]:
            return "embedding"
        if pipeline_tag == "text-classification":
            return "reranker"
        if pipeline_tag in ["image-to-text", "visual-question-answering"]:
            return "vision"
        return "llm"

    def _extract_context_length(
        self,
        hf_model_id: str,
        card_data: dict[str, Any],
    ) -> int | None:
        """Extract context length from card data or known values.

        Args:
            hf_model_id: HuggingFace model ID
            card_data: Model card data

        Returns:
            Context length or None
        """
        # Try card data first
        if "max_position_embeddings" in card_data:
            return card_data["max_position_embeddings"]

        # Check known context lengths
        for prefix, length in self.KNOWN_CONTEXT_LENGTHS.items():
            if hf_model_id.startswith(prefix):
                return length

        return None

    def _infer_capabilities(
        self,
        pipeline_tag: str,
        card_data: dict[str, Any],
    ) -> list[str]:
        """Infer capabilities from pipeline tag and card data.

        Args:
            pipeline_tag: HuggingFace pipeline tag
            card_data: Model card data

        Returns:
            List of capability strings
        """
        capabilities = []

        if pipeline_tag == "text-generation":
            capabilities.extend(["chat", "summarisation", "rag_generation"])

            # Check for code capabilities
            tags = card_data.get("tags", [])
            if any("code" in t.lower() for t in tags):
                capabilities.append("coding")

        elif pipeline_tag in ["feature-extraction", "sentence-similarity"]:
            capabilities.extend(["semantic_search", "clustering", "classification"])

        return capabilities

    def _extract_parameters(self, hf_model_id: str) -> float | None:
        """Extract parameter count from model ID.

        Args:
            hf_model_id: HuggingFace model ID

        Returns:
            Parameters in billions or None
        """
        # Try common patterns
        patterns = [
            r"-(\d+\.?\d*)B-",  # Llama-3.2-3B-
            r"-(\d+\.?\d*)b-",  # Llama-2-7b-
            r"(\d+\.?\d*)B$",  # Qwen2.5-7B
            r"-(\d+)b$",  # phi-2b
        ]

        for pattern in patterns:
            match = re.search(pattern, hf_model_id, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self._cache.clear()
