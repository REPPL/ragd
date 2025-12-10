# F-064: Tag Provenance

## Overview

**Use Case**: Distinguish auto-generated tags from user-defined tags
**Milestone**: v0.3.2 (patch release)
**Priority**: P1
**Depends On**: [F-031](../completed/F-031-tag-management.md)

## Problem Statement

As ragd adds auto-tagging capabilities (KeyBERT keywords, LLM classification), users need to distinguish between tags they explicitly added and tags the system suggested. Without provenance tracking:
- Users can't identify which tags to trust
- Quality metrics for auto-tagging are impossible
- Bulk removal of auto-tags requires manual identification
- WebUI can't visually differentiate tag sources

## Design Approach

Extend the tag storage schema to track **provenance metadata** for each tag: source (manual/auto), confidence score, creation timestamp, and creator (user or model). This is a **schema-only change** that prepares for F-061 (Auto-Tag Suggestions) without changing external behaviour.

**Key Design Decisions:**
1. **Backward compatible**: Existing tags default to `source: "manual"`
2. **Minimal storage overhead**: Provenance stored as JSON in existing `ragd_tags` field
3. **CLI shows source**: `ragd tag list` can optionally show provenance
4. **Foundation for F-061**: Auto-tagging builds on this schema

**Tag Entry Structure:**
```python
# Current (v0.3.1)
ragd_tags: list[str] = ["finance", "q3-2024", "important"]

# New (v0.3.2)
ragd_tags: list[TagEntry] = [
    TagEntry(name="finance", source="manual"),
    TagEntry(name="q3-2024", source="manual"),
    TagEntry(name="important", source="auto-keybert", confidence=0.89),
]

# Backward compatible: strings auto-convert to TagEntry(source="manual")
```

**CLI Interface:**
```bash
# Default output unchanged
ragd tag list doc-123
# finance, q3-2024, important

# New: show provenance
ragd tag list doc-123 --provenance
# finance       [manual]
# q3-2024       [manual]
# important     [auto-keybert, 0.89]

# Filter by source
ragd tag list doc-123 --source manual
ragd tag list doc-123 --source auto

# Bulk remove auto-generated tags
ragd tag remove doc-123 --source auto
```

## Implementation Tasks

- [ ] Create `TagEntry` dataclass with provenance fields
- [ ] Update `DocumentMetadata.ragd_tags` to use `list[TagEntry]`
- [ ] Implement backward-compatible deserialisation (strings → TagEntry)
- [ ] Update `TagManager` methods to handle `TagEntry`
- [ ] Add `--provenance` flag to `ragd tag list`
- [ ] Add `--source` filter to tag commands
- [ ] Update schema version to 2.2
- [ ] Add migration for existing tags (set source="legacy")
- [ ] Update tests for new schema

## Success Criteria

- [ ] Existing tags migrate to `source: "legacy"` or `source: "manual"`
- [ ] New manual tags have `source: "manual"`
- [ ] Schema version bumped to 2.2
- [ ] `ragd tag list --provenance` shows source info
- [ ] `--source` filter works on list/remove commands
- [ ] All existing tests pass
- [ ] No breaking changes to external API

## Dependencies

- [F-031: Tag Management](../completed/F-031-tag-management.md) - Extends tag storage

## Technical Notes

**TagEntry Schema:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

@dataclass
class TagEntry:
    """A tag with provenance tracking."""

    name: str
    source: Literal["manual", "legacy", "auto-keybert", "auto-llm", "auto-ner", "imported"] = "manual"
    confidence: float | None = None  # 0.0-1.0 for auto-generated
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str | None = None  # User ID or model name

    def to_dict(self) -> dict:
        """Serialise for JSON storage."""
        return {
            "name": self.name,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: dict | str) -> "TagEntry":
        """Deserialise from storage (backward compatible)."""
        if isinstance(data, str):
            # Legacy: plain string tag
            return cls(name=data, source="legacy")
        return cls(
            name=data["name"],
            source=data.get("source", "legacy"),
            confidence=data.get("confidence"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            created_by=data.get("created_by"),
        )

    def __str__(self) -> str:
        """String representation (just the name for compatibility)."""
        return self.name

    def __eq__(self, other) -> bool:
        """Compare by name for set operations."""
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, TagEntry):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)
```

**Schema Migration (2.1 → 2.2):**
```python
def migrate_tags_v21_to_v22(metadata: dict) -> dict:
    """Migrate tag storage from strings to TagEntry."""
    tags = metadata.get("ragd_tags", [])
    if not tags:
        return metadata

    # Convert string tags to TagEntry format
    new_tags = []
    for tag in tags:
        if isinstance(tag, str):
            new_tags.append({
                "name": tag,
                "source": "legacy",
                "confidence": None,
                "created_at": None,
                "created_by": None,
            })
        else:
            new_tags.append(tag)  # Already in new format

    metadata["ragd_tags"] = new_tags
    metadata["ragd_schema_version"] = "2.2"
    return metadata
```

**Backward Compatibility:**

The `DocumentMetadata` class provides a compatibility property:
```python
@property
def tag_names(self) -> list[str]:
    """Get tag names only (for backward compatibility)."""
    return [t.name if isinstance(t, TagEntry) else t for t in self.ragd_tags]
```

## Related Documentation

- [State-of-the-Art Tagging](../../research/state-of-the-art-tagging.md) - Provenance tracking patterns
- [ADR-0023: Metadata Schema Evolution](../../decisions/adrs/0023-metadata-schema-evolution.md) - Migration strategy
- [F-031: Tag Management](../completed/F-031-tag-management.md) - Core tag operations
- [F-061: Auto-Tag Suggestions](./F-061-auto-tag-suggestions.md) - Uses provenance

---

**Status**: Completed
