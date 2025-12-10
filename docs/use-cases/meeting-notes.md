# Use Case: Meeting Notes

Managing work meeting notes with ragd.

## Scenario

You attend multiple meetings daily and want to:
- Search across all meeting notes
- Find action items and decisions
- Track topics discussed over time

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/meetings

chunking:
  strategy: sentence
  chunk_size: 512
  overlap: 50

search:
  mode: hybrid
  semantic_weight: 0.7
```

### Initial Indexing

```bash
ragd index ~/Documents/meetings --recursive
```

### Watch for New Notes

```bash
ragd watch start ~/Documents/meetings
```

## Workflow

### After Each Meeting

Index the new notes:

```bash
ragd index ~/Documents/meetings/2024-01-15-standup.md
```

Tag with context:

```bash
ragd tag add meeting-123 "meeting:standup" "project:alpha"
```

### Finding Information

**Find decisions:**
```bash
ragd search "decision about deployment schedule"
```

**Find action items:**
```bash
ragd search "action items assigned to me"
```

**Find by date:**
```bash
ragd search "discussed last week" --after 2024-01-08
```

### Organising Meetings

Create collections by type:

```bash
ragd collection create "Standups" --include-all "meeting:standup"
ragd collection create "Project Alpha" --include-all "project:alpha"
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "what was decided about the API" | Find API decisions |
| "action items from project alpha" | Track project tasks |
| "discussions about timeline" | Schedule information |
| "who mentioned database migration" | Find specific topics |

## Tips

1. **Consistent naming** - Use `YYYY-MM-DD-meeting-type.md`
2. **Tag immediately** - Tag while context is fresh
3. **Use collections** - Group by project or meeting type
4. **Regular search** - Review past meetings weekly

---

## Related Documentation

- [Use Case: Personal Notes](personal-notes.md)
- [Tutorial: Organising Your Knowledge Base](../tutorials/organising-knowledge-base.md)
- [F-031: Tag Management](../development/features/completed/F-031-tag-management.md)

---

**Status**: Stub - full content planned
