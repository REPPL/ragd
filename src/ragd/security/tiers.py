"""Data sensitivity tier management for ragd.

This module provides data classification and tier-based access control.
Documents can be assigned to sensitivity tiers that determine access requirements.

F-018: Data Sensitivity Tiers - Classify documents by sensitivity level.

Tier Hierarchy:
    PUBLIC < PERSONAL < SENSITIVE < CRITICAL

Each tier has different access requirements:
    - PUBLIC: Always accessible, no authentication
    - PERSONAL: Requires basic password authentication (default)
    - SENSITIVE: Requires active session (session must be unlocked)
    - CRITICAL: Requires active session + explicit confirmation

Usage:
    from ragd.security.tiers import DataTier, TierManager

    # Set document tier
    manager = TierManager(metadata_store, session_manager)
    manager.set_tier("doc-123", DataTier.SENSITIVE)

    # Check access
    if manager.can_access(DataTier.SENSITIVE):
        # Show document
    else:
        # Prompt for authentication
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragd.metadata.store import MetadataStore
    from ragd.security.session import SessionManager

logger = logging.getLogger(__name__)


class DataTier(Enum):
    """Data sensitivity classification tiers.

    Tiers are ordered from least to most sensitive:
        PUBLIC < PERSONAL < SENSITIVE < CRITICAL

    Each tier has different security requirements:
        - PUBLIC: No authentication required
        - PERSONAL: Password authentication (default tier)
        - SENSITIVE: Active unlocked session required
        - CRITICAL: Active session + explicit access confirmation
    """

    PUBLIC = "public"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"

    @property
    def level(self) -> int:
        """Get numeric level for comparison.

        Returns:
            Integer level (0=public, 3=critical).
        """
        levels = {
            DataTier.PUBLIC: 0,
            DataTier.PERSONAL: 1,
            DataTier.SENSITIVE: 2,
            DataTier.CRITICAL: 3,
        }
        return levels[self]

    def __lt__(self, other: object) -> bool:
        """Compare tiers by sensitivity level."""
        if not isinstance(other, DataTier):
            return NotImplemented
        return self.level < other.level

    def __le__(self, other: object) -> bool:
        """Compare tiers by sensitivity level."""
        if not isinstance(other, DataTier):
            return NotImplemented
        return self.level <= other.level

    def __gt__(self, other: object) -> bool:
        """Compare tiers by sensitivity level."""
        if not isinstance(other, DataTier):
            return NotImplemented
        return self.level > other.level

    def __ge__(self, other: object) -> bool:
        """Compare tiers by sensitivity level."""
        if not isinstance(other, DataTier):
            return NotImplemented
        return self.level >= other.level

    @classmethod
    def from_string(cls, value: str) -> DataTier:
        """Parse tier from string value.

        Args:
            value: Tier name (case-insensitive).

        Returns:
            Corresponding DataTier.

        Raises:
            ValueError: If value is not a valid tier.
        """
        value = value.lower().strip()
        for tier in cls:
            if tier.value == value:
                return tier
        valid = ", ".join(t.value for t in cls)
        raise ValueError(f"Invalid tier '{value}'. Valid tiers: {valid}")

    @property
    def description(self) -> str:
        """Get human-readable description of the tier."""
        descriptions = {
            DataTier.PUBLIC: "Always accessible, no authentication required",
            DataTier.PERSONAL: "Requires password authentication (default)",
            DataTier.SENSITIVE: "Requires active unlocked session",
            DataTier.CRITICAL: "Requires active session + confirmation",
        }
        return descriptions[self]


class TierAccessError(Exception):
    """Raised when tier access requirements are not met."""

    def __init__(self, message: str, required_tier: DataTier) -> None:
        super().__init__(message)
        self.required_tier = required_tier


@dataclass
class TierConfig:
    """Configuration for tier-based access control.

    Attributes:
        default_tier: Default tier for new documents.
        require_confirmation_for_critical: Require explicit confirmation for critical tier.
        auto_lock_on_sensitive_access: Lock session after accessing sensitive+ tiers.
    """

    default_tier: DataTier = DataTier.PERSONAL
    require_confirmation_for_critical: bool = True
    auto_lock_on_sensitive_access: bool = False


class TierManager:
    """Manages data sensitivity tiers and access control.

    Provides tier assignment, access checking, and filtering operations
    for documents based on their sensitivity classification.

    Example:
        >>> from ragd.security.tiers import DataTier, TierManager
        >>> manager = TierManager(metadata_store, session_manager)
        >>> manager.set_tier("doc-123", DataTier.SENSITIVE)
        >>> manager.get_tier("doc-123")
        <DataTier.SENSITIVE: 'sensitive'>
        >>> manager.can_access(DataTier.SENSITIVE)
        True  # If session is unlocked
    """

    def __init__(
        self,
        store: MetadataStore,
        session: SessionManager | None = None,
        config: TierConfig | None = None,
    ) -> None:
        """Initialise the tier manager.

        Args:
            store: MetadataStore instance for persistence.
            session: SessionManager for auth checking (optional).
            config: Tier configuration.
        """
        self._store = store
        self._session = session
        self._config = config or TierConfig()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def set_tier(self, doc_id: str, tier: DataTier) -> bool:
        """Set the sensitivity tier for a document.

        Args:
            doc_id: Document identifier.
            tier: Sensitivity tier to assign.

        Returns:
            True if document was found and updated, False otherwise.
        """
        result = self._store.update(doc_id, ragd_data_tier=tier.value)
        if result:
            self._logger.info(
                "Set tier for document %s to %s", doc_id, tier.value
            )
        return result

    def get_tier(self, doc_id: str) -> DataTier:
        """Get the sensitivity tier for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            Document's tier, or default tier if not found/not set.
        """
        metadata = self._store.get(doc_id)
        if metadata is None:
            return self._config.default_tier

        tier_value = getattr(metadata, "ragd_data_tier", None)
        if not tier_value:
            return self._config.default_tier

        try:
            return DataTier.from_string(tier_value)
        except ValueError:
            self._logger.warning(
                "Invalid tier '%s' for document %s, using default",
                tier_value,
                doc_id,
            )
            return self._config.default_tier

    def can_access(self, tier: DataTier, confirmed: bool = False) -> bool:
        """Check if current session can access the given tier.

        Args:
            tier: Tier to check access for.
            confirmed: Whether user has explicitly confirmed (for critical tier).

        Returns:
            True if access is allowed.
        """
        # PUBLIC tier always accessible
        if tier == DataTier.PUBLIC:
            return True

        # PERSONAL tier requires initialised security or no session manager
        if tier == DataTier.PERSONAL:
            if self._session is None:
                return True  # No session management = allow
            return True  # PERSONAL only needs basic auth (not active session)

        # SENSITIVE and CRITICAL require active session
        if self._session is None:
            return False

        if not self._session.is_active:
            return False

        # CRITICAL requires explicit confirmation
        if tier == DataTier.CRITICAL:
            if self._config.require_confirmation_for_critical and not confirmed:
                return False

        return True

    def check_access(self, tier: DataTier, confirmed: bool = False) -> None:
        """Check tier access, raising if not allowed.

        Args:
            tier: Tier to check access for.
            confirmed: Whether user has explicitly confirmed.

        Raises:
            TierAccessError: If access is not allowed.
        """
        if not self.can_access(tier, confirmed):
            if tier == DataTier.CRITICAL and not confirmed:
                raise TierAccessError(
                    "Access to CRITICAL tier requires explicit confirmation",
                    tier,
                )
            raise TierAccessError(
                f"Access to {tier.value} tier requires an active session. "
                "Run 'ragd unlock' first.",
                tier,
            )

    def filter_by_tier(
        self,
        doc_ids: list[str],
        max_tier: DataTier | None = None,
        confirmed: bool = False,
    ) -> list[str]:
        """Filter document IDs by accessible tiers.

        Args:
            doc_ids: List of document IDs to filter.
            max_tier: Maximum tier to include (None = all accessible).
            confirmed: Whether critical tier access is confirmed.

        Returns:
            List of document IDs that are accessible.
        """
        accessible: list[str] = []

        for doc_id in doc_ids:
            doc_tier = self.get_tier(doc_id)

            # Check max_tier filter
            if max_tier is not None and doc_tier > max_tier:
                continue

            # Check access permissions
            if self.can_access(doc_tier, confirmed):
                accessible.append(doc_id)

        return accessible

    def list_by_tier(self, tier: DataTier) -> list[str]:
        """List all documents with a specific tier.

        Args:
            tier: Tier to filter by.

        Returns:
            List of document IDs with the specified tier.
        """
        result: list[str] = []

        for doc_id in self._store.list_ids():
            if self.get_tier(doc_id) == tier:
                result.append(doc_id)

        return result

    def tier_counts(self) -> dict[DataTier, int]:
        """Count documents in each tier.

        Returns:
            Dictionary mapping tiers to document counts.
        """
        counts: dict[DataTier, int] = dict.fromkeys(DataTier, 0)

        for doc_id in self._store.list_ids():
            tier = self.get_tier(doc_id)
            counts[tier] += 1

        return counts

    def tier_summary(self) -> dict[str, Any]:
        """Get summary of tier distribution.

        Returns:
            Dictionary with tier statistics.
        """
        counts = self.tier_counts()
        total = sum(counts.values())

        summary: dict[str, Any] = {
            "total_documents": total,
            "tiers": {},
        }

        for tier in DataTier:
            count = counts[tier]
            percentage = (count / total * 100) if total > 0 else 0.0
            summary["tiers"][tier.value] = {
                "count": count,
                "percentage": round(percentage, 1),
                "description": tier.description,
            }

        return summary

    def bulk_set_tier(self, doc_ids: list[str], tier: DataTier) -> int:
        """Set tier for multiple documents.

        Args:
            doc_ids: List of document IDs to update.
            tier: Tier to assign.

        Returns:
            Number of documents updated.
        """
        updated = 0
        for doc_id in doc_ids:
            if self.set_tier(doc_id, tier):
                updated += 1

        self._logger.info(
            "Bulk set tier to %s for %d documents", tier.value, updated
        )
        return updated

    def promote_tier(self, doc_id: str) -> DataTier | None:
        """Increase document sensitivity by one level.

        Args:
            doc_id: Document identifier.

        Returns:
            New tier, or None if already at maximum.
        """
        current = self.get_tier(doc_id)
        tiers = list(DataTier)
        current_idx = tiers.index(current)

        if current_idx >= len(tiers) - 1:
            return None  # Already at max

        new_tier = tiers[current_idx + 1]
        self.set_tier(doc_id, new_tier)
        return new_tier

    def demote_tier(self, doc_id: str) -> DataTier | None:
        """Decrease document sensitivity by one level.

        Args:
            doc_id: Document identifier.

        Returns:
            New tier, or None if already at minimum.
        """
        current = self.get_tier(doc_id)
        tiers = list(DataTier)
        current_idx = tiers.index(current)

        if current_idx <= 0:
            return None  # Already at min

        new_tier = tiers[current_idx - 1]
        self.set_tier(doc_id, new_tier)
        return new_tier


def get_tier_colour(tier: DataTier) -> str:
    """Get Rich console colour for tier display.

    Args:
        tier: Data tier.

    Returns:
        Rich colour name.
    """
    colours = {
        DataTier.PUBLIC: "green",
        DataTier.PERSONAL: "blue",
        DataTier.SENSITIVE: "yellow",
        DataTier.CRITICAL: "red",
    }
    return colours.get(tier, "white")


def get_tier_icon(tier: DataTier) -> str:
    """Get icon/emoji for tier display.

    Args:
        tier: Data tier.

    Returns:
        Unicode icon character.
    """
    icons = {
        DataTier.PUBLIC: "\u25cb",  # White circle
        DataTier.PERSONAL: "\u25cf",  # Black circle
        DataTier.SENSITIVE: "\u26a0",  # Warning sign
        DataTier.CRITICAL: "\u2622",  # Radioactive sign
    }
    return icons.get(tier, "\u25cf")
