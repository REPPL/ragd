# F-023: PII Detection

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**Milestone**: v0.7
**Priority**: P1

## Problem Statement

Personal documents often contain sensitive information: names, addresses, phone numbers, financial data. Users should be warned before indexing PII and given control over what gets stored. This builds trust and enables ragd for professional use.

## Design Approach

### Architecture

```
Document Ingestion
    ↓
PII Detection (Presidio/spaCy)
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

- [ ] Integrate Presidio for PII detection
- [ ] Add spaCy NER fallback
- [ ] Implement regex patterns for common PII
- [ ] Create PII report generation
- [ ] Add `--scan-pii` flag to index command
- [ ] Implement user prompts for PII handling
- [ ] Add PII redaction option (experimental)
- [ ] Create PII allowlist/blocklist configuration
- [ ] Write unit tests for each PII type
- [ ] Write integration tests for detection pipeline

## Success Criteria

- [ ] Detects common PII types (names, emails, phones)
- [ ] Reports PII before indexing
- [ ] User can choose to proceed, skip, or redact
- [ ] Detection works offline (local models)
- [ ] False positive rate < 10%
- [ ] Processing overhead < 20%

## Dependencies

- presidio-analyzer (Microsoft PII detection)
- spacy (NER fallback)
- F-001: Document Ingestion (integration point)

## Technical Notes

### Configuration

```yaml
pii:
  enabled: true
  scan_on_index: prompt  # always, never, prompt

  detection:
    engine: presidio  # presidio, spacy, hybrid
    confidence_threshold: 0.7
    entities:
      - PERSON
      - EMAIL_ADDRESS
      - PHONE_NUMBER
      - CREDIT_CARD
      - US_SSN
      - LOCATION

  handling:
    default_action: prompt  # index, skip, redact, prompt
    redaction_char: "█"

  allowlist:
    - example.com  # Don't flag example domains
    - 555-*  # Don't flag 555 phone numbers
```

### PII Detection

```python
from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

def detect_pii(text: str) -> list[PIIResult]:
    results = analyzer.analyze(
        text=text,
        entities=config.pii.detection.entities,
        language="en"
    )
    return [
        PIIResult(
            type=r.entity_type,
            value=text[r.start:r.end],
            start=r.start,
            end=r.end,
            confidence=r.score
        )
        for r in results
        if r.score >= config.pii.detection.confidence_threshold
    ]
```

### PII Report

```python
@dataclass
class PIIReport:
    document: str
    total_pii_found: int
    by_type: dict[str, int]
    high_confidence: list[PIIResult]
    low_confidence: list[PIIResult]

def generate_pii_report(document: Document) -> PIIReport:
    results = detect_pii(document.content)
    return PIIReport(
        document=document.path,
        total_pii_found=len(results),
        by_type=Counter(r.type for r in results),
        high_confidence=[r for r in results if r.confidence > 0.85],
        low_confidence=[r for r in results if r.confidence <= 0.85]
    )
```

### CLI Integration

```bash
# Scan before indexing (interactive)
ragd index ~/Documents/contracts/ --scan-pii

# Output:
# ⚠️ PII Detected in 3 documents:
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

# Always scan, never prompt (for scripts)
ragd index ~/Documents/ --scan-pii --pii-action skip

# Generate PII report only
ragd scan ~/Documents/contracts/
```

### Redaction (Optional)

```python
def redact_pii(text: str, results: list[PIIResult]) -> str:
    """Replace PII with redaction characters."""
    redacted = text
    # Process in reverse order to preserve positions
    for pii in sorted(results, key=lambda x: x.start, reverse=True):
        replacement = config.pii.handling.redaction_char * len(pii.value)
        redacted = redacted[:pii.start] + replacement + redacted[pii.end:]
    return redacted
```

## Related Documentation

- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md) - Research basis
- [v0.7.0 Milestone](../../milestones/v0.7.0.md) - Release planning
- [F-015: Database Encryption](./F-015-database-encryption.md) - Related privacy feature
- [F-017: Secure Deletion](./F-017-secure-deletion.md) - For removing PII later

---
