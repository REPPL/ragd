"""Tests for configuration module."""

import tempfile
from pathlib import Path

from ragd.config import (
    RagdConfig,
    HardwareConfig,
    StorageConfig,
    EmbeddingConfig,
    ChunkingConfig,
    create_default_config,
    load_config,
    save_config,
    ensure_data_dir,
    config_exists,
)
from ragd.hardware import HardwareTier


def test_ragd_config_defaults() -> None:
    """Test RagdConfig default values."""
    config = RagdConfig()
    assert config.version == 1
    assert isinstance(config.hardware, HardwareConfig)
    assert isinstance(config.storage, StorageConfig)
    assert isinstance(config.embedding, EmbeddingConfig)
    assert isinstance(config.chunking, ChunkingConfig)


def test_config_chroma_path() -> None:
    """Test chroma_path property."""
    config = RagdConfig()
    expected = config.storage.data_dir / config.storage.chroma_dir
    assert config.chroma_path == expected


def test_config_documents_path() -> None:
    """Test documents_path property."""
    config = RagdConfig()
    expected = config.storage.data_dir / config.storage.documents_dir
    assert config.documents_path == expected


def test_create_default_config() -> None:
    """Test default config creation with hardware detection."""
    config = create_default_config()
    assert config.hardware.backend in ("mps", "cuda", "cpu")
    assert config.hardware.tier in HardwareTier
    assert config.hardware.memory_gb > 0


def test_save_and_load_config() -> None:
    """Test config save and load roundtrip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        original = RagdConfig(
            hardware=HardwareConfig(
                backend="cpu",
                tier=HardwareTier.STANDARD,
                memory_gb=16.0,
            ),
            embedding=EmbeddingConfig(
                model="test-model",
                dimension=512,
            ),
            chunking=ChunkingConfig(
                chunk_size=256,
            ),
        )

        save_config(original, config_path)
        assert config_path.exists()

        loaded = load_config(config_path)
        assert loaded.hardware.backend == original.hardware.backend
        assert loaded.hardware.tier == original.hardware.tier
        assert loaded.embedding.model == original.embedding.model
        assert loaded.chunking.chunk_size == original.chunking.chunk_size


def test_ensure_data_dir() -> None:
    """Test data directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "ragd_test"
        config = RagdConfig(
            storage=StorageConfig(data_dir=data_dir)
        )

        ensure_data_dir(config)

        assert data_dir.exists()
        assert config.chroma_path.exists()
        assert config.documents_path.exists()


def test_config_exists_false() -> None:
    """Test config_exists returns False for missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nonexistent.yaml"
        assert not config_exists(path)


def test_config_exists_true() -> None:
    """Test config_exists returns True for existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.yaml"
        path.write_text("version: 1")
        assert config_exists(path)
