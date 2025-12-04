"""Exit codes for CLI operations (F-113).

Consistent exit codes for scripting integration.
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes for ragd CLI.

    Standard codes for scripting integration.
    """

    SUCCESS = 0
    """Operation completed successfully."""

    GENERAL_ERROR = 1
    """General/unknown error occurred."""

    USAGE_ERROR = 2
    """Invalid command usage or arguments."""

    CONFIG_ERROR = 3
    """Configuration error (missing/invalid config)."""

    DEPENDENCY_ERROR = 4
    """Missing or incompatible dependency."""

    PARTIAL_SUCCESS = 5
    """Operation partially completed (some items failed)."""

    NOT_FOUND = 6
    """Requested resource not found."""

    PERMISSION_ERROR = 7
    """Permission denied."""

    TIMEOUT_ERROR = 8
    """Operation timed out."""

    INTERRUPTED = 130
    """Operation interrupted (Ctrl+C)."""


def get_exit_code_description(code: ExitCode) -> str:
    """Get human-readable description for exit code.

    Args:
        code: Exit code

    Returns:
        Description string
    """
    descriptions = {
        ExitCode.SUCCESS: "Operation completed successfully",
        ExitCode.GENERAL_ERROR: "General error occurred",
        ExitCode.USAGE_ERROR: "Invalid command usage",
        ExitCode.CONFIG_ERROR: "Configuration error",
        ExitCode.DEPENDENCY_ERROR: "Missing dependency",
        ExitCode.PARTIAL_SUCCESS: "Partial success (some items failed)",
        ExitCode.NOT_FOUND: "Resource not found",
        ExitCode.PERMISSION_ERROR: "Permission denied",
        ExitCode.TIMEOUT_ERROR: "Operation timed out",
        ExitCode.INTERRUPTED: "Operation interrupted",
    }
    return descriptions.get(code, "Unknown exit code")


def exit_code_from_exception(exc: Exception) -> ExitCode:
    """Determine exit code from exception type.

    Args:
        exc: Exception instance

    Returns:
        Appropriate exit code
    """
    exc_type = type(exc).__name__

    if "NotFound" in exc_type or "DoesNotExist" in exc_type:
        return ExitCode.NOT_FOUND

    if "Permission" in exc_type or "Access" in exc_type:
        return ExitCode.PERMISSION_ERROR

    if "Config" in exc_type or "Configuration" in exc_type:
        return ExitCode.CONFIG_ERROR

    if "Import" in exc_type or "Dependency" in exc_type:
        return ExitCode.DEPENDENCY_ERROR

    if "Timeout" in exc_type:
        return ExitCode.TIMEOUT_ERROR

    if "Usage" in exc_type or "Argument" in exc_type:
        return ExitCode.USAGE_ERROR

    if isinstance(exc, KeyboardInterrupt):
        return ExitCode.INTERRUPTED

    return ExitCode.GENERAL_ERROR
