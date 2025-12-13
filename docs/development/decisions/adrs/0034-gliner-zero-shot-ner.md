# ADR-0034: GLiNER for Zero-Shot Named Entity Recognition

## Status

Accepted

## Context

ragd's current entity extraction uses two approaches:

1. **Pattern-based extraction** (`PatternEntityExtractor`) - regex patterns for technologies, concepts, organisations
2. **spaCy NER** (`SpacyEntityExtractor`) - ML-based extraction for standard entity types (PERSON, ORG, GPE, DATE, etc.)

Both approaches have limitations:
- Pattern-based extraction requires manual rule maintenance
- spaCy is limited to predefined entity types (cannot extract custom types like "TECHNOLOGY", "CONCEPT", "METHOD" without fine-tuning)

Users need the ability to extract **arbitrary entity types** without training custom models. Use cases include:
- Domain-specific entities (legal: STATUTE, CASE_NUMBER; medical: DISEASE, DRUG)
- Project-specific entities (custom taxonomies, internal terminology)
- Exploratory analysis (discovering entity types in new document collections)

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **GLiNER** | Fast (200-800MB), zero-shot, Apache 2.0, NAACL 2024 | New dependency |
| **UniversalNER** | Higher accuracy | 7B params, slow, resource-intensive |
| **GoLLIE** | Guidelines support, relations | 7B params, complex setup |
| **LLM-based** | Most flexible | Slow, expensive, requires API/large model |
| **Fine-tune spaCy** | Well-integrated | Requires training data per entity type |

## Decision

Adopt **GLiNER** as the zero-shot NER backend for custom entity extraction.

## Rationale

1. **Speed/Size Trade-off**: GLiNER uses bidirectional transformers (BERT-like) for parallel entity extraction, achieving near-LLM accuracy at 200-800MB model size vs 7B+ for alternatives.

2. **Zero-Shot Capability**: Users specify entity types at inference time without training. Extract ["TECHNOLOGY", "CONCEPT", "METRIC"] from any document immediately.

3. **Benchmark Performance**: GLiNER outperforms ChatGPT in zero-shot NER benchmarks (NAACL 2024). Fine-tuned GLiNER achieves 93.4% F1 vs 87% baseline.

4. **Practical Deployment**: Runs on CPU (slower) or GPU, local-first aligned. Apache 2.0 licence permits commercial use.

5. **Complements Existing Stack**: GLiNER handles custom types; spaCy continues handling standard types (PERSON, ORG, DATE). Tiered approach optimises cost/accuracy.

6. **Optional Dependency**: GLiNER is an optional dependency. Users who don't need zero-shot extraction use the existing spaCy/pattern pipeline without additional installation.

## Consequences

### Positive

- Zero-shot extraction of arbitrary entity types
- No fine-tuning required for new entity types
- State-of-the-art accuracy for zero-shot NER
- Local-first (no API calls)
- Optional dependency (doesn't increase base installation size)

### Negative

- New dependency (~200-800MB model download on first use)
- Additional memory footprint when loaded (~400MB for medium model)
- Requires PyTorch (already a dependency via sentence-transformers)

### Mitigations

- Lazy-load GLiNER model only when custom entity types requested
- Default to spaCy for standard entity types (no GLiNER overhead)
- Cache model in `~/.ragd/models/` alongside other models
- Provide clear documentation on when to use GLiNER vs spaCy

## Implementation Notes

**Integration Pattern:**

```python
from gliner import GLiNER

class GlinerEntityExtractor:
    """Zero-shot entity extraction using GLiNER."""

    def __init__(self, model: str = "urchade/gliner_medium-v2.1"):
        self._model = None
        self._model_name = model

    def _ensure_model(self) -> GLiNER:
        if self._model is None:
            self._model = GLiNER.from_pretrained(self._model_name)
        return self._model

    def extract(
        self,
        text: str,
        entity_types: list[str],
        threshold: float = 0.5,
    ) -> list[Entity]:
        model = self._ensure_model()
        results = model.predict_entities(text, entity_types, threshold=threshold)
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
```

**Tiered Extraction Pipeline:**

1. **Tier 1**: Pattern-based (emails, URLs, dates) - always enabled
2. **Tier 2**: spaCy (PERSON, ORG, GPE, DATE, etc.) - standard entities
3. **Tier 3**: GLiNER (custom types) - when user specifies custom entity types
4. **Tier 4**: LLM (optional) - complex/ambiguous cases

**Available Models:**

| Model | Size | Use Case |
|-------|------|----------|
| `gliner_small-v2.1` | ~200MB | Resource-constrained |
| `gliner_medium-v2.1` | ~400MB | Default, balanced |
| `gliner_large-v2.1` | ~800MB | Best accuracy |
| `gliner_multi-v2.1` | ~400MB | Multilingual |
| `gliner_multi_pii-v1` | ~400MB | PII detection |

---

## Related Documentation

- [State-of-the-Art NER](../../research/state-of-the-art-ner.md) - Research context
- [F-128: GLiNER NER Integration](../../features/planned/F-128-gliner-ner.md) - Feature specification
- [NLP Library Integration](../../research/nlp-library-integration.md) - Existing NER integration

---

**Decided**: December 2024
