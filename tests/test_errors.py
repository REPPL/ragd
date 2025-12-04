"""Tests for error handling module (F-084)."""

from __future__ import annotations

import logging
from io import StringIO

import pytest

from ragd.errors import (
    AuthenticationError,
    ConfigError,
    DependencyError,
    FeatureDisabledError,
    IndexingError,
    RagdError,
    SearchError,
    StorageError,
    ValidationError,
    handle_error,
)


class TestRagdError:
    """Tests for RagdError base class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = RagdError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.hint is None
        assert error.internal is None

    def test_error_with_hint(self) -> None:
        """Test error with hint."""
        error = RagdError(
            "Cannot connect to database",
            hint="Check if the service is running",
        )
        assert error.hint == "Check if the service is running"

    def test_error_with_internal(self) -> None:
        """Test error with internal details."""
        error = RagdError(
            "Operation failed",
            internal="ConnectionError at socket.py:123",
        )
        assert error.internal == "ConnectionError at socket.py:123"

    def test_error_with_context(self) -> None:
        """Test error with additional context."""
        error = RagdError(
            "File not found",
            path="/some/path",
            operation="read",
        )
        assert error.context["path"] == "/some/path"
        assert error.context["operation"] == "read"

    def test_format_for_user_without_hint(self) -> None:
        """Test user formatting without hint."""
        error = RagdError("Error occurred")
        result = error.format_for_user()
        assert result == "Error occurred"

    def test_format_for_user_with_hint(self) -> None:
        """Test user formatting with hint."""
        error = RagdError(
            "Cannot load file",
            hint="Check file permissions",
        )
        result = error.format_for_user()
        assert "Cannot load file" in result
        assert "Hint: Check file permissions" in result

    def test_format_for_user_hint_disabled(self) -> None:
        """Test user formatting with hint disabled."""
        error = RagdError(
            "Cannot load file",
            hint="Check file permissions",
        )
        result = error.format_for_user(include_hint=False)
        assert "Cannot load file" in result
        assert "Hint:" not in result

    def test_format_for_log(self) -> None:
        """Test log formatting includes all details."""
        error = RagdError(
            "Operation failed",
            internal="Stack trace here",
            operation="index",
        )
        result = error.format_for_log()
        assert "Operation failed" in result
        assert "Stack trace here" in result
        assert "operation" in result


class TestErrorHierarchy:
    """Tests for error type hierarchy."""

    def test_config_error(self) -> None:
        """Test ConfigError."""
        error = ConfigError("Invalid configuration")
        assert error.exit_code == 3
        assert isinstance(error, RagdError)

    def test_storage_error(self) -> None:
        """Test StorageError."""
        error = StorageError("Database locked")
        assert error.exit_code == 1
        assert isinstance(error, RagdError)

    def test_indexing_error(self) -> None:
        """Test IndexingError."""
        error = IndexingError("Failed to extract text")
        assert error.exit_code == 5  # Partial success
        assert isinstance(error, RagdError)

    def test_search_error(self) -> None:
        """Test SearchError."""
        error = SearchError("Query syntax error")
        assert error.exit_code == 1
        assert isinstance(error, RagdError)

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid password")
        assert error.exit_code == 1
        assert isinstance(error, RagdError)


class TestDependencyError:
    """Tests for DependencyError."""

    def test_with_package(self) -> None:
        """Test error with package name."""
        error = DependencyError(
            "OCR functionality requires paddleocr",
            package="paddleocr",
        )
        assert "paddleocr" in str(error.hint)
        assert "pip install" in str(error.hint)

    def test_with_install_command(self) -> None:
        """Test error with custom install command."""
        error = DependencyError(
            "SQLCipher required for encryption",
            install_command="pip install ragd[encryption]",
        )
        assert error.hint == "Install with: pip install ragd[encryption]"

    def test_without_package(self) -> None:
        """Test error without package info."""
        error = DependencyError("Missing dependency")
        assert error.hint is None


class TestValidationError:
    """Tests for ValidationError."""

    def test_with_field(self) -> None:
        """Test error with field name."""
        error = ValidationError(
            "Invalid document ID",
            field="document_id",
        )
        assert error.field == "document_id"
        assert error.exit_code == 2  # Usage error


class TestFeatureDisabledError:
    """Tests for FeatureDisabledError."""

    def test_with_enable_hint(self) -> None:
        """Test error with enable hint."""
        error = FeatureDisabledError(
            "Encryption is not enabled",
            feature="encryption",
            enable_hint="Run 'ragd init --encrypted' to enable",
        )
        assert error.feature == "encryption"
        assert "ragd init" in str(error.hint)


class TestHandleError:
    """Tests for handle_error function."""

    def test_handles_ragd_error(self) -> None:
        """Test handling of RagdError."""
        error = RagdError(
            "Something failed",
            hint="Try again",
        )
        message, code = handle_error(error)

        assert "Something failed" in message
        assert "Hint: Try again" in message
        assert code == 1

    def test_respects_exit_code(self) -> None:
        """Test that exit code is respected."""
        error = ConfigError("Bad config")
        _, code = handle_error(error)
        assert code == 3

    def test_logs_internal_details(self) -> None:
        """Test that internal details are logged."""
        logger = logging.getLogger("test")
        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        error = RagdError(
            "Public message",
            internal="Secret internal detail",
        )
        message, _ = handle_error(error, logger=logger)

        # User message should not contain internal
        assert "Secret internal" not in message

    def test_debug_mode_shows_internal(self) -> None:
        """Test that debug mode shows internal details."""
        error = RagdError(
            "Public message",
            internal="Internal detail for debugging",
        )
        message, _ = handle_error(error, debug=True)

        assert "Internal detail for debugging" in message

    def test_handles_generic_exception(self) -> None:
        """Test handling of non-RagdError exceptions."""
        error = ValueError("Something unexpected")
        message, code = handle_error(error)

        assert "unexpected error" in message.lower()
        assert code == 1

    def test_generic_exception_shows_traceback_in_debug(self) -> None:
        """Test that generic exceptions show details in debug mode."""
        error = ValueError("Unexpected")
        message, _ = handle_error(error, debug=True)

        # Should show the error message
        assert "Unexpected" in message
