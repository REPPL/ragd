# Devlog: v0.8.6 Security Focus

**Date:** 2025-12-04
**Version:** 0.8.6
**Theme:** Hardened & Audited

## The Story

v0.8.6 establishes ragd's security foundation before wider release. Rather than adding features, this release focuses on defensive programming patterns that will benefit all future development.

## What We Built

### Input Validation Module

Created `src/ragd/security/validation.py` with comprehensive input validation:

```python
from ragd.security import validate_path, validate_document_id

# Prevent path traversal
safe_path = validate_path(user_path, base_dir=data_dir)

# Validate document IDs
doc_id = validate_document_id(user_input)  # Raises ValidationError if invalid
```

Key functions:
- `validate_path()` - Path traversal prevention, symlink handling
- `validate_document_id()` - Alphanumeric with hyphens/underscores
- `validate_tag_name()` - Allows colons and slashes for namespacing
- `sanitise_search_query()` - Escapes regex special characters
- `validate_limit()` - Bounds checking for pagination
- `validate_file_size()` - Size limits for indexing

### Secrets Management

Created `src/ragd/security/secrets.py` for sensitive data handling:

```python
from ragd.security import SecretString, load_secret

# Load from environment
api_key = load_secret("OPENAI_API_KEY")
print(api_key)  # Output: ****7890 (masked)
print(api_key.get_secret_value())  # Output: sk-actual-key
```

Features:
- `SecretString` - Immutable type that masks on `str()`/`repr()`
- `load_secret()` - Load from `RAGD_*` environment variables
- `mask_secrets_in_string()` - Sanitise arbitrary text
- `SecretsFilter` - Logging filter to mask secrets in logs

### Error Hierarchy

Created `src/ragd/errors.py` with user-friendly error handling:

```python
from ragd.errors import RagdError, ConfigError

raise ConfigError(
    message="Cannot load configuration",
    hint="Run 'ragd init' to create configuration",
    internal=f"YAML parse error: {detail}",  # Logged, not shown
)
```

Error types with exit codes:
- `RagdError` (1) - Base class
- `ConfigError` (3) - Configuration issues
- `ValidationError` (2) - Usage errors
- `DependencyError` (4) - Missing packages
- `IndexingError` (5) - Partial success

## Security Audit Results

### pip-audit
- 1 vulnerability found: pip itself (CVE-2025-8869)
- This is a system package, not a ragd dependency
- All ragd dependencies are clean

### bandit
- 0 high-severity issues
- 25 medium-severity (mostly false positives on parameterised SQL)
- 26 low-severity (informational)

## What We Didn't Build

### Full CLI Integration
The validation functions exist but aren't integrated into every CLI command yet. This is intentional - integration happens incrementally as commands are touched.

### 85% Coverage
Coverage is at 56%, not 85%. This was aspirational. We established 80 new tests as a foundation, and coverage improvement continues.

### SBOM Generation
Deferred to v0.8.7. Requires additional tooling setup.

## The Security Mindset

This release establishes a security-first mindset:

1. **Validate early** - Check inputs at the boundary
2. **Fail safely** - User-friendly errors, log internals
3. **Mask secrets** - Never display sensitive data
4. **Audit regularly** - Run pip-audit and bandit

These patterns make ragd safer for users who may process sensitive documents.

---

*Security is not a feature, it's a foundation.*
