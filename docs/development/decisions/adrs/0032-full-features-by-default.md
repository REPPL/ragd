# ADR-0032: Full Features by Default (v1.0)

## Status

Proposed

**Supersedes:** [ADR-0024](./0024-optional-dependencies.md)

## Context

ADR-0024 established an opt-in dependency model for v0.x:
- Minimal core install by default
- Users explicitly install extras (`ragd[pdf]`, `ragd[ocr]`, etc.)

This worked for early development but creates friction for v1.0:

1. **User confusion**: Non-experts don't know which extras they need
2. **Silent failures**: Features unavailable without clear guidance
3. **Documentation burden**: Must explain many installation variants
4. **Support overhead**: "Why doesn't X work?" - "Did you install [extra]?"

## Decision

**Invert the model for v1.0: Full features by default.**

### Default Installation

```bash
pip install ragd
```

Installs ALL runtime features:
- Core (CLI, ChromaDB, embeddings)
- pdf (docling, docling-core)
- ocr-fallback (easyocr)
- metadata (keybert, spacy, langdetect)
- export (pyarrow)
- watch (watchdog)
- web (trafilatura, selectolax)
- privacy (presidio-analyzer)

### Expert Opt-Out

```bash
RAGD_MINIMAL=1 pip install ragd
```

Installs only core dependencies for:
- CI/CD pipelines needing fast builds
- Resource-constrained environments
- Users who genuinely need minimal install

### Still Optional

Some extras remain optional due to system requirements:

| Extra | Reason | Installation |
|-------|--------|--------------|
| encryption | Requires SQLCipher | `pip install ragd[encryption]` |
| faiss | Platform-specific issues | `pip install ragd[faiss]` |
| dev/test/security | Development tools | `pip install ragd[dev]` |

### Implementation

Use hybrid setup.py + pyproject.toml:

1. pyproject.toml: `dynamic = ["dependencies"]`
2. setup.py: Read RAGD_MINIMAL, return appropriate dependency list
3. Optional extras remain in pyproject.toml

```python
# setup.py
import os
from setuptools import setup

CORE_DEPS = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    # ... other core deps
]

FULL_FEATURE_DEPS = [
    "docling>=2.0.0",
    "easyocr>=1.7.0",
    "keybert>=0.8.0",
    # ... other feature deps
]

def get_dependencies():
    minimal = os.environ.get("RAGD_MINIMAL", "").lower() in ("1", "true", "yes")
    return CORE_DEPS if minimal else CORE_DEPS + FULL_FEATURE_DEPS

setup(install_requires=get_dependencies())
```

## Consequences

### Positive

- **Simpler onboarding**: `pip install ragd` just works
- **Reduced support**: No "install the extra" guidance needed
- **Feature discovery**: Users see all capabilities immediately
- **Consistent experience**: Everyone gets the same ragd

### Negative

- **Larger install**: ~2-3GB vs ~500MB (acceptable for v1.0)
- **Slower install**: 2-5 minutes vs 30 seconds
- **Expert friction**: Must know about RAGD_MINIMAL

### Mitigation

- Document RAGD_MINIMAL in README and CLI reference
- `ragd doctor` shows installation mode
- Clear messaging in release notes

## Alternatives Considered

### 1. Keep Current Model (Rejected)

Continue with opt-in extras. Rejected because user confusion outweighs install size concerns for a v1.0 release targeting non-technical users.

### 2. Separate Packages (Rejected)

Publish `ragd` (minimal) and `ragd-full` (everything). Rejected because it fragments the ecosystem and creates version synchronisation issues.

### 3. Build-time Configuration (Rejected)

Use pip's `--config-settings` for customisation. Rejected because it's less intuitive than environment variables and has poor tooling support.

## Related Documentation

- [ADR-0024](./0024-optional-dependencies.md) - Original strategy (superseded)
- [F-119](../../features/planned/F-119-full-features-by-default.md) - Feature spec
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)

---

**Status**: Proposed
