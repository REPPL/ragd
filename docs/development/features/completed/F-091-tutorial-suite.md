# F-091: Tutorial Suite

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

New users lack guided learning paths. Scattered documentation makes it difficult to get started effectively.

## Design Approach

Create progressive tutorials from beginner to advanced, each building on previous knowledge.

### Tutorial Structure
```
docs/tutorials/
├── README.md              # Tutorial index
├── 01-getting-started.md  # Installation, first index
├── 02-searching.md        # Search queries, filters
├── 03-chat-interface.md   # Interactive chat
├── 04-organisation.md     # Tags, collections
├── 05-advanced-search.md  # Hybrid search, scoring
└── 06-automation.md       # Scripts, JSON output
```

### Tutorial Format
Each tutorial includes:
1. **Goal** - What you'll learn
2. **Prerequisites** - What you need to know
3. **Time estimate** - Expected duration
4. **Steps** - Numbered instructions
5. **Verification** - How to check success
6. **Next steps** - Where to go next

## Implementation Tasks

- [ ] Create tutorial directory structure
- [ ] Write 01-getting-started.md
- [ ] Write 02-searching.md
- [ ] Write 03-chat-interface.md
- [ ] Write 04-organisation.md
- [ ] Write 05-advanced-search.md
- [ ] Write 06-automation.md
- [ ] Create tutorial index with learning paths
- [ ] Add sample documents for tutorials

## Success Criteria

- [ ] Complete tutorial path from install to advanced usage
- [ ] Each tutorial is self-contained and testable
- [ ] Sample documents included for hands-on practice

## Dependencies

- v0.8.6 (Security Focus)

---

## Related Documentation

- [v0.8.7 Milestone](../../milestones/v0.8.7.md)
- [F-093 Troubleshooting Guide](./F-093-troubleshooting-guide.md)

---

**Status**: Completed
