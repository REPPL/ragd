"""Hardware detection for ragd.

This module detects system hardware capabilities and classifies them into
performance tiers for optimal configuration.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal

import psutil


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


def classify_tier(memory_gb: float, backend: BackendType) -> HardwareTier:
    """Classify hardware into a performance tier.

    Args:
        memory_gb: Total system memory in GB
        backend: Detected compute backend

    Returns:
        Appropriate hardware tier
    """
    if memory_gb < 8:
        return HardwareTier.MINIMAL
    elif memory_gb < 16:
        return HardwareTier.STANDARD
    elif memory_gb < 32:
        return HardwareTier.HIGH
    else:
        return HardwareTier.EXTREME


def detect_hardware() -> HardwareInfo:
    """Detect system hardware and classify performance tier.

    Returns:
        HardwareInfo with detected capabilities
    """
    backend, gpu_name = detect_backend()
    memory_gb = get_memory_gb()
    cpu_cores = get_cpu_cores()
    tier = classify_tier(memory_gb, backend)

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
        "llm_model": "qwen2.5:72b",
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
