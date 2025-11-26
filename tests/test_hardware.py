"""Tests for hardware detection module."""

from ragd.hardware import (
    HardwareInfo,
    HardwareTier,
    classify_tier,
    detect_backend,
    detect_hardware,
    get_memory_gb,
    get_cpu_cores,
    get_recommendations,
    TIER_RECOMMENDATIONS,
)


def test_detect_backend() -> None:
    """Test backend detection returns valid type."""
    backend, gpu_name = detect_backend()
    assert backend in ("mps", "cuda", "cpu")


def test_get_memory_gb() -> None:
    """Test memory detection returns positive value."""
    memory = get_memory_gb()
    assert memory > 0


def test_get_cpu_cores() -> None:
    """Test CPU core detection returns positive value."""
    cores = get_cpu_cores()
    assert cores > 0


def test_classify_tier_minimal() -> None:
    """Test minimal tier classification."""
    tier = classify_tier(4.0, "cpu")
    assert tier == HardwareTier.MINIMAL


def test_classify_tier_standard() -> None:
    """Test standard tier classification."""
    tier = classify_tier(12.0, "cpu")
    assert tier == HardwareTier.STANDARD


def test_classify_tier_high() -> None:
    """Test high tier classification."""
    tier = classify_tier(24.0, "cpu")
    assert tier == HardwareTier.HIGH


def test_classify_tier_extreme() -> None:
    """Test extreme tier classification."""
    tier = classify_tier(64.0, "cpu")
    assert tier == HardwareTier.EXTREME


def test_detect_hardware() -> None:
    """Test full hardware detection."""
    info = detect_hardware()
    assert isinstance(info, HardwareInfo)
    assert info.backend in ("mps", "cuda", "cpu")
    assert info.tier in HardwareTier
    assert info.memory_gb > 0
    assert info.cpu_cores > 0
    assert info.detected_at is not None


def test_get_recommendations() -> None:
    """Test tier-based recommendations."""
    for tier in HardwareTier:
        recs = get_recommendations(tier)
        assert "embedding_model" in recs
        assert "llm_model" in recs
        assert "chunk_size" in recs


def test_hardware_info_to_dict() -> None:
    """Test HardwareInfo serialisation."""
    info = HardwareInfo(
        backend="cpu",
        tier=HardwareTier.STANDARD,
        memory_gb=16.0,
        cpu_cores=8,
        gpu_name=None,
        detected_at="2024-01-01T00:00:00",
    )
    data = info.to_dict()
    assert data["backend"] == "cpu"
    assert data["tier"] == "standard"
    assert data["memory_gb"] == 16.0
    assert data["cpu_cores"] == 8
