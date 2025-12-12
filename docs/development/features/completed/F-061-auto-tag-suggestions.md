# F-061: Auto-Tag Suggestions

## Overview

**Use Case**: Document organisation through intelligent automation
**Milestone**: v0.7.0 (stretch goal)
**Priority**: P2
**Depends On**: [F-031](../completed/F-031-tag-management.md), [F-030](../completed/F-030-metadata-extraction.md)

## Problem Statement

Users must manually tag every document, which is time-consuming and leads to inconsistent tagging. While ragd already extracts keywords (KeyBERT) and can classify documents (LLM), these insights are not surfaced as actionable tag suggestions that users can review and accept.

## Design Approach

Surface auto-extracted metadata as **suggested tags** that users can confirm, reject, or edit. Confirmed suggestions become regular tags with provenance tracking to distinguish auto-generated from manual tags.

**Tag Suggestion Flow:**
```
Document Ingestion
       ↓
┌─────────────────────────────────────────────────────┐
│ Metadata Extraction (existing F-030)                │
│   - KeyBERT keywords → candidate tags               │
│   - LLM classification → category tag               │
│   - spaCy NER → entity tags (people, orgs, places)  │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ Tag Suggestion Engine (new)                         │
│   - Filter by confidence threshold                  │
│   - Match against existing tag library              │
│   - Normalise to tag format (lowercase, hyphens)    │
│   - Store as "unconfirmed" suggestions              │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ User Review (CLI or WebUI)                          │
│   - View suggestions per document                   │
│   - Bulk confirm/reject                             │
│   - Edit before confirming                          │
└─────────────────────────────────────────────────────┘
```

**CLI Interface:**
```bash
# View suggested tags for a document
ragd tag suggestions <doc-id>
# Output:
#   Suggested tags for "Q3 Financial Report":
#   [auto-keybert] finance (0.89)     [confirm] [reject] [edit]
#   [auto-keybert] quarterly (0.85)   [confirm] [reject] [edit]
#   [auto-llm] report (0.95)          [confirm] [reject] [edit]

# Confirm specific suggestions
ragd tag confirm <doc-id> finance quarterly

# Confirm all suggestions above threshold
ragd tag confirm <doc-id> --all --min-confidence 0.8

# Reject suggestions
ragd tag reject <doc-id> quarterly

# View all documents with pending suggestions
ragd tag suggestions --pending
```

## Implementation Tasks

- [ ] Create `TagSuggestion` dataclass with source, confidence, status
- [ ] Implement `TagSuggestionEngine` to convert metadata to suggestions
- [ ] Add confidence threshold configuration
- [ ] Implement `ragd tag suggestions` command
- [ ] Implement `ragd tag confirm` command
- [ ] Implement `ragd tag reject` command
- [ ] Add `--suggest-tags` flag to `ragd index`
- [ ] Store suggestions in metadata (separate from confirmed tags)
- [ ] Add suggestion review to batch processing

## Success Criteria

- [ ] Keywords from KeyBERT surfaced as suggestions
- [ ] LLM classification surfaced as category suggestion
- [ ] Confidence scores displayed to user
- [ ] Bulk confirm/reject operations work
- [ ] Confirmed suggestions become regular tags
- [ ] Rejected suggestions not shown again
- [ ] Suggestion source tracked (keybert, llm, ner)

## Dependencies

- [F-031: Tag Management](../completed/F-031-tag-management.md) - Core tag CRUD
- [F-030: Metadata Extraction](../completed/F-030-metadata-extraction.md) - Source of suggestions
- [F-064: Tag Provenance](./F-064-tag-provenance.md) - Tracks auto vs manual (v0.3.2)

## Technical Notes

**TagSuggestion Schema:**
```python
@dataclass
class TagSuggestion:
    """A suggested tag pending user review."""

    tag_name: str
    source: Literal["keybert", "llm", "ner", "imported"]
    confidence: float  # 0.0-1.0
    status: Literal["pending", "confirmed", "rejected"] = "pending"
    created_at: datetime = field(default_factory=datetime.now)

    # Original extraction context
    source_text: str = ""  # Text that triggered this suggestion
    source_model: str = ""  # e.g., "all-MiniLM-L6-v2" for KeyBERT
```

**Configuration:**
```yaml
tagging:
  suggestions:
    enabled: true
    min_confidence: 0.7
    max_suggestions_per_doc: 10
    sources:
      keybert: true
      llm: true
      ner: true
```

## Related Documentation

- [State-of-the-Art Tagging](../../research/state-of-the-art-tagging.md)
- [F-031: Tag Management](../completed/F-031-tag-management.md)
- [F-030: Metadata Extraction](../completed/F-030-metadata-extraction.md)
- [F-062: Tag Library](./F-062-tag-library.md)

