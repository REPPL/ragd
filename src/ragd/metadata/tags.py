"""Tag management for document metadata.

This module provides tag CRUD operations for documents, enabling
organisation of the knowledge base via user-defined tags.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragd.metadata.store import MetadataStore

logger = logging.getLogger(__name__)


class TagManager:
    """Manages document tags in the metadata store.

    Provides operations for adding, removing, and querying tags
    on documents. Tags are stored in the ragd_tags field of
    DocumentMetadata.

    Example:
        >>> from ragd.metadata import MetadataStore
        >>> store = MetadataStore(Path("~/.ragd/metadata.sqlite"))
        >>> tags = TagManager(store)
        >>> tags.add("doc-123", "important")
        >>> tags.add("doc-123", ["reviewed", "priority"])
        >>> print(tags.get("doc-123"))
        ['important', 'priority', 'reviewed']
        >>> tags.remove("doc-123", "reviewed")
    """

    def __init__(self, store: "MetadataStore") -> None:
        """Initialise the tag manager.

        Args:
            store: MetadataStore instance for persistence
        """
        self._store = store
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def add(self, doc_id: str, tags: str | list[str]) -> bool:
        """Add tags to a document.

        Tags are deduplicated and sorted alphabetically.

        Args:
            doc_id: Document identifier
            tags: Tag string or list of tags to add

        Returns:
            True if document exists and was updated, False otherwise
        """
        if isinstance(tags, str):
            tags = [tags]

        metadata = self._store.get(doc_id)
        if metadata is None:
            self._logger.warning("Document not found: %s", doc_id)
            return False

        # Get existing tags and merge
        existing_tags = set(metadata.ragd_tags)
        new_tags = set(t.strip() for t in tags if t.strip())
        merged_tags = sorted(existing_tags | new_tags)

        # Update if changed
        if merged_tags != metadata.ragd_tags:
            return self._store.update(doc_id, ragd_tags=merged_tags)

        return True

    def remove(self, doc_id: str, tags: str | list[str]) -> bool:
        """Remove tags from a document.

        Args:
            doc_id: Document identifier
            tags: Tag string or list of tags to remove

        Returns:
            True if document exists and was updated, False otherwise
        """
        if isinstance(tags, str):
            tags = [tags]

        metadata = self._store.get(doc_id)
        if metadata is None:
            self._logger.warning("Document not found: %s", doc_id)
            return False

        # Remove specified tags
        tags_to_remove = set(t.strip() for t in tags)
        new_tags = sorted(t for t in metadata.ragd_tags if t not in tags_to_remove)

        # Update if changed
        if new_tags != metadata.ragd_tags:
            return self._store.update(doc_id, ragd_tags=new_tags)

        return True

    def get(self, doc_id: str) -> list[str]:
        """Get all tags for a document.

        Args:
            doc_id: Document identifier

        Returns:
            List of tags (empty if document not found)
        """
        metadata = self._store.get(doc_id)
        if metadata is None:
            return []
        return metadata.ragd_tags

    def set(self, doc_id: str, tags: list[str]) -> bool:
        """Set exact tags for a document (replaces existing).

        Args:
            doc_id: Document identifier
            tags: Complete list of tags

        Returns:
            True if document exists and was updated, False otherwise
        """
        clean_tags = sorted(set(t.strip() for t in tags if t.strip()))
        return self._store.update(doc_id, ragd_tags=clean_tags)

    def clear(self, doc_id: str) -> bool:
        """Remove all tags from a document.

        Args:
            doc_id: Document identifier

        Returns:
            True if document exists and was updated, False otherwise
        """
        return self._store.update(doc_id, ragd_tags=[])

    def list_all_tags(self) -> list[str]:
        """Get all unique tags across all documents.

        Returns:
            Sorted list of all tags in use
        """
        all_tags: set[str] = set()
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                all_tags.update(metadata.ragd_tags)
        return sorted(all_tags)

    def find_by_tags(
        self,
        tags: list[str],
        match_all: bool = True,
    ) -> list[str]:
        """Find documents matching given tags.

        Args:
            tags: Tags to search for
            match_all: If True, documents must have ALL tags.
                      If False, documents with ANY tag match.

        Returns:
            List of matching document IDs
        """
        if not tags:
            return []

        matching_ids: list[str] = []
        search_tags = set(t.strip() for t in tags)

        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata is None:
                continue

            doc_tags = set(metadata.ragd_tags)

            if match_all:
                # All search tags must be present
                if search_tags <= doc_tags:
                    matching_ids.append(doc_id)
            else:
                # Any search tag present
                if search_tags & doc_tags:
                    matching_ids.append(doc_id)

        return matching_ids

    def tag_counts(self) -> dict[str, int]:
        """Get count of documents for each tag.

        Returns:
            Dictionary mapping tag names to document counts
        """
        counts: dict[str, int] = {}
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                for tag in metadata.ragd_tags:
                    counts[tag] = counts.get(tag, 0) + 1
        return counts

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all documents.

        Args:
            old_tag: Current tag name
            new_tag: New tag name

        Returns:
            Number of documents updated
        """
        if old_tag == new_tag:
            return 0

        updated = 0
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and old_tag in metadata.ragd_tags:
                new_tags = [new_tag if t == old_tag else t for t in metadata.ragd_tags]
                new_tags = sorted(set(new_tags))
                if self._store.update(doc_id, ragd_tags=new_tags):
                    updated += 1

        self._logger.info(
            "Renamed tag '%s' to '%s' in %d documents",
            old_tag,
            new_tag,
            updated,
        )
        return updated

    def delete_tag(self, tag: str) -> int:
        """Delete a tag from all documents.

        Args:
            tag: Tag to delete

        Returns:
            Number of documents updated
        """
        updated = 0
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and tag in metadata.ragd_tags:
                new_tags = [t for t in metadata.ragd_tags if t != tag]
                if self._store.update(doc_id, ragd_tags=new_tags):
                    updated += 1

        self._logger.info("Deleted tag '%s' from %d documents", tag, updated)
        return updated
