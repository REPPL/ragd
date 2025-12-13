# Advanced Indexing Guide

This guide covers advanced indexing features introduced in v0.9.0.

## New File Types

### EPUB (Ebooks)

ragd can index EPUB ebooks when the `ebooklib` package is installed:

```bash
pip install ebooklib

# Index your ebook collection
ragd index ~/Books/
```

The extractor:
- Extracts text from all document items
- Preserves chapter structure
- Captures metadata (title, author)

### DOCX (Word Documents)

Index Microsoft Word documents with the `python-docx` package:

```bash
pip install python-docx

# Index Word documents
ragd index ~/Documents/Reports/
```

The extractor:
- Extracts all paragraphs
- Extracts table content (pipe-separated)
- Preserves document structure

### XLSX (Excel Spreadsheets)

Index Excel spreadsheets with the `openpyxl` package:

```bash
pip install openpyxl

# Index spreadsheets
ragd index ~/Documents/Data/
```

The extractor:
- Processes all sheets
- Creates sheet headers
- Extracts cell values (pipe-separated rows)

## Smart Chunking

v0.9.0 introduces structural chunking that respects document structure.

### Configuration

In your `config.yaml`:

```yaml
chunking:
  strategy: structural
  max_chunk_size: 512
  min_chunk_size: 100
  overlap: 50
  respect_headers: true
  respect_lists: true
  respect_code: true
```

### How It Works

The structural chunker:

1. **Identifies elements** - Headers, lists, code blocks, paragraphs
2. **Preserves boundaries** - Never splits mid-list or mid-code-block
3. **Groups small elements** - Combines paragraphs up to max size
4. **Maintains context** - Keeps headers with their content

### Example

Input document:
```markdown
# Introduction

This is the intro paragraph.

## Features

- Feature 1
- Feature 2
- Feature 3

## Code Example

```python
def hello():
    print("Hello")
```
```

With structural chunking:
- Header stays with content
- List items stay together
- Code block is one chunk

## Indexing Resume

Long indexing operations can be resumed after interruption.

### Enable Checkpoints

```bash
# Enable checkpoint saving
ragd index ~/LargeLibrary/ --checkpoint

# View progress
ragd info --detailed
```

### Resume After Interruption

```bash
# Resume from last checkpoint
ragd index --resume

# Clear checkpoint and start fresh
ragd index ~/LargeLibrary/ --clear-checkpoint
```

### Checkpoint File

Checkpoints are stored at `~/.ragd/.indexing_checkpoint.json`:

```json
{
  "started_at": "2024-12-04T10:00:00+00:00",
  "source_path": "/path/to/Documents",
  "total_files": 1000,
  "completed": 450,
  "last_file": "/path/to/Documents/report450.pdf",
  "files_completed": ["..."],
  "errors": []
}
```

## Change Detection

ragd detects file changes to avoid re-indexing unchanged content.

### How It Works

1. **Fast check** - Compare file size and modification time
2. **If different** - Calculate content hash (SHA-256)
3. **If content changed** - Re-index the document
4. **If unchanged** - Skip the document

### Force Re-indexing

```bash
# Ignore change detection, re-index everything
ragd index ~/Documents/ --force
```

## Duplicate Detection

ragd identifies and handles duplicate content during indexing.

### Policies

Configure in `config.yaml`:

```yaml
indexing:
  duplicate_policy: skip  # skip | index_all | link
```

- **skip** (default) - Index only first occurrence
- **index_all** - Index all occurrences
- **link** - Index once, link duplicates to original

### View Duplicates

```bash
# Show duplicate statistics
ragd info --detailed
```

## Best Practices

### Large Collections

1. **Use checkpoints** for collections over 1000 files
2. **Run overnight** for very large collections
3. **Monitor progress** with `ragd info --detailed`

### Mixed File Types

1. **Install optional dependencies** for your file types
2. **Check supported formats** with `ragd --supported-types`
3. **Use recursive indexing** for nested folders

### Optimising Performance

1. **Enable change detection** (default) to skip unchanged files
2. **Use skip duplicate policy** to avoid redundant indexing
3. **Consider smaller chunk sizes** for precise search results

---

## Related Documentation

- [Getting Started](../tutorials/01-getting-started.md)
- [Configuration Reference](../reference/configuration.md)
- [CLI Reference](../reference/cli-reference.md)

---

**Status**: Complete
