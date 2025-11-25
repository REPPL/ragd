# UC-001: Index Documents

## Summary

User indexes documents into the knowledge base for later retrieval.

## User Story

As an end user, I want to index my documents into ragd, so that I can search and retrieve information from them later.

## Trigger

CLI command: `ragd index <path>`

## Priority

P0

## Milestone

v0.1

## Preconditions

- ragd is installed and configured
- Document exists at specified path
- Supported format (PDF, TXT, Markdown)

## Success Criteria

- [ ] Single document can be indexed via CLI
- [ ] Multiple documents can be indexed via directory path
- [ ] Progress feedback shown during indexing
- [ ] Confirmation message shows indexed document count
- [ ] Indexed content is searchable immediately
- [ ] Duplicate detection prevents re-indexing same content

## Derives Features

- [F-001: Document Ingestion Pipeline](../../../development/features/planned/F-001-document-ingestion.md)
- [F-002: Text Extraction](../../../development/features/planned/F-002-text-extraction.md)
- [F-003: Chunking Engine](../../../development/features/planned/F-003-chunking-engine.md)
- [F-004: Embedding Generation](../../../development/features/planned/F-004-embedding-generation.md)

## Related Use Cases

- [UC-002: Search Knowledge](./UC-002-search-knowledge.md)
- [UC-004: Process Messy PDFs](./UC-004-process-messy-pdfs.md)
- [UC-005: Manage Metadata](./UC-005-manage-metadata.md)

---
