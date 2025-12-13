# Use Case: E-book Library

Managing personal book collections with ragd.

## Scenario

You have a growing e-book library across multiple formats. You want to:
- Search across all your books by concept or theme
- Find specific passages or quotes
- Organise by genre, author, and reading status

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/books

chunking:
  strategy: recursive
  chunk_size: 1024  # Larger for books
  overlap: 100

search:
  mode: hybrid
  semantic_weight: 0.8  # Conceptual search
```

### Initial Indexing

```bash
# Index Calibre library
ragd index ~/Calibre\ Library --recursive

# Index other e-book folders
ragd index ~/Books --recursive
```

**Supported formats:** PDF, EPUB, TXT

## Workflow

### Searching Your Library

**Find books by theme:**
```bash
ragd search "themes of isolation and redemption"
```

**Find specific content:**
```bash
ragd search "dialogue about the nature of time"
```

**Find by author style:**
```bash
ragd search "passages with vivid nature descriptions"
```

### Organising Your Collection

**Tag by genre and status:**
```bash
ragd tag add book-123 "genre:sci-fi" "status:reading"
ragd tag add book-456 "genre:non-fiction" "topic:history"
```

**Create reading list collections:**
```bash
ragd collection create "To Read" --include-all "status:unread"
ragd collection create "Science Fiction" --include-all "genre:sci-fi"
ragd collection create "Favourites" --include-all "rating:5"
```

### Exploring with Chat

```bash
ragd chat
> Compare how different authors in my library approach the hero's journey
> What philosophical themes appear across my non-fiction collection?
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "quotes about perseverance" | Find inspirational passages |
| "world-building descriptions" | Explore fantasy settings |
| "character development arcs" | Study narrative techniques |
| "scientific explanations" | Find educational content |
| "plot twists and revelations" | Discover narrative moments |

## Tips

1. **Larger chunks** - Books benefit from 1024+ token chunks for context
2. **High semantic weight** - Literature is conceptual; favour semantic search
3. **Tag consistently** - Use `genre:`, `status:`, `author:` prefixes
4. **Collections for lists** - Create "To Read", "Reading", "Completed" collections
5. **Chat for synthesis** - Use chat to compare themes across books

## Sample Reading Session

```bash
# Find books about a topic
ragd search "exploration of artificial intelligence"

# Search within a genre
ragd search "mystery plot twists" --tag "genre:mystery"

# Explore themes across your library
ragd chat
> What common themes appear in the science fiction books I've read?

# Organise as you go
ragd tag add book-789 "status:completed" "rating:5"
```

---

## Related Documentation

- [Tutorial: Getting Started](../tutorials/01-getting-started.md)
- [Tutorial: Organising Your Knowledge Base](../tutorials/04-organisation.md)
- [F-100: New File Types](../development/features/completed/F-100-new-file-types.md)

## Related Use Cases

- [Personal Notes](personal-notes.md) - Note management
- [Research Papers](research-papers.md) - Academic content
