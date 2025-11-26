# F-030: Metadata Extraction

## Overview

**Use Case**: [UC-005](../../../use-cases/briefs/UC-005-manage-metadata.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Manually entering metadata for every document is tedious and error-prone. Automatic extraction from document properties, content analysis, and NLP techniques dramatically improves metadata quality and coverage.

## Design Approach

Implement a multi-stage extraction pipeline: algorithmic methods (fast, free) for all documents, with optional LLM enhancement for high-value documents.

**Extraction Pipeline:**
```
Document Input
      ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Algorithmic Extraction (always, free)      │
│   - PDF properties (title, author, dates)           │
│   - File metadata (path, size, hash)                │
│   - Language detection (langdetect)                 │
│   - KeyBERT keywords                                │
│   - spaCy NER entities                              │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: LLM Enhancement (optional, configurable)   │
│   - Document summary                                │
│   - Document type classification                    │
│   - Questions each chunk answers                    │
└─────────────────────────────────────────────────────┘
      ↓
Merged Metadata → Storage
```

**Extraction Methods:**

| Field | Method | Cost |
|-------|--------|------|
| Title, author, dates | PDF properties | Free |
| Language | langdetect/fastText | Free |
| Keywords | KeyBERT | Low (local) |
| Entities | spaCy NER | Low (local) |
| Summary | LLM (optional) | Medium |
| Document type | LLM classification | Medium |

## Implementation Tasks

- [ ] Implement PDF properties extraction (PyMuPDF)
- [ ] Implement file system metadata extraction
- [ ] Integrate langdetect for language detection
- [ ] Integrate KeyBERT for keyword extraction
- [ ] Integrate spaCy for named entity recognition
- [ ] Create LLM extraction module (optional, uses Ollama)
- [ ] Implement extraction pipeline orchestrator
- [ ] Add configuration for enabling/disabling extraction stages
- [ ] Handle extraction failures gracefully

## Success Criteria

- [ ] PDF properties extracted automatically
- [ ] Keywords generated for all documents
- [ ] Named entities extracted (people, organisations, locations)
- [ ] Language detected with >95% accuracy
- [ ] LLM enhancement available but optional
- [ ] Extraction completes in <5s per document (algorithmic only)

## Dependencies

- [F-029: Metadata Storage](./F-029-metadata-storage.md) - Stores extracted metadata
- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Triggers extraction
- KeyBERT, spaCy, langdetect libraries

## Technical Notes

**PDF Properties Extraction:**
```python
import fitz  # PyMuPDF

doc = fitz.open("document.pdf")
metadata = doc.metadata
# Returns: title, author, subject, keywords, creator, producer, dates
```

**KeyBERT Keyword Extraction:**
```python
from keybert import KeyBERT

kw_model = KeyBERT()
keywords = kw_model.extract_keywords(
    doc_text,
    keyphrase_ngram_range=(1, 2),
    stop_words='english',
    top_n=10
)
# Returns: [("machine learning", 0.89), ("neural network", 0.85), ...]
```

**spaCy NER:**
```python
import spacy

nlp = spacy.load("en_core_web_sm")  # or en_core_web_trf for accuracy
doc = nlp(text)
entities = [(ent.text, ent.label_) for ent in doc.ents]
# Returns: [("Apple Inc.", "ORG"), ("Tim Cook", "PERSON"), ...]
```

**Configuration:**
```yaml
metadata:
  extraction:
    pdf_properties: true      # Always on
    language_detection: true  # Always on
    keybert_keywords: true    # Recommended
    spacy_ner: true           # Recommended
    llm_summary: false        # Optional, requires Ollama
    llm_classification: false # Optional, requires Ollama
```

## Related Documentation

- [State-of-the-Art Metadata](../../research/state-of-the-art-metadata.md)
- [KeyBERT GitHub](https://github.com/MaartenGr/KeyBERT)
- [F-029: Metadata Storage](./F-029-metadata-storage.md)

---

**Status**: Planned
