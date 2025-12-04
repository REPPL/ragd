"""Input validation and sanitisation for ragd.

This module provides security-focused validation for user inputs including
paths, document IDs, tags, and search queries. All external input should
be validated before use.

Features:
    - Path traversal prevention
    - Document ID validation
    - Tag name validation
    - Search query sanitisation
    - Input length limits
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

# Maximum lengths for various inputs
MAX_DOCUMENT_ID_LENGTH: Final[int] = 256
MAX_TAG_NAME_LENGTH: Final[int] = 128
MAX_SEARCH_QUERY_LENGTH: Final[int] = 4096
MAX_PATH_LENGTH: Final[int] = 4096

# Patterns for validation
DOCUMENT_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$"
)
TAG_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9_:/-]*$"
)

# Characters that should be escaped in search queries
SEARCH_ESCAPE_CHARS: Final[str] = r'[]{}()^$.|*+?\\'


class ValidationError(ValueError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialise validation error.

        Args:
            message: Human-readable error message.
            field: Name of the field that failed validation.
        """
        super().__init__(message)
        self.field = field
        self.message = message


def validate_path(
    path: Path | str,
    base_dir: Path | None = None,
    must_exist: bool = False,
    allow_symlinks: bool = True,
) -> Path:
    """Validate a file path for security.

    Checks for path traversal attacks and optionally verifies the path
    is within a base directory.

    Args:
        path: Path to validate.
        base_dir: If provided, path must resolve within this directory.
        must_exist: If True, path must exist.
        allow_symlinks: If False, symlinks are rejected.

    Returns:
        Resolved, validated Path object.

    Raises:
        ValidationError: If validation fails.
    """
    if isinstance(path, str):
        path = Path(path)

    # Check length
    if len(str(path)) > MAX_PATH_LENGTH:
        raise ValidationError(
            f"Path exceeds maximum length of {MAX_PATH_LENGTH} characters",
            field="path",
        )

    # Check for null bytes (could bypass path checks)
    if "\x00" in str(path):
        raise ValidationError(
            "Path contains null bytes",
            field="path",
        )

    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError(
            f"Cannot resolve path: {e}",
            field="path",
        ) from e

    # Check symlinks if not allowed
    if not allow_symlinks and path.is_symlink():
        raise ValidationError(
            "Symbolic links are not allowed",
            field="path",
        )

    # Check base directory constraint
    if base_dir is not None:
        try:
            base_resolved = base_dir.resolve()
        except (OSError, RuntimeError) as e:
            raise ValidationError(
                f"Cannot resolve base directory: {e}",
                field="base_dir",
            ) from e

        # Ensure resolved path is within base directory
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValidationError(
                f"Path '{path}' is outside allowed directory",
                field="path",
            )

    # Check existence if required
    if must_exist and not resolved.exists():
        raise ValidationError(
            f"Path does not exist: {path}",
            field="path",
        )

    return resolved


def validate_document_id(doc_id: str) -> str:
    """Validate a document identifier.

    Document IDs must:
    - Start with alphanumeric character
    - Contain only alphanumeric, underscore, or hyphen
    - Be 1-256 characters

    Args:
        doc_id: Document identifier to validate.

    Returns:
        Validated document ID.

    Raises:
        ValidationError: If validation fails.
    """
    if not doc_id:
        raise ValidationError(
            "Document ID cannot be empty",
            field="document_id",
        )

    if len(doc_id) > MAX_DOCUMENT_ID_LENGTH:
        raise ValidationError(
            f"Document ID exceeds maximum length of {MAX_DOCUMENT_ID_LENGTH}",
            field="document_id",
        )

    if not DOCUMENT_ID_PATTERN.match(doc_id):
        raise ValidationError(
            "Document ID must start with alphanumeric and contain only "
            "alphanumeric, underscore, or hyphen characters",
            field="document_id",
        )

    return doc_id


def validate_tag_name(tag: str) -> str:
    """Validate a tag name.

    Tag names must:
    - Start with alphanumeric character
    - Contain only alphanumeric, underscore, colon, slash, or hyphen
    - Be 1-128 characters

    Colons are allowed for namespaced tags (e.g., "project:alpha").
    Slashes are allowed for hierarchical tags (e.g., "topic/ml/transformers").

    Args:
        tag: Tag name to validate.

    Returns:
        Validated tag name.

    Raises:
        ValidationError: If validation fails.
    """
    if not tag:
        raise ValidationError(
            "Tag name cannot be empty",
            field="tag",
        )

    if len(tag) > MAX_TAG_NAME_LENGTH:
        raise ValidationError(
            f"Tag name exceeds maximum length of {MAX_TAG_NAME_LENGTH}",
            field="tag",
        )

    if not TAG_NAME_PATTERN.match(tag):
        raise ValidationError(
            "Tag name must start with alphanumeric and contain only "
            "alphanumeric, underscore, colon, slash, or hyphen characters",
            field="tag",
        )

    return tag


def sanitise_search_query(query: str) -> str:
    """Sanitise a search query for safe use.

    Escapes special characters that could cause issues in search backends
    while preserving the semantic meaning of the query.

    Args:
        query: Raw search query from user.

    Returns:
        Sanitised query safe for backend use.

    Raises:
        ValidationError: If query is invalid.
    """
    if not query:
        raise ValidationError(
            "Search query cannot be empty",
            field="query",
        )

    if len(query) > MAX_SEARCH_QUERY_LENGTH:
        raise ValidationError(
            f"Search query exceeds maximum length of {MAX_SEARCH_QUERY_LENGTH}",
            field="query",
        )

    # Check for null bytes
    if "\x00" in query:
        raise ValidationError(
            "Search query contains null bytes",
            field="query",
        )

    # Escape special regex/search characters
    sanitised = query
    for char in SEARCH_ESCAPE_CHARS:
        sanitised = sanitised.replace(char, "\\" + char)

    return sanitised


def validate_limit(limit: int, max_limit: int = 1000, min_limit: int = 1) -> int:
    """Validate a limit/count parameter.

    Args:
        limit: Limit value to validate.
        max_limit: Maximum allowed value.
        min_limit: Minimum allowed value.

    Returns:
        Validated limit value.

    Raises:
        ValidationError: If limit is out of range.
    """
    if limit < min_limit:
        raise ValidationError(
            f"Limit must be at least {min_limit}",
            field="limit",
        )

    if limit > max_limit:
        raise ValidationError(
            f"Limit cannot exceed {max_limit}",
            field="limit",
        )

    return limit


def validate_file_size(
    path: Path,
    max_size_mb: float = 100.0,
) -> Path:
    """Validate file size is within limits.

    Args:
        path: Path to file to check.
        max_size_mb: Maximum file size in megabytes.

    Returns:
        Validated path.

    Raises:
        ValidationError: If file exceeds size limit.
    """
    if not path.exists():
        raise ValidationError(
            f"File does not exist: {path}",
            field="path",
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(
            f"File size ({size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)",
            field="path",
        )

    return path
