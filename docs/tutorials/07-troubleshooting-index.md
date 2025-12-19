# Troubleshooting Indexing Issues

Learn to diagnose and fix common indexing problems using ragd's inspection tools.

**Time:** 15 minutes
**Level:** Intermediate
**Prerequisites:** Completed [Getting Started](./01-getting-started.md)

## What You'll Learn

- Using `ragd inspect` to examine your index
- Finding duplicate content
- Understanding why files are skipped
- Diagnosing extraction issues

## The Inspect Command

The `ragd inspect` command helps you understand what's in your index and troubleshoot problems.

```bash
ragd inspect
```

This shows an overview of your indexed documents.

## Finding Duplicates

If you've indexed the same document multiple times (perhaps from different locations), you can find duplicates:

```bash
ragd inspect --duplicates
```

**Example output:**
```
Duplicate Content Detected
──────────────────────────

Hash: a1b2c3d4...
  - ~/Documents/report.pdf (indexed 2024-01-15)
  - ~/Downloads/report.pdf (indexed 2024-01-20)

Hash: e5f6g7h8...
  - ~/Work/notes.md
  - ~/Backup/notes.md
```

### Removing Duplicates

Once you've identified duplicates, you can remove the older or unwanted copies:

```bash
# Remove a specific document by ID
ragd delete doc-abc123

# Or re-index with duplicate detection enabled (default)
ragd reindex --all
```

## Understanding Why Files Are Skipped

When indexing, ragd may skip certain files. To understand why:

```bash
ragd inspect --explain ~/Documents/problem-file.pdf
```

**Common reasons for skipping:**

| Reason | Explanation | Solution |
|--------|-------------|----------|
| Already indexed | File hasn't changed since last index | Use `--force` to re-index |
| Unsupported format | File type not supported | Convert to supported format |
| Empty content | No extractable text | Check if file is valid |
| Too large | Exceeds size limits | Increase limits in config |
| Access denied | Permission issues | Check file permissions |

## Viewing Content Hashes

To see the content hash for each document (useful for debugging):

```bash
ragd inspect --hashes
```

This shows:
- Document ID
- File path
- Content hash (SHA256)
- Index date

## Common Scenarios

### Scenario 1: "My search isn't finding a document I know I indexed"

1. Check if it's indexed:
   ```bash
   ragd list | grep "filename"
   ```

2. If not found, check why it was skipped:
   ```bash
   ragd inspect --explain ~/path/to/file.pdf
   ```

3. Force re-index if needed:
   ```bash
   ragd index ~/path/to/file.pdf --force
   ```

### Scenario 2: "I have duplicate results in my searches"

1. Find duplicates:
   ```bash
   ragd inspect --duplicates
   ```

2. Remove unwanted duplicates:
   ```bash
   ragd delete <document-id>
   ```

### Scenario 3: "Indexing seems to skip files silently"

Use verbose mode to see what's happening:

```bash
ragd index ~/Documents/ --verbose
```

Or check the index for issues:

```bash
ragd doctor
```

## Verification

You've succeeded if you can:
- [ ] Run `ragd inspect` to view your index
- [ ] Find duplicate content with `--duplicates`
- [ ] Explain why a file would be skipped with `--explain`
- [ ] View content hashes with `--hashes`

## Next Steps

- [Processing Difficult PDFs](./processing-difficult-pdfs.md) - Handle complex documents
- [Automation](./06-automation.md) - Script your workflows

---

## Related Documentation

- [CLI Reference: inspect](../reference/cli-reference.md#ragd-inspect) - Full command options
- [Troubleshooting Guide](../guides/troubleshooting.md) - Common issues and solutions

---
