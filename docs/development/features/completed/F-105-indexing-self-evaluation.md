# F-105: Indexing Self-Evaluation

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Indexing quality issues are discovered only when search fails. Need proactive quality monitoring.

## Design Approach

Self-evaluation system that compares source to indexed content and reports quality metrics.

### Evaluation Metrics
- **Completeness** - Text coverage vs source
- **Accuracy** - Character-level comparison
- **Structure** - Headers, lists preserved
- **Metadata** - Title, author extracted

### CLI Usage
```bash
# Evaluate indexing quality
ragd index --evaluate ~/Documents/

# Generate detailed report
ragd quality report

# Compare source to indexed
ragd quality compare doc-123
```

## Implementation Tasks

- [ ] Implement source-to-index comparison
- [ ] Create completeness metrics
- [ ] Create structure preservation metrics
- [ ] Add --evaluate flag to index command
- [ ] Create quality report command
- [ ] Store evaluation results

## Success Criteria

- [ ] Completeness score calculated
- [ ] Structure preservation measured
- [ ] Quality reports generated

## Dependencies

- v0.8.7 (CLI Polish)

## Related Documentation

- [F-115: Source Quality Scoring](./F-115-source-quality-scoring.md)
- [v0.9.6 Implementation](../../implementation/v0.9.6.md)

---

**Status**: Completed
