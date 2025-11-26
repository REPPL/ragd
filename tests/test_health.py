"""Tests for health check module."""

import tempfile
from pathlib import Path

from ragd.config import RagdConfig, StorageConfig
from ragd.health.checker import (
    HealthResult,
    check_config,
    check_dependencies,
    run_health_checks,
    HEALTH_CHECKS,
)


class TestHealthResult:
    """Tests for HealthResult dataclass."""

    def test_health_result_healthy(self) -> None:
        """Test healthy HealthResult."""
        result = HealthResult(
            name="Test Check",
            status="healthy",
            message="All good",
            duration_ms=10.5,
        )
        assert result.name == "Test Check"
        assert result.status == "healthy"
        assert result.message == "All good"
        assert result.duration_ms == 10.5
        assert result.details is None

    def test_health_result_unhealthy(self) -> None:
        """Test unhealthy HealthResult."""
        result = HealthResult(
            name="Test Check",
            status="unhealthy",
            message="Something wrong",
            duration_ms=5.0,
            details={"error": "details"},
        )
        assert result.status == "unhealthy"
        assert result.details is not None
        assert result.details["error"] == "details"


class TestHealthChecks:
    """Tests for individual health checks."""

    def test_check_config_with_existing_dir(self) -> None:
        """Test config check with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RagdConfig(
                storage=StorageConfig(data_dir=Path(tmpdir))
            )
            result = check_config(config)
            assert result.name == "Configuration"
            # Status is degraded because config file doesn't exist, but that's OK
            assert result.status in ("healthy", "degraded")
            assert result.duration_ms >= 0

    def test_check_config_with_missing_dir(self) -> None:
        """Test config check with missing directory."""
        config = RagdConfig(
            storage=StorageConfig(data_dir=Path("/nonexistent/path"))
        )
        result = check_config(config)
        assert result.name == "Configuration"
        assert result.status == "degraded"

    def test_check_dependencies(self) -> None:
        """Test dependency check."""
        config = RagdConfig()
        result = check_dependencies(config)
        assert result.name == "Dependencies"
        assert result.status == "healthy"
        assert result.details is not None
        assert "versions" in result.details


class TestRunHealthChecks:
    """Tests for run_health_checks function."""

    def test_health_checks_registered(self) -> None:
        """Test health checks are registered."""
        assert len(HEALTH_CHECKS) >= 4

    def test_run_health_checks(self) -> None:
        """Test running all health checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RagdConfig(
                storage=StorageConfig(data_dir=Path(tmpdir))
            )
            results = run_health_checks(config)
            assert len(results) == len(HEALTH_CHECKS)
            assert all(isinstance(r, HealthResult) for r in results)
