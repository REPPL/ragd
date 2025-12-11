"""Tests for CLI interface."""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from ragd import __version__
from ragd.cli import app

runner = CliRunner()


def test_version() -> None:
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help() -> None:
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ragd" in result.stdout
    assert "init" in result.stdout
    assert "index" in result.stdout
    assert "search" in result.stdout
    assert "info" in result.stdout  # Renamed from status


def test_init_help() -> None:
    """Test init command help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialise" in result.stdout


def test_index_help() -> None:
    """Test index command help."""
    result = runner.invoke(app, ["index", "--help"])
    assert result.exit_code == 0
    assert "Index" in result.stdout
    assert "PDF" in result.stdout


def test_search_help() -> None:
    """Test search command help."""
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "Search" in result.stdout


def test_doctor_help() -> None:
    """Test doctor command help."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "health" in result.stdout.lower()


def test_config_help() -> None:
    """Test config command help."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "configuration" in result.stdout.lower()


def test_index_nonexistent_path() -> None:
    """Test index command with nonexistent path."""
    result = runner.invoke(app, ["index", "/nonexistent/path"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


class TestAutoInit:
    """Tests for auto-init feature on first chat/ask."""

    def test_config_exists_function(self, tmp_path: Path) -> None:
        """Test config_exists function."""
        from ragd.config import config_exists

        # Test with non-existent config
        assert config_exists(tmp_path / "nonexistent.yaml") is False

        # Test with existing config
        config_file = tmp_path / "config.yaml"
        config_file.write_text("version: 1\n")
        assert config_exists(config_file) is True

    def test_chat_help_without_init(self) -> None:
        """Test chat help works without init."""
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "chat" in result.stdout.lower()

    def test_ask_help_without_init(self) -> None:
        """Test ask help works without init."""
        result = runner.invoke(app, ["ask", "--help"])
        assert result.exit_code == 0
        assert "ask" in result.stdout.lower()

    def test_models_recommend_help(self) -> None:
        """Test models recommend help - this command exists."""
        result = runner.invoke(app, ["models", "recommend", "--help"])
        assert result.exit_code == 0
        assert "Recommend" in result.stdout or "recommend" in result.stdout.lower()

    def test_models_set_help(self) -> None:
        """Test models set help - this command exists."""
        result = runner.invoke(app, ["models", "set", "--help"])
        assert result.exit_code == 0
        assert "Set" in result.stdout or "model" in result.stdout.lower()
