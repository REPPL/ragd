# Devlog: v0.7.0 Privacy Core

**Version:** v0.7.0
**Status:** Backfilled 2025-12-03

---

## Summary

Foundational privacy features: database encryption (AES-256-GCM), session management with auto-lock, secure deletion with three levels, and PII detection.

## Key Decisions

### Encryption Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| KDF | Argon2id | Memory-hard, modern standard |
| Cipher | AES-256-GCM | Authenticated encryption |
| Storage | SQLCipher | Battle-tested encrypted SQLite |

### Session Model

State machine approach:
```
Locked → Unlocked → Extended → Locked
           ↓
        Auto-lock (timeout)
```

### Secure Deletion Levels

| Level | Method | Use Case |
|-------|--------|----------|
| Standard | Index removal | Quick deletion |
| Secure | Multi-pass overwrite | HDD/magnetic |
| Cryptographic | Key rotation | SSD/flash |

### PII Detection

Multi-engine approach for reliability:
- Presidio (Microsoft, enterprise-grade)
- spaCy (NER fallback)
- Regex (patterns, fast)
- Hybrid (consensus voting)

## Scope Management

Original v0.7.0 scope was 9 features. Deferred 5 to maintain focus:
- F-018: Data Tiers → v0.7.5
- F-061-F-064: Tagging → v0.7.5

This was the right call - privacy core shipped solid.

## Challenges

1. **Memory protection**: mlock() not always available
2. **Key lifecycle**: Secure clearing from memory
3. **PII accuracy**: Balancing precision vs recall

## Lessons Learned

- Scope reduction improved quality
- Security features need extra testing
- Offline PII detection is viable

---

**Note:** This devlog was created retroactively to establish documentation consistency.
