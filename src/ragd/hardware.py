"""Hardware detection for ragd.

This module detects system hardware capabilities and classifies them into
performance tiers for optimal configuration.

v1.0.5: Configuration exposure - thresholds now configurable.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal

import psutil

if TYPE_CHECKING:
    from ragd.config import RagdConfig


class HardwareTier(str, Enum):
    """Hardware performance tier classification."""

    MINIMAL = "minimal"  # <8GB RAM, basic CPU
    STANDARD = "standard"  # 8-16GB RAM
    HIGH = "high"  # 16-32GB RAM, GPU available
    EXTREME = "extreme"  # >32GB RAM, high-end GPU


BackendType = Literal["mps", "cuda", "cpu"]


@dataclass
class HardwareInfo:
    """Detected hardware information."""

    backend: BackendType
    tier: HardwareTier
    memory_gb: float
    cpu_cores: int
    gpu_name: str | None
    detected_at: str

    def to_dict(self) -> dict[str, str | float | int | None]:
        """Convert to dictionary for serialisation."""
        return {
            "backend": self.backend,
            "tier": self.tier.value,
            "memory_gb": self.memory_gb,
            "cpu_cores": self.cpu_cores,
            "gpu_name": self.gpu_name,
            "detected_at": self.detected_at,
        }


def detect_backend() -> tuple[BackendType, str | None]:
    """Detect the best available compute backend.

    Returns:
        Tuple of (backend_type, gpu_name if available)
    """
    system = platform.system()

    # Check for Apple Silicon MPS
    if system == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            cpu_brand = result.stdout.strip()
            if "Apple" in cpu_brand:
                return "mps", cpu_brand
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check for CUDA
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return "cuda", gpu_name
    except ImportError:
        pass

    return "cpu", None


def get_memory_gb() -> float:
    """Get total system memory in GB."""
    return psutil.virtual_memory().total / (1024**3)


def get_cpu_cores() -> int:
    """Get number of CPU cores."""
    return psutil.cpu_count(logical=False) or psutil.cpu_count() or 1


def classify_tier(
    memory_gb: float,
    backend: BackendType,
    config: RagdConfig | None = None,
) -> HardwareTier:
    """Classify hardware into a performance tier.

    Args:
        memory_gb: Total system memory in GB
        backend: Detected compute backend
        config: Optional ragd config for tier thresholds

    Returns:
        Appropriate hardware tier
    """
    # Get thresholds from config or use defaults
    if config is not None:
        thresholds = config.hardware_thresholds
        minimal_max = thresholds.minimal_max_memory_gb
        standard_max = thresholds.standard_max_memory_gb
        high_max = thresholds.high_max_memory_gb
    else:
        # Default thresholds
        minimal_max = 8
        standard_max = 16
        high_max = 32

    if memory_gb < minimal_max:
        return HardwareTier.MINIMAL
    elif memory_gb < standard_max:
        return HardwareTier.STANDARD
    elif memory_gb < high_max:
        return HardwareTier.HIGH
    else:
        return HardwareTier.EXTREME


def detect_hardware(config: RagdConfig | None = None) -> HardwareInfo:
    """Detect system hardware and classify performance tier.

    Args:
        config: Optional ragd config for tier thresholds

    Returns:
        HardwareInfo with detected capabilities
    """
    backend, gpu_name = detect_backend()
    memory_gb = get_memory_gb()
    cpu_cores = get_cpu_cores()
    tier = classify_tier(memory_gb, backend, config)

    return HardwareInfo(
        backend=backend,
        tier=tier,
        memory_gb=round(memory_gb, 2),
        cpu_cores=cpu_cores,
        gpu_name=gpu_name,
        detected_at=datetime.now().isoformat(),
    )


# Tier-based model recommendations
TIER_RECOMMENDATIONS: dict[HardwareTier, dict[str, str]] = {
    HardwareTier.MINIMAL: {
        "embedding_model": "all-MiniLM-L6-v2",
        "llm_model": "llama3.2:1b",
        "chunk_size": "256",
    },
    HardwareTier.STANDARD: {
        "embedding_model": "all-MiniLM-L6-v2",
        "llm_model": "llama3.2:3b",
        "chunk_size": "512",
    },
    HardwareTier.HIGH: {
        "embedding_model": "all-mpnet-base-v2",
        "llm_model": "llama3.1:8b",
        "chunk_size": "512",
    },
    HardwareTier.EXTREME: {
        "embedding_model": "all-mpnet-base-v2",
        "llm_model": "llama3.1:70b",  # Fallback - init uses dynamic detection
        "chunk_size": "1024",
    },
}


def get_recommendations(tier: HardwareTier) -> dict[str, str]:
    """Get model recommendations for a given tier.

    Args:
        tier: Hardware performance tier

    Returns:
        Dictionary of recommended settings
    """
    return TIER_RECOMMENDATIONS.get(tier, TIER_RECOMMENDATIONS[HardwareTier.STANDARD])


# Extreme tier model candidates (in preference order)
EXTREME_TIER_MODELS = [
    "llama3.1:70b",
    "qwen2.5:32b",
    "mixtral:8x22b",
    "command-r-plus",
    "llama3.3:70b",
    "deepseek-coder:33b",
]


def get_extreme_tier_model(installed_models: list[str] | None = None) -> str:
    """Get the best LLM model for EXTREME tier.

    Checks installed models first, returns first available extreme-tier model.
    Falls back to llama3.1:70b (recommended for download) if none installed.

    Args:
        installed_models: List of installed model names (from Ollama).
                         If None, returns default recommendation.

    Returns:
        Model name to use for EXTREME tier
    """
    if installed_models is None:
        return TIER_RECOMMENDATIONS[HardwareTier.EXTREME]["llm_model"]

    # Normalise model names for comparison (handle tags like :latest)
    installed_base = {m.split(":")[0].lower() for m in installed_models}
    installed_full = {m.lower() for m in installed_models}

    # Check for installed extreme-tier models
    for model in EXTREME_TIER_MODELS:
        model_base = model.split(":")[0].lower()
        # Check both full name and base name
        if model.lower() in installed_full or model_base in installed_base:
            # Return the actual installed name if we matched on base
            for installed in installed_models:
                if installed.lower().startswith(model_base):
                    return installed
            return model

    # None installed, return default recommendation
    return TIER_RECOMMENDATIONS[HardwareTier.EXTREME]["llm_model"]
