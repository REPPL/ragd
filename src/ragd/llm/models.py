"""Multi-model orchestration for ragd.

Provides model registry, routing, and fallback handling for
using multiple LLM models based on task type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ragd.llm.ollama import OllamaClient, OllamaError


class ModelNotAvailableError(Exception):
    """Raised when a requested model is not available."""

    def __init__(self, model: str, available: list[str] | None = None):
        self.model = model
        self.available = available or []
        super().__init__(f"Model '{model}' is not available")

    def user_message(self) -> str:
        """Get user-friendly error message."""
        msg = f"Model '{self.model}' is not available."
        if self.available:
            suggestions = ", ".join(self.available[:5])
            msg += f"\nAvailable models: {suggestions}"
        msg += "\n\nTo download this model: ollama pull " + self.model
        return msg


class TaskType(str, Enum):
    """Types of generation tasks."""

    DEFAULT = "default"
    COMPLEX = "complex"
    SIMPLE = "simple"
    SUMMARISE = "summarise"
    COMPARE = "compare"


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    size_bytes: int = 0
    quantisation: str | None = None
    family: str | None = None
    parameters: str | None = None
    loaded: bool = False
    last_used: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size_gb(self) -> float:
        """Get size in gigabytes."""
        return self.size_bytes / (1024 ** 3)

    @property
    def display_size(self) -> str:
        """Get human-readable size."""
        if self.size_bytes >= 1024 ** 3:
            return f"{self.size_gb:.1f} GB"
        elif self.size_bytes >= 1024 ** 2:
            return f"{self.size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{self.size_bytes} B"

    @classmethod
    def from_ollama_response(cls, data: dict[str, Any]) -> ModelInfo:
        """Create from Ollama API response."""
        name = data.get("name", "")
        size = data.get("size", 0)
        details = data.get("details", {})

        return cls(
            name=name,
            size_bytes=size,
            quantisation=details.get("quantization_level"),
            family=details.get("family"),
            parameters=details.get("parameter_size"),
            metadata=data,
        )


@dataclass
class ModelsConfig:
    """Configuration for model selection."""

    # Primary generation model
    default: str = "llama3.2:3b"

    # Optional: model for complex queries
    complex: str | None = None

    # Fallback if primary unavailable
    fallback: str | None = None

    # Whether routing is enabled
    routing_enabled: bool = False

    # Routing strategy
    routing_strategy: str = "manual"  # manual | task_type


class ModelRegistry:
    """Track and manage available models."""

    def __init__(self, ollama_client: OllamaClient | None = None):
        """Initialise model registry.

        Args:
            ollama_client: Ollama client instance
        """
        self._client = ollama_client
        self._cache: dict[str, ModelInfo] = {}
        self._cache_time: datetime | None = None
        self._cache_ttl_seconds = 60

    @property
    def client(self) -> OllamaClient:
        """Get or create Ollama client."""
        if self._client is None:
            self._client = OllamaClient()
        return self._client

    def list_available(self, refresh: bool = False) -> list[ModelInfo]:
        """List all models available in Ollama.

        Args:
            refresh: Force refresh from Ollama

        Returns:
            List of ModelInfo objects
        """
        # Check cache
        if not refresh and self._is_cache_valid():
            return list(self._cache.values())

        try:
            # Get models from Ollama
            models_data = self._get_models_raw()
            models = []

            for data in models_data:
                info = ModelInfo.from_ollama_response(data)
                self._cache[info.name] = info
                models.append(info)

            self._cache_time = datetime.now()
            return models

        except OllamaError:
            # Return cached data if available
            if self._cache:
                return list(self._cache.values())
            return []

    def _get_models_raw(self) -> list[dict[str, Any]]:
        """Get raw model data from Ollama API."""
        import json
        import urllib.request

        url = f"{self.client.base_url}/api/tags"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("models", [])
        except Exception:
            return []

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache or not self._cache_time:
            return False
        age = (datetime.now() - self._cache_time).total_seconds()
        return age < self._cache_ttl_seconds

    def is_available(self, model: str) -> bool:
        """Check if model is available (downloaded).

        Args:
            model: Model name to check

        Returns:
            True if model is available
        """
        models = self.list_available()

        # Check exact match
        if any(m.name == model for m in models):
            return True

        # Check base name match (e.g., "llama3.2" matches "llama3.2:3b")
        base_name = model.split(":")[0]
        return any(m.name.startswith(base_name) for m in models)

    def get_model_info(self, model: str) -> ModelInfo | None:
        """Get info for a specific model.

        Args:
            model: Model name

        Returns:
            ModelInfo or None if not found
        """
        models = self.list_available()
        for m in models:
            if m.name == model:
                return m
        return None


class ModelRouter:
    """Route requests to appropriate models."""

    def __init__(
        self,
        config: ModelsConfig | None = None,
        registry: ModelRegistry | None = None,
    ):
        """Initialise model router.

        Args:
            config: Models configuration
            registry: Model registry instance
        """
        self.config = config or ModelsConfig()
        self.registry = registry or ModelRegistry()

    def get_model(
        self,
        task: TaskType | str = TaskType.DEFAULT,
        override: str | None = None,
    ) -> str:
        """Get model for task, with optional override.

        Args:
            task: Task type for routing
            override: Manual model override

        Returns:
            Model name to use

        Raises:
            ModelNotAvailableError: If model not available
        """
        if isinstance(task, str):
            try:
                task = TaskType(task)
            except ValueError:
                task = TaskType.DEFAULT

        # Manual override takes precedence
        if override:
            if self.registry.is_available(override):
                return override
            available = [m.name for m in self.registry.list_available()]
            raise ModelNotAvailableError(override, available)

        # Task-specific model if routing enabled
        if self.config.routing_enabled:
            model = self._get_model_for_task(task)
        else:
            model = self.config.default

        # Check availability, fall back if needed
        if not self.registry.is_available(model):
            if self.config.fallback and self.registry.is_available(self.config.fallback):
                return self.config.fallback
            available = [m.name for m in self.registry.list_available()]
            raise ModelNotAvailableError(model, available)

        return model

    def _get_model_for_task(self, task: TaskType) -> str:
        """Get model for specific task type.

        Args:
            task: Task type

        Returns:
            Model name
        """
        if task == TaskType.COMPLEX and self.config.complex:
            return self.config.complex
        return self.config.default

    def validate_config(self) -> list[str]:
        """Validate model configuration.

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        available = self.registry.list_available()
        available_names = [m.name for m in available]

        # Check default model
        if not self._model_available(self.config.default, available_names):
            warnings.append(f"Default model '{self.config.default}' not available")

        # Check complex model
        if self.config.complex and not self._model_available(self.config.complex, available_names):
            warnings.append(f"Complex model '{self.config.complex}' not available")

        # Check fallback
        if self.config.fallback and not self._model_available(self.config.fallback, available_names):
            warnings.append(f"Fallback model '{self.config.fallback}' not available")

        return warnings

    def _model_available(self, model: str, available: list[str]) -> bool:
        """Check if model is in available list."""
        if model in available:
            return True
        base = model.split(":")[0]
        return any(a.startswith(base) for a in available)


def create_model_router(
    base_url: str = "http://localhost:11434",
    default_model: str = "llama3.2:3b",
    complex_model: str | None = None,
    fallback_model: str | None = None,
    routing_enabled: bool = False,
) -> ModelRouter:
    """Create a configured ModelRouter.

    Args:
        base_url: Ollama API URL
        default_model: Default model for generation
        complex_model: Optional model for complex queries
        fallback_model: Fallback if primary unavailable
        routing_enabled: Enable task-based routing

    Returns:
        Configured ModelRouter
    """
    client = OllamaClient(base_url=base_url, model=default_model)
    registry = ModelRegistry(client)

    config = ModelsConfig(
        default=default_model,
        complex=complex_model,
        fallback=fallback_model,
        routing_enabled=routing_enabled,
    )

    return ModelRouter(config=config, registry=registry)
