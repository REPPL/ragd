# F-008: Health Checks

## Overview

**Use Case**: [UC-003: View System Status](../../../use-cases/briefs/UC-003-view-system-status.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Users need to verify that ragd is working correctly. Health checks validate that all components are functional and ready for use, aiding troubleshooting and building confidence.

## Design Approach

### Architecture

```
ragd health
    ↓
Health Check Runner
    ├── Storage Check (ChromaDB accessible)
    ├── Embedding Check (model loadable)
    ├── Config Check (valid configuration)
    └── Dependency Check (required packages)
    ↓
Health Report
```

### Health Check Categories

| Check | What it Validates |
|-------|-------------------|
| **Storage** | ChromaDB is accessible and writable |
| **Embedding** | Embedding model can be loaded |
| **Config** | Configuration file is valid |
| **Dependencies** | Required packages are installed |

### Health Status

| Status | Meaning |
|--------|---------|
| ✅ Healthy | All checks pass |
| ⚠️ Degraded | Some non-critical checks fail |
| ❌ Unhealthy | Critical checks fail |

## Implementation Tasks

- [ ] Define `HealthCheck` protocol and `HealthResult` dataclass
- [ ] Implement `StorageHealthCheck` for ChromaDB
- [ ] Implement `EmbeddingHealthCheck` for model loading
- [ ] Implement `ConfigHealthCheck` for configuration validation
- [ ] Implement `DependencyHealthCheck` for package verification
- [ ] Create `HealthRunner` to orchestrate checks
- [ ] Add `ragd health` CLI command
- [ ] Add verbose mode for detailed output
- [ ] Write unit tests for each health check
- [ ] Write integration tests for health runner

## Success Criteria

- [ ] Health check identifies common issues
- [ ] Clear pass/fail status for each component
- [ ] Actionable error messages when checks fail
- [ ] Quick execution (< 5 seconds total)
- [ ] JSON output option for automation
- [ ] Verbose mode shows detailed diagnostics

## Dependencies

- ChromaDB
- sentence-transformers
- Pydantic (config validation)

## Technical Notes

### Health Check Interface

```python
@dataclass
class HealthResult:
    name: str
    status: Literal["healthy", "degraded", "unhealthy"]
    message: str
    duration_ms: float
    details: dict[str, Any] | None = None

class HealthCheck(Protocol):
    def check(self) -> HealthResult:
        """Run health check and return result."""
        ...
```

### CLI Output

```
ragd health
```

```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Component Checks:                                           │
│                                                             │
│ ✅ Storage          ChromaDB accessible (12ms)              │
│ ✅ Embedding        Model loaded successfully (234ms)       │
│ ✅ Configuration    Valid configuration (2ms)               │
│ ✅ Dependencies     All packages installed (5ms)            │
│                                                             │
│ Total time: 253ms                                           │
└─────────────────────────────────────────────────────────────┘
```

### Failure Example

```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ❌ Unhealthy                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Component Checks:                                           │
│                                                             │
│ ✅ Storage          ChromaDB accessible (12ms)              │
│ ❌ Embedding        Failed to load model (timeout)          │
│ ✅ Configuration    Valid configuration (2ms)               │
│ ✅ Dependencies     All packages installed (5ms)            │
│                                                             │
│ ⚠️ Action Required:                                         │
│   Embedding model failed to load. Try:                      │
│   1. Check internet connection for model download           │
│   2. Verify sufficient disk space                           │
│   3. Run: ragd config set embedding.model all-MiniLM-L6-v2  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Verbose Mode

```bash
ragd health --verbose
```

Shows detailed diagnostics including:
- Model file locations
- ChromaDB collection details
- Configuration file contents
- Installed package versions

### JSON Output

```bash
ragd health --format json
```

```json
{
  "status": "healthy",
  "checks": [
    {
      "name": "Storage",
      "status": "healthy",
      "message": "ChromaDB accessible",
      "duration_ms": 12,
      "details": {
        "path": "~/.ragd/chroma",
        "collections": 1
      }
    }
  ],
  "total_duration_ms": 253
}
```

## Related Documentation

- [F-007: Status Dashboard](./F-007-status-dashboard.md) - Integrates health status
- [UC-003: View System Status](../../../use-cases/briefs/UC-003-view-system-status.md) - Parent use case

---
