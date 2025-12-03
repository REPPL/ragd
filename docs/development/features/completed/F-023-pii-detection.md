# F-023: PII Detection

## Overview

**Research**: [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)
**ADR**: [ADR-0028: PII Handling Architecture](../../decisions/adrs/0028-pii-handling-architecture.md)
**Milestone**: v0.7.0
**Priority**: P1
**Status**: Completed

## Problem Statement

Personal documents often contain sensitive information: names, addresses, phone numbers, financial data. Users should be warned before indexing PII and given control over what gets stored. This builds trust and enables ragd for professional use.

## Design Approach

### Architecture

```
Document Ingestion
    ↓
PII Detection (Presidio/spaCy/Regex)
    ↓
User Decision
    ├── Index as-is
    ├── Skip document
    └── Redact PII (optional)
    ↓
Continue Pipeline
```

### Technologies

- **Presidio**: Microsoft's PII detection framework
- **spaCy NER**: Entity recognition for PII types
- **Regex patterns**: Known formats (SSN, phone, email)
- **Local models**: No external API calls

### PII Categories

| Category | Examples | Detection Method |
|----------|----------|------------------|
| **Names** | John Smith, Dr. Jones | NER |
| **Contact** | Emails, phone numbers | Regex + NER |
| **Financial** | SSN, account numbers | Regex |
| **Location** | Addresses, coordinates | NER + patterns |
| **Medical** | Patient IDs, conditions | Domain patterns |
| **Dates** | DOB, appointments | NER + patterns |

## Implementation Tasks

- [x] Integrate Presidio for PII detection
- [x] Add spaCy NER fallback
- [x] Implement regex patterns for common PII
- [x] Create PII report generation
- [x] Add `--scan-pii` flag to index command
- [x] Implement user prompts for PII handling
- [x] Add PII redaction option (experimental)
- [x] Create PII allowlist/blocklist configuration
- [x] Write unit tests for each PII type
- [x] Write integration tests for detection pipeline

## Success Criteria

- [x] Detects common PII types (names, emails, phones)
- [x] Reports PII before indexing
- [x] User can choose to proceed, skip, or redact
- [x] Detection works offline (local models)
- [x] False positive rate < 10%
- [x] Processing overhead < 20%

## Dependencies

- presidio-analyzer (Microsoft PII detection)
- spacy (NER fallback)
- F-001: Document Ingestion (integration point)

## Implementation Notes

### Module Structure

```
src/ragd/privacy/
├── __init__.py
└── pii.py  # PII detection engines
```

### Detection Engines

```python
class PIIEngine(Enum):
    PRESIDIO = "presidio"  # Microsoft's framework
    SPACY = "spacy"        # NER fallback
    REGEX = "regex"        # Pattern matching
    HYBRID = "hybrid"      # Best of all
```

### Entity Types

```python
class PIIEntityType(Enum):
    PERSON = "PERSON"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    US_SSN = "US_SSN"
    UK_NINO = "UK_NINO"
    IBAN_CODE = "IBAN_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    LOCATION = "LOCATION"
    DATE_TIME = "DATE_TIME"
    ORGANIZATION = "ORGANIZATION"
```

### Configuration

```yaml
pii:
  enabled: false  # Default: OFF (opt-in per folder or command)

  detection:
    engine: presidio  # presidio, spacy, hybrid
    confidence_threshold: 0.7
    entities:
      - PERSON
      - EMAIL_ADDRESS
      - PHONE_NUMBER
      - CREDIT_CARD
      - UK_NINO
      - IBAN_CODE

  handling:
    default_action: prompt  # index, skip, redact, prompt
    redaction_char: "█"

  # Per-folder overrides (opt-in for sensitive folders)
  folders:
    ~/Documents/Medical/:
      enabled: true
      default_action: redact
    ~/Documents/Financial/:
      enabled: true
      default_action: prompt

  allowlist:
    - example.com  # Don't flag example domains
    - 555-*  # Don't flag 555 phone numbers
```

### CLI Integration

```bash
# Default: NO PII scanning (news, articles, general documents)
ragd index ~/Documents/articles/

# Opt-in: Scan before indexing (interactive)
ragd index ~/Documents/contracts/ --scan-pii

# Output:
# PII Detected in 3 documents:
#
# contract-2024.pdf:
#   - 5 PERSON names
#   - 2 EMAIL_ADDRESS
#   - 1 PHONE_NUMBER
#
# How do you want to proceed?
# [I] Index as-is
# [S] Skip these documents
# [R] Redact PII and index
# [V] View details
# [Q] Quit

# Opt-in: Scan and auto-redact (for scripts)
ragd index ~/Documents/medical/ --scan-pii --pii-action redact

# Configure folder for persistent scanning
ragd config set pii.folders."~/Documents/medical/".enabled true

# Generate PII report only (no indexing)
ragd scan ~/Documents/contracts/
```

### Redaction

```python
def redact_pii(text: str, entities: list[PIIEntity], redaction_char: str = "█") -> str:
    """Replace PII with redaction characters."""
    redacted = text
    # Process in reverse order to preserve positions
    for entity in sorted(entities, key=lambda x: x.start, reverse=True):
        replacement = redaction_char * (entity.end - entity.start)
        redacted = redacted[:entity.start] + replacement + redacted[entity.end:]
    return redacted
```

## Related Documentation

- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md) - Comprehensive PII research
- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md) - Privacy architecture research
- [ADR-0028: PII Handling Architecture](../../decisions/adrs/0028-pii-handling-architecture.md) - Architecture decision
- [F-059: Embedding Privacy Protection](../planned/F-059-embedding-privacy-protection.md) - Embedding-level defence
- [F-060: GDPR-Compliant Deletion](../planned/F-060-gdpr-compliant-deletion.md) - Compliance deletion
- [F-015: Database Encryption](./F-015-database-encryption.md) - Related privacy feature
- [F-017: Secure Deletion](./F-017-secure-deletion.md) - For removing PII later

---

**Status**: Completed
