"""Tests for multi-model orchestration."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ragd.llm.models import (
    ModelInfo,
    ModelNotAvailableError,
    ModelRegistry,
    ModelRouter,
    ModelsConfig,
    TaskType,
    create_model_router,
)


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_create_model_info(self):
        """Test creating ModelInfo."""
        info = ModelInfo(
            name="llama3.2:3b",
            size_bytes=2_000_000_000,
            quantisation="Q4_K_M",
            family="llama",
            parameters="3B",
        )
        assert info.name == "llama3.2:3b"
        assert info.size_bytes == 2_000_000_000
        assert info.quantisation == "Q4_K_M"

    def test_size_gb(self):
        """Test size in GB calculation."""
        info = ModelInfo(name="test", size_bytes=1024 ** 3)  # 1 GB
        assert info.size_gb == 1.0

    def test_display_size_gb(self):
        """Test display size for GB range."""
        info = ModelInfo(name="test", size_bytes=2 * 1024 ** 3)  # 2 GB
        assert "2.0 GB" in info.display_size

    def test_display_size_mb(self):
        """Test display size for MB range."""
        info = ModelInfo(name="test", size_bytes=500 * 1024 ** 2)  # 500 MB
        assert "MB" in info.display_size

    def test_from_ollama_response(self):
        """Test creating from Ollama API response."""
        data = {
            "name": "llama3.2:3b",
            "size": 2_147_483_648,
            "details": {
                "quantization_level": "Q4_K_M",
                "family": "llama",
                "parameter_size": "3B",
            },
        }
        info = ModelInfo.from_ollama_response(data)
        assert info.name == "llama3.2:3b"
        assert info.quantisation == "Q4_K_M"
        assert info.family == "llama"


class TestModelsConfig:
    """Tests for ModelsConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = ModelsConfig()
        assert config.default == "llama3.2:3b"
        assert config.complex is None
        assert config.fallback is None
        assert config.routing_enabled is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = ModelsConfig(
            default="qwen2.5:3b",
            complex="llama3.1:8b",
            fallback="llama3.2:3b",
            routing_enabled=True,
        )
        assert config.default == "qwen2.5:3b"
        assert config.complex == "llama3.1:8b"
        assert config.routing_enabled is True


class TestModelRegistry:
    """Tests for ModelRegistry."""

    def test_create_registry(self):
        """Test creating registry."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)
        assert registry._client is mock_client

    def test_list_available_empty(self):
        """Test listing when no models available."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)

        with patch.object(registry, "_get_models_raw", return_value=[]):
            models = registry.list_available()
            assert models == []

    def test_list_available_with_models(self):
        """Test listing available models."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)

        mock_data = [
            {"name": "llama3.2:3b", "size": 2_000_000_000, "details": {}},
            {"name": "qwen2.5:3b", "size": 1_900_000_000, "details": {}},
        ]

        with patch.object(registry, "_get_models_raw", return_value=mock_data):
            models = registry.list_available(refresh=True)
            assert len(models) == 2
            assert any(m.name == "llama3.2:3b" for m in models)

    def test_is_available_exact_match(self):
        """Test checking exact model availability."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)

        mock_data = [{"name": "llama3.2:3b", "size": 0, "details": {}}]

        with patch.object(registry, "_get_models_raw", return_value=mock_data):
            assert registry.is_available("llama3.2:3b") is True
            assert registry.is_available("nonexistent") is False

    def test_is_available_base_match(self):
        """Test checking model availability with base name match."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)

        mock_data = [{"name": "llama3.2:3b", "size": 0, "details": {}}]

        with patch.object(registry, "_get_models_raw", return_value=mock_data):
            # Base name should match
            assert registry.is_available("llama3.2") is True

    def test_cache_invalidation(self):
        """Test cache is invalidated after TTL."""
        mock_client = MagicMock()
        registry = ModelRegistry(mock_client)
        registry._cache_ttl_seconds = 0  # Immediate expiry

        mock_data = [{"name": "test", "size": 0, "details": {}}]

        with patch.object(registry, "_get_models_raw", return_value=mock_data):
            # First call populates cache
            registry.list_available()
            # Second call should refresh due to TTL
            registry.list_available()


class TestModelRouter:
    """Tests for ModelRouter."""

    def test_create_router(self):
        """Test creating router."""
        config = ModelsConfig()
        registry = MagicMock()
        router = ModelRouter(config=config, registry=registry)
        assert router.config is config
        assert router.registry is registry

    def test_get_model_default(self):
        """Test getting default model."""
        config = ModelsConfig(default="llama3.2:3b")
        registry = MagicMock()
        registry.is_available.return_value = True
        router = ModelRouter(config=config, registry=registry)

        model = router.get_model()
        assert model == "llama3.2:3b"

    def test_get_model_with_override(self):
        """Test getting model with override."""
        config = ModelsConfig(default="llama3.2:3b")
        registry = MagicMock()
        registry.is_available.return_value = True
        router = ModelRouter(config=config, registry=registry)

        model = router.get_model(override="qwen2.5:3b")
        assert model == "qwen2.5:3b"

    def test_get_model_override_not_available(self):
        """Test override when model not available."""
        config = ModelsConfig()
        registry = MagicMock()
        registry.is_available.return_value = False
        registry.list_available.return_value = []
        router = ModelRouter(config=config, registry=registry)

        with pytest.raises(ModelNotAvailableError):
            router.get_model(override="nonexistent")

    def test_get_model_fallback(self):
        """Test fallback when primary not available."""
        config = ModelsConfig(
            default="llama3.1:8b",
            fallback="llama3.2:3b",
        )
        registry = MagicMock()
        # Default not available, fallback is
        registry.is_available.side_effect = lambda m: m == "llama3.2:3b"
        registry.list_available.return_value = []

        router = ModelRouter(config=config, registry=registry)
        model = router.get_model()
        assert model == "llama3.2:3b"

    def test_get_model_routing_enabled(self):
        """Test task-based routing."""
        config = ModelsConfig(
            default="llama3.2:3b",
            complex="llama3.1:8b",
            routing_enabled=True,
        )
        registry = MagicMock()
        registry.is_available.return_value = True
        router = ModelRouter(config=config, registry=registry)

        # Complex task should use complex model
        model = router.get_model(task=TaskType.COMPLEX)
        assert model == "llama3.1:8b"

        # Default task should use default model
        model = router.get_model(task=TaskType.DEFAULT)
        assert model == "llama3.2:3b"

    def test_validate_config_all_available(self):
        """Test validation when all models available."""
        config = ModelsConfig(
            default="llama3.2:3b",
            complex="llama3.1:8b",
            fallback="qwen2.5:3b",
        )
        registry = MagicMock()
        registry.list_available.return_value = [
            ModelInfo(name="llama3.2:3b"),
            ModelInfo(name="llama3.1:8b"),
            ModelInfo(name="qwen2.5:3b"),
        ]
        router = ModelRouter(config=config, registry=registry)

        warnings = router.validate_config()
        assert len(warnings) == 0

    def test_validate_config_missing_models(self):
        """Test validation when models missing."""
        config = ModelsConfig(
            default="nonexistent",
            complex="also-nonexistent",
        )
        registry = MagicMock()
        registry.list_available.return_value = []
        router = ModelRouter(config=config, registry=registry)

        warnings = router.validate_config()
        assert len(warnings) >= 1


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_types(self):
        """Test task type values."""
        assert TaskType.DEFAULT.value == "default"
        assert TaskType.COMPLEX.value == "complex"
        assert TaskType.SIMPLE.value == "simple"
        assert TaskType.SUMMARISE.value == "summarise"


class TestModelNotAvailableError:
    """Tests for ModelNotAvailableError."""

    def test_error_message(self):
        """Test error message."""
        error = ModelNotAvailableError("llama3.1:70b")
        assert "llama3.1:70b" in str(error)

    def test_user_message_with_available(self):
        """Test user-friendly message with suggestions."""
        error = ModelNotAvailableError(
            "nonexistent",
            available=["llama3.2:3b", "qwen2.5:3b"],
        )
        msg = error.user_message()
        assert "nonexistent" in msg
        assert "llama3.2:3b" in msg
        assert "ollama pull" in msg

    def test_user_message_without_available(self):
        """Test user-friendly message without suggestions."""
        error = ModelNotAvailableError("test")
        msg = error.user_message()
        assert "test" in msg


class TestCreateModelRouter:
    """Tests for create_model_router helper."""

    def test_create_with_defaults(self):
        """Test creating router with defaults."""
        router = create_model_router()
        assert router.config.default == "llama3.2:3b"
        assert router.config.routing_enabled is False

    def test_create_with_custom_config(self):
        """Test creating router with custom config."""
        router = create_model_router(
            default_model="qwen2.5:3b",
            complex_model="llama3.1:8b",
            routing_enabled=True,
        )
        assert router.config.default == "qwen2.5:3b"
        assert router.config.complex == "llama3.1:8b"
        assert router.config.routing_enabled is True
