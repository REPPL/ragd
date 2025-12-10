# F-056: Specialised Task Models

## Overview

**Research**: [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md)
**ADR**: [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md)
**Milestone**: v1.0+
**Priority**: P3

## Problem Statement

General-purpose LLMs underperform on structured extraction tasks compared to fine-tuned Small Language Models (SLMs). Tasks like entity extraction, classification, and sentiment analysis benefit from specialised models that:

1. Generate structured outputs (JSON, Python dicts)
2. Run faster than general LLMs
3. Achieve higher accuracy for their specific task
4. Can run on CPU without GPU requirements

LLMWare's SLIM models demonstrate this pattern with 1-3B parameter models that outperform larger models on structured tasks.

## Design Approach

### Use Cases

1. **Auto-classification on ingest**: Automatically tag/categorise documents
2. **Entity extraction**: Extract named entities (people, organisations, dates)
3. **Sentiment analysis**: Analyse document sentiment for prioritisation
4. **Intent detection**: Classify query intent for routing

### Architecture

```
Document/Query
    |
    v
+------------------------------------------+
| Task Model Router                         |
|   - Detect required task type             |
|   - Load appropriate SLIM model           |
+------------------------------------------+
    |
    v
+------------------------------------------+
| Specialised Model (SLIM-style)            |
|   - slim-ner-tool                         |
|   - slim-intent-tool                      |
|   - slim-sentiment-tool                   |
+------------------------------------------+
    |
    v
Structured Output (JSON)
```

### Configuration Schema

```yaml
# ~/.ragd/config.yaml

task_models:
  # Classification models
  classification:
    enabled: false
    model: slim-intent-tool       # LLMWare SLIM
    on_ingest: false              # Auto-classify on document ingest

  # Entity extraction
  extraction:
    enabled: false
    model: slim-ner-tool
    entity_types:
      - PERSON
      - ORG
      - DATE
      - LOCATION

  # Sentiment analysis
  sentiment:
    enabled: false
    model: slim-sentiment-tool

  # Custom extraction
  custom:
    enabled: false
    model: slim-extract-tool
    keys: []                      # Custom keys to extract
```

### CLI Commands

```bash
# Classification
ragd ingest doc.pdf --auto-classify    # Classify on ingest
ragd classify doc.pdf                   # Standalone classification

# Entity extraction
ragd extract entities doc.pdf           # Extract NER entities
ragd extract entities --types PERSON,ORG doc.pdf

# Sentiment
ragd analyse sentiment doc.pdf

# Query intent (for debugging routing)
ragd debug intent "Show me documents about Python"
```

## Implementation Tasks

- [ ] Research SLIM model integration options (Ollama, direct GGUF, llmware)
- [ ] Create TaskModelClient abstract class
- [ ] Implement SLIM model loader (CPU-optimised)
- [ ] Add `--auto-classify` flag to ingest command
- [ ] Create `ragd extract entities` command
- [ ] Create `ragd classify` command
- [ ] Create `ragd analyse sentiment` command
- [ ] Store extracted entities in document metadata
- [ ] Add entity search capability (`ragd search --entity "OpenAI"`)
- [ ] Write unit tests for structured output parsing
- [ ] Write integration tests for SLIM models
- [ ] Document model download and setup

## Success Criteria

- [ ] SLIM-style models can be loaded and run
- [ ] Structured JSON output is correctly parsed
- [ ] Auto-classification works on ingest
- [ ] Entity extraction populates document metadata
- [ ] Sentiment analysis returns valid scores
- [ ] Models run on CPU without GPU
- [ ] Documentation covers model setup

## Dependencies

- F-055: Multi-Model Orchestration (model registry)
- F-030: Metadata Extraction (metadata storage)
- SLIM models (download separately)

## Technical Notes

### SLIM Model Integration

SLIM models are available in two formats:
1. **PyTorch/Huggingface FP16** - Full precision
2. **GGUF Quantised "tools"** - CPU-optimised (recommended)

```python
# Option A: Via llmware library
from llmware.models import ModelCatalog

ner_model = ModelCatalog().load_model("slim-ner-tool")
result = ner_model.function_call(text)
# Returns: {"entities": [{"text": "OpenAI", "type": "ORG"}, ...]}

# Option B: Direct GGUF loading (no llmware dependency)
# Use llama-cpp-python for inference
```

### Structured Output Parsing

```python
from dataclasses import dataclass

@dataclass
class ExtractedEntity:
    text: str
    entity_type: str
    start: int | None = None
    end: int | None = None
    confidence: float = 1.0

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    sub_categories: list[str] = None

class StructuredOutputParser:
    """Parse SLIM model outputs."""

    def parse_ner(self, output: str) -> list[ExtractedEntity]:
        """Parse NER model output."""
        data = json.loads(output)
        return [
            ExtractedEntity(
                text=e["text"],
                entity_type=e["type"],
                confidence=e.get("confidence", 1.0)
            )
            for e in data.get("entities", [])
        ]

    def parse_classification(self, output: str) -> ClassificationResult:
        """Parse classification model output."""
        data = json.loads(output)
        return ClassificationResult(
            category=data["category"],
            confidence=data.get("confidence", 1.0)
        )
```

### Auto-Classification on Ingest

```python
class IngestPipeline:
    async def ingest_with_classification(
        self,
        document: Document,
        auto_classify: bool = False
    ) -> IngestResult:
        # Standard ingestion
        result = await self.ingest(document)

        # Optional auto-classification
        if auto_classify and self.config.task_models.classification.enabled:
            classification = await self.classify(document.text[:2000])
            result.metadata["auto_category"] = classification.category
            result.metadata["auto_confidence"] = classification.confidence

        return result
```

### CLI Output Examples

```bash
$ ragd extract entities report.pdf

Extracted Entities
------------------
PERSON:       John Smith, Jane Doe
ORG:          OpenAI, Anthropic, Google
DATE:         2024-01-15, March 2025
LOCATION:     San Francisco, London

Total: 8 entities extracted


$ ragd classify report.pdf

Classification Result
---------------------
Category:     Technical Documentation
Confidence:   0.92
Sub-categories:
  - API Reference (0.78)
  - Tutorial (0.45)


$ ragd analyse sentiment feedback.txt

Sentiment Analysis
------------------
Overall:      Positive (0.73)
Breakdown:
  - Introduction: Neutral (0.52)
  - Main Content: Positive (0.81)
  - Conclusion: Very Positive (0.89)
```

## Related Documentation

- [State-of-the-Art Multi-Model RAG](../../research/state-of-the-art-multi-model-rag.md) - SLIM research
- [ADR-0026: Multi-Model Architecture](../../decisions/adrs/0026-multi-model-architecture.md) - Decision
- [F-055: Multi-Model Orchestration](../completed/F-055-multi-model-orchestration.md) - Model registry
- [F-030: Metadata Extraction](../completed/F-030-metadata-extraction.md) - Metadata storage
- [LLMWare SLIM Models](https://llmware.ai/resources/slims-small-specialized-models-function-calling-and-multi-model-agents) - External

---
