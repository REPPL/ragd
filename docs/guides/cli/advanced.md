# CLI Advanced Guide

Configuration, debugging, and power user features.

**Time:** 15 minutes
**Prerequisite:** [Intermediate](./intermediate.md)

---

## Configuration

### Configuration file location

```bash
~/.ragd/config.yaml
```

### View current configuration

```bash
ragd config show
```

### Set configuration values

```bash
ragd config set embedding.model all-MiniLM-L6-v2
ragd config set chunking.size 512
ragd config set output.theme high-contrast
```

### Example configuration

```yaml
# ~/.ragd/config.yaml

# Embedding settings
embedding:
  model: all-MiniLM-L6-v2    # or multi-qa-mpnet-base-dot-v1

# Chunking settings
chunking:
  size: 512                   # tokens per chunk
  overlap: 50                 # overlap between chunks

# Output settings
output:
  theme: default              # default | high-contrast | monochrome
  format: rich                # rich | plain | json

# Citation settings
citations:
  style: plain                # plain | apa | ieee | acm | chicago
  show_page: true
  link_to_source: true

# Storage settings
storage:
  path: ~/.ragd/data
```

---

## Themes and Accessibility

### Available themes

| Theme | Description |
|-------|-------------|
| `default` | Auto-detect terminal capabilities |
| `high-contrast` | Maximum readability |
| `colourblind-safe` | Avoids red/green distinctions |
| `monochrome` | No colour, text only |

### Set theme

```bash
# Via config
ragd config set output.theme high-contrast

# Via environment variable
export RAGD_THEME=monochrome
ragd search "query"

# Via flag (per-command)
ragd search "query" --theme monochrome
```

### Disable colour entirely

```bash
# Standard NO_COLOR environment variable
export NO_COLOR=1
ragd search "query"

# Or use --no-color flag
ragd search "query" --no-color
```

---

## Debugging

### Verbose output

```bash
ragd search "query" --verbose
```

Shows:
- Query embedding timing
- Number of chunks searched
- Similarity scores before ranking

### Debug mode

```bash
ragd search "query" --debug
```

Shows:
- Full stack traces on errors
- ChromaDB query details
- Memory usage statistics

### Check health with details

```bash
ragd health --verbose
```

Shows:
- Model file locations
- ChromaDB collection details
- Configuration file path
- Installed package versions

---

## Scripting and Automation

### Disable interactive prompts

```bash
ragd index ~/Documents/ --no-input
```

Never prompts for confirmation; uses defaults.

### Quiet mode for cron jobs

```bash
ragd index ~/Documents/ --quiet
```

Only outputs errors.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | File not found |
| 4 | Storage error |

```bash
ragd health
if [ $? -eq 0 ]; then
    echo "System healthy"
fi
```

---

## Performance Tuning

### Chunk size

Larger chunks provide more context but slower search:

```yaml
chunking:
  size: 1024    # Default: 512
  overlap: 100  # Default: 50
```

### Embedding model

Trade-off between quality and speed:

| Model | Quality | Speed |
|-------|---------|-------|
| `all-MiniLM-L6-v2` | Good | Fast |
| `multi-qa-mpnet-base-dot-v1` | Better | Slower |

### Search limit

Default returns 10 results. Reduce for faster responses:

```bash
ragd search "query" --limit 3
```

---

## Data Management

### Data location

```bash
~/.ragd/
├── config.yaml      # Configuration
├── data/            # ChromaDB storage
│   └── chroma/
└── logs/            # Application logs
```

### Custom data path

```yaml
storage:
  path: /path/to/custom/location
```

Or via environment:

```bash
export RAGD_DATA_PATH=/path/to/data
```

### Backup your knowledge base

```bash
# Simple backup
cp -r ~/.ragd ~/ragd-backup-$(date +%Y%m%d)

# Or just the data
tar -czf ragd-data.tar.gz ~/.ragd/data
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `RAGD_CONFIG` | Config file path | `/custom/config.yaml` |
| `RAGD_DATA_PATH` | Data directory | `/custom/data` |
| `RAGD_THEME` | Output theme | `high-contrast` |
| `NO_COLOR` | Disable colour | `1` |
| `RAGD_LOG_LEVEL` | Logging level | `DEBUG` |

---

## Troubleshooting

### "Model failed to load"

1. Check internet connection (model downloads on first use)
2. Verify disk space (~500MB for default model)
3. Try a smaller model:
   ```bash
   ragd config set embedding.model all-MiniLM-L6-v2
   ```

### "ChromaDB error"

1. Check data directory permissions
2. Verify disk space
3. Try resetting:
   ```bash
   rm -rf ~/.ragd/data/chroma
   ragd health
   ```

### Slow searches

1. Reduce result limit: `--limit 3`
2. Check index size: `ragd status`
3. Consider smaller embedding model

---

## What's Next?

- **[Reference](./reference.md)** - Complete command specifications
- **[Troubleshooting Guide](../troubleshooting.md)** - Common issues

---
