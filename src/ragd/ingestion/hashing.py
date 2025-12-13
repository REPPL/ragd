"""Content hashing for change detection (F-103).

Provides efficient change detection for indexed documents.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileHash:
    """File-level hash for quick change detection."""

    path: str
    size: int
    mtime: float

    @classmethod
    def from_path(cls, path: Path) -> FileHash:
        """Create hash from file path.

        Args:
            path: Path to file

        Returns:
            FileHash instance
        """
        stat = path.stat()
        return cls(
            path=str(path.resolve()),
            size=stat.st_size,
            mtime=stat.st_mtime,
        )

    def to_string(self) -> str:
        """Convert to string for comparison."""
        return f"{self.path}:{self.size}:{self.mtime}"


@dataclass(frozen=True, slots=True)
class ContentHash:
    """Content-level hash for duplicate detection."""

    algorithm: str
    digest: str

    @classmethod
    def from_content(cls, content: str | bytes, algorithm: str = "sha256") -> ContentHash:
        """Create hash from content.

        Args:
            content: Text or bytes to hash
            algorithm: Hash algorithm (default: sha256)

        Returns:
            ContentHash instance
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        hasher = hashlib.new(algorithm)
        hasher.update(content)

        return cls(algorithm=algorithm, digest=hasher.hexdigest())

    @classmethod
    def from_file(cls, path: Path, algorithm: str = "sha256") -> ContentHash:
        """Create hash from file.

        Args:
            path: Path to file
            algorithm: Hash algorithm

        Returns:
            ContentHash instance
        """
        hasher = hashlib.new(algorithm)

        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return cls(algorithm=algorithm, digest=hasher.hexdigest())


def file_changed(path: Path, stored_hash: FileHash | None) -> bool:
    """Check if file has changed since last indexing.

    Uses fast file-level comparison (size + mtime).

    Args:
        path: Path to file
        stored_hash: Previously stored hash

    Returns:
        True if file changed or no stored hash
    """
    if stored_hash is None:
        return True

    current = FileHash.from_path(path)
    return current.to_string() != stored_hash.to_string()


def content_changed(content: str, stored_hash: ContentHash | None) -> bool:
    """Check if content has changed.

    Uses content hash for accurate comparison.

    Args:
        content: Current content
        stored_hash: Previously stored hash

    Returns:
        True if content changed or no stored hash
    """
    if stored_hash is None:
        return True

    current = ContentHash.from_content(content, algorithm=stored_hash.algorithm)
    return current.digest != stored_hash.digest


def is_duplicate(content: str, existing_hashes: set[str]) -> tuple[bool, str]:
    """Check if content is a duplicate.

    Args:
        content: Content to check
        existing_hashes: Set of existing content hashes

    Returns:
        Tuple of (is_duplicate, hash_digest)
    """
    content_hash = ContentHash.from_content(content)
    is_dup = content_hash.digest in existing_hashes
    return is_dup, content_hash.digest
