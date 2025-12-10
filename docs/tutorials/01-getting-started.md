# Getting Started with ragd

Learn to install ragd and index your first documents.

**Time:** 15 minutes
**Level:** Beginner
**Prerequisites:** Python 3.12+, pip

## What You'll Learn

- Installing ragd
- Initialising your knowledge base
- Indexing documents
- Running your first search

## Step 1: Install ragd

```bash
pip install ragd
```

Verify installation:

```bash
ragd --version
```

## Step 2: Initialise ragd

Run the initialisation wizard:

```bash
ragd init
```

ragd will:
1. Detect your hardware capabilities
2. Recommend optimal settings
3. Create configuration at `~/.ragd/config.yaml`
4. Download required embedding models

## Step 3: Index Your Documents

Index a single file:

```bash
ragd index ~/Documents/report.pdf
```

Index a directory:

```bash
ragd index ~/Documents/research
```

Check what's indexed:

```bash
ragd info
```

## Step 4: Search Your Knowledge Base

Run a search:

```bash
ragd search "key findings from the research"
```

Use the interactive navigator (j/k to move, Enter to view, q to quit).

## Verification

You've succeeded if:
- [ ] `ragd --version` shows version number
- [ ] `ragd info` shows indexed documents
- [ ] `ragd search` returns relevant results

## Next Steps

- [Searching Tutorial](02-searching.md) - Master search queries
- [Chat Interface](03-chat-interface.md) - Interactive Q&A

---

## Troubleshooting

**"No module named ragd"**
- Ensure Python 3.12+ is installed
- Try `pip install --upgrade ragd`

**"Embedding model not found"**
- Run `ragd init` again to download models

**Slow indexing**
- First run downloads models (one-time)
- Large PDFs with images take longer
