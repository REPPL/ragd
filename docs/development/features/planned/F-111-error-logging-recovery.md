# F-111: Error Logging & Recovery

## Problem Statement

When indexing large document collections, users cannot easily identify:

- **Which specific documents failed** and why
- **Which documents had partial extraction** (e.g., 87% of pages processed)
- **What remediation steps** would fix the issues
- **Historical patterns** of failures across indexing sessions

Current behaviour shows generic error messages without actionable guidance.

## Design Approach

### 1. Per-Document Statistics Tracking

Extend `IndexResult` dataclass to track granular statistics:

```python
@dataclass
class IndexResult:
    # ... existing fields ...
    total_pages: int = 0
    processed_pages: int = 0
    failed_pages: list[int] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_pages == 0:
            return 1.0 if self.success else 0.0
        return self.processed_pages / self.total_pages
```

### 2. Session Statistics Aggregation

New `IndexSessionStats` dataclass to aggregate results:

```python
@dataclass
class IndexSessionStats:
    documents_indexed: int
    documents_skipped: int
    documents_failed: int
    total_chunks: int
    total_pages: int
    overall_quality: float  # Weighted average success_rate
    duration_seconds: float
    partial_extractions: list[IndexResult]  # 0.5 <= success_rate < 0.95
    failures_by_category: dict[FailureCategory, list[IndexResult]]
    log_file: Path | None
```

### 3. Failure Categorisation

Expand `FailureCategory` enum with remediation hints:

| Category | Example | Remediation Hint |
|----------|---------|------------------|
| `ENCRYPTED` | Password-protected PDF | Remove password protection |
| `IMAGE_ONLY` | Scanned PDF without OCR layer | Install: `pip install 'ragd[ocr]'` |
| `MALFORMED` | Corrupted file structure | File may be corrupted |
| `UNSUPPORTED` | Unknown file format | Convert to supported format |
| `OCR_FAILED` | OCR confidence too low | Try higher resolution scan |
| `TIMEOUT` | Processing exceeded limit | Increase timeout or split file |

### 4. Partial Extraction Tracking

Documents with `0.5 <= success_rate < 0.95` are flagged as partial extractions with details:

```
Partial extractions (3 documents):
  scanned-form.pdf         87% (13/15 pages) - 2 pages failed OCR
  old-report.pdf           92% (23/25 pages) - low confidence
  faded-scan.pdf           78% (7/9 pages)   - below threshold
```

## Implementation Tasks

- [ ] Extend `IndexResult` with page tracking fields
- [ ] Create `IndexSessionStats` dataclass in `statistics.py`
- [ ] Update `_process_pdf()` to track per-page results
- [ ] Update OCR pipeline to return per-page success info
- [ ] Expand `FailureCategory` enum with new categories
- [ ] Add remediation hints to each failure category
- [ ] Aggregate statistics across all processed documents
- [ ] Log per-document details to structured log file (F-110)

## Success Criteria

- [ ] Every failed document has a specific failure category
- [ ] Every failure category has a remediation hint
- [ ] Partial extractions (< 95% success) are identified and listed
- [ ] Per-document statistics available in log file
- [ ] Session summary includes quality percentage
- [ ] `IndexSessionStats` aggregates all document results

## Dependencies

- F-110 (Structured Logging) - log file infrastructure
- Existing `FailureCategory` enum in `pipeline.py`

---

## Related Documentation

- [F-110 Structured Logging](./F-110-structured-logging.md)
- [F-114 CLI User Feedback](./F-114-cli-user-feedback.md)
- [v0.9.5 Milestone](../../milestones/v0.9.5.md)

---

**Status**: Planned
