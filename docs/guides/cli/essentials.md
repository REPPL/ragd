# CLI Essentials

The 4 commands you need to be productive with ragd.

**Time:** 15 minutes
**Prerequisite:** ragd installed

---

## The Essential Commands

| Command | Purpose |
|---------|---------|
| `ragd doctor` | Run health checks |
| `ragd index` | Add documents |
| `ragd search` | Find information |
| `ragd info` | View statistics |

---

## 1. ragd doctor

**Run health checks on ragd components.**

```bash
ragd doctor
```

**What it does:**
- Verifies ChromaDB storage is accessible
- Checks embedding model loads correctly
- Validates configuration
- Confirms dependencies are installed

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│ ✅ Storage          ChromaDB accessible                     │
│ ✅ Embedding        Model loaded successfully               │
│ ✅ Configuration    Valid configuration                     │
│ ✅ Dependencies     All packages installed                  │
└─────────────────────────────────────────────────────────────┘
```

**If something fails:** See [Troubleshooting Guide](../troubleshooting.md)

---

## 2. ragd index

**Add documents to your knowledge base.**

```bash
# Index a single file
ragd index document.pdf

# Index a directory
ragd index ~/Documents/notes/

# Index with verbose output
ragd index report.pdf --verbose
```

**What it does:**
1. Reads document content
2. Splits text into searchable chunks
3. Creates vector embeddings
4. Stores in local database

**Expected output:**
```
Indexing: document.pdf
  ├─ Extracting text... done
  ├─ Creating chunks... 47 chunks
  ├─ Generating embeddings... done
  └─ Storing in database... done

✅ Indexed 1 document (47 chunks)
```

**Supported formats:** PDF, Markdown, Plain text, HTML

---

## 3. ragd search

**Find information in your knowledge base.**

```bash
# Basic search
ragd search "your question here"

# Limit results
ragd search "machine learning" --limit 5

# JSON output for scripts
ragd search "neural networks" --format json
```

**What it does:**
1. Converts your query to a vector embedding
2. Finds semantically similar chunks
3. Returns ranked results with sources

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search Results for: "machine learning"                   │
├─────────────────────────────────────────────────────────────┤
│ 1. paper.pdf (Score: 0.89)                                  │
│    Page 5                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Machine learning is a subset of AI that learns from    │ │
│ │ examples rather than explicit programming...           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Tip:** Search understands meaning, not just keywords. Ask natural questions!

---

## 4. ragd info

**View the state of your knowledge base.**

```bash
ragd info
```

**What it does:**
- Shows document count
- Shows chunk/embedding count
- Displays storage usage
- Shows configuration summary

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 42                      │          │
│ │ Chunks              │ 1,247                   │          │
│ └─────────────────────┴─────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Options

These flags work with all commands:

| Flag | Short | Purpose |
|------|-------|---------|
| `--help` | `-h` | Show help for command |
| `--version` | `-v` | Show ragd version |
| `--quiet` | `-q` | Minimal output |
| `--format` | | Output format (rich/plain/json) |

**Examples:**
```bash
ragd search --help          # Help for search command
ragd --version              # Show version
ragd search "AI" --quiet    # Minimal output
```

---

## What's Next?

You've learned the essentials! When you're ready:

- **[Intermediate Guide](./intermediate.md)** - Task-specific workflows
- **[Advanced Guide](./advanced.md)** - Configuration and debugging
- **[Reference](./reference.md)** - Complete command specifications

---
