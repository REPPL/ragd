# Use Case: Personal Notes

Managing Obsidian vaults and note collections with ragd.

## Scenario

You're a knowledge worker with hundreds of notes in Obsidian (or similar). You want to:
- Search across all notes semantically
- Find connections between ideas
- Quickly recall past insights

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/notes

chunking:
  strategy: sentence
  chunk_size: 256  # Smaller for notes
  overlap: 30

search:
  mode: hybrid
  semantic_weight: 0.8  # More semantic for ideas
```

### Initial Indexing

```bash
ragd index ~/Obsidian/vault --recursive
```

### Watch for New Notes

```bash
ragd watch start ~/Obsidian/vault
```

## Workflow

### Daily Usage

**Morning review:**
```bash
ragd search "what did I learn yesterday about"
```

**During work:**
```bash
ragd search "notes about project X deadline"
```

**Evening reflection:**
```bash
ragd search "ideas I haven't explored yet"
```

### Organising Notes

Tag your notes by topic:
```bash
ragd tag add note-123 "topic:productivity"
ragd tag add note-123 "status:actionable"
```

Create collections:
```bash
ragd collection create projects --tag "topic:project"
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "what books did I want to read" | Find reading list notes |
| "ideas about improving workflow" | Productivity insights |
| "notes from last month's planning" | Historical review |
| "connections between sleep and productivity" | Find related concepts |
| "todos I haven't completed" | Action items |

## Tips

1. **Smaller chunks** - Notes benefit from smaller chunk sizes (256-512)
2. **High semantic weight** - Notes are conceptual, favour semantic search
3. **Watch mode** - Auto-index new notes as you create them
4. **Tags for status** - Use `status:actionable`, `status:archived`
5. **Regular reindex** - Reindex after significant edits

## Sample Queries Session

```bash
# Find all project ideas
ragd search "project ideas I've brainstormed"

# Find notes about a specific topic
ragd search "notes about time management techniques"

# Find related concepts
ragd search "how sleep affects creativity"

# Chat for deeper exploration
ragd chat
> What patterns do my notes show about productivity?
```

---

## Related Documentation

- [Tutorial: Getting Started](../tutorials/01-getting-started.md)
- [Tutorial: Organising Your Knowledge Base](../tutorials/organising-knowledge-base.md)
- [F-037: Watch Folder](../development/features/completed/F-037-watch-folder.md)

## Related Use Cases

- [Research Papers](research-papers.md) - Academic research
- [Meeting Notes](meeting-notes.md) - Work meetings
