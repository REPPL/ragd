"""User card storage for discovered model cards.

Manages persistence of user-created and cached model cards
in the user's home directory.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ragd.models.cards import ModelCard

logger = logging.getLogger(__name__)


class UserCardStorage:
    """Manage user-created and cached model cards.

    Storage hierarchy:
    - ~/.ragd/model_cards/           Confirmed cards (user-approved)
    - ~/.ragd/model_cards/_cache/    Auto-discovered cache
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialise user card storage.

        Args:
            base_dir: Base directory for cards (default: ~/.ragd/model_cards)
        """
        self.base_dir = base_dir or Path.home() / ".ragd" / "model_cards"
        self.cache_dir = self.base_dir / "_cache"

    def save_card(
        self,
        card: ModelCard,
        confirmed: bool = False,
    ) -> Path:
        """Save a model card to user storage.

        Args:
            card: ModelCard to save
            confirmed: If True, save to main dir; if False, save to cache

        Returns:
            Path where card was saved
        """
        target_dir = self.base_dir if confirmed else self.cache_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Normalise filename
        filename = self._normalise_filename(card.id)
        card_path = target_dir / filename

        # Convert to YAML-friendly dict
        data = card.to_dict()

        # Add discovery metadata
        if not confirmed:
            data["_cached_at"] = datetime.now().isoformat()

        # Write YAML
        with open(card_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        logger.info(
            "Saved model card %s to %s",
            card.id,
            "confirmed" if confirmed else "cache",
        )

        return card_path

    def load_card(self, model_id: str) -> ModelCard | None:
        """Load a user card by model ID.

        Checks confirmed cards first, then cache.

        Args:
            model_id: Model identifier

        Returns:
            ModelCard if found, None otherwise
        """
        filename = self._normalise_filename(model_id)

        # Try confirmed cards first
        confirmed_path = self.base_dir / filename
        if confirmed_path.exists():
            return self._load_from_path(confirmed_path)

        # Try cache
        cache_path = self.cache_dir / filename
        if cache_path.exists():
            return self._load_from_path(cache_path)

        return None

    def list_cards(
        self,
        include_cache: bool = True,
    ) -> list[tuple[ModelCard, bool]]:
        """List all user cards.

        Args:
            include_cache: Include cached (unconfirmed) cards

        Returns:
            List of (ModelCard, is_confirmed) tuples
        """
        cards = []

        # List confirmed cards
        if self.base_dir.exists():
            for path in self.base_dir.glob("*.yaml"):
                if path.name.startswith("_"):
                    continue
                card = self._load_from_path(path)
                if card:
                    cards.append((card, True))

        # List cached cards
        if include_cache and self.cache_dir.exists():
            for path in self.cache_dir.glob("*.yaml"):
                if path.name.startswith("_"):
                    continue
                card = self._load_from_path(path)
                if card:
                    # Skip if already in confirmed
                    if not any(c.id == card.id for c, _ in cards):
                        cards.append((card, False))

        return sorted(cards, key=lambda x: x[0].id)

    def delete_card(self, model_id: str) -> bool:
        """Delete a user card.

        Args:
            model_id: Model identifier

        Returns:
            True if deleted, False if not found
        """
        filename = self._normalise_filename(model_id)
        deleted = False

        # Try confirmed
        confirmed_path = self.base_dir / filename
        if confirmed_path.exists():
            confirmed_path.unlink()
            deleted = True
            logger.info("Deleted confirmed card: %s", model_id)

        # Try cache
        cache_path = self.cache_dir / filename
        if cache_path.exists():
            cache_path.unlink()
            deleted = True
            logger.info("Deleted cached card: %s", model_id)

        return deleted

    def confirm_card(self, model_id: str) -> bool:
        """Promote a cached card to confirmed.

        Args:
            model_id: Model identifier

        Returns:
            True if promoted, False if not found in cache
        """
        filename = self._normalise_filename(model_id)
        cache_path = self.cache_dir / filename

        if not cache_path.exists():
            return False

        # Load from cache
        card = self._load_from_path(cache_path)
        if card is None:
            return False

        # Save as confirmed
        self.save_card(card, confirmed=True)

        # Remove from cache
        cache_path.unlink()

        logger.info("Confirmed cached card: %s", model_id)
        return True

    def is_cached(self, model_id: str) -> bool:
        """Check if a model has a cached card.

        Args:
            model_id: Model identifier

        Returns:
            True if cached card exists
        """
        filename = self._normalise_filename(model_id)
        cache_path = self.cache_dir / filename
        return cache_path.exists()

    def is_confirmed(self, model_id: str) -> bool:
        """Check if a model has a confirmed card.

        Args:
            model_id: Model identifier

        Returns:
            True if confirmed card exists
        """
        filename = self._normalise_filename(model_id)
        confirmed_path = self.base_dir / filename
        return confirmed_path.exists()

    def _normalise_filename(self, model_id: str) -> str:
        """Convert model ID to filename.

        Args:
            model_id: Model identifier

        Returns:
            Normalised filename with .yaml extension
        """
        return model_id.replace(":", "-").replace("/", "-") + ".yaml"

    def _load_from_path(self, path: Path) -> ModelCard | None:
        """Load a ModelCard from a YAML file.

        Args:
            path: Path to YAML file

        Returns:
            ModelCard if successful, None otherwise
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data:
                # Remove internal metadata before parsing
                data.pop("_cached_at", None)
                return ModelCard.from_dict(data)

        except Exception as e:
            logger.warning("Failed to load card from %s: %s", path, e)

        return None
