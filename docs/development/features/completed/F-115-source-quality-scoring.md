# F-115: Source Quality Scoring

## Overview

**Milestone**: v0.9.6
**Priority**: P2 - Medium
**Deferred From**: v0.9.5

## Problem Statement

Not all indexed content is equal quality. Users need to understand:

- How confident is the extraction?
- Was OCR required (potentially lower accuracy)?
- Are there formatting issues or missing content?
- Should this source be trusted for important queries?

## Design Approach

### Quality Dimensions

Score content on multiple dimensions:

```python
@dataclass
class QualityScore:
    extraction_confidence: float  # 0.0-1.0
    text_completeness: float      # 0.0-1.0
    formatting_quality: float     # 0.0-1.0
    overall: float                # Weighted average

    flags: list[str]  # ["ocr_required", "tables_detected", "images_skipped"]
```

### Scoring Criteria

| Factor | High Score | Low Score |
|--------|-----------|-----------|
| Extraction | Native text | OCR required |
| Completeness | All content captured | Missing sections |
| Formatting | Structure preserved | Flat text only |

### Integration Points

- Show quality indicator in search results
- Filter search by minimum quality
- Highlight low-quality sources in status

```bash
# Search with quality filter
ragd search "query" --min-quality 0.8

# Show quality in results
ragd search "query" --show-quality
```

## Implementation Tasks

- [ ] Define QualityScore dataclass
- [ ] Implement extraction confidence scoring
- [ ] Implement text completeness scoring
- [ ] Implement formatting quality scoring
- [ ] Store quality scores in chunk metadata
- [ ] Add quality display to search results
- [ ] Add `--min-quality` filter to search
- [ ] Add quality summary to `ragd status`
- [ ] Write unit tests
- [ ] Write integration tests

## Success Criteria

- [ ] All indexed chunks have quality scores
- [ ] Quality scores reflect actual content quality
- [ ] Search results can be filtered by quality
- [ ] Low-quality sources clearly indicated
- [ ] Tests verify scoring accuracy

## Dependencies

- F-100: New File Type Support (completed)
- F-101: Smart Chunking v2 (completed)

## Technical Notes

### OCR Quality Detection

For OCR-processed documents:
- Use confidence scores from OCR engine
- Check for common OCR errors (l/1, O/0)
- Detect garbled text patterns

### Validation

Quality scores should be validated:
- Compare against known-good documents
- Calibrate thresholds empirically
- Allow user override for trusted sources

## Related Documentation

- [F-100 New File Types](../completed/F-100-new-file-types.md)
- [F-101 Smart Chunking v2](../completed/F-101-smart-chunking-v2.md)
- [v0.9.6 Milestone](../../milestones/v0.9.6.md)

