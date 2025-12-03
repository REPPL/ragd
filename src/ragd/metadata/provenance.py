"""Tag provenance tracking for document metadata.

This module provides the TagEntry dataclass for tracking tag provenance,
including source (manual, auto-generated), confidence scores, and timestamps.

F-064: Tag Provenance - Distinguish auto-generated tags from user-defined tags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


# Valid tag source types
TagSource = Literal[
    "manual",      # User explicitly added
    "legacy",      # Migrated from pre-provenance schema
    "auto-keybert",  # KeyBERT keyword extraction
    "auto-llm",    # LLM classification
    "auto-ner",    # Named Entity Recognition
    "imported",    # Imported from archive
]


@dataclass
class TagEntry:
    """A tag with provenance tracking.

    Tracks how a tag was applied to enable:
    - Distinguishing user tags from auto-generated suggestions
    - Quality metrics for auto-tagging algorithms
    - Bulk operations (e.g., remove all auto-generated tags)

    Example:
        >>> tag = TagEntry(name="machine-learning", source="auto-keybert", confidence=0.89)
        >>> print(tag)
        machine-learning
        >>> tag.is_auto_generated
        True
    """

    name: str
    source: TagSource = "manual"
    confidence: float | None = None  # 0.0-1.0 for auto-generated tags
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str | None = None  # User ID or model name

    def __post_init__(self) -> None:
        """Validate tag entry after initialisation."""
        # Normalise tag name
        self.name = self.name.strip().lower()

        # Validate confidence score
        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    @property
    def is_auto_generated(self) -> bool:
        """Check if tag was auto-generated."""
        return self.source.startswith("auto-")

    @property
    def is_manual(self) -> bool:
        """Check if tag was manually added."""
        return self.source == "manual"

    @property
    def is_legacy(self) -> bool:
        """Check if tag was migrated from pre-provenance schema."""
        return self.source == "legacy"

    def to_dict(self) -> dict[str, Any]:
        """Serialise for JSON storage.

        Returns:
            Dictionary with all provenance fields.
        """
        return {
            "name": self.name,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> TagEntry:
        """Deserialise from storage (backward compatible).

        Handles both:
        - New format: dict with provenance fields
        - Legacy format: plain string tag name

        Args:
            data: Dictionary with tag data or plain string tag name.

        Returns:
            TagEntry instance.
        """
        if isinstance(data, str):
            # Legacy: plain string tag
            return cls(name=data, source="legacy")

        # Parse created_at if present
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = None

        return cls(
            name=data.get("name", ""),
            source=data.get("source", "legacy"),
            confidence=data.get("confidence"),
            created_at=created_at or datetime.now(),
            created_by=data.get("created_by"),
        )

    @classmethod
    def manual(cls, name: str, created_by: str | None = None) -> TagEntry:
        """Create a manually added tag.

        Args:
            name: Tag name.
            created_by: Optional user identifier.

        Returns:
            TagEntry with source="manual".
        """
        return cls(name=name, source="manual", created_by=created_by)

    @classmethod
    def auto_keybert(
        cls,
        name: str,
        confidence: float,
        model: str | None = None,
    ) -> TagEntry:
        """Create an auto-generated KeyBERT tag.

        Args:
            name: Tag name.
            confidence: Confidence score (0.0-1.0).
            model: Optional model name.

        Returns:
            TagEntry with source="auto-keybert".
        """
        return cls(
            name=name,
            source="auto-keybert",
            confidence=confidence,
            created_by=model,
        )

    @classmethod
    def auto_llm(
        cls,
        name: str,
        confidence: float,
        model: str | None = None,
    ) -> TagEntry:
        """Create an auto-generated LLM tag.

        Args:
            name: Tag name.
            confidence: Confidence score (0.0-1.0).
            model: Optional model name.

        Returns:
            TagEntry with source="auto-llm".
        """
        return cls(
            name=name,
            source="auto-llm",
            confidence=confidence,
            created_by=model,
        )

    def __str__(self) -> str:
        """String representation (just the name for compatibility)."""
        return self.name

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        conf = f", confidence={self.confidence}" if self.confidence else ""
        return f"TagEntry(name={self.name!r}, source={self.source!r}{conf})"

    def __eq__(self, other: object) -> bool:
        """Compare by name for set operations.

        Allows comparison with both TagEntry and plain strings.
        """
        if isinstance(other, str):
            return self.name == other.strip().lower()
        if isinstance(other, TagEntry):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        """Hash by name for set operations."""
        return hash(self.name)

    def __lt__(self, other: object) -> bool:
        """Enable sorting by name."""
        if isinstance(other, str):
            return self.name < other.strip().lower()
        if isinstance(other, TagEntry):
            return self.name < other.name
        return NotImplemented


def normalise_tags(tags: list[str | TagEntry | dict[str, Any]]) -> list[TagEntry]:
    """Convert mixed tag formats to TagEntry list.

    Handles:
    - Plain strings (legacy format)
    - TagEntry instances
    - Dictionaries (from JSON storage)

    Args:
        tags: List of tags in various formats.

    Returns:
        List of TagEntry instances.
    """
    result: list[TagEntry] = []
    for tag in tags:
        if isinstance(tag, TagEntry):
            result.append(tag)
        elif isinstance(tag, dict):
            result.append(TagEntry.from_dict(tag))
        elif isinstance(tag, str):
            result.append(TagEntry.from_dict(tag))
        else:
            raise TypeError(f"Unexpected tag type: {type(tag)}")
    return result


def serialise_tags(tags: list[TagEntry]) -> list[dict[str, Any]]:
    """Serialise TagEntry list for JSON storage.

    Args:
        tags: List of TagEntry instances.

    Returns:
        List of dictionaries for JSON storage.
    """
    return [tag.to_dict() for tag in tags]


def get_tag_names(tags: list[TagEntry]) -> list[str]:
    """Extract tag names from TagEntry list.

    Args:
        tags: List of TagEntry instances.

    Returns:
        List of tag names (strings).
    """
    return [tag.name for tag in tags]
