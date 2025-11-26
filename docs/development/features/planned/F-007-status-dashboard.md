# F-007: Status Dashboard

## Overview

**Use Case**: [UC-003: View System Status](../../../use-cases/briefs/UC-003-view-system-status.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Users need visibility into the state of their ragd installation - how many documents are indexed, storage usage, and system configuration. This builds trust and aids troubleshooting.

## Design Approach

### Architecture

```
ragd status
    ↓
Status Collector
    ├── Index Statistics (ChromaDB)
    ├── Storage Usage (disk)
    ├── Configuration (settings)
    └── Health Checks (F-008)
    ↓
Rich Dashboard Display
```

### Technologies

- **Rich**: Tables, panels, progress bars for dashboard
- **ChromaDB**: Index statistics
- **shutil**: Disk space calculation

### Status Information

| Category | Metrics |
|----------|---------|
| **Index** | Document count, chunk count, embedding count |
| **Storage** | Index size, available space |
| **Config** | Embedding model, chunk settings, data path |
| **Health** | Ready status, component health |

## Implementation Tasks

- [ ] Create `StatusCollector` class
- [ ] Implement ChromaDB statistics retrieval
- [ ] Implement disk usage calculation
- [ ] Implement configuration summary
- [ ] Create Rich dashboard layout
- [ ] Add `ragd status` CLI command
- [ ] Handle empty index state gracefully
- [ ] Add JSON output format option
- [ ] Write unit tests for status collection
- [ ] Write integration tests for CLI

## Success Criteria

- [ ] Shows total indexed documents
- [ ] Shows total chunks/embeddings
- [ ] Shows storage usage (MB/GB)
- [ ] Shows active embedding model
- [ ] Shows configuration file location
- [ ] Indicates system health/readiness
- [ ] Works correctly with empty index

## Dependencies

- Rich
- ChromaDB
- Typer

## Technical Notes

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 42                      │          │
│ │ Chunks              │ 1,247                   │          │
│ │ Embeddings          │ 1,247                   │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ 💾 Storage                                                  │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Index Size          │ 156.3 MB                │          │
│ │ Available Space     │ 45.2 GB                 │          │
│ │ Data Location       │ ~/.ragd/                │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ ⚙️ Configuration                                            │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Embedding Model     │ all-MiniLM-L6-v2        │          │
│ │ Chunk Size          │ 512 tokens              │          │
│ │ Config File         │ ~/.ragd/config.yaml     │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Empty Index State

```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 0                       │          │
│ │ Chunks              │ 0                       │          │
│ │ Embeddings          │ 0                       │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ 💡 Get started: ragd index <path-to-documents>              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### JSON Output

```bash
ragd status --format json
```

```json
{
  "status": "ready",
  "index": {
    "documents": 42,
    "chunks": 1247,
    "embeddings": 1247
  },
  "storage": {
    "index_size_bytes": 163887104,
    "available_bytes": 48523837440,
    "data_path": "~/.ragd"
  },
  "config": {
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 512,
    "config_file": "~/.ragd/config.yaml"
  }
}
```

## Related Documentation

- [State-of-the-Art Setup UX](../../research/state-of-the-art-setup-ux.md) - Research basis for dashboard design
- [F-008: Health Checks](./F-008-health-checks.md) - Component health details
- [UC-003: View System Status](../../../use-cases/briefs/UC-003-view-system-status.md) - Parent use case

---
