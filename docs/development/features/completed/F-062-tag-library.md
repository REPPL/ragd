# F-062: Tag Library Management

## Overview

**Use Case**: Consistent document organisation through controlled vocabulary
**Milestone**: v0.7.0 (stretch goal)
**Priority**: P2
**Depends On**: [F-031](../completed/F-031-tag-management.md)

## Problem Statement

Free-form tagging leads to inconsistency: "finance", "Finance", "financial", and "money" might all describe the same concept. Without a controlled vocabulary, tag sprawl reduces searchability and creates maintenance burden. Users need a way to define approved tags while still allowing flexibility for new categories.

## Design Approach

Implement a **tag library** with system-defined namespaces (immutable defaults) and user-defined namespaces (fully customisable). Tags can be "open" (any value) or "closed" (from predefined list). Auto-tag suggestions can propose new tags for user review before adding to the library.

**Tag Library Structure:**
```
Tag Library
├── System Namespaces (built-in, can be hidden but not deleted)
│   ├── document-type: [report, article, documentation, legal, financial, academic, other]
│   ├── sensitivity: [public, internal, confidential]
│   └── status: [draft, review, approved, archived]
│
├── User Namespaces (fully customisable)
│   ├── project: [alpha, beta, gamma]  # User-defined closed set
│   ├── topic: *  # Open - any value allowed
│   └── client: [acme, globex]  # User-defined closed set
│
└── Pending Suggestions (from auto-tagging, awaiting promotion)
    └── [machine-learning, quarterly, compliance, ...]
```

**CLI Interface:**
```bash
# List tag library
ragd tag library
# Output:
#   System Namespaces:
#     document-type: report, article, documentation, legal, financial, academic, other
#     sensitivity: public, internal, confidential
#     status: draft, review, approved, archived
#
#   User Namespaces:
#     project: alpha, beta, gamma (closed)
#     topic: * (open)
#
#   Pending Suggestions: 5 tags awaiting review

# Create user namespace
ragd tag library create project --closed
ragd tag library add project alpha beta gamma

# Create open namespace (any value allowed)
ragd tag library create topic --open

# Add tag to existing namespace
ragd tag library add project delta

# Remove tag from namespace
ragd tag library remove project gamma

# Rename tag (updates all documents)
ragd tag library rename project/alpha project/apollo

# Delete namespace (warns if tags in use)
ragd tag library delete project

# Promote suggestion to library
ragd tag library promote machine-learning --namespace topic

# Hide system namespace (still works, not shown in UI)
ragd tag library hide sensitivity

# Validate tags against library
ragd tag validate
# Output: 3 documents have tags not in library: "custom-tag", "misc"
```

## Implementation Tasks

- [ ] Create `TagLibrary` class with namespace management
- [ ] Define system namespaces with immutable defaults
- [ ] Implement user namespace CRUD
- [ ] Add open vs closed namespace modes
- [ ] Implement tag validation against library
- [ ] Add `ragd tag library` command group
- [ ] Implement suggestion promotion workflow
- [ ] Add tag normalisation (lowercase, hyphens)
- [ ] Store library in metadata database
- [ ] Add library sync to config export/import

## Success Criteria

- [ ] System namespaces available by default
- [ ] User can create custom namespaces
- [ ] Closed namespaces reject invalid tags
- [ ] Open namespaces accept any tag
- [ ] Tags can be renamed across all documents
- [ ] Library validates existing tags
- [ ] Suggestions can be promoted to library
- [ ] Library persists across sessions

## Dependencies

- [F-031: Tag Management](../completed/F-031-tag-management.md) - Core tag operations
- [F-061: Auto-Tag Suggestions](./F-061-auto-tag-suggestions.md) - Source of suggestions

## Technical Notes

**TagLibrary Schema:**
```python
@dataclass
class TagNamespace:
    """A namespace in the tag library."""

    name: str
    tags: list[str]  # Allowed tags (empty if open)
    is_open: bool = False  # True = any tag allowed
    is_system: bool = False  # True = cannot be deleted
    is_hidden: bool = False  # True = not shown in UI
    description: str = ""


@dataclass
class TagLibrary:
    """Manages the controlled vocabulary for tags."""

    namespaces: dict[str, TagNamespace] = field(default_factory=dict)
    pending_suggestions: list[str] = field(default_factory=list)

    # Default system namespaces
    SYSTEM_DEFAULTS = {
        "document-type": ["report", "article", "documentation",
                         "legal", "financial", "academic", "other"],
        "sensitivity": ["public", "internal", "confidential"],
        "status": ["draft", "review", "approved", "archived"],
    }

    def validate_tag(self, tag: str) -> tuple[bool, str]:
        """Check if tag is valid against library.

        Returns:
            (is_valid, message)
        """
        if "/" not in tag:
            return True, "Unnamespaced tags always allowed"

        namespace, value = tag.split("/", 1)
        if namespace not in self.namespaces:
            return False, f"Unknown namespace: {namespace}"

        ns = self.namespaces[namespace]
        if ns.is_open:
            return True, "Open namespace"

        if value in ns.tags:
            return True, "Tag in namespace"

        return False, f"Tag '{value}' not in closed namespace '{namespace}'"
```

**Storage:**
```sql
CREATE TABLE tag_namespaces (
    name TEXT PRIMARY KEY,
    is_open BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,
    description TEXT
);

CREATE TABLE tag_namespace_values (
    namespace TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    PRIMARY KEY (namespace, tag_value),
    FOREIGN KEY (namespace) REFERENCES tag_namespaces(name)
);
```

**Configuration:**
```yaml
tagging:
  library:
    enforce_namespaces: false  # If true, reject unnamespaced tags
    suggest_namespace: true    # Suggest namespace when adding tags
    auto_create_namespace: false  # Auto-create namespace for new patterns
```

## Related Documentation

- [State-of-the-Art Tagging](../../research/state-of-the-art-tagging.md)
- [F-031: Tag Management](../completed/F-031-tag-management.md)
- [F-061: Auto-Tag Suggestions](./F-061-auto-tag-suggestions.md)
- [F-063: Smart Collections](./F-063-smart-collections.md)

---

**Status**: Completed
