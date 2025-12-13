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
# Downgrade pip (required due to pip 24.1+ bug)
pip install pip==24.0

# Install ragd from GitHub
pip install git+https://github.com/REPPL/ragd.git
```

This installs ragd with all runtime features. Verify installation:

```bash
ragd --version
ragd doctor     # Shows installation status and feature availability
```

> **Expert users:** For minimal installations (CI, resource-constrained environments):
> `RAGD_MINIMAL=1 pip install git+https://github.com/REPPL/ragd.git`

## Step 2: Initialise ragd

Run the initialisation wizard:

```bash
ragd init
```

ragd will:
1. Detect your hardware capabilities
2. Recommend optimal settings (including the best LLM for your hardware)
3. Detect context window size from model card
4. Create configuration at `~/.ragd/config.yaml`
5. Download required embedding models

> **Note:** If you skip this step and run `ragd chat` or `ragd ask` directly, ragd will automatically run initialisation for you on first use.

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
- Try `pip install --upgrade git+https://github.com/REPPL/ragd.git`

**"Embedding model not found"**
- Run `ragd init` again to download models

**Slow indexing**
- First run downloads models (one-time)
- Large PDFs with images take longer

---

## Related Documentation

- [CLI Essentials Guide](../guides/cli/essentials.md) - Quick reference for core commands
- [CLI Reference](../reference/cli-reference.md) - Complete command specifications
- [Configuration Reference](../reference/configuration.md) - Configuration options
