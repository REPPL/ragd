"""Path utilities for ragd."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

FileType = Literal["pdf", "txt", "md", "html", "unknown"]

SUPPORTED_EXTENSIONS: dict[str, FileType] = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".text": "txt",
    ".md": "md",
    ".markdown": "md",
    ".html": "html",
    ".htm": "html",
}


def get_file_type(path: Path) -> FileType:
    """Get the file type from extension.

    Args:
        path: File path

    Returns:
        File type string
    """
    suffix = path.suffix.lower()
    return SUPPORTED_EXTENSIONS.get(suffix, "unknown")


def is_supported_file(path: Path) -> bool:
    """Check if file type is supported.

    Args:
        path: File path to check

    Returns:
        True if file type is supported
    """
    return get_file_type(path) != "unknown"


def discover_files(path: Path, recursive: bool = True) -> list[Path]:
    """Discover supported files in a path.

    Symlinks are skipped for security (prevents path traversal attacks).

    Args:
        path: File or directory path
        recursive: Whether to search recursively

    Returns:
        List of supported file paths
    """
    # Security: Skip symlinks to prevent path traversal
    if path.is_symlink():
        logger.warning("Skipping symlink: %s", path)
        return []

    if path.is_file():
        if is_supported_file(path):
            return [path]
        return []

    if not path.is_dir():
        return []

    files = []
    pattern = "**/*" if recursive else "*"

    for ext in SUPPORTED_EXTENSIONS:
        for file_path in path.glob(f"{pattern}{ext}"):
            # Security: Skip symlinks in directory traversal
            if file_path.is_symlink():
                logger.warning("Skipping symlink: %s", file_path)
                continue
            files.append(file_path)

    return sorted(files)
