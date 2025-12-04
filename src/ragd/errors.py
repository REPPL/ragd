"""Error handling for ragd.

This module provides a hierarchy of user-friendly exceptions that separate
user-facing messages from internal details. Internal details are logged
but never shown to users unless --debug is enabled.

Usage:
    from ragd.errors import RagdError, ConfigError, StorageError

    raise ConfigError(
        message="Cannot load configuration file",
        hint="Run 'ragd init' to create a new configuration",
        internal=f"YAML parse error at line {line}: {detail}",
    )
"""

from __future__ import annotations

from typing import Any


class RagdError(Exception):
    """Base error for all ragd exceptions.

    Provides separation between user-facing messages and internal details.
    The message and hint are shown to users; internal details are only logged.

    Attributes:
        message: User-friendly error message.
        hint: Optional actionable suggestion for the user.
        internal: Internal details for logging (never shown to users).
        exit_code: Suggested exit code for CLI.
    """

    exit_code: int = 1  # General error

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        internal: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise error with user and internal messages.

        Args:
            message: User-friendly error message.
            hint: Optional actionable suggestion.
            internal: Internal details for logging.
            **kwargs: Additional context data.
        """
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.internal = internal
        self.context = kwargs

    def __str__(self) -> str:
        """Return user-friendly message."""
        return self.message

    def format_for_user(self, include_hint: bool = True) -> str:
        """Format error for user display.

        Args:
            include_hint: Whether to include the hint.

        Returns:
            Formatted error message.
        """
        result = self.message
        if include_hint and self.hint:
            result += f"\n\nHint: {self.hint}"
        return result

    def format_for_log(self) -> str:
        """Format error for logging with all details.

        Returns:
            Full error message including internal details.
        """
        parts = [f"Error: {self.message}"]
        if self.internal:
            parts.append(f"Internal: {self.internal}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " | ".join(parts)


class ConfigError(RagdError):
    """Configuration-related errors.

    Raised when configuration files are missing, invalid, or cannot be
    loaded. Includes hints for common fixes.
    """

    exit_code: int = 3  # Config error


class StorageError(RagdError):
    """Storage and database errors.

    Raised when vector store, metadata database, or file operations fail.
    """

    exit_code: int = 1  # General error


class IndexingError(RagdError):
    """Document indexing errors.

    Raised when document extraction, chunking, or embedding fails.
    """

    exit_code: int = 5  # Partial success (some docs may have succeeded)


class SearchError(RagdError):
    """Search operation errors.

    Raised when search queries fail or return unexpected results.
    """

    exit_code: int = 1  # General error


class DependencyError(RagdError):
    """Missing or incompatible dependency errors.

    Raised when optional dependencies are not installed or have
    version conflicts.
    """

    exit_code: int = 4  # Dependency error

    def __init__(
        self,
        message: str,
        package: str | None = None,
        install_command: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise dependency error.

        Args:
            message: User-friendly error message.
            package: Name of the missing package.
            install_command: Command to install the package.
            **kwargs: Additional context.
        """
        hint = None
        if install_command:
            hint = f"Install with: {install_command}"
        elif package:
            hint = f"Install with: pip install {package}"

        super().__init__(message, hint=hint, **kwargs)
        self.package = package
        self.install_command = install_command


class AuthenticationError(RagdError):
    """Authentication and encryption errors.

    Raised when password verification fails or encryption keys are
    unavailable.
    """

    exit_code: int = 1  # General error


class ValidationError(RagdError):
    """Input validation errors.

    Raised when user input fails validation checks.
    """

    exit_code: int = 2  # Usage error

    def __init__(
        self,
        message: str,
        field: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise validation error.

        Args:
            message: User-friendly error message.
            field: Name of the field that failed validation.
            **kwargs: Additional context.
        """
        super().__init__(message, **kwargs)
        self.field = field


class FeatureDisabledError(RagdError):
    """Feature not enabled or available.

    Raised when a feature requires configuration or dependencies
    that are not present.
    """

    exit_code: int = 1  # General error

    def __init__(
        self,
        message: str,
        feature: str,
        enable_hint: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise feature disabled error.

        Args:
            message: User-friendly error message.
            feature: Name of the disabled feature.
            enable_hint: How to enable the feature.
            **kwargs: Additional context.
        """
        super().__init__(message, hint=enable_hint, **kwargs)
        self.feature = feature


def handle_error(
    error: Exception,
    debug: bool = False,
    logger: Any | None = None,
) -> tuple[str, int]:
    """Handle an error and return user message and exit code.

    This is the central error handler that converts exceptions to
    user-friendly output. Internal details are logged but not shown
    unless debug mode is enabled.

    Args:
        error: The exception to handle.
        debug: If True, include full traceback.
        logger: Optional logger for internal details.

    Returns:
        Tuple of (user_message, exit_code).
    """
    if isinstance(error, RagdError):
        # Log internal details
        if logger and error.internal:
            logger.debug(error.format_for_log())

        # Return user message
        message = error.format_for_user()
        if debug and error.internal:
            message += f"\n\nDebug: {error.internal}"

        return message, error.exit_code

    # Generic exception - wrap in RagdError
    if debug:
        import traceback

        message = f"Unexpected error: {error}\n\n{traceback.format_exc()}"
    else:
        message = f"An unexpected error occurred: {error}"
        if logger:
            import traceback

            logger.error(f"Unexpected error: {traceback.format_exc()}")

    return message, 1
