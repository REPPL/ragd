"""CLI error handling for ragd.

This module provides error handling and formatting for CLI commands,
ensuring user-friendly error messages for common issues like missing
optional dependencies.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TypeVar

import typer
from rich.console import Console

from ragd.ui.styles import print_dependency_error

F = TypeVar("F", bound=Callable[..., None])


def handle_dependency_errors(func: F) -> F:
    """Decorator to handle dependency-related errors gracefully.

    Catches DependencyError and BackendNotAvailableError exceptions
    and displays user-friendly error messages with installation instructions.

    Usage:
        @handle_dependency_errors
        def my_command(...):
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: object, **kwargs: object) -> None:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Check for DependencyError
            if e.__class__.__name__ == "DependencyError":
                _handle_dependency_error(e)

            # Check for BackendNotAvailableError
            if e.__class__.__name__ == "BackendNotAvailableError":
                _handle_backend_error(e)

            # Re-raise other exceptions
            raise

    return wrapper  # type: ignore


def _handle_dependency_error(error: Exception) -> None:
    """Handle DependencyError exceptions.

    Args:
        error: The DependencyError exception
    """
    console = Console()

    # Access attributes from DependencyError
    feature = getattr(error, "feature", "unknown")
    install_command = getattr(error, "install_command", None)
    extra_steps = getattr(error, "extra_steps", None)

    # Build install command if not provided
    if not install_command:
        install_command = f"pip install 'ragd[{feature}]'"

    print_dependency_error(console, feature, install_command, extra_steps)
    raise typer.Exit(1)


def _handle_backend_error(error: Exception) -> None:
    """Handle BackendNotAvailableError exceptions.

    Args:
        error: The BackendNotAvailableError exception
    """
    console = Console()

    # Access attributes from BackendNotAvailableError
    backend = getattr(error, "backend", None)
    reason = getattr(error, "reason", str(error))

    if backend:
        backend_name = getattr(backend, "value", str(backend))
        feature = backend_name
    else:
        feature = "backend"

    install_command = f"pip install 'ragd[{feature}]'"

    print_dependency_error(console, feature, install_command, None)
    raise typer.Exit(1)


def format_error_for_cli(error: Exception) -> str:
    """Format an exception for CLI display.

    Args:
        error: The exception to format

    Returns:
        Formatted error message string
    """
    error_class = error.__class__.__name__

    if error_class == "DependencyError":
        user_message = getattr(error, "user_message", None)
        if callable(user_message):
            return user_message()
        return str(error)

    if error_class == "BackendNotAvailableError":
        backend = getattr(error, "backend", None)
        if backend:
            return f"Backend '{getattr(backend, 'value', backend)}' not available. {getattr(error, 'reason', '')}"
        return str(error)

    # Default formatting
    return str(error)
