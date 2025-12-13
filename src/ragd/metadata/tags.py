"""Tag management for document metadata.

This module provides tag CRUD operations for documents, enabling
organisation of the knowledge base via user-defined tags.

F-064: Tag Provenance - Now supports TagEntry with provenance tracking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ragd.metadata.provenance import TagEntry, get_tag_names, normalise_tags

if TYPE_CHECKING:
    from ragd.metadata.store import MetadataStore

logger = logging.getLogger(__name__)


class TagManager:
    """Manages document tags in the metadata store.

    Provides operations for adding, removing, and querying tags
    on documents. Tags are stored in the ragd_tags field of
    DocumentMetadata as TagEntry objects with provenance tracking.

    F-064: Now tracks tag source (manual, auto-generated, legacy, etc.)

    Example:
        >>> from ragd.metadata import MetadataStore
        >>> store = MetadataStore(Path("~/.ragd/metadata.sqlite"))
        >>> tags = TagManager(store)
        >>> tags.add("doc-123", "important")  # source="manual"
        >>> tags.add("doc-123", ["reviewed", "priority"])
        >>> print(tags.get_names("doc-123"))  # Backward compat
        ['important', 'priority', 'reviewed']
        >>> print(tags.get("doc-123"))  # Returns TagEntry list
        [TagEntry(name='important', source='manual'), ...]
        >>> tags.remove("doc-123", "reviewed")
    """

    def __init__(self, store: MetadataStore) -> None:
        """Initialise the tag manager.

        Args:
            store: MetadataStore instance for persistence
        """
        self._store = store
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def add(
        self,
        doc_id: str,
        tags: str | list[str] | TagEntry | list[TagEntry],
        source: str = "manual",
        confidence: float | None = None,
    ) -> bool:
        """Add tags to a document.

        Tags are deduplicated and sorted alphabetically by name.

        Args:
            doc_id: Document identifier
            tags: Tag string, list of strings, TagEntry, or list of TagEntry
            source: Tag source for string tags (default: "manual")
            confidence: Confidence score for auto-generated tags

        Returns:
            True if document exists and was updated, False otherwise
        """
        # Normalise input to list
        if isinstance(tags, (str, TagEntry)):
            tags = [tags]

        metadata = self._store.get(doc_id)
        if metadata is None:
            self._logger.warning("Document not found: %s", doc_id)
            return False

        # Normalise existing tags to TagEntry list
        existing_entries = normalise_tags(metadata.ragd_tags)
        existing_names = {e.name for e in existing_entries}

        # Convert new tags to TagEntry and merge
        new_entries: list[TagEntry] = []
        for tag in tags:
            if isinstance(tag, TagEntry):
                new_entries.append(tag)
            elif isinstance(tag, str):
                tag_name = tag.strip().lower()
                if tag_name:
                    new_entries.append(TagEntry(
                        name=tag_name,
                        source=source,  # type: ignore
                        confidence=confidence,
                    ))

        # Add only new tags (by name)
        for entry in new_entries:
            if entry.name not in existing_names:
                existing_entries.append(entry)
                existing_names.add(entry.name)

        # Sort and serialise
        merged_tags = sorted(existing_entries, key=lambda t: t.name)
        serialised = [t.to_dict() for t in merged_tags]

        # Update if changed
        return self._store.update(doc_id, ragd_tags=serialised)

    def remove(
        self,
        doc_id: str,
        tags: str | list[str] | None = None,
        source: str | None = None,
    ) -> bool:
        """Remove tags from a document.

        Args:
            doc_id: Document identifier
            tags: Tag string or list of tags to remove (by name)
            source: Remove all tags with this source (e.g., "auto-keybert")

        Returns:
            True if document exists and was updated, False otherwise
        """
        metadata = self._store.get(doc_id)
        if metadata is None:
            self._logger.warning("Document not found: %s", doc_id)
            return False

        # Normalise existing tags
        existing_entries = normalise_tags(metadata.ragd_tags)

        # Build set of names to remove
        names_to_remove: set[str] = set()
        if tags:
            if isinstance(tags, str):
                tags = [tags]
            names_to_remove = {t.strip().lower() for t in tags}

        # Filter tags
        new_entries: list[TagEntry] = []
        for entry in existing_entries:
            # Remove by name if specified
            if names_to_remove and entry.name in names_to_remove:
                continue
            # Remove by source if specified
            if source and entry.source == source:
                continue
            new_entries.append(entry)

        # Sort and serialise
        new_entries = sorted(new_entries, key=lambda t: t.name)
        serialised = [t.to_dict() for t in new_entries]

        return self._store.update(doc_id, ragd_tags=serialised)

    def get(self, doc_id: str) -> list[TagEntry]:
        """Get all tags for a document as TagEntry objects.

        Args:
            doc_id: Document identifier

        Returns:
            List of TagEntry (empty if document not found)
        """
        metadata = self._store.get(doc_id)
        if metadata is None:
            return []
        return normalise_tags(metadata.ragd_tags)

    def get_names(self, doc_id: str) -> list[str]:
        """Get all tag names for a document (backward compatibility).

        Args:
            doc_id: Document identifier

        Returns:
            List of tag name strings (empty if document not found)
        """
        entries = self.get(doc_id)
        return get_tag_names(entries)

    def get_by_source(self, doc_id: str, source: str) -> list[TagEntry]:
        """Get tags filtered by source.

        Args:
            doc_id: Document identifier
            source: Tag source to filter by (e.g., "manual", "auto-keybert")

        Returns:
            List of TagEntry with matching source
        """
        entries = self.get(doc_id)
        return [e for e in entries if e.source == source]

    def set(
        self,
        doc_id: str,
        tags: list[str] | list[TagEntry],
        source: str = "manual",
    ) -> bool:
        """Set exact tags for a document (replaces existing).

        Args:
            doc_id: Document identifier
            tags: Complete list of tags (strings or TagEntry)
            source: Source for string tags

        Returns:
            True if document exists and was updated, False otherwise
        """
        entries: list[TagEntry] = []
        seen_names: set[str] = set()

        for tag in tags:
            if isinstance(tag, TagEntry):
                if tag.name not in seen_names:
                    entries.append(tag)
                    seen_names.add(tag.name)
            elif isinstance(tag, str):
                name = tag.strip().lower()
                if name and name not in seen_names:
                    entries.append(TagEntry(name=name, source=source))  # type: ignore
                    seen_names.add(name)

        entries = sorted(entries, key=lambda t: t.name)
        serialised = [t.to_dict() for t in entries]
        return self._store.update(doc_id, ragd_tags=serialised)

    def clear(self, doc_id: str) -> bool:
        """Remove all tags from a document.

        Args:
            doc_id: Document identifier

        Returns:
            True if document exists and was updated, False otherwise
        """
        return self._store.update(doc_id, ragd_tags=[])

    def list_all_tags(self) -> list[str]:
        """Get all unique tag names across all documents.

        Returns:
            Sorted list of all tag names in use
        """
        all_tags: set[str] = set()
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                entries = normalise_tags(metadata.ragd_tags)
                all_tags.update(e.name for e in entries)
        return sorted(all_tags)

    def list_all_entries(self) -> dict[str, list[TagEntry]]:
        """Get all tags with provenance grouped by document.

        Returns:
            Dictionary mapping doc_id to list of TagEntry
        """
        result: dict[str, list[TagEntry]] = {}
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                result[doc_id] = normalise_tags(metadata.ragd_tags)
        return result

    def find_by_tags(
        self,
        tags: list[str],
        match_all: bool = True,
    ) -> list[str]:
        """Find documents matching given tags.

        Args:
            tags: Tags to search for (by name)
            match_all: If True, documents must have ALL tags.
                      If False, documents with ANY tag match.

        Returns:
            List of matching document IDs
        """
        if not tags:
            return []

        matching_ids: list[str] = []
        search_tags = {t.strip().lower() for t in tags}

        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata is None:
                continue

            entries = normalise_tags(metadata.ragd_tags)
            doc_tags = {e.name for e in entries}

            if match_all:
                # All search tags must be present
                if search_tags <= doc_tags:
                    matching_ids.append(doc_id)
            else:
                # Any search tag present
                if search_tags & doc_tags:
                    matching_ids.append(doc_id)

        return matching_ids

    def find_by_source(self, source: str) -> list[tuple[str, list[TagEntry]]]:
        """Find all tags with a specific source.

        Args:
            source: Tag source to search for (e.g., "auto-keybert")

        Returns:
            List of (doc_id, matching_tags) tuples
        """
        results: list[tuple[str, list[TagEntry]]] = []
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                entries = normalise_tags(metadata.ragd_tags)
                matching = [e for e in entries if e.source == source]
                if matching:
                    results.append((doc_id, matching))
        return results

    def tag_counts(self) -> dict[str, int]:
        """Get count of documents for each tag.

        Returns:
            Dictionary mapping tag names to document counts
        """
        counts: dict[str, int] = {}
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                entries = normalise_tags(metadata.ragd_tags)
                for entry in entries:
                    counts[entry.name] = counts.get(entry.name, 0) + 1
        return counts

    def tag_stats(self) -> dict[str, dict[str, int]]:
        """Get tag statistics grouped by source.

        Returns:
            Dictionary mapping source to {tag_name: count}
        """
        stats: dict[str, dict[str, int]] = {}
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata and metadata.ragd_tags:
                entries = normalise_tags(metadata.ragd_tags)
                for entry in entries:
                    if entry.source not in stats:
                        stats[entry.source] = {}
                    stats[entry.source][entry.name] = (
                        stats[entry.source].get(entry.name, 0) + 1
                    )
        return stats

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all documents.

        Preserves provenance metadata during rename.

        Args:
            old_tag: Current tag name
            new_tag: New tag name

        Returns:
            Number of documents updated
        """
        old_tag = old_tag.strip().lower()
        new_tag = new_tag.strip().lower()

        if old_tag == new_tag:
            return 0

        updated = 0
        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata is None:
                continue

            entries = normalise_tags(metadata.ragd_tags)
            modified = False

            new_entries: list[TagEntry] = []
            seen_names: set[str] = set()

            for entry in entries:
                if entry.name == old_tag:
                    # Create new entry with new name, preserve provenance
                    new_entry = TagEntry(
                        name=new_tag,
                        source=entry.source,
                        confidence=entry.confidence,
                        created_at=entry.created_at,
                        created_by=entry.created_by,
                    )
                    if new_tag not in seen_names:
                        new_entries.append(new_entry)
                        seen_names.add(new_tag)
                    modified = True
                else:
                    if entry.name not in seen_names:
                        new_entries.append(entry)
                        seen_names.add(entry.name)

            if modified:
                new_entries = sorted(new_entries, key=lambda t: t.name)
                serialised = [t.to_dict() for t in new_entries]
                if self._store.update(doc_id, ragd_tags=serialised):
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
            tag: Tag name to delete

        Returns:
            Number of documents updated
        """
        tag = tag.strip().lower()
        updated = 0

        for doc_id in self._store.list_ids():
            metadata = self._store.get(doc_id)
            if metadata is None:
                continue

            entries = normalise_tags(metadata.ragd_tags)
            new_entries = [e for e in entries if e.name != tag]

            if len(new_entries) < len(entries):
                serialised = [t.to_dict() for t in new_entries]
                if self._store.update(doc_id, ragd_tags=serialised):
                    updated += 1

        self._logger.info("Deleted tag '%s' from %d documents", tag, updated)
        return updated
