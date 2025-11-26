# UC-002: Search Knowledge

## Summary

User searches indexed documents to find relevant information.

## User Story

As an end user, I want to search my indexed documents, so that I can find relevant information quickly without manually browsing files.

## Trigger

CLI command: `ragd search "<query>"`

## Priority

P0

## Milestone

v0.1

## Preconditions

- ragd is installed and configured
- At least one document has been indexed
- Embedding model is available (local)

## Success Criteria

- [ ] Natural language queries return relevant results
- [ ] Results include source document and location
- [ ] Results are ranked by relevance
- [ ] Search completes within 2 seconds for typical queries
- [ ] No results case handled gracefully with helpful message
- [ ] Results display snippet of matching content

## Derives Features

- [F-005: Semantic Search](../../development/features/planned/F-005-semantic-search.md)
- [F-006: Result Formatting](../../development/features/planned/F-006-result-formatting.md)

## Related Use Cases

- [UC-001: Index Documents](./UC-001-index-documents.md)
- [UC-003: View System Status](./UC-003-view-system-status.md)

---
