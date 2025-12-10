"""Ollama metadata fetcher.

Fetches model metadata from the local Ollama installation via API.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from ragd.models.discovery.connectivity import is_ollama_available
from ragd.models.discovery.fetchers.base import FetchedMetadata

logger = logging.getLogger(__name__)


class OllamaMetadataFetcher:
    """Fetch metadata from local Ollama installation.

    Uses the Ollama API /api/tags endpoint to get model information.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        """Initialise Ollama fetcher.

        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url
        self._models_cache: dict[str, dict[str, Any]] | None = None

    def fetch(self, model_id: str) -> FetchedMetadata | None:
        """Fetch metadata for a model from Ollama.

        Args:
            model_id: Model identifier (e.g., 'llama3.2:3b')

        Returns:
            FetchedMetadata if model found, None otherwise
        """
        if not self.is_available():
            return None

        # Get all models (cached)
        models = self._get_all_models()
        if models is None:
            return None

        # Find matching model
        model_data = models.get(model_id)
        if model_data is None:
            # Try base name without tag
            base_name = model_id.split(":")[0]
            for name, data in models.items():
                if name.startswith(base_name):
                    model_data = data
                    model_id = name  # Use actual name
                    break

        if model_data is None:
            logger.debug("Model %s not found in Ollama", model_id)
            return None

        return self._parse_model_data(model_id, model_data)

    def is_available(self) -> bool:
        """Check if Ollama is reachable.

        Returns:
            True if Ollama API is responding
        """
        return is_ollama_available(self.base_url)

    def _get_all_models(self) -> dict[str, dict[str, Any]] | None:
        """Get all models from Ollama API.

        Returns:
            Dictionary mapping model names to their data, or None on error
        """
        if self._models_cache is not None:
            return self._models_cache

        try:
            url = f"{self.base_url}/api/tags"
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            models = {}
            for model in data.get("models", []):
                name = model.get("name", "")
                if name:
                    models[name] = model

            self._models_cache = models
            return models

        except Exception as e:
            logger.debug("Failed to fetch Ollama models: %s", e)
            return None

    def _parse_model_data(
        self, model_id: str, data: dict[str, Any]
    ) -> FetchedMetadata:
        """Parse Ollama API response into FetchedMetadata.

        Args:
            model_id: Model identifier
            data: Raw API response data

        Returns:
            FetchedMetadata instance
        """
        details = data.get("details", {})

        # Extract parameter size (e.g., "3.2B" -> 3.2)
        parameters = None
        param_str = details.get("parameter_size", "")
        if param_str:
            try:
                # Remove 'B' suffix and parse
                parameters = float(param_str.rstrip("Bb"))
            except ValueError:
                pass

        # Extract family
        family = details.get("family")
        families = details.get("families", [])
        if not family and families:
            family = families[0]

        # Extract quantisation
        quantisation = details.get("quantization_level")

        # Estimate RAM from model size (bytes)
        hardware_min_ram = None
        size_bytes = data.get("size")
        if size_bytes:
            # Convert to GB with 20% overhead
            hardware_min_ram = round((size_bytes / (1024**3)) * 1.2, 1)

        # Generate human-readable name
        name = self._generate_name(model_id, family, parameters)

        # Infer model type from family
        model_type = self._infer_type(model_id, family)

        return FetchedMetadata(
            source="ollama",
            model_id=model_id,
            name=name,
            model_type=model_type,
            family=family,
            parameters=parameters,
            quantisation=quantisation,
            hardware_min_ram_gb=hardware_min_ram,
            raw_data=data,
        )

    def _generate_name(
        self,
        model_id: str,
        family: str | None,
        parameters: float | None,
    ) -> str:
        """Generate human-readable name.

        Args:
            model_id: Model identifier
            family: Model family
            parameters: Parameter count

        Returns:
            Human-readable name
        """
        parts = []

        if family:
            parts.append(family.capitalize())

        if parameters:
            if parameters >= 1:
                parts.append(f"{parameters:.1f}B".rstrip("0").rstrip(".") + "B")
            else:
                parts.append(f"{int(parameters * 1000)}M")

        if not parts:
            # Fall back to model ID
            return model_id.replace(":", " ").replace("-", " ").title()

        return " ".join(parts)

    def _infer_type(self, model_id: str, family: str | None) -> str:
        """Infer model type from ID and family.

        Args:
            model_id: Model identifier
            family: Model family

        Returns:
            Model type string
        """
        name_lower = model_id.lower()

        # Check for embedding patterns
        if any(p in name_lower for p in ["embed", "minilm", "bge", "nomic", "jina"]):
            return "embedding"

        # Check for vision patterns
        if any(p in name_lower for p in ["llava", "vision", "moondream"]):
            return "vision"

        # Check for reranker patterns
        if any(p in name_lower for p in ["rerank", "cross-encoder"]):
            return "reranker"

        return "llm"

    def clear_cache(self) -> None:
        """Clear the models cache."""
        self._models_cache = None
