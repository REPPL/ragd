# Automation

Scripts, JSON output, and system integrations.

**Time:** 20 minutes
**Level:** Advanced
**Prerequisites:** Completed basic tutorials

## What You'll Learn

- JSON output for scripting
- Shell scripting with ragd
- Watch mode for automatic indexing
- Export and backup

## JSON Output

### Enable JSON Mode

Add `--format json` to any command:

```bash
ragd search "query" --format json
```

Or set environment variable:

```bash
export RAGD_OUTPUT_FORMAT=json
ragd search "query"
```

### Parse with jq

Get first result content:

```bash
ragd search "query" --format json | jq '.results[0].content'
```

List document IDs:

```bash
ragd list --format json | jq -r '.documents[].id'
```

Count results:

```bash
ragd search "query" --format json | jq '.count'
```

## Shell Scripting

### Index All PDFs

```bash
#!/bin/bash
find ~/Documents -name "*.pdf" -type f | while read file; do
    ragd index "$file"
done
```

### Search and Process Results

```bash
#!/bin/bash
query="$1"
ragd search "$query" --format json --no-interactive | \
    jq -r '.results[] | "\(.document_id): \(.content[:100])..."'
```

### Daily Re-index

```bash
#!/bin/bash
# re-index-daily.sh
ragd reindex --type pdf --force
ragd quality --below 0.5 --format json | jq -r '.documents[].id' | \
    xargs -I{} ragd reindex {}
```

## Watch Mode

Automatically index new documents.

### Start Watching

```bash
ragd watch start ~/Documents/inbox
```

### Check Status

```bash
ragd watch status
```

### Stop Watching

```bash
ragd watch stop
```

### Multiple Directories

```bash
ragd watch start ~/Documents/research ~/Documents/notes
```

## Export and Backup

### Export Knowledge Base

```bash
ragd export backup.ragd
```

### Import Knowledge Base

```bash
ragd import backup.ragd
```

### Automated Backup Script

```bash
#!/bin/bash
# backup-ragd.sh
DATE=$(date +%Y%m%d)
ragd export "ragd-backup-$DATE.ragd"

# Keep only last 7 backups
ls -t ragd-backup-*.ragd | tail -n +8 | xargs rm -f
```

## CSV Export

For spreadsheet analysis:

```bash
ragd list --format csv > documents.csv
```

## Verification

You've succeeded if you can:
- [ ] Extract data using JSON output
- [ ] Write shell scripts using ragd
- [ ] Set up watch mode
- [ ] Export and import knowledge bases

---

## Integration Ideas

- **Obsidian**: Watch vault folder, search from Obsidian
- **Alfred/Raycast**: Quick search launcher
- **cron**: Daily re-indexing and backup
- **Git hooks**: Index documentation on commit

## Tips

- Use `--no-interactive` in scripts
- Pipe JSON through jq for processing
- Set RAGD_OUTPUT_FORMAT for session-wide JSON
- Export regularly for backups

---

## Related Documentation

- [CLI Advanced Guide](../guides/cli/advanced.md) - Configuration and debugging
- [CLI Reference](../reference/cli-reference.md) - Complete command specifications
- [Backing Up Your Data](backing-up-data.md) - Export and backup guide
