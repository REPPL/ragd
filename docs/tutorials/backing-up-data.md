# Backing Up Your Data

Learn how to export, backup, and restore your ragd knowledge base.

**Time:** 15 minutes
**Level:** Beginner
**Prerequisites:** Completed Getting Started tutorial, indexed documents

## What You'll Learn

- Creating full and partial backups
- Exporting documents by tag or project
- Restoring from backup archives
- Migration between machines
- Backup strategies for different needs

## Understanding ragd Archives

ragd exports create `.tar.gz` archives containing:
- Document metadata and text content
- Chunk boundaries and relationships
- Embeddings (optional - can be regenerated)
- Tags and collection definitions

Archives are portable between machines and ragd versions.

## Step 1: Create a Full Backup

Export everything in your knowledge base:

```bash
# Full backup with embeddings
ragd export ~/backups/ragd-backup.tar.gz

# Full backup without embeddings (smaller file, regenerates on import)
ragd export ~/backups/ragd-backup.tar.gz --no-embeddings
```

**Tip:** The `--no-embeddings` option creates smaller archives. Embeddings are regenerated automatically during import.

### Verbose Output

See detailed progress during export:

```bash
ragd export ~/backups/ragd-backup.tar.gz --verbose
```

## Step 2: Create Partial Backups

Export specific subsets of your knowledge base.

### Export by Tag

```bash
# Export all documents tagged with "topic:ml"
ragd export ~/backups/ml-papers.tar.gz --tag "topic:ml"

# Export documents with a status tag
ragd export ~/backups/reviewed.tar.gz --tag "status:reviewed"
```

### Export by Project

```bash
# Export all documents in a project
ragd export ~/backups/project-alpha.tar.gz --project "alpha"
```

### Combined Filters

```bash
# Export machine learning papers that have been reviewed
ragd export ~/backups/ml-reviewed.tar.gz \
  --tag "topic:ml" \
  --project "research"
```

## Step 3: Restore from Backup

Import archives to restore your knowledge base.

### Basic Import

```bash
# Import everything from archive
ragd import ~/backups/ragd-backup.tar.gz
```

### Handling Conflicts

When importing documents that already exist:

```bash
# Skip documents that already exist (keep existing)
ragd import ~/backups/ragd-backup.tar.gz --skip-conflicts

# Overwrite existing documents with archived versions
ragd import ~/backups/ragd-backup.tar.gz --overwrite
```

### Validate Before Importing

Check what would be imported without making changes:

```bash
ragd import ~/backups/ragd-backup.tar.gz --dry-run
```

This shows:
- Documents that would be added
- Documents that would conflict
- Total size of import

## Step 4: Migration Between Machines

### On the Source Machine

```bash
# Create a complete backup
ragd export ~/ragd-export.tar.gz --verbose

# Copy to destination (examples)
scp ~/ragd-export.tar.gz user@newmachine:~/
# or use cloud storage, USB drive, etc.
```

### On the Destination Machine

```bash
# Initialise ragd if needed
ragd init

# Import the backup
ragd import ~/ragd-export.tar.gz --verbose

# Verify
ragd info
ragd search "test query"
```

## Backup Strategies

Choose a strategy based on your needs:

### Personal Use (Minimal)

```bash
# Weekly full backup
ragd export ~/backups/ragd-weekly-$(date +%Y%m%d).tar.gz
```

### Active Research (Regular)

| When | Command |
|------|---------|
| Daily | `ragd export ~/backups/daily/ragd-$(date +%Y%m%d).tar.gz --no-embeddings` |
| Weekly | `ragd export ~/backups/weekly/ragd-$(date +%Y%m%d).tar.gz` |
| Before major changes | `ragd export ~/backups/pre-change.tar.gz` |

### Critical Data (Redundant)

```bash
# Local backup
ragd export ~/backups/ragd-backup.tar.gz

# Cloud sync (example with rclone)
rclone copy ~/backups/ragd-backup.tar.gz remote:backups/

# Verify backup integrity
tar -tzf ~/backups/ragd-backup.tar.gz > /dev/null && echo "Archive OK"
```

## Verification

You've succeeded if:
- [ ] `ragd export` creates an archive file
- [ ] The archive file exists and has content (check with `ls -lh`)
- [ ] `ragd import --dry-run` shows expected documents
- [ ] `ragd import` successfully restores documents
- [ ] `ragd info` shows correct document counts after import

## Example Workflow

```bash
# 1. Check current state
ragd info

# 2. Create backup before making changes
ragd export ~/backups/pre-cleanup.tar.gz

# 3. Make changes (delete old documents, reorganise, etc.)
ragd delete doc-123 doc-456

# 4. If something went wrong, restore
ragd import ~/backups/pre-cleanup.tar.gz --overwrite

# 5. Regular weekly backup
ragd export ~/backups/weekly/ragd-$(date +%Y%m%d).tar.gz
```

## Next Steps

- [Organising Your Knowledge Base](organising-knowledge-base.md) - Tag and organise before backup
- [Powerful Searching](powerful-searching.md) - Find documents to backup by topic

---

## Troubleshooting

**"Archive not found"**
- Check the file path is correct
- Ensure the file exists: `ls -la ~/backups/`

**"Permission denied"**
- Check directory permissions
- Try a different backup location

**Import conflicts**
- Use `--dry-run` first to see conflicts
- Choose `--skip-conflicts` or `--overwrite` based on your needs

**Large archive size**
- Use `--no-embeddings` for smaller files
- Export subsets by tag or project instead of full backup

**Slow import**
- Normal for large archives (embeddings take time)
- Use `--verbose` to see progress
- Consider `--no-embeddings` exports for faster restore

---

## Related Documentation

- [Tutorial: Getting Started](01-getting-started.md)
- [F-032: Export Engine](../development/features/completed/F-032-export-engine.md)
- [F-033: Import Engine](../development/features/completed/F-033-import-engine.md)
- [F-034: Archive Format](../development/features/completed/F-034-archive-format.md)
