# UC-003: View System Status

## Summary

User views the current state of ragd including indexed documents and system health.

## User Story

As an end user, I want to see the status of my ragd installation, so that I can understand what documents are indexed and if the system is working correctly.

## Trigger

CLI command: `ragd status`

## Priority

P0

## Milestone

v0.1

## Preconditions

- ragd is installed

## Success Criteria

- [ ] Shows total number of indexed documents
- [ ] Shows total number of chunks/embeddings
- [ ] Shows storage usage (disk space)
- [ ] Shows embedding model in use
- [ ] Shows configuration file location
- [ ] Indicates if system is healthy/ready
- [ ] Works even with empty index (shows zeros)

## Derives Features

- [F-007: Status Dashboard](../../development/features/completed/F-007-status-dashboard.md)
- [F-035: Health Check Command](../../development/features/completed/F-035-health-check.md)

## Related Use Cases

- [UC-001: Index Documents](./UC-001-index-documents.md)
- [UC-006: Export & Backup](./UC-006-export-backup.md)

---
