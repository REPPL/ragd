"""Model recommendation engine for ragd.

Recommends appropriate models based on hardware capabilities,
use case requirements, and installed models.
"""

from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum

from ragd.models.cards import (
    ModelCapability,
    ModelCard,
    ModelType,
    get_installed_models,
    list_model_cards,
    load_model_card,
)

logger = logging.getLogger(__name__)


class UseCase(str, Enum):
    """Predefined use cases for model selection."""

    QUICK_QA = "quick_qa"  # Fast Q&A, low latency priority
    RESEARCH = "research"  # In-depth analysis, quality priority
    CODING = "coding"  # Code-related queries
    SUMMARISATION = "summarisation"  # Document summarisation
    MULTILINGUAL = "multilingual"  # Non-English documents
    AGENTIC = "agentic"  # CRAG/Self-RAG evaluation
    EMBEDDING = "embedding"  # Document embedding
    CONTEXTUAL = "contextual"  # Contextual retrieval


@dataclass
class HardwareProfile:
    """Detected hardware capabilities."""

    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    has_gpu: bool
    gpu_vram_gb: float | None = None
    gpu_name: str | None = None
    is_apple_silicon: bool = False
    metal_supported: bool = False

    @classmethod
    def detect(cls) -> HardwareProfile:
        """Detect current hardware capabilities.

        Returns:
            HardwareProfile with detected specs
        """
        import os

        # Get RAM info
        try:
            import psutil

            mem = psutil.virtual_memory()
            total_ram = mem.total / (1024**3)
            available_ram = mem.available / (1024**3)
        except ImportError:
            # Fallback estimation
            total_ram = 8.0
            available_ram = 4.0

        # Get CPU cores
        cpu_cores = os.cpu_count() or 4

        # Detect Apple Silicon
        is_apple_silicon = False
        metal_supported = False
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "Apple" in result.stdout:
                    is_apple_silicon = True
                    metal_supported = True
            except Exception:
                pass

        # Detect GPU
        has_gpu = False
        gpu_vram_gb = None
        gpu_name = None

        # Check for Apple Silicon (unified memory)
        if is_apple_silicon:
            has_gpu = True
            # On Apple Silicon, GPU can use most of unified memory
            gpu_vram_gb = total_ram * 0.75  # Conservative estimate
            gpu_name = "Apple Silicon (MPS)"

        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) >= 2:
                    has_gpu = True
                    gpu_name = parts[0].strip()
                    gpu_vram_gb = float(parts[1].strip()) / 1024  # MB to GB
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return cls(
            total_ram_gb=total_ram,
            available_ram_gb=available_ram,
            cpu_cores=cpu_cores,
            has_gpu=has_gpu,
            gpu_vram_gb=gpu_vram_gb,
            gpu_name=gpu_name,
            is_apple_silicon=is_apple_silicon,
            metal_supported=metal_supported,
        )


@dataclass
class ModelRecommendation:
    """A model recommendation with reasoning."""

    model_id: str
    model_card: ModelCard | None
    score: float  # 0-1 score
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_installed: bool = False
    is_fallback: bool = False


class ModelRecommender:
    """Recommends models based on hardware and use case.

    The recommender considers:
    - Hardware capabilities (RAM, VRAM, CPU/GPU)
    - Use case requirements
    - Installed models (prioritised for immediate use)
    - Fallback chains (filtered to installed models)
    """

    # Default fallback chains per use case
    # These define preference order; at runtime, filtered to installed models
    DEFAULT_FALLBACK_CHAINS: dict[UseCase, list[str]] = {
        UseCase.QUICK_QA: [
            "llama3.2:3b",
            "phi3:mini",
            "gemma:2b",
            "llama3.2:1b",
        ],
        UseCase.RESEARCH: [
            "llama3.2:8b",
            "qwen2.5:7b",
            "mistral:7b",
            "llama3.2:3b",
        ],
        UseCase.CODING: [
            "qwen2.5:7b",
            "codellama:7b",
            "deepseek-coder:6.7b",
            "llama3.2:8b",
        ],
        UseCase.SUMMARISATION: [
            "llama3.2:8b",
            "qwen2.5:7b",
            "llama3.2:3b",
        ],
        UseCase.MULTILINGUAL: [
            "qwen2.5:7b",
            "llama3.2:8b",
            "mistral:7b",
        ],
        UseCase.AGENTIC: [
            "llama3.2:8b",
            "qwen2.5:7b",
            "mistral:7b",
        ],
        UseCase.EMBEDDING: [
            "nomic-embed-text",
            "all-minilm",
            "mxbai-embed-large",
        ],
        UseCase.CONTEXTUAL: [
            "llama3.2:3b",
            "phi3:mini",
            "llama3.2:1b",
        ],
    }

    def __init__(
        self,
        hardware: HardwareProfile | None = None,
        custom_fallback_chains: dict[UseCase, list[str]] | None = None,
    ):
        """Initialise recommender.

        Args:
            hardware: Hardware profile (auto-detected if None)
            custom_fallback_chains: Custom fallback chains to merge with defaults
        """
        self.hardware = hardware or HardwareProfile.detect()
        self.fallback_chains = dict(self.DEFAULT_FALLBACK_CHAINS)
        if custom_fallback_chains:
            self.fallback_chains.update(custom_fallback_chains)

        # Cache installed models
        self._installed_models: list[str] | None = None

    @property
    def installed_models(self) -> list[str]:
        """Get installed models (cached)."""
        if self._installed_models is None:
            self._installed_models = get_installed_models()
        return self._installed_models

    def refresh_installed_models(self) -> None:
        """Refresh the cached list of installed models."""
        self._installed_models = None

    def get_fallback_chain(
        self,
        use_case: UseCase,
        installed_only: bool = True,
    ) -> list[str]:
        """Get fallback chain for a use case.

        Args:
            use_case: The use case
            installed_only: Filter to installed models only (default True)

        Returns:
            List of model IDs in preference order
        """
        chain = self.fallback_chains.get(use_case, [])

        if installed_only:
            installed = set(self.installed_models)
            # Match by prefix to handle version tags
            chain = [
                m
                for m in chain
                if m in installed or any(i.startswith(m.split(":")[0]) for i in installed)
            ]

        return chain

    def recommend(
        self,
        use_case: UseCase | None = None,
        model_type: ModelType = ModelType.LLM,
        capabilities: list[ModelCapability] | None = None,
        prefer_installed: bool = True,
        max_recommendations: int = 3,
    ) -> list[ModelRecommendation]:
        """Recommend models based on criteria.

        Args:
            use_case: Predefined use case (optional)
            model_type: Type of model to recommend
            capabilities: Required capabilities (optional)
            prefer_installed: Prioritise installed models
            max_recommendations: Maximum number of recommendations

        Returns:
            List of ModelRecommendation in preference order
        """
        recommendations: list[ModelRecommendation] = []

        # Get candidate models
        all_cards = list_model_cards(model_type)
        installed = set(self.installed_models)

        for card in all_cards:
            score, reasons, warnings = self._score_model(
                card,
                use_case=use_case,
                capabilities=capabilities,
            )

            if score > 0:
                is_installed = card.id in installed or any(
                    i.startswith(card.id.split(":")[0]) for i in installed
                )

                # Boost installed models
                if prefer_installed and is_installed:
                    score = min(1.0, score + 0.2)
                    reasons.insert(0, "Already installed")

                recommendations.append(
                    ModelRecommendation(
                        model_id=card.id,
                        model_card=card,
                        score=score,
                        reasons=reasons,
                        warnings=warnings,
                        is_installed=is_installed,
                    )
                )

        # Sort by score (highest first)
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Add fallback from chain if use_case specified
        if use_case and len(recommendations) < max_recommendations:
            chain = self.get_fallback_chain(use_case, installed_only=prefer_installed)
            existing_ids = {r.model_id for r in recommendations}

            for model_id in chain:
                if model_id not in existing_ids:
                    card = load_model_card(model_id)
                    is_installed = model_id in installed or any(
                        i.startswith(model_id.split(":")[0]) for i in installed
                    )
                    recommendations.append(
                        ModelRecommendation(
                            model_id=model_id,
                            model_card=card,
                            score=0.5,
                            reasons=["In fallback chain for " + use_case.value],
                            is_installed=is_installed,
                            is_fallback=True,
                        )
                    )

        return recommendations[:max_recommendations]

    def _score_model(
        self,
        card: ModelCard,
        use_case: UseCase | None = None,
        capabilities: list[ModelCapability] | None = None,
    ) -> tuple[float, list[str], list[str]]:
        """Score a model based on hardware and requirements.

        Args:
            card: Model card to score
            use_case: Target use case
            capabilities: Required capabilities

        Returns:
            Tuple of (score, reasons, warnings)
        """
        score = 0.5  # Base score
        reasons: list[str] = []
        warnings: list[str] = []

        hw = self.hardware

        # Check hardware compatibility
        if card.hardware:
            # RAM check
            if hw.total_ram_gb >= card.hardware.recommended_ram_gb:
                score += 0.1
                reasons.append("Sufficient RAM")
            elif hw.total_ram_gb >= card.hardware.min_ram_gb:
                score += 0.05
                warnings.append("RAM below recommended")
            else:
                score -= 0.3
                warnings.append("Insufficient RAM")

            # GPU/VRAM check
            if hw.has_gpu and card.hardware.min_vram_gb:
                if hw.gpu_vram_gb and hw.gpu_vram_gb >= card.hardware.recommended_vram_gb:
                    score += 0.15
                    reasons.append("Optimal VRAM")
                elif hw.gpu_vram_gb and hw.gpu_vram_gb >= card.hardware.min_vram_gb:
                    score += 0.1
                    reasons.append("Sufficient VRAM")

            # Apple Silicon bonus
            if hw.is_apple_silicon and card.hardware.mps_inference:
                score += 0.05
                reasons.append("MPS acceleration available")

        # Check capabilities
        if capabilities:
            card_caps = set(card.capabilities)
            required_caps = set(capabilities)
            matched = card_caps & required_caps

            if matched == required_caps:
                score += 0.2
                reasons.append(f"All {len(required_caps)} capabilities matched")
            elif matched:
                score += 0.1 * (len(matched) / len(required_caps))
                missing = required_caps - matched
                warnings.append(f"Missing: {', '.join(c.value for c in missing)}")
            else:
                score -= 0.2
                warnings.append("No matching capabilities")

        # Use case scoring
        if use_case:
            use_case_caps = {
                UseCase.QUICK_QA: [ModelCapability.CHAT, ModelCapability.RAG_GENERATION],
                UseCase.RESEARCH: [
                    ModelCapability.REASONING,
                    ModelCapability.RAG_GENERATION,
                ],
                UseCase.CODING: [ModelCapability.CODING, ModelCapability.CHAT],
                UseCase.SUMMARISATION: [ModelCapability.SUMMARISATION],
                UseCase.MULTILINGUAL: [ModelCapability.CHAT],
                UseCase.AGENTIC: [
                    ModelCapability.RAG_EVALUATION,
                    ModelCapability.REASONING,
                ],
                UseCase.EMBEDDING: [ModelCapability.SEMANTIC_SEARCH],
                UseCase.CONTEXTUAL: [ModelCapability.CONTEXTUAL_RETRIEVAL],
            }

            required = set(use_case_caps.get(use_case, []))
            card_caps = set(card.capabilities)

            if required and required <= card_caps:
                score += 0.15
                reasons.append(f"Suited for {use_case.value}")

        # Clamp score
        score = max(0.0, min(1.0, score))

        return score, reasons, warnings

    def get_best_model(
        self,
        use_case: UseCase,
        model_type: ModelType = ModelType.LLM,
        require_installed: bool = True,
    ) -> str | None:
        """Get the single best model for a use case.

        Args:
            use_case: The use case
            model_type: Type of model
            require_installed: Only return installed models

        Returns:
            Model ID or None if no suitable model found
        """
        recommendations = self.recommend(
            use_case=use_case,
            model_type=model_type,
            prefer_installed=require_installed,
            max_recommendations=1,
        )

        if recommendations:
            rec = recommendations[0]
            if not require_installed or rec.is_installed:
                return rec.model_id

        # Fall back to chain
        chain = self.get_fallback_chain(use_case, installed_only=require_installed)
        return chain[0] if chain else None


def recommend_model(
    use_case: UseCase | str,
    model_type: ModelType = ModelType.LLM,
    require_installed: bool = True,
) -> str | None:
    """Convenience function to get a model recommendation.

    Args:
        use_case: Use case (string or UseCase enum)
        model_type: Type of model
        require_installed: Only return installed models

    Returns:
        Model ID or None
    """
    if isinstance(use_case, str):
        use_case = UseCase(use_case)

    recommender = ModelRecommender()
    return recommender.get_best_model(
        use_case=use_case,
        model_type=model_type,
        require_installed=require_installed,
    )
