"""Auto-discovery service for model cards.

Orchestrates fetching metadata from multiple sources and building
model cards with offline-first architecture.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ragd.models.cards import ModelCard
from ragd.models.discovery.builder import CardBuilder
from ragd.models.discovery.connectivity import is_internet_available
from ragd.models.discovery.fetchers.base import FetchedMetadata
from ragd.models.discovery.fetchers.heuristics import HeuristicInferrer
from ragd.models.discovery.fetchers.ollama import OllamaMetadataFetcher
from ragd.models.discovery.storage import UserCardStorage

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)


class AutoDiscoveryService:
    """Orchestrates auto-discovery of model cards.

    Fetches metadata from multiple sources (Ollama, HuggingFace, heuristics),
    merges them into a ModelCard, and optionally saves to user storage.
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        enable_hf_fetch: bool = True,
        enable_heuristics: bool = True,
        user_cards_dir: Path | None = None,
        cache_discovered: bool = True,
    ) -> None:
        """Initialise auto-discovery service.

        Args:
            ollama_base_url: Ollama API base URL
            enable_hf_fetch: Enable HuggingFace Hub fetching
            enable_heuristics: Enable heuristic inference
            user_cards_dir: Directory for user cards
            cache_discovered: Cache discovered cards to disk
        """
        self._ollama_base_url = ollama_base_url
        self._ollama_fetcher = OllamaMetadataFetcher(ollama_base_url)
        self._heuristic = HeuristicInferrer() if enable_heuristics else None
        self._enable_hf = enable_hf_fetch
        self._hf_fetcher = None  # Lazy load

        self._builder = CardBuilder()
        self._storage = UserCardStorage(user_cards_dir)
        self._cache_discovered = cache_discovered

        # In-memory session cache
        self._session_cache: dict[str, ModelCard] = {}

    def discover(
        self,
        model_id: str,
        interactive: bool = False,
        console: Console | None = None,
    ) -> ModelCard | None:
        """Discover and optionally create a model card.

        Args:
            model_id: Model identifier (e.g., 'llama3.2:3b')
            interactive: Prompt user for confirmation
            console: Rich console for interactive mode

        Returns:
            ModelCard if discovery successful, None otherwise
        """
        # Check session cache
        if model_id in self._session_cache:
            logger.debug("Using session-cached card for %s", model_id)
            return self._session_cache[model_id]

        # Check user storage (confirmed + cache)
        stored_card = self._storage.load_card(model_id)
        if stored_card:
            self._session_cache[model_id] = stored_card
            return stored_card

        # Fetch from all available sources
        metadata_list = self._fetch_all(model_id)
        if not metadata_list:
            logger.warning("No metadata found for %s", model_id)
            return None

        # Build draft card
        try:
            draft_card = self._builder.build(metadata_list)
        except Exception as e:
            logger.error("Failed to build card for %s: %s", model_id, e)
            return None

        # Interactive confirmation or auto-cache
        if interactive and console:
            card = self._prompt_confirmation(draft_card, console)
            if card:
                self._storage.save_card(card, confirmed=True)
        else:
            card = draft_card
            if self._cache_discovered:
                self._storage.save_card(card, confirmed=False)

        # Cache in session
        if card:
            self._session_cache[model_id] = card
            self._log_discovery(model_id, metadata_list)

        return card

    def _fetch_all(self, model_id: str) -> list[FetchedMetadata]:
        """Fetch metadata from all available sources.

        Follows offline-first architecture:
        1. Heuristics (always available)
        2. Ollama (if running locally)
        3. HuggingFace (if internet available)

        Args:
            model_id: Model identifier

        Returns:
            List of FetchedMetadata from available sources
        """
        results = []

        # 1. Always try heuristics (offline)
        if self._heuristic:
            meta = self._heuristic.fetch(model_id)
            if meta:
                results.append(meta)
                logger.debug("Got heuristic metadata for %s", model_id)

        # 2. Try Ollama if available (local network only)
        if self._ollama_fetcher.is_available():
            meta = self._ollama_fetcher.fetch(model_id)
            if meta:
                results.append(meta)
                logger.debug("Got Ollama metadata for %s", model_id)

        # 3. Try HuggingFace only if internet available
        if self._enable_hf and is_internet_available():
            hf_meta = self._fetch_huggingface(model_id)
            if hf_meta:
                results.append(hf_meta)
                logger.debug("Got HuggingFace metadata for %s", model_id)

        return results

    def _fetch_huggingface(self, model_id: str) -> FetchedMetadata | None:
        """Fetch from HuggingFace Hub (lazy loaded).

        Args:
            model_id: Model identifier

        Returns:
            FetchedMetadata if found, None otherwise
        """
        # Lazy load HF fetcher
        if self._hf_fetcher is None:
            try:
                from ragd.models.discovery.fetchers.huggingface import (
                    HuggingFaceMetadataFetcher,
                )

                self._hf_fetcher = HuggingFaceMetadataFetcher()
            except ImportError:
                logger.debug("HuggingFace fetcher not available")
                return None

        if self._hf_fetcher and self._hf_fetcher.is_available():
            return self._hf_fetcher.fetch(model_id)

        return None

    def _prompt_confirmation(
        self,
        card: ModelCard,
        console: Console,
    ) -> ModelCard | None:
        """Interactive prompt for user to confirm/edit card.

        Args:
            card: Draft ModelCard to confirm
            console: Rich console for output

        Returns:
            Confirmed ModelCard or None if cancelled
        """
        # This will be implemented in prompts.py
        # For now, just return the card as-is
        from ragd.models.discovery.prompts import prompt_card_confirmation

        return prompt_card_confirmation(card, console)

    def _log_discovery(
        self,
        model_id: str,
        metadata_list: list[FetchedMetadata],
    ) -> None:
        """Log discovery result.

        Args:
            model_id: Model identifier
            metadata_list: Sources used
        """
        sources = [m.source for m in metadata_list]
        logger.info(
            "Auto-discovered card for %s from: %s",
            model_id,
            ", ".join(sources),
        )

    def clear_session_cache(self) -> None:
        """Clear the session cache."""
        self._session_cache.clear()

    def get_storage(self) -> UserCardStorage:
        """Get the underlying storage instance.

        Returns:
            UserCardStorage instance
        """
        return self._storage
