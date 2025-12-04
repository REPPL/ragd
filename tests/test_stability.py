"""Tests for stability and logging features (F-110 to F-118)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ragd.logging.structured import (
    LogLevel,
    LogEntry,
    StructuredLogger,
    get_logger,
    configure_logging,
    suppress_third_party_logs,
)
from ragd.ui.cli.exit_codes import (
    ExitCode,
    get_exit_code_description,
    exit_code_from_exception,
)
from ragd.ui.cli.doctor import (
    HealthCheckResult,
    HealthReport,
    check_database_exists,
    check_vector_store,
    run_health_checks,
    fix_orphaned_chunks,
)


class TestLogEntry:
    """Tests for LogEntry (F-110)."""

    def test_create(self) -> None:
        """Test creating log entry."""
        entry = LogEntry.create(
            level=LogLevel.INFO,
            message="Test message",
            operation="index",
        )

        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.operation == "index"
        assert entry.timestamp is not None

    def test_to_json(self) -> None:
        """Test JSON serialisation."""
        entry = LogEntry.create(
            level=LogLevel.INFO,
            message="Test",
            operation="search",
            file="test.pdf",
            duration_ms=123.4,
        )

        json_str = entry.to_json()
        data = json.loads(json_str)

        assert data["level"] == "INFO"
        assert data["message"] == "Test"
        assert data["operation"] == "search"
        assert data["file"] == "test.pdf"
        assert data["duration_ms"] == 123.4

    def test_to_json_extra_fields(self) -> None:
        """Test extra fields in JSON."""
        entry = LogEntry.create(
            level=LogLevel.DEBUG,
            message="Test",
            chunks=42,
            quality=0.95,
        )

        json_str = entry.to_json()
        data = json.loads(json_str)

        assert data["chunks"] == 42
        assert data["quality"] == 0.95


class TestStructuredLogger:
    """Tests for StructuredLogger (F-110)."""

    def test_default_logger(self) -> None:
        """Test default logger creation."""
        logger = StructuredLogger()

        assert logger.console_level == LogLevel.INFO
        assert logger.file_level == LogLevel.DEBUG

    def test_file_logging(self) -> None:
        """Test logging to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = StructuredLogger(log_file=log_file)

            logger.info("Test message", operation="test")
            logger.close()

            content = log_file.read_text()
            assert "Test message" in content
            assert "INFO" in content

    def test_log_levels(self) -> None:
        """Test log level methods."""
        logger = StructuredLogger()

        # These should not raise
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

    def test_level_filtering(self) -> None:
        """Test level filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = StructuredLogger(
                log_file=log_file,
                file_level=LogLevel.WARNING,
            )

            logger.debug("debug")
            logger.info("info")
            logger.warning("warning")
            logger.error("error")
            logger.close()

            content = log_file.read_text()
            assert "debug" not in content
            assert "info" not in content
            assert "warning" in content
            assert "error" in content


class TestConfigureLogging:
    """Tests for logging configuration (F-110)."""

    def test_configure_logging(self) -> None:
        """Test configuring global logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            logger = configure_logging(
                console_level=LogLevel.WARNING,
                file_level=LogLevel.DEBUG,
                log_file=log_file,
            )

            assert logger.console_level == LogLevel.WARNING
            assert logger.file_level == LogLevel.DEBUG
            logger.close()

    def test_get_logger(self) -> None:
        """Test getting global logger."""
        logger = get_logger()
        assert logger is not None


class TestSuppressThirdPartyLogs:
    """Tests for log suppression (F-110)."""

    def test_suppress_default_loggers(self) -> None:
        """Test suppressing default loggers."""
        import logging

        suppress_third_party_logs()

        # Check loggers are configured
        transformers_logger = logging.getLogger("transformers")
        assert transformers_logger.level >= logging.WARNING


class TestExitCode:
    """Tests for ExitCode (F-113)."""

    def test_exit_code_values(self) -> None:
        """Test exit code values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.USAGE_ERROR == 2
        assert ExitCode.CONFIG_ERROR == 3
        assert ExitCode.DEPENDENCY_ERROR == 4
        assert ExitCode.PARTIAL_SUCCESS == 5

    def test_get_exit_code_description(self) -> None:
        """Test getting descriptions."""
        desc = get_exit_code_description(ExitCode.SUCCESS)
        assert "success" in desc.lower()

        desc = get_exit_code_description(ExitCode.CONFIG_ERROR)
        assert "config" in desc.lower()

    def test_exit_code_from_exception(self) -> None:
        """Test determining exit code from exception."""
        assert exit_code_from_exception(KeyboardInterrupt()) == ExitCode.INTERRUPTED
        assert exit_code_from_exception(ValueError()) == ExitCode.GENERAL_ERROR


class TestHealthCheckResult:
    """Tests for HealthCheckResult (F-116)."""

    def test_create_ok(self) -> None:
        """Test creating OK result."""
        result = HealthCheckResult(
            name="Test",
            status="ok",
            message="All good",
        )

        assert result.status == "ok"
        assert result.fixable is False

    def test_create_warning(self) -> None:
        """Test creating warning result."""
        result = HealthCheckResult(
            name="Test",
            status="warning",
            message="Minor issue",
            fixable=True,
        )

        assert result.status == "warning"
        assert result.fixable is True


class TestHealthReport:
    """Tests for HealthReport (F-116)."""

    def test_empty_report(self) -> None:
        """Test empty report is healthy."""
        report = HealthReport()

        assert report.is_healthy
        assert not report.has_errors
        assert not report.has_warnings

    def test_report_with_error(self) -> None:
        """Test report with error."""
        report = HealthReport(checks=[
            HealthCheckResult(name="Test", status="error", message="Error"),
        ])

        assert not report.is_healthy
        assert report.has_errors

    def test_report_with_warning(self) -> None:
        """Test report with warning."""
        report = HealthReport(checks=[
            HealthCheckResult(name="Test", status="warning", message="Warning"),
        ])

        assert not report.is_healthy
        assert report.has_warnings
        assert not report.has_errors

    def test_fixable_issues(self) -> None:
        """Test getting fixable issues."""
        report = HealthReport(checks=[
            HealthCheckResult(name="OK", status="ok", message="Fine"),
            HealthCheckResult(name="Fixable", status="warning", message="Fix me", fixable=True),
            HealthCheckResult(name="Not Fixable", status="error", message="Broken", fixable=False),
        ])

        fixable = report.fixable_issues
        assert len(fixable) == 1
        assert fixable[0].name == "Fixable"


class TestHealthChecks:
    """Tests for health check functions (F-116)."""

    def test_check_database_exists_missing(self) -> None:
        """Test database check with missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_database_exists(Path(tmpdir))

            assert result.status == "error"
            assert "not found" in result.message.lower()

    def test_check_database_exists_present(self) -> None:
        """Test database check with existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "ragd.db"
            db_path.write_text("test")

            result = check_database_exists(Path(tmpdir))

            assert result.status == "ok"

    def test_check_vector_store_missing(self) -> None:
        """Test vector store check with missing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_vector_store(Path(tmpdir))

            assert result.status == "warning"
            assert result.fixable is True

    def test_check_vector_store_present(self) -> None:
        """Test vector store check with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chroma_path = Path(tmpdir) / "chroma"
            chroma_path.mkdir()

            result = check_vector_store(Path(tmpdir))

            assert result.status == "ok"

    def test_run_health_checks(self) -> None:
        """Test running all health checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_health_checks(Path(tmpdir))

            assert len(report.checks) > 0
            assert any(c.name == "Database" for c in report.checks)


class TestAutoFix:
    """Tests for auto-fix functionality (F-117)."""

    def test_fix_orphaned_chunks_no_db(self) -> None:
        """Test fixing with no database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            removed = fix_orphaned_chunks(Path(tmpdir))
            assert removed == 0

    def test_fix_orphaned_chunks_with_db(self) -> None:
        """Test fixing with database."""
        import sqlite3

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "ragd.db"

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY)")
            cursor.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, document_id INTEGER)")
            cursor.execute("INSERT INTO documents (id) VALUES (1)")
            cursor.execute("INSERT INTO chunks (document_id) VALUES (1)")  # Valid
            cursor.execute("INSERT INTO chunks (document_id) VALUES (999)")  # Orphan
            conn.commit()
            conn.close()

            removed = fix_orphaned_chunks(Path(tmpdir))

            # One orphan should be removed
            assert removed == 1
