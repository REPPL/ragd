# ADR-0029: Privacy-Preserving Embedding Strategy

## Status

Proposed

## Context

Text embeddings can leak sensitive information. Research demonstrates:

- **92% exact text recovery** from embeddings (Morris et al., ACL 2024)
- Attackers can reconstruct names, health diagnoses, and other PII
- Embeddings must be treated with the same security as raw text

This creates a layered defence problem:

1. **Text layer**: Detect and remove PII before embedding (ADR-0026)
2. **Embedding layer**: Protect embeddings from inversion attacks
3. **Storage layer**: Encrypt embeddings at rest (ADR-0010)

### Protection Options

| Method | Protection | Performance | Complexity |
|--------|------------|-------------|------------|
| **None** | None | Baseline | None |
| **Eguard transformation** | High (95% tokens) | ~20% overhead | Medium |
| **Differential privacy** | Configurable | Variable | High |
| **Homomorphic encryption** | Very high | 10-100x overhead | Very high |

### Key Trade-offs

1. **Security vs Utility**: More protection = less retrieval accuracy
2. **Security vs Performance**: More protection = slower indexing
3. **Simplicity vs Security**: Simpler = less comprehensive

## Decision

Implement a **defence-in-depth strategy** with pre-vectorisation sanitisation as the primary defence and optional embedding protection as a secondary layer.

### Strategy: Defence-in-Depth

```
User Document
    ↓
┌─────────────────────────────────────┐
│ Layer 1: Text Sanitisation          │ ← PRIMARY DEFENCE
│ (Presidio PII detection/redaction)  │
└─────────────────────────────────────┘
    ↓
Sanitised Text
    ↓
┌─────────────────────────────────────┐
│ Layer 2: Embedding Generation       │
│ (sentence-transformers)             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Layer 3: Embedding Protection       │ ← OPTIONAL
│ (Eguard transformation)             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Layer 4: Storage Encryption         │
│ (SQLCipher for ChromaDB)            │
└─────────────────────────────────────┘
```

### Primary Defence: Pre-Vectorisation Sanitisation

**Rationale:**
1. Most effective—PII never reaches embedding model
2. Most practical—no embedding model changes required
3. User-controllable—visible what gets redacted
4. Compliance-friendly—audit trail of what was removed

**Approach:**
- Detect PII in text using Presidio (ADR-0026)
- Redact or skip documents based on user preference
- Only sanitised text gets embedded

### Secondary Defence: Optional Embedding Protection

**When to use:**
- High-security environments (medical, legal, financial)
- Documents that may contain context-dependent PII
- Users with elevated threat models

**Implementation:**
- Eguard-style transformation as optional feature
- Disabled by default (performance consideration)
- Configurable via CLI flag or config file

### Configuration

```yaml
embedding:
  model: all-MiniLM-L6-v2

  protection:
    enabled: false  # Disabled by default
    method: eguard  # eguard | none

    eguard:
      model_path: ~/.ragd/models/eguard/
      device: auto
```

### Why NOT Differential Privacy

1. **Utility degradation**: Large noise required for meaningful privacy
2. **Complexity**: Epsilon selection is domain-specific
3. **Research maturity**: Less proven for RAG than Eguard
4. **Performance**: Variable overhead difficult to predict

### Why NOT Homomorphic Encryption

1. **Performance**: 10-100x overhead unacceptable for local use
2. **Complexity**: HE libraries are complex to integrate
3. **Overkill**: Local storage with database encryption sufficient

## Consequences

### Positive

- Clear, layered defence strategy
- Primary defence (sanitisation) is practical and effective
- Optional advanced protection for high-security needs
- No performance penalty for users who don't need protection
- Aligns with privacy-first architecture

### Negative

- Sanitisation may reduce retrieval quality (removed context)
- Embedding protection has ~20% overhead when enabled
- Users must opt-in to advanced protection
- Eguard requires additional model (~50MB)

### Security Assessment

| Attack | Primary Defence | Secondary Defence | Combined |
|--------|-----------------|-------------------|----------|
| Embedding inversion | Partial (if PII missed) | High (95%) | High |
| Direct text access | N/A | N/A | Encryption |
| Semantic inference | Limited | Medium | Medium |
| Physical access | N/A | N/A | Encryption |

## Implementation Strategy

**v0.7.0:**
- Pre-vectorisation PII sanitisation (F-023)
- Database encryption (F-015)

**v0.8.0:**
- Optional Eguard protection (F-056)
- Protection metrics/monitoring
- CLI integration

**Future:**
- Research newer protection methods
- Evaluate DP-based approaches as research matures

## Alternatives Considered

### Alternative 1: Embedding Protection as Default

- **Pros**: Maximum security for all users
- **Cons**: 20% performance penalty always, complexity
- **Rejected**: Against principle of minimal overhead

### Alternative 2: No Embedding Protection

- **Pros**: Simplest, fastest
- **Cons**: Embeddings remain vulnerable
- **Rejected**: Insufficient for high-security use cases

### Alternative 3: Homomorphic Encryption

- **Pros**: Strongest theoretical guarantees
- **Cons**: 10-100x overhead, complexity
- **Rejected**: Impractical for local, offline use

## Research Sources

- [Eguard: Defending LLM Embeddings](https://arxiv.org/abs/2411.05034)
- [Transferable Embedding Inversion Attack](https://aclanthology.org/2024.acl-long.230/)
- [Text Embedding Privacy Risks](https://ironcorelabs.com/ai-encryption/)
- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)

## Related Documentation

- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)
- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
- [ADR-0010: Vector Database Security](./0010-vector-database-security.md)
- [ADR-0028: PII Handling Architecture](./0028-pii-handling-architecture.md)
- [F-059: Embedding Privacy Protection](../../features/planned/F-059-embedding-privacy-protection.md)
- [F-023: PII Detection](../../features/completed/F-023-pii-detection.md)

---
