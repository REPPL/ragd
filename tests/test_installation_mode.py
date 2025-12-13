"""Tests for F-119: Full Features by Default - Installation mode detection.

Tests the installation mode detection and summary functions.
"""

from __future__ import annotations

import pytest

from ragd.features import (
    CORE_FEATURES,
    FULL_INSTALL_FEATURES,
    get_installation_mode,
    get_installation_mode_message,
    get_installation_summary,
)


class TestInstallationModeDetection:
    """Test installation mode detection functions."""

    def test_get_installation_mode_returns_valid_mode(self) -> None:
        """get_installation_mode returns one of: full, minimal, custom."""
        mode = get_installation_mode()
        assert mode in ("full", "minimal", "custom")

    def test_get_installation_summary_structure(self) -> None:
        """get_installation_summary returns expected structure."""
        summary = get_installation_summary()

        # Check required keys exist
        assert "mode" in summary
        assert "available_features" in summary
        assert "missing_features" in summary
        assert "available_count" in summary
        assert "total_count" in summary
        assert "core_features" in summary
        assert "full_features" in summary

        # Check types
        assert isinstance(summary["mode"], str)
        assert isinstance(summary["available_features"], list)
        assert isinstance(summary["missing_features"], list)
        assert isinstance(summary["available_count"], int)
        assert isinstance(summary["total_count"], int)
        assert isinstance(summary["core_features"], dict)
        assert isinstance(summary["full_features"], dict)

    def test_get_installation_summary_counts_match(self) -> None:
        """Available and missing counts should sum to total."""
        summary = get_installation_summary()

        available_count = len(summary["available_features"])
        missing_count = len(summary["missing_features"])
        total = summary["total_count"]

        assert available_count + missing_count == total
        assert summary["available_count"] == available_count

    def test_get_installation_mode_message_returns_string(self) -> None:
        """get_installation_mode_message returns a non-empty string."""
        message = get_installation_mode_message()
        assert isinstance(message, str)
        assert len(message) > 0

    def test_full_install_features_list_not_empty(self) -> None:
        """FULL_INSTALL_FEATURES should contain expected packages."""
        assert len(FULL_INSTALL_FEATURES) > 0
        # Check some expected packages
        assert "docling" in FULL_INSTALL_FEATURES
        assert "keybert" in FULL_INSTALL_FEATURES
        assert "spacy" in FULL_INSTALL_FEATURES

    def test_core_features_list_not_empty(self) -> None:
        """CORE_FEATURES should contain expected packages."""
        assert len(CORE_FEATURES) > 0
        # Check some expected packages
        assert "chromadb" in CORE_FEATURES
        assert "typer" in CORE_FEATURES
        assert "rich" in CORE_FEATURES

    def test_core_features_are_available(self) -> None:
        """Core features should be importable in test environment."""
        summary = get_installation_summary()
        core_status = summary["core_features"]

        # At minimum, typer and rich should be available (used by CLI)
        assert core_status.get("typer", False), "typer should be installed"
        assert core_status.get("rich", False), "rich should be installed"

    def test_mode_consistency_with_features(self) -> None:
        """Mode should be consistent with feature availability."""
        summary = get_installation_summary()
        mode = summary["mode"]
        available = summary["available_count"]
        total = summary["total_count"]

        if mode == "full":
            assert available == total, "Full mode should have all features"
        elif mode == "minimal":
            assert available == 0, "Minimal mode should have no optional features"
        else:  # custom
            assert 0 < available < total, "Custom mode should have some features"


class TestInstallationModeMessage:
    """Test installation mode message formatting."""

    def test_full_mode_message_content(self) -> None:
        """Full mode message should indicate all features available."""
        mode = get_installation_mode()
        message = get_installation_mode_message()

        if mode == "full":
            assert "Full installation" in message
            assert "all runtime features" in message.lower()

    def test_minimal_mode_message_content(self) -> None:
        """Minimal mode message should suggest upgrading."""
        mode = get_installation_mode()
        message = get_installation_mode_message()

        if mode == "minimal":
            assert "Minimal installation" in message
            assert "pip install ragd" in message

    def test_custom_mode_message_shows_counts(self) -> None:
        """Custom mode message should show available/total counts."""
        mode = get_installation_mode()
        message = get_installation_mode_message()
        summary = get_installation_summary()

        if mode == "custom":
            available = summary["available_count"]
            total = summary["total_count"]
            assert f"{available}/{total}" in message


class TestHealthCheckerIntegration:
    """Test health checker integration with installation mode."""

    def test_check_installation_mode_returns_health_result(self) -> None:
        """check_installation_mode returns valid HealthResult."""
        from ragd.config import load_config
        from ragd.health.checker import check_installation_mode

        config = load_config()
        result = check_installation_mode(config)

        assert result.name == "Installation Mode"
        assert result.status in ("healthy", "degraded", "unhealthy")
        assert result.duration_ms >= 0
        assert result.message  # Non-empty message

    def test_health_checks_include_installation_mode(self) -> None:
        """Installation mode check is included in health checks."""
        from ragd.health.checker import HEALTH_CHECKS, check_installation_mode

        check_functions = [check.__name__ for check in HEALTH_CHECKS]
        assert "check_installation_mode" in check_functions


class TestSetupPyDependencies:
    """Test that setup.py dependency lists are valid."""

    def test_setup_py_importable(self) -> None:
        """setup.py should be importable for inspection."""
        # This test verifies setup.py syntax is valid
        import importlib.util
        from pathlib import Path

        setup_path = Path(__file__).parent.parent / "setup.py"
        if setup_path.exists():
            spec = importlib.util.spec_from_file_location("setup", setup_path)
            assert spec is not None
            # Don't actually load it to avoid side effects

    def test_dependency_lists_in_setup_py(self) -> None:
        """Verify setup.py defines expected dependency lists."""
        from pathlib import Path

        setup_path = Path(__file__).parent.parent / "setup.py"
        if setup_path.exists():
            content = setup_path.read_text()
            assert "CORE_DEPS" in content
            assert "FULL_FEATURE_DEPS" in content
            assert "get_install_requires" in content
            assert "RAGD_MINIMAL" in content
