# F-052: Metadata CLI

## Overview

**Use Case**: Command-line metadata management
**Milestone**: v0.3.0
**Priority**: P1

## Problem Statement

The metadata storage backend (F-029) and tag management backend (F-031) were implemented in v0.2.0, but users have no CLI interface to interact with them. Users need to view, edit, and search document metadata from the command line.

## Design Approach

Expose existing metadata and tag backends via CLI subcommands:

**Metadata Commands:**

```bash
ragd meta show doc-123                    # Show document metadata
ragd meta edit doc-123 --title "New Title"
ragd meta edit doc-123 --creator "Smith, J."
ragd meta edit doc-123 --project "Research"
```

**Tag Commands:**

```bash
ragd tag add doc-123 important            # Add single tag
ragd tag add doc-123 "topic:ml" "status:reading"  # Multiple tags
ragd tag remove doc-123 draft             # Remove tag
ragd tag list                             # List all tags
ragd tag list --counts                    # Tags with document counts
ragd tag list doc-123                     # Tags for specific document
```

**List Command:**

```bash
ragd list                                 # All documents
ragd list --tag important                 # Filter by tag
ragd list --project Research              # Filter by project
ragd list -n 10                           # Limit results
```

## Implementation Tasks

- [x] Add `meta_show_command()` to display document metadata
- [x] Add `meta_edit_command()` for editing metadata fields
- [x] Add `tag_add_command()` for adding tags
- [x] Add `tag_remove_command()` for removing tags
- [x] Add `tag_list_command()` for listing tags
- [x] Add `list_documents_command()` for document listing
- [x] Add `metadata_path` property to `RagdConfig`
- [x] Create `meta` subcommand group in CLI
- [x] Create `tag` subcommand group in CLI
- [x] Support JSON output format for all commands

## Success Criteria

- [x] Users can view document metadata via CLI
- [x] Users can edit metadata fields via CLI
- [x] Users can add/remove tags via CLI
- [x] Users can list and filter documents
- [x] JSON output available for scripting
- [x] All existing tests pass

## Dependencies

- [F-029: Metadata Storage](./F-029-metadata-storage.md) - MetadataStore backend
- [F-031: Tag Management](./F-031-tag-management.md) - TagManager backend

## Technical Notes

**Subcommand Structure:**

```python
meta_app = typer.Typer(help="Manage document metadata.")
tag_app = typer.Typer(help="Manage document tags.")
app.add_typer(meta_app, name="meta")
app.add_typer(tag_app, name="tag")
```

**Output Formats:**

- `rich`: Formatted tables with colours (default)
- `plain`: Simple text output
- `json`: Machine-readable JSON

## Related Documentation

- [F-029: Metadata Storage](./F-029-metadata-storage.md)
- [F-031: Tag Management](./F-031-tag-management.md)
- [v0.3.0 Milestone](../../milestones/v0.3.0.md)

