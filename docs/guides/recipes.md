# Recipes

Copy-paste scripts for common ragd workflows.

---

## Quick Reference

| Recipe | Description |
|--------|-------------|
| [Daily Backup](#daily-backup) | Automated backup with rotation |
| [Batch Index](#batch-index-multiple-directories) | Index from multiple sources |
| [Health Monitor](#health-monitor) | Cron-friendly health checks |
| [Model Comparison](#model-comparison) | Compare LLM responses |
| [Search to Markdown](#search-to-markdown) | Export search results |
| [Weekly Re-index](#weekly-re-index) | Scheduled re-indexing |

---

## Daily Backup

Automated backup with rotation (keeps last 7 days).

```bash
#!/bin/bash
# backup-ragd.sh

set -euo pipefail

BACKUP_DIR="${RAGD_BACKUP_DIR:-$HOME/ragd-backups}"
KEEP_DAYS="${RAGD_BACKUP_KEEP:-7}"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Exporting ragd knowledge base..."
ragd export "$BACKUP_DIR/ragd-backup-$DATE.ragd"

echo "Cleaning up old backups (keeping $KEEP_DAYS days)..."
find "$BACKUP_DIR" -name "ragd-backup-*.ragd" -mtime +"$KEEP_DAYS" -delete

echo "Done. Backup: $BACKUP_DIR/ragd-backup-$DATE.ragd"
```

**Cron entry (daily at 2am):**
```bash
0 2 * * * /path/to/backup-ragd.sh >> ~/.ragd/logs/backup.log 2>&1
```

---

## Batch Index Multiple Directories

Index documents from multiple locations with progress tracking.

```bash
#!/bin/bash
# batch-index.sh

set -euo pipefail

SOURCES=(
    "$HOME/Documents/Research"
    "$HOME/Documents/Work"
    "$HOME/Downloads"
)

echo "=== Batch Indexing ==="
echo "Started: $(date)"

for source in "${SOURCES[@]}"; do
    if [[ -d "$source" ]]; then
        echo "Indexing: $source"
        ragd index "$source" --recursive
    else
        echo "Skipping (not found): $source"
    fi
done

echo "=== Complete ==="
ragd info
```

---

## Health Monitor

Cron-friendly health monitoring with optional notifications.

```bash
#!/bin/bash
# monitor-ragd.sh

set -euo pipefail

LOG_FILE="${RAGD_MONITOR_LOG:-$HOME/.ragd/logs/monitor.log}"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

if ragd doctor --format json > /dev/null 2>&1; then
    log "Health check: PASS"
    exit 0
else
    log "Health check: FAIL"

    # macOS notification (optional)
    if command -v osascript &> /dev/null; then
        osascript -e 'display notification "ragd health check failed" with title "ragd Monitor"'
    fi

    exit 1
fi
```

**Cron entry (every hour):**
```bash
0 * * * * /path/to/monitor-ragd.sh
```

---

## Model Comparison

Compare responses from multiple LLM models.

```bash
#!/bin/bash
# compare-models.sh

set -euo pipefail

QUERY="${1:-"Summarise the key points"}"
MODELS=("llama3.2:3b" "llama3.2:8b" "mistral:7b")
OUTPUT_DIR="$HOME/.ragd/comparisons"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/comparison-$DATE.md"

cat > "$OUTPUT_FILE" << EOF
# Model Comparison

**Query:** $QUERY
**Date:** $(date)

EOF

for model in "${MODELS[@]}"; do
    echo "Testing: $model..."
    echo "## $model" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"

    if ragd ask "$QUERY" --model "$model" --format plain >> "$OUTPUT_FILE" 2>&1; then
        echo '```' >> "$OUTPUT_FILE"
    else
        echo "(Model unavailable)" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
    fi

    echo "" >> "$OUTPUT_FILE"
done

echo "Saved: $OUTPUT_FILE"
```

**Usage:**
```bash
./compare-models.sh "What are the main findings?"
```

---

## Search to Markdown

Export search results to a markdown file.

```bash
#!/bin/bash
# search-to-md.sh

set -euo pipefail

QUERY="$1"
OUTPUT="${2:-search-results.md}"

cat > "$OUTPUT" << EOF
# Search Results

**Query:** $QUERY
**Date:** $(date)

---

EOF

ragd search "$QUERY" --format json --no-interactive | \
    jq -r '.results[] | "## \(.document_title)\n\n\(.content)\n\n*Source: \(.source_path)*\n\n---\n"' \
    >> "$OUTPUT"

echo "Results saved to: $OUTPUT"
```

**Usage:**
```bash
./search-to-md.sh "machine learning" results.md
```

---

## Weekly Re-index

Re-index all documents to pick up extraction improvements.

```bash
#!/bin/bash
# weekly-reindex.sh

set -euo pipefail

LOG_FILE="$HOME/.ragd/logs/reindex.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Weekly Re-index Started ==="

# Re-index PDFs (most likely to benefit from improvements)
log "Re-indexing PDFs..."
ragd reindex --type pdf --force

# Re-index HTML
log "Re-indexing HTML..."
ragd reindex --type html --force

log "=== Complete ==="
ragd info >> "$LOG_FILE"
```

**Cron entry (every Sunday at 3am):**
```bash
0 3 * * 0 /path/to/weekly-reindex.sh
```

---

## Integration Recipes

### Obsidian Vault Sync

```bash
#!/bin/bash
# obsidian-sync.sh

VAULT="${OBSIDIAN_VAULT:-$HOME/Obsidian}"

ragd index "$VAULT" --recursive --tags obsidian,notes
```

### Git Hook: Index Docs on Commit

Add to `.git/hooks/post-commit`:

```bash
#!/bin/bash

if git diff --name-only HEAD~1 | grep -q "^docs/"; then
    ragd index docs/ --recursive --tags git-docs
fi
```

### Alfred/Raycast Quick Search

```bash
#!/bin/bash
# alfred-search.sh

QUERY="$1"
ragd search "$QUERY" --limit 5 --format json | \
    jq -r '.results[] | "\(.document_title): \(.content[:100])..."'
```

---

## Environment Variables

These variables can be used to configure recipe behaviour:

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGD_BACKUP_DIR` | `~/ragd-backups` | Backup directory |
| `RAGD_BACKUP_KEEP` | `7` | Days to keep backups |
| `RAGD_MONITOR_LOG` | `~/.ragd/logs/monitor.log` | Monitor log path |
| `RAGD_OUTPUT_FORMAT` | `rich` | Default output format |
| `OBSIDIAN_VAULT` | `~/Obsidian` | Obsidian vault path |

---

## Tips

- **Use `--format json`** for parsing output in scripts
- **Use `--no-interactive`** to prevent prompts in automated scripts
- **Check exit codes** - ragd returns standard exit codes (0 = success)
- **Log everything** - Redirect output to log files for debugging
- **Test with `--dry-run`** where available

---

## Related Documentation

- [Automation Tutorial](../tutorials/06-automation.md) - Learn automation basics
- [CLI Advanced Guide](./cli/advanced.md) - Scripting and configuration
- [CLI Reference](../reference/cli-reference.md) - Complete command options

---
