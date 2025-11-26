# UC-005: Manage Metadata

## Summary

User views, edits, and manages metadata for indexed documents.

## User Story

As an end user, I want to manage metadata (tags, titles, dates) for my indexed documents, so that I can organise my knowledge base and filter searches effectively.

## Trigger

CLI commands:
- `ragd meta list` - List all documents with metadata
- `ragd meta show <doc-id>` - Show metadata for specific document
- `ragd meta edit <doc-id>` - Edit metadata for document
- `ragd meta tag <doc-id> <tags>` - Add tags to document

## Priority

P0

## Milestone

v0.2

## Preconditions

- ragd is installed and configured
- At least one document has been indexed

## Success Criteria

- [ ] List all indexed documents with basic metadata
- [ ] View detailed metadata for specific document
- [ ] Add/remove tags from documents
- [ ] Edit document title/description
- [ ] Auto-extracted metadata preserved (author, date, etc.)
- [ ] Metadata searchable/filterable
- [ ] Bulk tagging support for multiple documents

## Derives Features

- [F-029: Metadata Storage](../../development/features/planned/F-029-metadata-storage.md)
- [F-030: Metadata Extraction](../../development/features/planned/F-030-metadata-extraction.md)
- [F-031: Tag Management](../../development/features/planned/F-031-tag-management.md)

## Related Use Cases

- [UC-001: Index Documents](./UC-001-index-documents.md)
- [UC-002: Search Knowledge](./UC-002-search-knowledge.md)
- [UC-006: Export & Backup](./UC-006-export-backup.md)

---
