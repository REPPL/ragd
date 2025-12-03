# F-072: Backend Health Checks

## Overview

**Milestone**: v0.6.0
**Priority**: P2
**Depends On**: [F-021](./F-021-vector-store-abstraction.md)

## Problem Statement

When backends encounter issues (corrupt index, missing files, version mismatch), users need clear diagnostics and recovery guidance. Each backend has unique failure modes requiring specific health checks.

## Design Approach

### CLI Command

```bash
ragd backend health           # Check current backend
ragd backend health --all     # Check all available backends
ragd backend health chromadb  # Check specific backend
```

### Health Check Types

| Check | Description | Backends |
|-------|-------------|----------|
| **Connectivity** | Backend accessible | All |
| **Integrity** | Index/data validation | All |
| **Version** | Compatible version | All |
| **Performance** | Sample query latency | All |
| **Dependencies** | Required packages | FAISS |

### Output Format

```
ragd backend health

Backend: chromadb (current)
────────────────────────────
✓ Connectivity    OK (12ms)
✓ Integrity       OK (3,456 vectors)
✓ Version         0.4.22 (compatible)
✓ Performance     OK (p95: 23ms)

Overall: HEALTHY
```

### Health Status

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # Working but with issues
    UNHEALTHY = "unhealthy" # Not working
    UNKNOWN = "unknown"     # Cannot determine
```

## Implementation Tasks

- [ ] Create `src/ragd/storage/health/` module
- [ ] Define health check interface
- [ ] Implement ChromaDB-specific checks
- [ ] Implement FAISS-specific checks
- [ ] Create `ragd backend health` command
- [ ] Add Rich output formatting
- [ ] Add JSON output option
- [ ] Write unit tests

## Success Criteria

- [ ] Each backend has tailored health checks
- [ ] Clear status indicators (HEALTHY/DEGRADED/UNHEALTHY)
- [ ] Recovery guidance for common issues
- [ ] JSON output for automation

## Related Documentation

- [F-021: Vector Store Abstraction](./F-021-vector-store-abstraction.md)
- [F-035: Health Check](../completed/F-035-health-check.md) - General health pattern

---
