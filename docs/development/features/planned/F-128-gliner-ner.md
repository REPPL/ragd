# F-128: GLiNER Zero-Shot Entity Extraction

## Overview

**Research**: [State-of-the-Art NER](../../research/state-of-the-art-ner.md)
**ADR**: [ADR-0034: GLiNER Zero-Shot NER](../../decisions/adrs/0034-gliner-zero-shot-ner.md)
**Milestone**: [v1.1.0](../../milestones/v1.1.0.md)
**Priority**: P2

## Problem Statement

Users need to extract **custom entity types** from documents without training models:

1. Domain-specific entities (legal: STATUTE, CASE_NUMBER; medical: DISEASE, DRUG)
2. Project-specific entities (internal terminology, custom taxonomies)
3. Exploratory analysis (discovering entities in new document collections)

Current limitations:
- spaCy is restricted to predefined entity types (PERSON, ORG, GPE, DATE, etc.)
- Pattern-based extraction requires manual rule maintenance
- LLM-based extraction is slow and expensive for bulk processing

## Design Approach

### Integration Strategy

Add GLiNER as **Tier 3** in the entity extraction pipeline:

```
Document Text
    │
    ▼
Tier 1: Pattern-based (always)
    │ emails, URLs, dates, codes
    ▼
Tier 2: spaCy NER (standard entities)
    │ PERSON, ORG, GPE, DATE, MONEY
    ▼
Tier 3: GLiNER (custom entities) ← NEW
    │ User-specified types
    ▼
Entity Deduplication & Storage
```

### Architecture

```python
class GlinerEntityExtractor:
    """Zero-shot entity extraction using GLiNER."""

    def __init__(
        self,
        model: str = "urchade/gliner_medium-v2.1",
        threshold: float = 0.5,
    ):
        self._model = None
        self._model_name = model
        self._threshold = threshold

    def _ensure_model(self) -> GLiNER:
        """Lazy-load model on first use."""
        if self._model is None:
            from gliner import GLiNER
            self._model = GLiNER.from_pretrained(self._model_name)
        return self._model

    def extract(
        self,
        text: str,
        entity_types: list[str],
        threshold: float | None = None,
    ) -> list[Entity]:
        """Extract entities of specified types."""
        model = self._ensure_model()
        results = model.predict_entities(
            text,
            entity_types,
            threshold=threshold or self._threshold,
        )
        return [
            Entity(
                text=r["text"],
                type=r["label"],
                start=r["start"],
                end=r["end"],
                confidence=r["score"],
                source="gliner",
            )
            for r in results
        ]

    def extract_batch(
        self,
        texts: list[str],
        entity_types: list[str],
    ) -> list[list[Entity]]:
        """Batch extraction for efficiency."""
        model = self._ensure_model()
        # GLiNER supports batch prediction
        ...
```

### CLI Integration

```bash
# Extract custom entity types
ragd entities extract document.pdf --types "TECHNOLOGY,CONCEPT,METHOD"

# List extracted entities with custom types
ragd entities list --type TECHNOLOGY

# Search documents by custom entity
ragd search "RAG systems" --entity-type CONCEPT
```

### Configuration

```yaml
# ~/.ragd/config.yaml
entity_extraction:
  # Default entity types to extract
  default_types:
    - PERSON
    - ORG
    - GPE
    - DATE

  # Custom types for GLiNER (empty = disabled)
  custom_types:
    - TECHNOLOGY
    - CONCEPT
    - METHOD

  # GLiNER configuration
  gliner:
    enabled: true
    model: "urchade/gliner_medium-v2.1"
    threshold: 0.5
    # Only load when custom_types requested
    lazy_load: true
```

## Implementation Tasks

- [ ] Add `gliner` as optional dependency in pyproject.toml
- [ ] Create `GlinerEntityExtractor` class in `src/ragd/knowledge/entities.py`
- [ ] Integrate into `HybridEntityExtractor` as Tier 3
- [ ] Add CLI commands for custom entity extraction
- [ ] Add configuration options for GLiNER model selection
- [ ] Write unit tests with mocked GLiNER
- [ ] Write integration tests with real model
- [ ] Update documentation with custom entity examples

## Success Criteria

- [ ] Users can extract arbitrary entity types without training
- [ ] GLiNER model lazy-loads only when custom types requested
- [ ] Extraction speed < 500ms per document for medium model
- [ ] F1 score > 85% on test documents with custom entity types
- [ ] No impact on users who don't use GLiNER (optional dependency)

## Dependencies

- **gliner >= 0.2.0** (optional dependency)
- PyTorch (already present via sentence-transformers)

## Model Options

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `gliner_small-v2.1` | ~200MB | Fastest | Good | Resource-constrained |
| `gliner_medium-v2.1` | ~400MB | Fast | Better | **Default** |
| `gliner_large-v2.1` | ~800MB | Medium | Best | Maximum accuracy |
| `gliner_multi-v2.1` | ~400MB | Fast | Good | Multilingual |
| `gliner_multi_pii-v1` | ~400MB | Fast | Good | PII detection |

---

## Related Documentation

- [State-of-the-Art NER](../../research/state-of-the-art-ner.md) - Research context
- [ADR-0034: GLiNER Zero-Shot NER](../../decisions/adrs/0034-gliner-zero-shot-ner.md) - Architecture decision
- [NLP Library Integration](../../research/nlp-library-integration.md) - Existing NER patterns
- [F-022: Knowledge Graph Integration](../completed/F-022-knowledge-graph.md) - Entity storage

---

**Status**: Planned
