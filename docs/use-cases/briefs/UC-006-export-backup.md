# UC-006: Export & Backup

## Summary

User exports or backs up their ragd data for portability and safety.

## User Story

As an end user, I want to export and backup my ragd knowledge base, so that I can restore it if something goes wrong or migrate to a new machine.

## Trigger

CLI commands:
- `ragd export <path>` - Export knowledge base to archive
- `ragd import <path>` - Import knowledge base from archive

## Priority

P0

## Milestone

v0.2

## Preconditions

- ragd is installed and configured
- For export: At least one document indexed
- For import: Valid ragd export archive exists

## Success Criteria

- [ ] Export creates portable archive (zip/tar)
- [ ] Export includes all indexed content and embeddings
- [ ] Export includes metadata and configuration
- [ ] Import restores full knowledge base
- [ ] Import validates archive integrity before restore
- [ ] Progress feedback during export/import
- [ ] Option to export metadata-only (without embeddings)
- [ ] Import handles version compatibility gracefully

## Derives Features

- [F-032: Export Engine](../../development/features/completed/F-032-export-engine.md)
- [F-033: Import Engine](../../development/features/completed/F-033-import-engine.md)
- [F-034: Archive Format](../../development/features/completed/F-034-archive-format.md)

## Related Use Cases

- [UC-001: Index Documents](./UC-001-index-documents.md)
- [UC-003: View System Status](./UC-003-view-system-status.md)
- [UC-005: Manage Metadata](./UC-005-manage-metadata.md)

---
