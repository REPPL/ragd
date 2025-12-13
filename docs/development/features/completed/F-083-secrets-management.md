# F-083: Secrets Management

## Problem Statement

ragd may need to store sensitive configuration like API keys (for future cloud LLM support). Currently there's no standardised way to handle secrets securely. They could be exposed in config files, logs, or error messages.

## Design Approach

### 1. Environment Variable Priority

Secrets should be read from environment variables first:

```bash
RAGD_OLLAMA_API_KEY=sk-xxx
RAGD_OPENAI_API_KEY=sk-xxx
```

### 2. Masked Display

When showing configuration, secrets must be masked:

```bash
$ ragd config show
llm:
  api_key: ****-xxx  # Masked
```

### 3. Never Log Secrets

Even in debug mode, secrets must not appear in logs.

## Implementation Tasks

- [x] Create `src/ragd/security/secrets.py` module
- [x] Implement `SecretString` type that masks on display
- [x] Implement environment variable loading for secrets
- [x] Update config display to mask secrets
- [x] Add secret detection to logging filters
- [x] Add tests for secret masking

## Success Criteria

- [x] Secrets loaded from environment variables
- [x] `ragd config show` masks all secrets
- [x] Secrets never appear in log output
- [x] Clear documentation for setting secrets

## Dependencies

- v0.8.5 (Knowledge Graph Foundation)
- ADR-0013: Configuration Schema

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-082: Security Hardening](./F-082-security-hardening.md)
- [v0.8.5 Milestone](../../milestones/v0.8.5.md)

