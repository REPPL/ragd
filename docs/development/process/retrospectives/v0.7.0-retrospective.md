# v0.7.0 Retrospective

## Overview

**Milestone:** v0.7.0 - Privacy Core
**Agent:** Claude (claude-opus-4-5-20251101)
**Branch:** `main` (direct development)
**Date:** Backfilled 2025-12-03

---

## What Happened

| Phase | Plan | Actual | Notes |
|-------|------|--------|-------|
| **Research** | Encryption approaches | SQLCipher + Argon2id | Industry standards |
| **Architecture** | Security module design | `src/ragd/security/` | Clean separation |
| **Implementation** | 6 features | All complete | F-065, F-066, F-015-F-017, F-023 |
| **Scope Deferral** | 9 features planned | 6 delivered | Focused delivery |
| **Testing** | Security testing | ~200+ new tests | 1022 total passing |

## Features Completed

| Feature | Tests | Files | Notes |
|---------|-------|-------|-------|
| F-065: Chat Citation Display | ~15 | `src/ragd/chat/` | `--cite` flag |
| F-066: Configurable Chat Prompts | ~10 | `ChatConfig` | Prompt customisation |
| F-015: Database Encryption | ~45 | `src/ragd/security/crypto.py` | AES-256-GCM |
| F-016: Session Management | ~35 | `src/ragd/security/session.py` | Auto-lock, unlock |
| F-017: Secure Deletion | ~30 | `src/ragd/security/deletion.py` | 3 deletion levels |
| F-023: PII Detection | ~50 | `src/ragd/privacy/pii.py` | Multi-engine |

**Total:** ~185 new tests for v0.7.0 features

## Technical Achievements

### Database Encryption (`src/ragd/security/`)

| Component | Technology | Notes |
|-----------|------------|-------|
| Key Derivation | Argon2id | 64MB, 3 iterations, 4 parallel |
| Encryption | AES-256-GCM | Via SQLCipher |
| Key Storage | Keystore | Encrypted master key |
| Memory Protection | mlock(), ctypes.memset | Secure key clearing |

### Session Management

- **State Machine**: Locked → Unlocked → Extended → Locked
- **Auto-lock**: Configurable timeout (default 5 minutes)
- **CLI Commands**: `unlock`, `lock`, `session status`
- **Key Protection**: Keys cleared from memory on lock

### Secure Deletion

| Level | Method | Use Case |
|-------|--------|----------|
| Standard | Index removal | Quick deletion |
| Secure | Multi-pass overwrite | Physical media |
| Cryptographic | Key rotation | SSD/flash storage |

### PII Detection (`src/ragd/privacy/`)

- **Multi-Engine**: Presidio, spaCy, Regex, Hybrid
- **Entity Types**: Names, emails, phones, SSNs, credit cards
- **Offline**: No external API calls
- **Configurable**: Per-entity type detection

## Scope Management

**Deferred to v0.7.5:**
- F-018: Data Sensitivity Tiers
- F-061-F-064: Tagging features

**Deferred to v0.8.0:**
- Storage architecture decisions
- Knowledge graph integration

**Rationale:** Focused delivery of core privacy features over breadth.

## Lessons Learned

### What Worked Well

- **Focussed scope**: Deferring tagging kept release focussed
- **Security-first design**: Proper cryptographic primitives chosen
- **Memory protection**: Secure key handling implemented
- **Multi-level deletion**: Flexibility for different storage types

### What Needs Improvement

- **Retrospective timing**: Created post-release (backfilled)
- **Documentation cadence**: Impl record created, but no devlog
- **Scope estimation**: Original v0.7.0 scope was too ambitious

## Metrics

| Metric | v0.6.5 | v0.7.0 | Change |
|--------|--------|--------|--------|
| Total tests | ~920 | 1022 | +102 |
| New modules | 2 | 4 | Security, privacy |
| CLI commands | 14 | 20 | +unlock, lock, password, session, delete |

## Key Decisions

1. **SQLCipher over custom**: Industry-standard encryption
2. **Argon2id**: Modern, memory-hard KDF
3. **Presidio integration**: Enterprise-grade PII detection
4. **Session model**: Time-based auto-lock for security

---

## Related Documentation

- [v0.7.0 Milestone](../../milestones/v0.7.0.md) - Release planning
- [v0.7.0 Implementation](../../implementation/v0.7.0.md) - Technical record
- [F-015: Database Encryption](../../features/completed/F-015-database-encryption.md)
- [F-016: Session Management](../../features/completed/F-016-session-management.md)
- [F-017: Secure Deletion](../../features/completed/F-017-secure-deletion.md)
- [F-023: PII Detection](../../features/completed/F-023-pii-detection.md)
- [v0.6.5 Retrospective](./v0.6.5-retrospective.md) - Previous milestone

---

**Status**: Complete (backfilled)
