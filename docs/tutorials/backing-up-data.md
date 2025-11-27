# Backing Up Your Data

Learn to export and restore your knowledge base for backup and portability.

**Time:** 10 minutes
**Prerequisites:** ragd with export extras installed, some documents indexed
**Validates:** UC-006, F-032, F-033, F-034

> **Note:** This tutorial is a DRAFT for v0.2 specification validation. Implementation may differ.

---

## What You'll Learn

By the end of this tutorial, you'll know how to:
1. Export your entire knowledge base
2. Export specific documents or projects
3. Restore from a backup
4. Verify backup integrity
5. Transfer knowledge bases between machines

---

## Before You Start

### Install Export Dependencies

```bash
pip install "ragd[export]"
```

### Ensure You Have Data to Export

Check your knowledge base status:

```bash
ragd status
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 15                      │          │
│ │ Chunks              │ 523                     │          │
│ │ Tags                │ 12                      │          │
│ │ Projects            │ 2                       │          │
│ └─────────────────────┴─────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

You should have at least a few documents indexed before proceeding.

---

## Step 1: Export Your Knowledge Base

Create a full backup of your knowledge base:

```bash
ragd export ~/backups/ragd-backup.tar.gz
```

**Expected output:**
```
Creating export archive...

Exporting:
  ├─ Documents: 15
  ├─ Chunks: 523
  ├─ Metadata: 15 records
  ├─ Tags: 12 tags
  ├─ Embeddings: 523 vectors (Parquet format)
  ├─ Configuration: included
  └─ Manifest: generated

Compressing archive...

✅ Export complete: ~/backups/ragd-backup.tar.gz
   Size: 45.2 MB
   Documents: 15
   Checksum: sha256:a1b2c3d4e5...
```

**What's included in the export:**
- All indexed document chunks and text
- Vector embeddings (as Parquet files)
- Document metadata (Dublin Core)
- Tags and projects
- Configuration settings
- Manifest with checksums

**Checkpoint:** Export completes with checksum

---

## Step 2: View Export Contents

Inspect what's in an archive without extracting:

```bash
ragd export inspect ~/backups/ragd-backup.tar.gz
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Archive: ragd-backup.tar.gz                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Archive Version: 1.0                                        │
│ Created: 2025-11-26 14:32:15                                │
│ ragd Version: 0.2.0                                         │
│                                                             │
│ Contents:                                                   │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 15                      │          │
│ │ Chunks              │ 523                     │          │
│ │ Embeddings          │ 523 (384 dimensions)    │          │
│ │ Embedding Model     │ all-MiniLM-L6-v2        │          │
│ │ Tags                │ 12                      │          │
│ │ Projects            │ 2                       │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ File Structure:                                             │
│   manifest.json         2.1 KB                              │
│   documents/            12.3 MB                             │
│   embeddings.parquet    28.4 MB                             │
│   metadata.json         45.2 KB                             │
│   config.yaml           1.2 KB                              │
│                                                             │
│ Checksum: sha256:a1b2c3d4e5...  ✅ Valid                    │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Inspect archive contents

---

## Step 3: Export Specific Content

Export only certain documents:

```bash
# Export by tag
ragd export ~/backups/ml-research.tar.gz --tag "topic:ml"
```

**Expected output:**
```
Creating filtered export...

Filter: tag:topic:ml
Matching documents: 5

Exporting:
  ├─ Documents: 5
  ├─ Chunks: 189
  └─ Embeddings: 189 vectors

✅ Export complete: ~/backups/ml-research.tar.gz
   Size: 15.8 MB
```

**More export filters:**

```bash
# Export by project
ragd export ~/backups/project-backup.tar.gz --project "ML Research"

# Export by date range
ragd export ~/backups/recent.tar.gz --since "2024-01-01"

# Export without embeddings (smaller, requires re-embedding on import)
ragd export ~/backups/text-only.tar.gz --no-embeddings
```

**Checkpoint:** Export filtered subsets of your knowledge base

---

## Step 4: Verify Backup Integrity

Before relying on a backup, verify it:

```bash
ragd export verify ~/backups/ragd-backup.tar.gz
```

**Expected output:**
```
Verifying archive: ragd-backup.tar.gz

Checks:
  ✅ Archive readable
  ✅ Manifest valid
  ✅ Checksum matches (sha256:a1b2c3d4e5...)
  ✅ Document count: 15 (expected 15)
  ✅ Chunk count: 523 (expected 523)
  ✅ Embedding dimensions: 384 (compatible)
  ✅ All files intact

✅ Archive verified successfully
   Ready for import
```

**If verification fails:**

```
Verifying archive: corrupted-backup.tar.gz

Checks:
  ✅ Archive readable
  ✅ Manifest valid
  ❌ Checksum mismatch
     Expected: sha256:a1b2c3d4e5...
     Actual:   sha256:f6g7h8i9j0...

❌ Archive verification failed
   Do not use this backup - it may be corrupted
```

**Checkpoint:** Verify backup passes all checks

---

## Step 5: Restore from Backup

Restore your knowledge base from an archive:

```bash
ragd import ~/backups/ragd-backup.tar.gz
```

**Expected output:**
```
Importing archive: ragd-backup.tar.gz

Pre-import checks:
  ✅ Archive valid
  ✅ Version compatible (1.0)
  ✅ Embedding model matches (all-MiniLM-L6-v2)

Importing:
  ├─ Documents: 15
  ├─ Chunks: 523
  ├─ Embeddings: 523 vectors
  ├─ Metadata: 15 records
  ├─ Tags: 12 tags
  └─ Projects: 2 projects

✅ Import complete
   Documents imported: 15
   Chunks restored: 523
```

**Checkpoint:** Successfully restore from backup

---

## Step 6: Handle Import Conflicts

If you import into a knowledge base with existing documents:

```bash
ragd import ~/backups/ragd-backup.tar.gz
```

**Expected output (with conflicts):**
```
Importing archive: ragd-backup.tar.gz

Conflict Detection:
  ⚠️  3 documents already exist in knowledge base

Conflicting documents:
  1. research-paper.pdf (archive: 2025-11-20, current: 2025-11-26)
  2. ml-intro.pdf (archive: 2025-11-15, current: 2025-11-25)
  3. notes.md (archive: 2025-11-01, current: 2025-11-10)

How do you want to handle conflicts?
  [s] Skip conflicting documents (keep current)
  [o] Overwrite with archive versions
  [n] Import as new (create duplicates)
  [c] Cancel import

Choice [s]:
```

**Or use flags to handle automatically:**

```bash
# Skip conflicts (default)
ragd import backup.tar.gz --skip-conflicts

# Overwrite existing
ragd import backup.tar.gz --overwrite

# Keep both (creates duplicates)
ragd import backup.tar.gz --keep-both
```

**Checkpoint:** Handle import conflicts appropriately

---

## Step 7: Transfer Between Machines

Move your knowledge base to a new machine:

**On the source machine:**

```bash
# Create a full export
ragd export ~/knowledge-base-transfer.tar.gz

# Copy to USB drive or cloud storage
cp ~/knowledge-base-transfer.tar.gz /Volumes/USB/
```

**On the destination machine:**

```bash
# Install ragd
pip install "ragd[all]"

# Import the archive
ragd import /Volumes/USB/knowledge-base-transfer.tar.gz
```

**Expected output:**
```
Importing archive: knowledge-base-transfer.tar.gz

Pre-import checks:
  ✅ Archive valid
  ✅ Version compatible
  ⚠️  Embedding model differs
      Archive: all-MiniLM-L6-v2
      Current: (none configured)

      Options:
      [u] Use archive's model (recommended)
      [r] Re-embed with current model (slower)
      [c] Cancel

Choice [u]: u

Configuring embedding model: all-MiniLM-L6-v2

Importing:
  ├─ Documents: 15
  ├─ Embeddings: 523 vectors (reusing from archive)
  └─ Complete

✅ Import complete
   Your knowledge base has been transferred successfully
```

**Checkpoint:** Transfer knowledge base between machines

---

## Step 8: Export Without Embeddings

For smaller backups (text only, re-embed on import):

```bash
ragd export ~/backups/text-only.tar.gz --no-embeddings
```

**Expected output:**
```
Creating export archive (without embeddings)...

Exporting:
  ├─ Documents: 15
  ├─ Chunks: 523 (text only)
  ├─ Metadata: 15 records
  └─ Configuration: included

✅ Export complete: ~/backups/text-only.tar.gz
   Size: 12.1 MB (vs 45.2 MB with embeddings)

Note: Importing will require re-embedding (slower import)
```

**Import and re-embed:**

```bash
ragd import ~/backups/text-only.tar.gz
```

**Expected output:**
```
Importing archive: text-only.tar.gz

Notice: Archive does not contain embeddings
        Will generate embeddings during import

Importing:
  ├─ Documents: 15
  ├─ Chunks: 523
  ├─ Generating embeddings...
  │   Progress: [████████████████████] 100%
  │   Time: 45 seconds
  └─ Complete

✅ Import complete
   Embeddings regenerated for 523 chunks
```

**Checkpoint:** Export and import without embeddings

---

## What You Learned

Congratulations! You've completed the backup tutorial. You now know how to:

| Task | Command |
|------|---------|
| Full export | `ragd export backup.tar.gz` |
| Export with filter | `ragd export backup.tar.gz --tag "..."` |
| Export without embeddings | `ragd export backup.tar.gz --no-embeddings` |
| Inspect archive | `ragd export inspect backup.tar.gz` |
| Verify backup | `ragd export verify backup.tar.gz` |
| Import/restore | `ragd import backup.tar.gz` |
| Handle conflicts | `ragd import backup.tar.gz --skip-conflicts` |

---

## Archive Format

ragd archives use a standardised format:

```
ragd-backup.tar.gz
├── manifest.json       # Archive metadata, checksums
├── documents/          # Chunked document text (JSON)
├── embeddings.parquet  # Vector embeddings (Parquet)
├── metadata.json       # Dublin Core metadata
├── tags.json           # Tag definitions and assignments
├── projects.json       # Project definitions
└── config.yaml         # Configuration snapshot
```

**Version compatibility:**
- Archives include version information
- ragd can import archives from older versions
- Breaking changes increment the major version

---

## Backup Strategy Recommendations

| Use Case | Recommended Approach |
|----------|---------------------|
| Daily backup | `ragd export daily-$(date +%Y%m%d).tar.gz` |
| Before major changes | Full export with embeddings |
| Sharing with others | Export without embeddings (smaller) |
| Archival storage | Full export, verify, store offsite |
| Quick sync | Export specific project or tag |

**Automate backups:**

```bash
# Add to crontab for daily backups
0 2 * * * ragd export ~/backups/ragd-$(date +\%Y\%m\%d).tar.gz
```

---

## Next Steps

- **Automate indexing:** Watch Folder tutorial (v0.2.3)
- **Advanced search:** [Search Guide](../guides/search.md)
- **Configuration:** [Configuration Guide](../guides/configuration.md)

---

## Troubleshooting

### "Export failed: disk full"

- Check available disk space
- Use `--no-embeddings` for smaller exports
- Export to a different location

### "Import failed: version incompatible"

- Check ragd version: `ragd --version`
- Update ragd: `pip install --upgrade ragd`
- For very old archives, contact support

### "Embedding model mismatch"

- Choose to re-embed during import
- Or install the matching model first
- Configure: `ragd config set embedding.model <model-name>`

### "Checksum verification failed"

- Archive may be corrupted
- Re-download or re-copy from source
- Do not use corrupted archives

### Import is very slow

- Large knowledge bases take time
- Progress shown during import
- Use `--no-embeddings` export if re-embedding is acceptable

---

## Related Documentation

- [UC-006: Export & Backup](../use-cases/briefs/UC-006-export-backup.md)
- [F-032: Export Engine](../development/features/completed/F-032-export-engine.md)
- [F-033: Import Engine](../development/features/completed/F-033-import-engine.md)
- [F-034: Archive Format](../development/features/completed/F-034-archive-format.md)
- [Archive Format Specification](../reference/archive-format.md)

---
