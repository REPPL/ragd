# F-035: Health Check Command

## Overview

**Use Case**: Deployment troubleshooting and system verification
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Users need a quick way to verify their ragd installation is working correctly. Without a diagnostic command, troubleshooting involves manually checking multiple components (Python version, Ollama availability, vector database health, GPU detection). This creates friction for new users and increases support burden.

## Design Approach

Implement a `ragd doctor` command that performs comprehensive health checks and provides actionable fix suggestions.

**Command Interface:**

```bash
ragd doctor              # Run all checks
ragd doctor --verbose    # Detailed output
ragd doctor --json       # Machine-readable output
```

**Output Example:**

```
ragd doctor

System Health Check
───────────────────────────────────────────────────────

✓ Python version        3.12.0 (required: >=3.12)
✓ ragd version          0.1.0
✓ Configuration         ~/.ragd/config.yaml found

Hardware Detection
───────────────────────────────────────────────────────

✓ Compute backend       Apple Silicon (MPS)
✓ Memory available      128 GB unified
✓ Hardware tier         EXTREME (recommended: 70B models)

Dependencies
───────────────────────────────────────────────────────

✓ Ollama                Running (http://localhost:11434)
✓ Default model         llama3.2:3b (pulled)
✓ Embedding model       nomic-embed-text (pulled)

Vector Database
───────────────────────────────────────────────────────

✓ ChromaDB              Healthy
✓ Collections           2 collections, 15,234 vectors
✓ Storage               ~/.ragd/chroma_db (1.2 GB)

───────────────────────────────────────────────────────
All checks passed! ragd is ready to use.
```

## Implementation Tasks

- [ ] Create `ragd doctor` command in CLI
- [ ] Implement Python version check
- [ ] Implement configuration file detection
- [ ] Implement hardware detection (MPS, CUDA, CPU)
- [ ] Implement memory tier calculation
- [ ] Implement Ollama connectivity check
- [ ] Implement model availability check
- [ ] Implement ChromaDB health check
- [ ] Add `--verbose` flag for detailed output
- [ ] Add `--json` flag for machine-readable output
- [ ] Implement fix suggestions for failed checks

## Success Criteria

- [ ] Command completes in <5 seconds
- [ ] All critical components checked (Python, Ollama, ChromaDB)
- [ ] Hardware tier correctly identified
- [ ] Failed checks include actionable fix hints
- [ ] JSON output parseable for scripting

## Dependencies

- None (foundational feature)

## Technical Notes

**Health Check Structure:**

```python
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

@dataclass
class HealthCheck:
    name: str
    status: CheckStatus
    message: str
    fix_hint: str | None = None

def run_health_checks() -> list[HealthCheck]:
    checks = []

    # Python version
    import sys
    if sys.version_info >= (3, 12):
        checks.append(HealthCheck(
            "Python version",
            CheckStatus.PASS,
            f"{sys.version_info.major}.{sys.version_info.minor}"
        ))
    else:
        checks.append(HealthCheck(
            "Python version",
            CheckStatus.FAIL,
            f"{sys.version_info.major}.{sys.version_info.minor}",
            fix_hint="Install Python 3.12+: brew install python@3.12"
        ))

    # ... additional checks

    return checks
```

**Ollama Connectivity Check:**

```python
import httpx

def check_ollama() -> HealthCheck:
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return HealthCheck(
                "Ollama",
                CheckStatus.PASS,
                f"Running ({len(models)} models)"
            )
    except httpx.RequestError:
        pass

    return HealthCheck(
        "Ollama",
        CheckStatus.FAIL,
        "Not reachable",
        fix_hint="Start Ollama: ollama serve"
    )
```

## Related Documentation

- [State-of-the-Art Setup UX](../../research/state-of-the-art-setup-ux.md)
- [State-of-the-Art Apple Silicon](../../research/state-of-the-art-apple-silicon.md)
- [F-036: Guided Setup](./F-036-guided-setup.md)

---

**Status**: Planned
