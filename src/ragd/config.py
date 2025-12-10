"""Configuration management for ragd.

This module provides configuration loading, validation, and persistence
using Pydantic models and YAML storage.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    late_chunking: bool = False  # Use late chunking for context-aware embeddings
    late_chunking_model: str = "jinaai/jina-embeddings-v2-small-en"
    max_context_tokens: int = 8192  # Maximum tokens for late chunking context


class LLMConfig(BaseModel):
    """LLM configuration for future use."""

    provider: str = "ollama"
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"


class SearchConfig(BaseModel):
    """Search configuration for hybrid search."""

    mode: str = "hybrid"  # hybrid | semantic | keyword
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    rrf_k: int = 60
    bm25_k1: float = 1.2
    bm25_b: float = 0.75


class ContextualConfig(BaseModel):
    """Contextual retrieval configuration."""

    enabled: bool = False  # Disabled by default (requires Ollama)
    provider: str = "ollama"
    model: str = "llama3.2:3b"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 60
    batch_size: int = 10
    prompt_template: str = ""  # Custom prompt template (empty = use default)


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""

    default_limit: int = 10
    min_score: float = 0.55  # Filter low-relevance results (raised to reduce hallucination)
    rerank: bool = False
    contextual: ContextualConfig = Field(default_factory=ContextualConfig)


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


class MetadataConfig(BaseModel):
    """LLM-enhanced metadata extraction configuration."""

    llm_summary: bool = False  # Generate document summaries using LLM
    llm_classification: bool = False  # Auto-classify document types
    summary_model: str = "llama3.2:3b"  # Model for summary generation
    summary_max_tokens: int = 150  # Max tokens for summaries
    classification_model: str = "llama3.2:3b"  # Model for classification
    base_url: str = "http://localhost:11434"  # Ollama base URL


class NormalisationConfig(BaseModel):
    """Text normalisation configuration."""

    enabled: bool = True
    fix_spaced_letters: bool = True
    fix_word_boundaries: bool = True
    fix_line_breaks: bool = True
    fix_ocr_spelling: bool = True
    remove_boilerplate: bool = True
    boilerplate_mode: str = "aggressive"  # conservative | moderate | aggressive


class EncryptionConfig(BaseModel):
    """Encryption configuration (F-015)."""

    enabled: bool = False  # Opt-in at init
    algorithm: str = "AES-256-GCM"
    kdf: str = "argon2id"
    kdf_memory_mb: int = 64
    kdf_iterations: int = 3
    kdf_parallelism: int = 4


class SessionConfig(BaseModel):
    """Session management configuration (F-016)."""

    auto_lock_minutes: int = 5  # 0 = disabled
    failed_attempts_lockout: int = 5
    lockout_minutes: int = 15
    activity_resets_timer: bool = True


class DeletionConfig(BaseModel):
    """Secure deletion configuration (F-017)."""

    default_level: str = "standard"  # standard | secure | purge
    require_confirmation: bool = True
    audit_log: bool = True


class SecurityConfig(BaseModel):
    """Security configuration (v0.7)."""

    encryption: EncryptionConfig = Field(default_factory=EncryptionConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    deletion: DeletionConfig = Field(default_factory=DeletionConfig)


class MultiModalConfig(BaseModel):
    """Multi-modal (vision) configuration."""

    enabled: bool = False  # Disabled by default (requires ColPali)
    vision_model: str = "vidore/colpali-v1.0"
    vision_dimension: int = 128
    extract_images: bool = True
    min_image_width: int = 100  # Skip images smaller than this
    min_image_height: int = 100
    generate_captions: bool = False  # Requires Ollama with LLaVA
    caption_model: str = "llava:7b"
    caption_base_url: str = "http://localhost:11434"
    store_thumbnails: bool = True
    thumbnail_max_size: int = 256  # Max dimension for thumbnails


class DisplayConfig(BaseModel):
    """Display configuration for CLI output."""

    max_width: int = Field(default=120, ge=40, le=300)
    word_wrap: bool = True


class PromptOverrideConfig(BaseModel):
    """Custom prompt template override."""

    system: str | None = None
    user: str | None = None


class ChatPromptsConfig(BaseModel):
    """Configurable prompt settings for chat.

    Prompts can be customised via config.yaml to enable persona/role customisation.
    Built-in defaults serve as fallback when overrides are not specified.
    """

    citation_instruction: str = (
        "EVERY factual claim MUST be cited using the numbered markers [1], [2], etc. "
        "Use [1] for single source, [1;2] for multiple sources. "
        "Uncited claims are errors - if you cannot cite a claim from the context, do not make it. "
        "NEVER mention author names or publication years from the source text. "
        "NEVER create a References or Bibliography section."
    )

    # Template overrides: "template_name" → {system, user}
    overrides: dict[str, PromptOverrideConfig] = Field(
        default_factory=dict,
        description="Custom prompts per template (answer, chat, summarise, compare, refine)",
    )

    # Query rewriting prompt (for conversation context)
    query_rewrite: str = (
        "Rewrite this follow-up question to be self-contained.\n\n"
        "Conversation:\n{history}\n\n"
        "Documents cited:\n{cited_documents}\n\n"
        "Follow-up question: {question}\n\n"
        "Rewritten question (use exact document filenames when referring to papers):"
    )


class ChatConfig(BaseModel):
    """Chat session configuration."""

    temperature: float = 0.7
    max_tokens: int = 1024
    context_window: int | None = None  # None = auto-detect from model card
    history_turns: int = 5
    search_limit: int = 5
    auto_save: bool = True
    default_cite_mode: str = "numbered"  # numbered, none, inline
    min_relevance: float = 0.55  # Minimum relevance score (raised to reduce hallucination)
    # Dynamic allocation settings
    history_budget_ratio: float = 0.3  # 30% of available tokens for history
    min_history_tokens: int = 256
    min_context_tokens: int = 1024
    prompts: ChatPromptsConfig = Field(default_factory=ChatPromptsConfig)


class ModelDiscoveryConfig(BaseModel):
    """Model card auto-discovery configuration."""

    enabled: bool = True  # Enable auto-discovery for missing model cards
    auto_save_cache: bool = True  # Cache discovered cards to disk
    interactive_by_default: bool = False  # Prompt for confirmation (CLI only)
    enable_huggingface: bool = True  # Enable HuggingFace Hub fetching
    huggingface_timeout_seconds: int = 10  # HF API request timeout
    cache_ttl_days: int = 30  # Days before cached cards are refreshed


class RagdConfig(BaseModel):
    """Main ragd configuration."""

    version: int = 1
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    normalisation: NormalisationConfig = Field(default_factory=NormalisationConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    multi_modal: MultiModalConfig = Field(default_factory=MultiModalConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    model_discovery: ModelDiscoveryConfig = Field(default_factory=ModelDiscoveryConfig)

    @property
    def chroma_path(self) -> Path:
        """Get the ChromaDB storage path."""
        return self.storage.data_dir / self.storage.chroma_dir

    @property
    def documents_path(self) -> Path:
        """Get the documents storage path."""
        return self.storage.data_dir / self.storage.documents_dir

    @property
    def metadata_path(self) -> Path:
        """Get the metadata database path."""
        return self.storage.data_dir / "metadata.sqlite"

    @property
    def images_path(self) -> Path:
        """Get the images storage path."""
        return self.storage.data_dir / "images"

    @property
    def security_path(self) -> Path:
        """Get the security metadata path (salt, verification hash)."""
        return self.storage.data_dir / ".security"

    @property
    def is_encrypted(self) -> bool:
        """Check if encryption is enabled in configuration."""
        return self.security.encryption.enabled


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


def _check_config_permissions(path: Path) -> None:
    """Ensure config file has secure permissions (owner-only).

    Security: Config files should not be world-readable as they may
    contain sensitive paths or future credentials. Auto-fixes to 0600.

    Args:
        path: Path to config file
    """
    try:
        mode = os.stat(path).st_mode
        # Fix if group or other have any permissions
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            os.chmod(path, 0o600)
            logger.debug("Fixed config file permissions: %s -> 0600", path)
    except OSError:
        pass  # File may not exist or be inaccessible


def load_config(config_path: Path | None = None) -> RagdConfig:
    """Load configuration from file or create defaults.

    Args:
        config_path: Path to config file. Defaults to ~/.ragd/config.yaml

    Returns:
        Loaded or default configuration
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if path.exists():
        _check_config_permissions(path)
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
