"""Configuration management for ragd.

This module provides configuration loading, validation, and persistence
using Pydantic models and YAML storage.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any, Literal

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
    fix_ligature_errors: bool = True
    fix_title_ocr: bool = True
    remove_captions: bool = True
    remove_boilerplate: bool = True
    remove_zero_width_chars: bool = True
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


class IndexingConfig(BaseModel):
    """Indexing behaviour configuration (v1.0.8).

    Controls how documents are handled during indexing, including
    duplicate detection and handling policies.
    """

    # Duplicate handling policy
    duplicate_policy: Literal["skip", "overwrite", "error"] = "skip"

    # What constitutes a "duplicate"
    check_content_hash: bool = True  # Check by content hash (recommended)
    check_document_id: bool = False  # Check by document_id (path-based)

    # Exclusion patterns (glob-style)
    exclude_patterns: list[str] = Field(
        default_factory=lambda: [
            ".*",  # Hidden files
            "*~",  # Backup files
            "*.tmp",  # Temp files
        ],
        description="Glob patterns for files to exclude from indexing",
    )

    # Verbose skip reporting
    report_all_skips: bool = True  # Include all skip reasons in results


class MemoryConfig(BaseModel):
    """Memory optimisation configuration (F-124)."""

    max_peak_mb: int = 2048  # Warn if exceeded
    streaming_threshold_mb: int = 100  # Use streaming above this
    embedding_batch_size: int = 32  # Batch size for embeddings
    gc_frequency: str = "per_document"  # per_document | per_batch | manual


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
        "Resolved document references:\n{resolved_references}\n\n"
        "Follow-up question: {question}\n\n"
        "IMPORTANT: When the user refers to a document (e.g., 'the hummel paper'), "
        "use the EXACT filename from 'Resolved document references' in your rewritten query. "
        "This is critical for search accuracy.\n\n"
        "Rewritten question:"
    )


class ChatConfig(BaseModel):
    """Chat session configuration."""

    temperature: float = 0.7
    max_tokens: int = 1024
    context_window: int | None = None  # None = auto-detect from model card
    history_turns: int = 5
    search_limit: int = 15
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


# =============================================================================
# v1.0.5: Configuration Exposure Models
# =============================================================================


class PromptFileReference(BaseModel):
    """Reference to an external prompt file OR inline string.

    Supports hybrid approach: users can either reference an external file
    or provide the prompt inline in config.yaml.

    Example config.yaml usage:
        # File reference
        agentic_prompts:
          relevance_eval:
            file: ~/.ragd/prompts/agentic/relevance_eval.txt

        # Inline string
        agentic_prompts:
          query_rewrite:
            inline: |
              Rewrite this query to be more specific.
              Original: {query}
              Rewritten:
    """

    file: Path | None = None  # Path to external prompt file
    inline: str | None = None  # Inline prompt string

    def resolve(self, default: str) -> str:
        """Resolve to actual prompt string.

        Priority: file > inline > default

        Args:
            default: Default prompt to use if neither file nor inline specified

        Returns:
            Resolved prompt string
        """
        if self.file is not None:
            expanded = Path(str(self.file).replace("~", str(Path.home())))
            if expanded.exists():
                return expanded.read_text(encoding="utf-8")
            logger.warning("Prompt file not found: %s, using default", self.file)
        if self.inline is not None:
            return self.inline
        return default


class OperationParams(BaseModel):
    """LLM parameters for a specific operation.

    Allows fine-grained control over temperature and token limits
    for different operations (evaluation, generation, etc.).
    """

    temperature: float | None = None  # None = use operation default
    max_tokens: int | None = None  # None = use operation default


class AgenticParamsConfig(BaseModel):
    """Parameters for agentic RAG operations (CRAG/Self-RAG).

    Controls the behaviour of query rewriting, relevance evaluation,
    faithfulness checking, and response refinement.
    """

    # LLM parameters per operation
    relevance_eval: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.0, max_tokens=10),
        description="Parameters for relevance evaluation (deterministic)",
    )
    query_rewrite: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.3, max_tokens=100),
        description="Parameters for query rewriting",
    )
    answer_generation: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.7, max_tokens=1024),
        description="Parameters for answer generation",
    )
    faithfulness_eval: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.0, max_tokens=10),
        description="Parameters for faithfulness evaluation (deterministic)",
    )
    refine_response: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.3, max_tokens=1024),
        description="Parameters for response refinement",
    )

    # CRAG thresholds
    relevance_threshold: float = 0.6  # Minimum relevance for acceptable retrieval
    max_rewrites: int = 2  # Maximum query rewrite attempts

    # Self-RAG thresholds
    faithfulness_threshold: float = 0.7  # Minimum faithfulness score
    max_refinements: int = 1  # Maximum response refinement attempts

    # RetrievalQuality thresholds (for categorising retrieval quality)
    excellent_threshold: float = 0.8  # Score >= this = EXCELLENT
    good_threshold: float = 0.6  # Score >= this = GOOD
    poor_threshold: float = 0.4  # Score >= this = POOR, below = IRRELEVANT

    # Confidence calculation weights
    confidence_relevance_weight: float = 0.4  # Weight for relevance in confidence
    confidence_faithfulness_weight: float = 0.6  # Weight for faithfulness


class AgenticPromptsConfig(BaseModel):
    """Prompt references for agentic RAG operations.

    Each prompt can be customised via file reference or inline string.
    """

    relevance_eval: PromptFileReference | None = None
    query_rewrite: PromptFileReference | None = None
    faithfulness_eval: PromptFileReference | None = None
    refine_response: PromptFileReference | None = None


class MetadataParamsConfig(BaseModel):
    """Parameters for metadata extraction operations.

    Controls document summarisation, classification, and context generation.
    """

    # LLM parameters per operation
    summary: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.3, max_tokens=150),
        description="Parameters for document summary generation",
    )
    classification: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.0, max_tokens=20),
        description="Parameters for document classification (deterministic)",
    )
    context_generation: OperationParams = Field(
        default_factory=lambda: OperationParams(temperature=0.0, max_tokens=100),
        description="Parameters for contextual retrieval context generation",
    )

    # Text limits
    max_text_length: int = 8000  # Maximum chars to send to LLM for metadata
    max_context_length: int = 200  # Maximum chars for generated context

    # Classification categories (customisable)
    classification_categories: list[str] = Field(
        default_factory=lambda: [
            "report",
            "article",
            "documentation",
            "correspondence",
            "legal",
            "financial",
            "academic",
            "other",
        ],
        description="Valid document classification categories",
    )


class MetadataPromptsConfig(BaseModel):
    """Prompt references for metadata extraction operations."""

    summary: PromptFileReference | None = None
    classification: PromptFileReference | None = None
    context_generation: PromptFileReference | None = None


class EvaluationPromptsConfig(BaseModel):
    """Prompt references for RAG evaluation metrics."""

    faithfulness: PromptFileReference | None = None
    answer_relevancy: PromptFileReference | None = None


class SearchTuningConfig(BaseModel):
    """Fine-tuning parameters for search and retrieval.

    These parameters affect how search results are scored, combined,
    and ranked. Advanced users can tune these for their specific use case.
    """

    # BM25 normalisation
    bm25_normalisation_divisor: float = Field(
        default=10.0,
        description="Divisor for normalising BM25 scores to 0-1 range",
    )

    # Reciprocal Rank Fusion
    rrf_fetch_multiplier: int = Field(
        default=3,
        description="Multiplier for fetch limit before RRF (fetches limit * this)",
    )

    # Relevance scoring
    position_decay_factor: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Decay factor for position-weighted relevance (0-1)",
    )
    relevance_precision_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum score to consider a chunk relevant for precision",
    )


class ProcessingConfig(BaseModel):
    """Processing parameters for text handling.

    Controls tokenisation, truncation, and other text processing behaviours.
    """

    context_truncation_chars: int = Field(
        default=2000,
        description="Maximum characters for context in LLM prompts",
    )
    chars_per_token_estimate: int = Field(
        default=4,
        description="Estimated characters per token for fallback counting",
    )
    token_encoding: str = Field(
        default="cl100k_base",
        description="Tiktoken encoding name for token counting",
    )


class HardwareThresholdsConfig(BaseModel):
    """Thresholds for hardware tier classification.

    Defines memory boundaries for MINIMAL, STANDARD, HIGH, and EXTREME tiers.
    """

    minimal_max_gb: float = Field(
        default=8.0,
        description="Maximum RAM (GB) for MINIMAL tier (below this = MINIMAL)",
    )
    standard_max_gb: float = Field(
        default=16.0,
        description="Maximum RAM (GB) for STANDARD tier",
    )
    high_max_gb: float = Field(
        default=32.0,
        description="Maximum RAM (GB) for HIGH tier (above this = EXTREME)",
    )


class BoilerplateConfig(BaseModel):
    """Custom boilerplate removal configuration.

    Allows users to add custom patterns for boilerplate removal
    and site-specific patterns for web content.
    """

    custom_patterns: list[str] = Field(
        default_factory=list,
        description="Additional regex patterns to match boilerplate content",
    )
    site_patterns: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Site-specific boilerplate patterns (domain -> patterns)",
    )


class RagdConfig(BaseModel):
    """Main ragd configuration."""

    version: int = 2  # Bumped for v1.0.5 configuration exposure
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
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)  # v1.0.8
    chat: ChatConfig = Field(default_factory=ChatConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    model_discovery: ModelDiscoveryConfig = Field(default_factory=ModelDiscoveryConfig)

    # v1.0.5: Configuration exposure - advanced tuning options
    agentic_params: AgenticParamsConfig = Field(default_factory=AgenticParamsConfig)
    agentic_prompts: AgenticPromptsConfig = Field(default_factory=AgenticPromptsConfig)
    metadata_params: MetadataParamsConfig = Field(default_factory=MetadataParamsConfig)
    metadata_prompts: MetadataPromptsConfig = Field(default_factory=MetadataPromptsConfig)
    evaluation_prompts: EvaluationPromptsConfig = Field(
        default_factory=EvaluationPromptsConfig
    )
    search_tuning: SearchTuningConfig = Field(default_factory=SearchTuningConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    hardware_thresholds: HardwareThresholdsConfig = Field(
        default_factory=HardwareThresholdsConfig
    )
    boilerplate: BoilerplateConfig = Field(default_factory=BoilerplateConfig)

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
