# ADR-0010: Vector Database Security

## Status

Accepted

## Context

Vector embeddings present a unique security challenge. Research shows text can be reconstructed from embeddings with up to 92% accuracy (ACL 2024). This means encrypted documents can still leak information through their embeddings.

OWASP LLM Top 10 lists "Vector and Embedding Weaknesses" (LLM08) as a significant risk.

## Decision

Implement a pragmatic embedding protection strategy:

### Threat Assessment

| Risk | Mitigation | Phase |
|------|------------|-------|
| Raw embedding access | Database encryption | v0.7.0 |
| Embedding inversion | Encrypted chunks + access control | v0.7.0 |
| Semantic leakage | Eguard-style transformation | v0.9+ |

### Primary Defence: Encrypted Chunks

Store original text encrypted, embeddings unencrypted:

```
Document → Chunk → [AES-256 Encrypt] → Encrypted Chunk Storage
                → [Embed] → Unencrypted Vector Storage
```

**Rationale:**
- Embeddings alone reveal semantic topics but not exact text
- Encrypted chunks prevent text reconstruction
- Similarity search still works on unencrypted vectors
- Acceptable trade-off for v0.7

### Advanced Defence: Embedding Transformation (v0.9+)

Eguard-style defence transforms embeddings to resist inversion:

```
Original Embedding → [Transformation] → Protected Embedding
```

- 95% token protection reported
- Some utility trade-off
- Optional for high-security use cases

### Access Control

Combine encryption with access tiers:

| Tier | Data | Protection |
|------|------|------------|
| Standard | General notes | Database encryption |
| Sensitive | Medical, financial | + encrypted chunks |
| Critical | Credentials | + hardware key |

## Consequences

### Positive

- Addresses OWASP LLM08 risks
- Pragmatic approach balances security and usability
- Foundation for advanced protection later
- Clear upgrade path to stronger protection

### Negative

- Embeddings still reveal semantic topics
- Encrypted chunks add storage overhead
- Embedding transformation reduces search quality
- Complexity for users to understand tiers

## Implementation Strategy

**v0.7.0:**
- Database encryption (ADR-0009)
- Encrypted chunk storage
- Basic access control

**v0.9.0:**
- Optional embedding transformation
- Data sensitivity tiers
- Audit logging

## Research Sources

- [Text Embedding Privacy Risks](https://ironcorelabs.com/blog/2024/text-embedding-privacy-risks/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Eguard Defense](https://arxiv.org/abs/2411.05034)

## Related Documentation

- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)
- [ADR-0009: Security Architecture](./0009-security-architecture.md)
- [F-018: Data Tiers](../../features/completed/F-018-data-tiers.md)

---
