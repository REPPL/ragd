# F-125: Startup Time Optimisation

## Overview

**Milestone**: v1.1.0
**Priority**: P1
**Deferred From**: v1.0.0
**Target**: CLI startup < 500ms

## Problem Statement

Slow CLI startup creates poor user experience:
- `ragd --version` should be instant
- `ragd --help` should respond immediately
- Heavy imports at startup delay all operations
- Users perceive the tool as sluggish

Current state analysis shows:
- 60+ command functions imported eagerly in cli.py
- Heavy modules (chromadb, sentence-transformers) imported at startup
- All commands registered before any is invoked

## Design Approach

**Target: `ragd --help` and `ragd --version` in < 500ms.**

**Optimisation strategies:**
1. Lazy command imports - only import when command is invoked
2. Lazy module loading for heavy dependencies
3. Deferred model loading (embedding models)
4. Startup time measurement and CI regression testing

**Lazy import pattern:**
```python
# BEFORE: Eager import
from ragd.ui.cli.commands.core import index_command

# AFTER: Lazy import
@app.command()
def index(...):
    from ragd.ui.cli.commands.core import index_command
    index_command(...)
```

## Implementation Tasks

- [ ] Measure current startup time (baseline)
- [ ] Identify top startup time contributors (profile imports)
- [ ] Refactor cli.py to use lazy command imports
- [ ] Add lazy imports for chromadb, sentence-transformers
- [ ] Verify embedding models load lazily (on first use)
- [ ] Create `scripts/measure_startup.py` utility
- [ ] Add startup time CI test (fails if > 500ms)
- [ ] Optimise __init__.py files (remove unnecessary imports)
- [ ] Document startup optimisation patterns
- [ ] Write tests verifying lazy import behaviour

## Success Criteria

- [ ] `ragd --version` completes in < 500ms
- [ ] `ragd --help` completes in < 500ms
- [ ] `ragd status` completes in < 1000ms (includes DB check)
- [ ] CI test catches startup time regressions
- [ ] Heavy modules (chromadb, transformers) not imported until needed
- [ ] Embedding models not loaded until embedding operation

## Dependencies

- None (refactoring existing code)

## Technical Notes

### Current cli.py Problem

Lines 37-132 in `src/ragd/cli.py` show eager imports:
```python
from ragd.ui.cli import (
    index_command,
    search_command,
    ask_command,
    # ... 60+ more functions
)
```

This forces loading of all command dependencies at startup.

### Lazy Command Pattern

```python
# cli.py - AFTER refactoring
@app.command()
def index(
    path: Annotated[Path, typer.Argument(...)],
    # ... other args
) -> None:
    """Index documents for retrieval."""
    from ragd.ui.cli.commands.core import index_command
    index_command(path, ...)
```

### Startup Measurement

```python
# scripts/measure_startup.py
import subprocess
import time
import statistics

def measure_startup(command: list[str], iterations: int = 10) -> dict:
    """Measure CLI startup time."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(command, capture_output=True)
        times.append((time.perf_counter() - start) * 1000)

    return {
        "command": " ".join(command),
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
    }

if __name__ == "__main__":
    results = measure_startup(["ragd", "--version"])
    print(f"ragd --version: {results['mean_ms']:.0f}ms (target: <500ms)")
```

### CI Test

```python
# tests/test_startup.py
def test_startup_time():
    """CLI startup must be under 500ms."""
    result = measure_startup(["ragd", "--version"], iterations=5)
    assert result["mean_ms"] < 500, f"Startup too slow: {result['mean_ms']}ms"
```

### Import Profiling

```bash
# Profile Python imports
python -X importtime -c "import ragd" 2>&1 | head -50
```

## Related Documentation

- [F-123: Performance Profiling](./F-123-performance-profiling.md) - Measurement framework
- [F-124: Memory Optimisation](./F-124-memory-optimisation.md) - Related optimisation
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)
- [CLI Reference](../../../reference/cli-reference.md)

---

**Status**: Planned
