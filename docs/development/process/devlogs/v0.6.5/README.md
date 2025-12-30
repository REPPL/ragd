# Devlog: v0.6.5 Polish & Stability

**Version:** v0.6.5
**Status:** Backfilled 2025-12-03

---

## Summary

Polish release focusing on CLI visual improvements, configuration validation, RAGAS evaluation metrics, and user-friendly error handling.

## Key Decisions

### RAGAS Evaluation (F-076)

Implemented LLM-dependent evaluation metrics:
- Faithfulness score (answer grounded in context)
- Answer relevance (response matches query)
- Context utilisation (how well context is used)

### Configuration Validation

- Pydantic v2 validation for all config
- User-friendly error messages
- Sensible defaults for all options

### Visual Polish

- Rich console improvements
- Progress bars for long operations
- Colour-coded output for status

## Challenges

1. **RAGAS metrics**: Require LLM calls, added latency
2. **Error messages**: Balancing detail vs clarity
3. **Backward compatibility**: New config without breaking old

## Why a Patch Release?

v0.6.5 was a "polish" release between major features:
- Too substantial for v0.6.1
- Not enough new functionality for v0.7.0
- Focused on quality-of-life improvements

## Lessons Learned

- Polish releases are valuable for UX
- Evaluation metrics help track quality over time
- Good error messages reduce support burden

---

**Note:** This devlog was created retroactively to establish documentation consistency.
