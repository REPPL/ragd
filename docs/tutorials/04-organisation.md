# Organisation

Tags, collections, and metadata for organising your knowledge base.

**Time:** 25 minutes
**Level:** Intermediate
**Prerequisites:** Indexed documents

## What You'll Learn

- Adding and managing tags
- Creating smart collections
- Editing document metadata
- Sensitivity tiers

## Tags

### Adding Tags

Tag a document:

```bash
ragd tag add doc-123 important
```

Add multiple tags:

```bash
ragd tag add doc-123 "topic:ml" "status:reading" research
```

### Viewing Tags

List tags on a document:

```bash
ragd tag list doc-123
```

List all tags with counts:

```bash
ragd tag list --counts
```

### Removing Tags

```bash
ragd tag remove doc-123 draft
```

### Tag Namespaces

Organise tags with namespaces:

- `topic:machine-learning`
- `status:reading`
- `project:thesis`

View the tag library:

```bash
ragd library show
```

## Collections

Smart collections group documents by criteria.

### Create a Collection

```bash
ragd collection create research \
    --description "Research papers" \
    --tag "topic:research"
```

### List Collections

```bash
ragd collection list
```

### View Collection Contents

```bash
ragd collection show research
```

### Update Collection

```bash
ragd collection update research --add-tag "status:active"
```

## Metadata

### View Document Metadata

```bash
ragd meta show doc-123
```

### Edit Metadata

```bash
ragd meta edit doc-123 --title "My Research Paper"
ragd meta edit doc-123 --creator "Smith, J.; Doe, J."
ragd meta edit doc-123 --project "Thesis"
```

## Sensitivity Tiers

Control access requirements for sensitive documents.

### Available Tiers

| Tier | Description |
|------|-------------|
| public | Always accessible |
| personal | Default, basic auth |
| sensitive | Requires active session |
| critical | Session + confirmation |

### Set Tier

```bash
ragd tier set doc-123 sensitive
```

### View Tier

```bash
ragd tier show doc-123
```

### List by Tier

```bash
ragd tier list sensitive
```

## Verification

You've succeeded if you can:
- [ ] Add and remove tags from documents
- [ ] Create a smart collection
- [ ] Edit document metadata
- [ ] Set sensitivity tiers

## Next Steps

- [Advanced Search](05-advanced-search.md) - Advanced features
- [Automation](06-automation.md) - Scripts and integrations

---

## Tips

- Use namespaces for consistent tagging
- Collections update automatically based on criteria
- Tiers help protect sensitive documents
