# ADR-0028: PII Handling Architecture

## Status

Proposed

## Context

ragd processes personal documents that may contain Personally Identifiable Information (PII): names, addresses, phone numbers, financial data, and medical information. Users need control over what PII gets indexed, and the system must support compliance requirements.

### Key Decisions Required

1. **Detection approach**: Rule-based, ML-based, or hybrid?
2. **Default behaviour**: Scan always, never, or on request?
3. **Handling options**: Index, skip, redact, or user choice?
4. **Tool selection**: Which PII detection library?

### Detection Approach Options

| Approach | Pros | Cons |
|----------|------|------|
| **Rule-based (regex)** | Fast, predictable, offline | Misses context-dependent PII |
| **NER-only (spaCy)** | Good for names/locations | Misses structured PII (SSN, IBAN) |
| **LLM-based** | Best context understanding | Slow, inconsistent, requires LLM |
| **Hybrid** | Best accuracy | More complex, slower |

### Tool Comparison

| Tool | Accuracy | Speed | Offline | Maintenance |
|------|----------|-------|---------|-------------|
| Microsoft Presidio | High (F1: ~90%) | Fast | Yes | Active |
| spaCy only | Medium (F1: ~80%) | Fast | Yes | Active |
| GLiNER | Variable | Medium | Yes | Active |
| Custom regex | Medium | Fastest | Yes | Manual |

## Decision

Implement a **hybrid PII handling architecture** using Microsoft Presidio as the primary engine, with extensible support for custom recognisers.

### Architecture

```
Document Text
    ↓
┌─────────────────────────────────────┐
│ PII Detection Pipeline              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Presidio Analyzer           │   │
│  │  ├─ Pattern Recognizers     │   │◄── Regex for structured PII
│  │  ├─ spaCy NER              │   │◄── ML for context-dependent
│  │  ├─ Custom Recognizers     │   │◄── Domain-specific patterns
│  │  └─ Context Enhancement    │   │
│  └─────────────────────────────┘   │
│              ↓                      │
│  ┌─────────────────────────────┐   │
│  │ Confidence Filtering        │   │
│  │ (threshold: 0.7 default)    │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
    ↓
Detection Results → User Decision → Processing
```

### Configuration Schema

```yaml
pii:
  enabled: false  # Global default: OFF (opt-in)

  detection:
    engine: presidio
    model: en_core_web_lg
    confidence_threshold: 0.7
    entities:
      - PERSON
      - EMAIL_ADDRESS
      - PHONE_NUMBER
      - CREDIT_CARD
      - UK_NINO
      - IBAN_CODE

  handling:
    default_action: prompt  # index | skip | redact | prompt
    redaction_char: "█"

    per_entity:
      PERSON: prompt
      EMAIL_ADDRESS: redact
      PHONE_NUMBER: redact
      CREDIT_CARD: redact

  # Per-folder overrides (opt-in for sensitive folders)
  folders:
    ~/Documents/Medical/:
      enabled: true
      default_action: redact
    ~/Documents/Financial/:
      enabled: true
      default_action: prompt
    ~/Documents/News/:
      enabled: false  # Explicit override (no scanning)
```

### Rationale for Hybrid Approach

1. **Presidio provides best-in-class accuracy** (F1: ~90%) for general PII
2. **Regex catches structured PII** (credit cards, IBANs) that NER misses
3. **spaCy NER (via Presidio)** handles context-dependent PII
4. **Extensibility** allows domain-specific patterns
5. **Local execution** aligns with privacy-first architecture
6. **Active maintenance** reduces long-term technical debt

### Rationale Against LLM-Based Detection

1. **Inconsistency**: LLMs can hallucinate or miss structured PII
2. **Performance**: 10-100x slower than Presidio
3. **Offline requirement**: ragd must work without LLM
4. **Auditability**: Difficult to explain LLM decisions

### Default Behaviour: Off (Opt-In)

**Decision**: PII scanning is **disabled by default**, opt-in per folder or command.

**Rationale**:
1. **Legitimate names are common**: News articles, academic papers, business documents all contain names
2. **False positives degrade UX**: Flagging "Winston Churchill" or article bylines is unhelpful
3. **Users know their sensitive data**: Those indexing medical/financial records know they need protection
4. **Principle of least surprise**: Unexpected redaction would confuse users
5. **Performance**: No overhead for users who don't need PII scanning

**When to enable**:
- Medical records, patient data
- Financial documents with account numbers
- Legal documents with personal details
- HR records, contracts with personal information

**Alternatives Rejected**:
- **Default ON**: Too aggressive, flags legitimate content in news/history/business
- **Default PROMPT**: Still scans everything, unnecessary overhead and interruption

### CLI Integration

```bash
# Default: NO PII scanning (most common use case)
ragd index ~/Documents/articles/

# Opt-in: Enable PII scanning for sensitive folder
ragd index ~/Documents/medical/ --scan-pii

# Opt-in: Scan and automatically redact
ragd index ~/Documents/financial/ --scan-pii --pii-action redact

# Configure folder for persistent PII scanning
ragd config set pii.folders."~/Documents/medical/".enabled true
ragd config set pii.folders."~/Documents/medical/".default_action redact

# After configuration, folder is always scanned
ragd index ~/Documents/medical/  # PII scanning enabled automatically

# Scan only (report, don't index)
ragd scan ~/Documents/contracts/ --output report.json

# Override: Disable scanning even for configured folder
ragd index ~/Documents/medical/ --no-scan-pii
```

## Consequences

### Positive

- High accuracy PII detection (F1: ~90%)
- Works offline (no external APIs)
- User control over handling decisions
- Extensible for domain-specific PII
- Compliance-friendly audit trail
- Well-maintained upstream dependency

### Negative

- Additional dependency (presidio-analyzer, ~50MB)
- spaCy model download required (~560MB for en_core_web_lg)
- ~20% overhead on indexing when scanning enabled
- May miss novel or unusual PII formats
- False positives possible (configurable threshold)

### Trade-offs Accepted

| Aspect | Decision | Alternative |
|--------|----------|-------------|
| Accuracy vs Speed | Presidio (balanced) | Regex-only (faster, less accurate) |
| Complexity vs Capability | Hybrid (capable) | Simple NER (simpler, limited) |
| Default Behaviour | Off (opt-in) | Always scan (false positives on legitimate names) |
| Granularity | Per-folder config | Global only (less flexible) |

## Implementation Strategy

**v0.7.0 (F-023):**
- Presidio integration for detection
- Basic PII report generation
- CLI flags for scanning (`--scan-pii`, `--no-scan-pii`)
- Default: disabled

**v0.7.x:**
- Per-folder configuration support
- Redaction capabilities
- Per-entity-type handling
- Batch processing

**v0.8.0:**
- Custom recogniser configuration
- Allowlist/blocklist support
- Integration with GDPR deletion (F-060)

## Alternatives Considered

### Alternative 1: Regex-Only

- **Pros**: Simplest, fastest, no dependencies
- **Cons**: Poor accuracy for names/context-dependent PII
- **Rejected**: Insufficient for compliance use cases

### Alternative 2: LLM-Based (GPT/Claude)

- **Pros**: Best context understanding
- **Cons**: Requires LLM, slow, inconsistent, privacy concerns
- **Rejected**: Conflicts with offline-first, privacy principles

### Alternative 3: spaCy-Only

- **Pros**: Good NER, fast, offline
- **Cons**: Misses structured PII (SSN, credit cards)
- **Rejected**: Incomplete coverage

## Research Sources

- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)
- [Microsoft Presidio](https://github.com/microsoft/presidio)
- [Hybrid PII Detection Research](https://www.nature.com/articles/s41598-025-04971-9)

## Related Documentation

- [F-023: PII Detection](../../features/planned/F-023-pii-detection.md)
- [F-060: GDPR-Compliant Deletion](../../features/planned/F-060-gdpr-compliant-deletion.md)
- [ADR-0003: Privacy-First Architecture](./0003-privacy-first-architecture.md)
- [ADR-0029: Privacy-Preserving Embedding Strategy](./0029-embedding-privacy-strategy.md)

---
