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
    assert "status" in result.stdout
    assert "doctor" in result.stdout


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
