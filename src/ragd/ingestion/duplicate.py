"""Duplicate detection for indexed documents (F-104).

Identifies and handles duplicate content during indexing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ragd.ingestion.hashing import ContentHash, is_duplicate


@dataclass
class DuplicateInfo:
    """Information about a detected duplicate."""

    original_path: str
    duplicate_path: str
    hash_digest: str
    similarity: float = 1.0  # 1.0 = exact match


@dataclass
class DuplicateTracker:
    """Track and manage duplicate content during indexing.

    Maintains a registry of content hashes to detect duplicates.
    """

    hashes: dict[str, str] = field(default_factory=dict)  # hash -> first_path
    duplicates: list[DuplicateInfo] = field(default_factory=list)

    def check_and_register(
        self,
        content: str,
        path: str,
    ) -> tuple[bool, str | None]:
        """Check if content is duplicate and register it.

        Args:
            content: Document content
            path: Path to the document

        Returns:
            Tuple of (is_duplicate, original_path_if_duplicate)
        """
        content_hash = ContentHash.from_content(content)

        if content_hash.digest in self.hashes:
            original_path = self.hashes[content_hash.digest]
            self.duplicates.append(DuplicateInfo(
                original_path=original_path,
                duplicate_path=path,
                hash_digest=content_hash.digest,
            ))
            return True, original_path

        self.hashes[content_hash.digest] = path
        return False, None

    @property
    def duplicate_count(self) -> int:
        """Get count of detected duplicates."""
        return len(self.duplicates)

    @property
    def unique_count(self) -> int:
        """Get count of unique documents."""
        return len(self.hashes)

    def get_duplicates_for(self, path: str) -> list[str]:
        """Get all duplicates of a specific document.

        Args:
            path: Path to check

        Returns:
            List of paths that are duplicates of this document
        """
        return [
            dup.duplicate_path
            for dup in self.duplicates
            if dup.original_path == path
        ]

    def clear(self) -> None:
        """Clear all tracking data."""
        self.hashes.clear()
        self.duplicates.clear()


class DuplicatePolicy:
    """Policy for handling duplicates during indexing."""

    SKIP = "skip"  # Skip duplicate, index only first occurrence
    INDEX_ALL = "index_all"  # Index all occurrences
    LINK = "link"  # Index once, link duplicates to original


@dataclass
class DuplicateHandler:
    """Handle duplicates according to policy.

    Provides callbacks for different duplicate handling strategies.
    """

    policy: str = DuplicatePolicy.SKIP
    tracker: DuplicateTracker = field(default_factory=DuplicateTracker)
    on_duplicate: Callable[[DuplicateInfo], None] | None = None

    def should_index(self, content: str, path: str) -> bool:
        """Check if document should be indexed.

        Args:
            content: Document content
            path: Document path

        Returns:
            True if document should be indexed
        """
        is_dup, original = self.tracker.check_and_register(content, path)

        if is_dup:
            if self.on_duplicate:
                dup_info = self.tracker.duplicates[-1]
                self.on_duplicate(dup_info)

            if self.policy == DuplicatePolicy.SKIP:
                return False
            elif self.policy == DuplicatePolicy.INDEX_ALL:
                return True
            elif self.policy == DuplicatePolicy.LINK:
                # Caller should handle linking
                return False

        return True

    def get_stats(self) -> dict[str, int]:
        """Get duplicate detection statistics.

        Returns:
            Dictionary with unique_count and duplicate_count
        """
        return {
            "unique_count": self.tracker.unique_count,
            "duplicate_count": self.tracker.duplicate_count,
        }


def find_duplicates(
    contents: dict[str, str],
) -> list[DuplicateInfo]:
    """Find all duplicates in a collection of documents.

    Args:
        contents: Dictionary mapping path to content

    Returns:
        List of duplicate information
    """
    tracker = DuplicateTracker()

    for path, content in contents.items():
        tracker.check_and_register(content, path)

    return tracker.duplicates
