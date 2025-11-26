"""Configuration management for ragd.

This module provides configuration loading, validation, and persistence
using Pydantic models and YAML storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ragd.hardware import HardwareTier, detect_hardware, get_recommendations

# Default paths
DEFAULT_DATA_DIR = Path.home() / ".ragd"
DEFAULT_CONFIG_PATH = DEFAULT_DATA_DIR / "config.yaml"


class HardwareConfig(BaseModel):
    """Hardware configuration."""

    backend: str = "cpu"
    tier: HardwareTier = HardwareTier.STANDARD
    memory_gb: float = 8.0
    detected_at: str | None = None


class StorageConfig(BaseModel):
    """Storage configuration."""

    data_dir: Path = DEFAULT_DATA_DIR
    chroma_dir: str = "chroma"
    documents_dir: str = "documents"


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""

    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    device: str | None = None


class LLMConfig(BaseModel):
    """LLM configuration for future use."""

    provider: str = "ollama"
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""

    default_limit: int = 10
    min_score: float = 0.3  # Filter low-relevance results by default
    rerank: bool = False


class ChunkingConfig(BaseModel):
    """Text chunking configuration."""

    strategy: str = "sentence"  # sentence, fixed, recursive
    chunk_size: int = 512
    overlap: int = 50
    min_chunk_size: int = 100


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    max_size_mb: int = 100


class RagdConfig(BaseModel):
    """Main ragd configuration."""

    version: int = 1
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    @property
    def chroma_path(self) -> Path:
        """Get the ChromaDB storage path."""
        return self.storage.data_dir / self.storage.chroma_dir

    @property
    def documents_path(self) -> Path:
        """Get the documents storage path."""
        return self.storage.data_dir / self.storage.documents_dir


def create_default_config() -> RagdConfig:
    """Create a default configuration based on detected hardware.

    Returns:
        RagdConfig with defaults tuned for detected hardware
    """
    hw_info = detect_hardware()
    recommendations = get_recommendations(hw_info.tier)

    return RagdConfig(
        hardware=HardwareConfig(
            backend=hw_info.backend,
            tier=hw_info.tier,
            memory_gb=hw_info.memory_gb,
            detected_at=hw_info.detected_at,
        ),
        embedding=EmbeddingConfig(
            model=recommendations["embedding_model"],
            device=hw_info.backend if hw_info.backend != "cpu" else None,
        ),
        llm=LLMConfig(
            model=recommendations["llm_model"],
        ),
        chunking=ChunkingConfig(
            chunk_size=int(recommendations["chunk_size"]),
        ),
    )


def load_config(config_path: Path | None = None) -> RagdConfig:
    """Load configuration from file or create defaults.

    Args:
        config_path: Path to config file. Defaults to ~/.ragd/config.yaml

    Returns:
        Loaded or default configuration
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return RagdConfig.model_validate(data)

    return create_default_config()


def save_config(config: RagdConfig, config_path: Path | None = None) -> None:
    """Save configuration to file.

    Args:
        config: Configuration to save
        config_path: Path to save to. Defaults to ~/.ragd/config.yaml
    """
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict, handling Path objects
    data = _config_to_dict(config)

    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def _config_to_dict(config: RagdConfig) -> dict[str, Any]:
    """Convert config to serialisable dictionary.

    Args:
        config: Configuration to convert

    Returns:
        Dictionary safe for YAML serialisation
    """
    data = config.model_dump()

    # Convert Path objects to strings
    if "storage" in data and "data_dir" in data["storage"]:
        data["storage"]["data_dir"] = str(data["storage"]["data_dir"])

    # Convert HardwareTier enum to string
    if "hardware" in data and "tier" in data["hardware"]:
        tier = data["hardware"]["tier"]
        if hasattr(tier, "value"):
            data["hardware"]["tier"] = tier.value

    return data


def ensure_data_dir(config: RagdConfig) -> None:
    """Ensure all required data directories exist.

    Args:
        config: Configuration with paths to create
    """
    config.storage.data_dir.mkdir(parents=True, exist_ok=True)
    config.chroma_path.mkdir(parents=True, exist_ok=True)
    config.documents_path.mkdir(parents=True, exist_ok=True)


def config_exists(config_path: Path | None = None) -> bool:
    """Check if configuration file exists.

    Args:
        config_path: Path to check. Defaults to ~/.ragd/config.yaml

    Returns:
        True if config file exists
    """
    path = config_path or DEFAULT_CONFIG_PATH
    return path.exists()
