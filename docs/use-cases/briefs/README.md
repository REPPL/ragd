# Use Case Briefs

Lightweight use case specifications for ragd.

## Purpose

Use case briefs capture **what users want to accomplish** in a concise format. They inform feature specifications and tutorials.

## Template

```markdown
# UC-NNN: [Use Case Name]

## Summary
[One sentence describing what the user accomplishes]

## User Story
As an end user, I want to [goal], so that [benefit].

## Trigger
[What initiates this use case - CLI command, UI action, etc.]

## Priority
[P0 | P1 | P2 | P3]

## Milestone
[Target version]

## Preconditions
- [What must be true before this use case can execute]

## Success Criteria
- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Testable criterion 3]

## Derives Features
- [Feature 1]
- [Feature 2]

## Related Use Cases
- [UC-NNN: Related use case]
```

## Contents

### P0 Use Cases (v0.1-v0.2)

| Brief | Description |
|-------|-------------|
| [UC-001](./UC-001-index-documents.md) | Index documents into the knowledge base |
| [UC-002](./UC-002-search-knowledge.md) | Search indexed documents |
| [UC-003](./UC-003-view-system-status.md) | View system and index status |
| [UC-004](./UC-004-process-messy-pdfs.md) | Process messy/scanned PDFs |
| [UC-005](./UC-005-manage-metadata.md) | Manage document metadata |
| [UC-006](./UC-006-export-backup.md) | Export and backup data |

## What Belongs Here

- Use case brief documents (UC-NNN-name.md)
- User journey specifications
- Acceptance criteria

## What Doesn't Belong Here

- **Detailed feature specs** → `../../development/features/`
- **Implementation details** → `../../development/implementation/`
- **Tutorials** → `../../tutorials/`

---
