# F-119: Full Features by Default

## Overview

**Milestone**: v1.0
**Priority**: P1
**Supersedes**: ADR-0024 (optional dependencies strategy)

## Problem Statement

The current opt-in dependency model (ADR-0024) creates uncertainty:
- Non-expert users don't know which extras to install
- Features fail silently or with confusing errors
- "pip install ragd" provides incomplete experience
- Documentation must explain many installation variants

## Design Approach

**Invert the model for v1.0:**
- Default `pip install ragd` installs ALL runtime features
- Expert users opt-out with `RAGD_MINIMAL=1 pip install ragd`
- System-dependent extras (encryption, faiss) remain optional

**Technical implementation:**
- Hybrid setup.py + pyproject.toml approach
- setup.py reads RAGD_MINIMAL environment variable
- pyproject.toml marks dependencies as dynamic

## Implementation Tasks

- [ ] Create setup.py with conditional dependency logic
- [ ] Update pyproject.toml to mark dependencies as dynamic
- [ ] Update feature detection (src/ragd/features.py)
- [ ] Update ragd doctor to show installation mode
- [ ] Update README installation instructions
- [ ] Update getting-started tutorial
- [ ] Update CLI reference (env vars section)
- [ ] Add RAGD_MINIMAL to environment variable docs

## Success Criteria

- [ ] `pip install ragd` installs all runtime features by default
- [ ] `RAGD_MINIMAL=1 pip install ragd` installs only core
- [ ] `ragd doctor` displays current installation mode
- [ ] Documentation reflects new installation model
- [ ] CI tests both installation modes

## Dependencies

- None (packaging change only)

## Dependency Categories (v1.0)

| Category | Default Install | Expert Opt-Out |
|----------|-----------------|----------------|
| Core (CLI, embeddings, ChromaDB) | Yes | Yes |
| pdf (docling) | Yes | RAGD_MINIMAL=1 |
| ocr-fallback (easyocr) | Yes | RAGD_MINIMAL=1 |
| metadata (keybert, spacy) | Yes | RAGD_MINIMAL=1 |
| export (pyarrow) | Yes | RAGD_MINIMAL=1 |
| watch (watchdog) | Yes | RAGD_MINIMAL=1 |
| web (trafilatura) | Yes | RAGD_MINIMAL=1 |
| privacy (presidio) | Yes | RAGD_MINIMAL=1 |
| encryption | No (system deps) | N/A |
| faiss | No (platform issues) | N/A |
| dev/test/security | No | N/A |

## Technical Notes

### Why Environment Variable?

pip/pyproject.toml don't natively support conditional dependencies. The hybrid setup.py approach allows reading `RAGD_MINIMAL` at install time:

```python
# setup.py
import os
from setuptools import setup

def get_dependencies():
    minimal = os.environ.get("RAGD_MINIMAL", "").lower() in ("1", "true", "yes")
    return CORE_DEPS if minimal else CORE_DEPS + FULL_FEATURE_DEPS

setup(install_requires=get_dependencies())
```

### System-Dependent Extras

Some extras cannot be included by default:

- **encryption**: Requires SQLCipher system library (brew/apt install)
- **faiss**: Has platform-specific build issues on some systems

These remain as optional extras users must explicitly install.

## Related Documentation

- [ADR-0024](../../decisions/adrs/0024-optional-dependencies.md) - Original strategy (superseded)
- [ADR-0032](../../decisions/adrs/0032-full-features-by-default.md) - New strategy
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)

---

**Status**: Planned
