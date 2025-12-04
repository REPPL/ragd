"""Tests for configuration tools (F-088, F-096, F-097)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ragd.ui.cli.config_debug import (
    show_effective_config,
    show_config_diff,
    show_config_source,
    validate_config,
    _config_to_dict,
    _find_differences,
)
from ragd.ui.cli.config_migration import (
    CURRENT_VERSION,
    get_config_version,
    needs_migration,
    create_backup,
    migrate_config,
    rollback_config,
    migrate_v1_to_v2,
)
from ragd.ui.cli.help_system import (
    show_extended_help,
    show_examples,
    list_help_topics,
    EXTENDED_HELP,
)
from ragd.config import RagdConfig


class TestConfigDebug:
    """Tests for configuration debugging tools (F-097)."""

    def test_config_to_dict(self) -> None:
        """Test config to dict conversion."""
        config = RagdConfig()
        data = _config_to_dict(config)

        assert isinstance(data, dict)
        assert "embedding" in data
        assert "llm" in data

    def test_find_differences_empty(self) -> None:
        """Test no differences found."""
        config1 = {"a": 1, "b": 2}
        config2 = {"a": 1, "b": 2}
        diff = _find_differences(config1, config2)
        assert diff == {}

    def test_find_differences_simple(self) -> None:
        """Test finding simple differences."""
        config1 = {"a": 1, "b": 3}
        config2 = {"a": 1, "b": 2}
        diff = _find_differences(config1, config2)
        assert diff == {"b": 3}

    def test_find_differences_nested(self) -> None:
        """Test finding nested differences."""
        config1 = {"outer": {"inner": 1}}
        config2 = {"outer": {"inner": 2}}
        diff = _find_differences(config1, config2)
        assert diff == {"outer": {"inner": 1}}


class TestConfigMigration:
    """Tests for configuration migration tools (F-096)."""

    def test_get_config_version_default(self) -> None:
        """Test default version is 1."""
        config = {}
        assert get_config_version(config) == 1

    def test_get_config_version_explicit(self) -> None:
        """Test explicit version."""
        config = {"version": 2}
        assert get_config_version(config) == 2

    def test_migrate_v1_to_v2(self) -> None:
        """Test v1 to v2 migration."""
        config = {
            "embedding": {"model": "test"},
        }
        migrated = migrate_v1_to_v2(config)

        assert migrated["version"] == 2
        assert "contextual" in migrated["retrieval"]
        assert "session" in migrated["security"]

    def test_migrate_v1_to_v2_preserves_existing(self) -> None:
        """Test migration preserves existing values."""
        config = {
            "embedding": {"model": "my-model"},
            "security": {"session": {"auto_lock_minutes": 10}},
        }
        migrated = migrate_v1_to_v2(config)

        assert migrated["embedding"]["model"] == "my-model"
        assert migrated["security"]["session"]["auto_lock_minutes"] == 10

    def test_needs_migration_new_config(self) -> None:
        """Test new config doesn't need migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            # No file exists
            needs, current, target = needs_migration(config_path)
            assert needs is False

    def test_needs_migration_old_config(self) -> None:
        """Test old config needs migration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\n")

            needs, current, target = needs_migration(config_path)
            assert needs is True
            assert current == 1
            assert target == CURRENT_VERSION

    def test_create_backup(self) -> None:
        """Test backup creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("version: 1\ntest: value\n")

            backup_path = create_backup(config_path)

            assert backup_path.exists()
            assert ".backup" in backup_path.suffix
            assert backup_path.read_text() == "version: 1\ntest: value\n"


class TestHelpSystem:
    """Tests for help system (F-089)."""

    def test_extended_help_exists(self) -> None:
        """Test extended help content exists."""
        assert len(EXTENDED_HELP) > 0
        assert "search" in EXTENDED_HELP
        assert "index" in EXTENDED_HELP

    def test_extended_help_format(self) -> None:
        """Test extended help format."""
        for topic, content in EXTENDED_HELP.items():
            assert content.strip(), f"Empty content for {topic}"
            assert "##" in content or "#" in content, f"No headers in {topic}"

    def test_show_extended_help_found(self) -> None:
        """Test showing extended help for known topic."""
        from io import StringIO
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        result = show_extended_help("search", console)
        assert result is True

    def test_show_extended_help_not_found(self) -> None:
        """Test showing extended help for unknown topic."""
        from io import StringIO
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        result = show_extended_help("nonexistent_command", console)
        assert result is False

    def test_show_examples(self) -> None:
        """Test showing examples."""
        from io import StringIO
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        result = show_examples("search", console)
        assert result is True


class TestOutputFormatting:
    """Tests for output formatting (F-090)."""

    def test_output_format_enum(self) -> None:
        """Test OutputFormat enum."""
        from ragd.ui.output import OutputFormat

        assert OutputFormat.RICH.value == "rich"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.PLAIN.value == "plain"
        assert OutputFormat.CSV.value == "csv"

    def test_get_output_format_default(self) -> None:
        """Test default output format."""
        from ragd.ui.output import get_output_format, OutputFormat

        assert get_output_format(None) == OutputFormat.RICH

    def test_get_output_format_explicit(self) -> None:
        """Test explicit output format."""
        from ragd.ui.output import get_output_format, OutputFormat

        assert get_output_format("json") == OutputFormat.JSON
        assert get_output_format("plain") == OutputFormat.PLAIN

    def test_get_output_format_env(self) -> None:
        """Test output format from environment."""
        import os
        from ragd.ui.output import get_output_format, OutputFormat

        with patch.dict(os.environ, {"RAGD_OUTPUT_FORMAT": "json"}):
            assert get_output_format(None) == OutputFormat.JSON

    def test_format_json(self) -> None:
        """Test JSON formatting."""
        from ragd.ui.output import _format_json

        data = {"key": "value", "number": 42}
        result = _format_json(data)

        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_format_csv(self) -> None:
        """Test CSV formatting."""
        from ragd.ui.output import _format_csv

        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = _format_csv(data)

        assert "name,age" in result
        assert "Alice,30" in result
        assert "Bob,25" in result

    def test_format_plain(self) -> None:
        """Test plain text formatting."""
        from ragd.ui.output import _format_plain

        data = {"key": "value", "number": 42}
        result = _format_plain(data)

        assert "key: value" in result
        assert "number: 42" in result

    def test_output_writer_success(self) -> None:
        """Test OutputWriter success message."""
        from io import StringIO
        from ragd.ui.output import OutputWriter, OutputFormat

        writer = OutputWriter(format=OutputFormat.PLAIN)
        # Capture stdout
        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        writer.success("Test message")
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert "OK: Test message" in output

    def test_output_writer_json_format(self) -> None:
        """Test OutputWriter with JSON format."""
        from io import StringIO
        from ragd.ui.output import OutputWriter, OutputFormat
        import json

        writer = OutputWriter(format=OutputFormat.JSON)
        import sys
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        writer.success("Test message")
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        data = json.loads(output)
        assert data["status"] == "success"
        assert data["message"] == "Test message"
