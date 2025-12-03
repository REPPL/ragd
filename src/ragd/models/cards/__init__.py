"""Model cards for LLM and embedding models.

This module provides structured metadata about models including capabilities,
hardware requirements, strengths, weaknesses, and limitations.

Terminology:
- strengths: What the model does well (operational advantages)
- weaknesses: Operational downsides (slow, high VRAM, etc.)
- limitations: Capability gaps (complex reasoning, long context, etc.)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Directory containing model card YAML files
CARDS_DIR = Path(__file__).parent


class ModelType(str, Enum):
    """Type of model."""

    LLM = "llm"
    EMBEDDING = "embedding"
    RERANKER = "reranker"
    VISION = "vision"


class ModelCapability(str, Enum):
    """Model capabilities."""

    # LLM capabilities
    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    SUMMARISATION = "summarisation"
    EXTRACTION = "extraction"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    LONG_CONTEXT = "long_context"

    # Embedding capabilities
    SEMANTIC_SEARCH = "semantic_search"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"

    # RAG-specific capabilities
    RAG_GENERATION = "rag_generation"
    RAG_EVALUATION = "rag_evaluation"
    CONTEXTUAL_RETRIEVAL = "contextual_retrieval"


@dataclass
class HardwareRequirements:
    """Hardware requirements for running a model."""

    min_ram_gb: float
    recommended_ram_gb: float
    min_vram_gb: float | None = None
    recommended_vram_gb: float | None = None
    quantisation_supported: bool = True
    cpu_inference: bool = True
    mps_inference: bool = True  # Apple Silicon
    cuda_inference: bool = True


@dataclass
class ModelCard:
    """Structured metadata about a model.

    Attributes:
        id: Unique identifier (e.g., 'llama3.2:3b')
        name: Human-readable name
        model_type: Type of model (llm, embedding, reranker)
        provider: Model provider (ollama, openai, local)
        description: Brief description of the model
        capabilities: List of model capabilities
        hardware: Hardware requirements
        strengths: Operational advantages (what it does well)
        weaknesses: Operational downsides (slow, high VRAM, etc.)
        limitations: Capability gaps (complex reasoning, long context, etc.)
        use_cases: Recommended use cases
        context_length: Maximum context length in tokens
        parameters: Model size in billions of parameters
        licence: Model licence
        metadata: Additional metadata
    """

    id: str
    name: str
    model_type: ModelType
    provider: str
    description: str
    capabilities: list[ModelCapability] = field(default_factory=list)
    hardware: HardwareRequirements | None = None
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    use_cases: list[str] = field(default_factory=list)
    context_length: int | None = None
    parameters: float | None = None
    licence: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelCard:
        """Create a ModelCard from a dictionary.

        Args:
            data: Dictionary representation of model card

        Returns:
            ModelCard instance
        """
        # Parse hardware requirements
        hardware = None
        if hw_data := data.get("hardware"):
            hardware = HardwareRequirements(
                min_ram_gb=hw_data.get("min_ram_gb", 4.0),
                recommended_ram_gb=hw_data.get("recommended_ram_gb", 8.0),
                min_vram_gb=hw_data.get("min_vram_gb"),
                recommended_vram_gb=hw_data.get("recommended_vram_gb"),
                quantisation_supported=hw_data.get("quantisation_supported", True),
                cpu_inference=hw_data.get("cpu_inference", True),
                mps_inference=hw_data.get("mps_inference", True),
                cuda_inference=hw_data.get("cuda_inference", True),
            )

        # Parse capabilities
        capabilities = []
        for cap in data.get("capabilities", []):
            try:
                capabilities.append(ModelCapability(cap))
            except ValueError:
                logger.warning("Unknown capability: %s", cap)

        # Parse model type
        model_type = ModelType(data.get("model_type", "llm"))

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            model_type=model_type,
            provider=data.get("provider", "ollama"),
            description=data.get("description", ""),
            capabilities=capabilities,
            hardware=hardware,
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            limitations=data.get("limitations", []),
            use_cases=data.get("use_cases", []),
            context_length=data.get("context_length"),
            parameters=data.get("parameters"),
            licence=data.get("licence"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of model card
        """
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "model_type": self.model_type.value,
            "provider": self.provider,
            "description": self.description,
        }

        if self.capabilities:
            result["capabilities"] = [c.value for c in self.capabilities]

        if self.hardware:
            result["hardware"] = {
                "min_ram_gb": self.hardware.min_ram_gb,
                "recommended_ram_gb": self.hardware.recommended_ram_gb,
            }
            if self.hardware.min_vram_gb is not None:
                result["hardware"]["min_vram_gb"] = self.hardware.min_vram_gb
            if self.hardware.recommended_vram_gb is not None:
                result["hardware"]["recommended_vram_gb"] = self.hardware.recommended_vram_gb
            result["hardware"]["quantisation_supported"] = self.hardware.quantisation_supported
            result["hardware"]["cpu_inference"] = self.hardware.cpu_inference
            result["hardware"]["mps_inference"] = self.hardware.mps_inference
            result["hardware"]["cuda_inference"] = self.hardware.cuda_inference

        if self.strengths:
            result["strengths"] = self.strengths
        if self.weaknesses:
            result["weaknesses"] = self.weaknesses
        if self.limitations:
            result["limitations"] = self.limitations
        if self.use_cases:
            result["use_cases"] = self.use_cases
        if self.context_length:
            result["context_length"] = self.context_length
        if self.parameters:
            result["parameters"] = self.parameters
        if self.licence:
            result["licence"] = self.licence
        if self.metadata:
            result["metadata"] = self.metadata

        return result


# Cache for loaded model cards
_model_cards_cache: dict[str, ModelCard] = {}


def load_model_card(model_id: str) -> ModelCard | None:
    """Load a model card by ID.

    Args:
        model_id: Model identifier (e.g., 'llama3.2:3b')

    Returns:
        ModelCard if found, None otherwise
    """
    # Check cache
    if model_id in _model_cards_cache:
        return _model_cards_cache[model_id]

    # Try to load from file
    # Normalise model ID to filename (replace : with -)
    filename = model_id.replace(":", "-").replace("/", "-") + ".yaml"
    card_path = CARDS_DIR / filename

    if card_path.exists():
        try:
            with open(card_path) as f:
                data = yaml.safe_load(f)
            card = ModelCard.from_dict(data)
            _model_cards_cache[model_id] = card
            return card
        except Exception as e:
            logger.warning("Failed to load model card %s: %s", model_id, e)

    # Try loading from combined cards file
    combined_path = CARDS_DIR / "_all_cards.yaml"
    if combined_path.exists():
        try:
            with open(combined_path) as f:
                all_cards = yaml.safe_load(f) or {}
            if model_id in all_cards:
                card = ModelCard.from_dict(all_cards[model_id])
                _model_cards_cache[model_id] = card
                return card
        except Exception as e:
            logger.warning("Failed to load combined cards: %s", e)

    return None


def list_model_cards(model_type: ModelType | None = None) -> list[ModelCard]:
    """List all available model cards.

    Args:
        model_type: Filter by model type (optional)

    Returns:
        List of ModelCard instances
    """
    cards = []

    # Load all YAML files in the cards directory
    for card_path in CARDS_DIR.glob("*.yaml"):
        if card_path.name.startswith("_"):
            continue  # Skip private files

        try:
            with open(card_path) as f:
                data = yaml.safe_load(f)
            if data:
                card = ModelCard.from_dict(data)
                if model_type is None or card.model_type == model_type:
                    cards.append(card)
                    _model_cards_cache[card.id] = card
        except Exception as e:
            logger.warning("Failed to load model card %s: %s", card_path, e)

    return sorted(cards, key=lambda c: c.id)


def get_installed_models(provider: str = "ollama") -> list[str]:
    """Get list of installed models for a provider.

    Args:
        provider: Model provider (default: ollama)

    Returns:
        List of installed model IDs
    """
    if provider == "ollama":
        return _get_ollama_models()
    else:
        logger.warning("Unknown provider: %s", provider)
        return []


def _get_ollama_models() -> list[str]:
    """Get list of models installed in Ollama.

    Returns:
        List of model names
    """
    import subprocess

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            # Skip header line
            models = []
            for line in lines[1:]:
                if line.strip():
                    # First column is model name
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug("Failed to get Ollama models: %s", e)

    return []


def clear_cache() -> None:
    """Clear the model cards cache."""
    _model_cards_cache.clear()
