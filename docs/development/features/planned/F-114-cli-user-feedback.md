# F-114: CLI User Feedback

## Problem Statement

The current CLI output during indexing operations is:

- **Noisy** - progress bar buried under third-party warnings
- **Generic** - no per-document breakdown of results
- **Non-actionable** - errors lack remediation guidance
- **Unparseable** - summary format not suitable for scripting

Users need clean, informative output that helps them understand what happened and what to do next.

## Design Approach

### 1. Clean Progress Display

During indexing (default mode):

```
Indexing 2,183 documents...

[=================>          ] 1,284/2,183 (59%) | report-q3.pdf

Processing: 12 docs/sec | Elapsed: 1m 42s | ETA: 1m 10s
```

Key improvements:
- Third-party warnings suppressed (see F-110)
- Current document name visible
- Processing rate and ETA shown
- Progress bar uninterrupted

### 2. Enhanced Final Summary

```
+-- Indexing Complete ------------------------------------------------+
|                                                                      |
|  Documents:  2,145 indexed | 30 skipped | 8 failed                  |
|  Content:    45,231 chunks | 12,847 pages                           |
|  Quality:    98.2% extraction success                               |
|                                                                      |
|  Time: 3m 24s | Rate: 10.5 docs/sec                                 |
+----------------------------------------------------------------------+

Partial extractions (3 documents):
  scanned-form.pdf         87% (13/15 pages) - 2 pages failed OCR
  old-report.pdf           92% (23/25 pages) - low confidence
  faded-scan.pdf           78% (7/9 pages)   - below threshold

Failed documents (8):
  encrypted-file.pdf       ENCRYPTED - Remove password protection
  scan-only.pdf            IMAGE_ONLY - Install: pip install 'ragd[ocr]'
  corrupted.pdf            MALFORMED - File may be corrupted

Detailed log: ~/.ragd/logs/ragd_2024-12-04_05-34-20.jsonl
```

### 3. Output Modes

| Mode | Flag | Description |
|------|------|-------------|
| Default | (none) | Progress bar + summary |
| Verbose | `-V` | Per-document output during indexing |
| Quiet | `-q` | Summary only, no progress |
| JSON | `--output-format json` | Machine-parseable output |
| Plain | `--output-format plain` | No colours/formatting |

### 4. Colour Coding

| Colour | Meaning |
|--------|---------|
| Green | Success, indexed |
| Yellow | Warning, partial extraction |
| Red | Error, failed |
| Cyan | Info, processing |

Disabled with `--no-color` flag.

## Implementation Tasks

- [ ] Rewrite `format_index_results()` for new summary format
- [ ] Add partial extractions table to summary
- [ ] Add failures by category with remediation hints
- [ ] Add `--quiet, -q` flag to suppress progress
- [ ] Add quality percentage calculation
- [ ] Add log file path to summary footer
- [ ] Ensure Rich progress bar integrates cleanly
- [ ] Test colour output and `--no-color` flag
- [ ] Test JSON output mode with new statistics

## CLI Options

```
ragd index <path> [OPTIONS]

Existing:
  --verbose, -V         Per-document progress output
  --no-color            Disable colour output
  --output-format       rich | json | plain

New:
  --quiet, -q           Suppress progress, show only final summary
```

## Success Criteria

- [ ] Progress bar visible and uninterrupted during indexing
- [ ] Final summary shows documents indexed/skipped/failed counts
- [ ] Quality percentage calculated and displayed
- [ ] Partial extractions listed with filename and percentage
- [ ] Failed documents listed with category and remediation
- [ ] Log file path shown at end of summary
- [ ] `--quiet` mode shows only summary
- [ ] `--output-format json` produces valid JSON
- [ ] Colours disabled with `--no-color`

## Dependencies

- F-110 (Structured Logging) - log file path
- F-111 (Error Logging & Recovery) - per-document statistics
- Rich library (existing dependency)

---

## Related Documentation

- [F-110 Structured Logging](./F-110-structured-logging.md)
- [F-111 Error Logging & Recovery](./F-111-error-logging-recovery.md)
- [v0.9.5 Milestone](../../milestones/v0.9.5.md)

---

**Status**: Planned
