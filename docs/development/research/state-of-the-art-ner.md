# State-of-the-Art Named Entity Recognition for Document Processing

> **Research Date:** December 2024
>
> This document surveys current best practices for extracting named entities from documents across formats (PDF, HTML, EPUB/Ebooks). The key insight is that **document NER is a two-stage problem**: (1) structure-preserving text extraction, then (2) entity recognition. Modern approaches increasingly blur this boundary with layout-aware models.

## Executive Summary

**Key Recommendations for ragd:**
1. **Hybrid NER Pipeline**: GLiNER (zero-shot) + spaCy (fast, reliable) + optional LLM (complex)
2. **Layout-Aware Processing**: Use Docling (already integrated) for PDFs to preserve structure
3. **HTML Extraction**: Trafilatura (already in dependencies) with selectolax fallback
4. **EPUB/Ebook**: EbookLib + BeautifulSoup pipeline
5. **Efficient Inference**: SpanMarker for fine-tuned domain-specific models

---

## Part 1: NER Architecture Landscape (2024-2025)

### Taxonomy of Modern NER Approaches

| Approach | Speed | Flexibility | Accuracy | Memory | Best For |
|----------|-------|-------------|----------|--------|----------|
| **spaCy (sm/trf)** | Fast | Limited types | High | Low | Standard entities (PERSON, ORG, GPE, DATE) |
| **GLiNER** | Fast | Any type (zero-shot) | High | ~200MB | Custom entities without training |
| **SpanMarker** | Fast | Fine-tunable | Very High | ~400MB | Domain-specific with training data |
| **UniversalNER** | Medium | Any type | Very High | ~7B params | Best zero-shot quality |
| **GoLLIE** | Slow | Any + relations | Excellent | ~7B params | Complex extraction with guidelines |
| **LLM (GPT-4/Claude)** | Slow | Unlimited | Excellent | API | Complex reasoning, few-shot |

### State-of-the-Art Performance (CoNLL-2003 Benchmark)

| Model | F1 Score | Notes |
|-------|----------|-------|
| XLM-RoBERTa (fine-tuned) | 98.0% | Highest reported |
| SpanMarker + xlm-roberta-large | 95.5% | With document context |
| GLiNER-large (fine-tuned) | 93.4% | After domain fine-tuning |
| BERT-large-cased (fine-tuned) | ~92.8% | Classic baseline |
| GPT-4 (zero-shot) | ~80-85% | Varies by prompt |

**Source:** [Recent Advances in NER Survey (2024)](https://arxiv.org/abs/2401.10825)

---

## Part 2: Zero-Shot NER Revolution

### GLiNER: The Practical Choice

[GLiNER](https://github.com/urchade/GLiNER) (NAACL 2024) uses bidirectional transformers to match entity types to text spans in latent space—avoiding slow LLM token generation.

**Key Advantages:**
- **Speed**: Parallel entity extraction (not sequential like LLMs)
- **Size**: 200MB-800MB vs 7B+ for LLMs
- **Flexibility**: Any entity type at inference time
- **Quality**: Outperforms ChatGPT in zero-shot NER benchmarks

**Available Models:**

| Model | Size | Licence | Use Case |
|-------|------|---------|----------|
| `gliner_small-v2.1` | ~200MB | Apache 2.0 | Resource-constrained |
| `gliner_medium-v2.1` | ~400MB | Apache 2.0 | Balanced |
| `gliner_large-v2.1` | ~800MB | Apache 2.0 | Best accuracy |
| `gliner_multi-v2.1` | ~400MB | Apache 2.0 | Multilingual |
| `gliner_multi_pii-v1` | ~400MB | Apache 2.0 | PII detection (6 languages) |
| `gliner_large_bio-v0.1` | ~800MB | Apache 2.0 | Biomedical |

**Usage Example:**

```python
from gliner import GLiNER

model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

text = "Apple Inc. announced a new iPhone at WWDC 2024 in Cupertino."
labels = ["company", "product", "event", "location"]

entities = model.predict_entities(text, labels, threshold=0.5)
# [{'text': 'Apple Inc.', 'label': 'company', 'score': 0.95}, ...]
```

### UniversalNER vs GLiNER

| Aspect | UniversalNER | GLiNER |
|--------|--------------|--------|
| Architecture | Auto-regressive (LLM) | Bidirectional encoder |
| Parameters | ~7B | ~200M-800M |
| Speed | Slow (token-by-token) | Fast (parallel) |
| Quality | Slightly higher | Near-equivalent |
| Deployment | Challenging | Easy (local CPU/GPU) |

**Recommendation for ragd:** Use **GLiNER** as primary zero-shot NER due to speed/size/quality trade-off. Reserve UniversalNER for highest-accuracy batch processing.

### GoLLIE: Guideline-Following Extraction

[GoLLIE](https://arxiv.org/abs/2310.03668) (ICLR 2024) uses annotation guidelines in prompts—entity types as Python classes with docstrings. Best for complex extraction where guidelines matter.

**When to Use GoLLIE:**
- Strict adherence to annotation guidelines required
- Entity definitions are nuanced/ambiguous
- Relation extraction alongside NER
- Sufficient compute resources available

### NuNER: Distillation Approach

[NuNER](https://aclanthology.org/2024.emnlp-main.660.pdf) (EMNLP 2024) pre-trains BERT on LLM-annotated multi-domain NER data. Only 155M parameters but competes with GPT-4 when fine-tuned with ~12 examples per entity type.

**Key Insight:** Distillation from large models into small, specialised encoders is highly effective for NER.

---

## Part 3: Document-Specific NER Approaches

### Layout-Aware Models

Traditional NER treats text as linear sequences, losing spatial information critical for documents (forms, tables, receipts).

**DocLLM (ACL 2024):**
- Layout-aware attention without expensive image encoders
- Uses bounding boxes to capture spatial relationships
- Infilling pre-training objective
- Outperforms on 14/16 document understanding benchmarks

**LayoutLMv3:**
- Combines text, layout, and image features
- Token classification head for NER on document images
- Position and layout embeddings for spatial awareness
- Pre-trained on large document corpus

**When to Use Layout-Aware Models:**
- Forms with labelled fields
- Tables with entity-containing cells
- Invoices, receipts, contracts
- Any document where position conveys meaning

**ragd Integration:**

Docling (already integrated) provides structured Markdown with layout preservation. For NER on form-like documents, consider:
1. Extract with Docling (structure-aware)
2. Apply GLiNER/spaCy to structured chunks
3. Use chunk metadata (section, table cell) for context

### PDF-Specific Challenges

| Challenge | Solution |
|-----------|----------|
| Layout vs reading order | Docling with DocLayNet |
| Tables | TableFormer (via Docling) |
| Scanned/OCR | PaddleOCR → NER on OCR text |
| Multi-column | Layout analysis before chunking |
| Headers/footers | Filter via layout classification |

### HTML Extraction for NER

**Best Tools (2024 Benchmarks):**

| Tool | F1 (mean) | Precision | Recall | Notes |
|------|-----------|-----------|--------|-------|
| Trafilatura | 0.937 | 0.978 | — | Best overall, near-perfect precision |
| Readability | 0.970* | High | 0.929 | Highest median score |
| Newspaper3k | >0.9 | >0.9 | >0.9 | Best for news articles |

*Median score

**Source:** [Sandia National Laboratories Report (2024)](https://www.osti.gov/servlets/purl/2429881)

**Recommended Pipeline:**

```python
# Tiered extraction approach
def extract_html_content(html: str) -> str:
    # 1. Fast, high precision
    from trafilatura import extract
    content = extract(html)
    if content and len(content) > 100:
        return content

    # 2. Fallback: reader-mode
    from readability import Document
    doc = Document(html)
    return doc.summary()
```

### EPUB/Ebook Extraction

EPUBs are ZIP files containing XHTML + metadata. Two approaches:

**1. EbookLib (Recommended):**

```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_epub_text(epub_path: str) -> tuple[str, dict]:
    book = epub.read_epub(epub_path)

    # Extract metadata
    metadata = {
        'title': book.get_metadata('DC', 'title'),
        'creator': book.get_metadata('DC', 'creator'),
        'language': book.get_metadata('DC', 'language'),
    }

    # Extract text from chapters
    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
        text = soup.get_text(separator='\n')
        chapters.append(text)

    return '\n\n'.join(chapters), metadata
```

**2. Apache Tika (Simpler but heavier):**

```python
from tika import parser
parsed = parser.from_file('book.epub')
text = parsed['content']
metadata = parsed['metadata']
```

**Comparison:**

| Tool | Pros | Cons |
|------|------|------|
| EbookLib | Lightweight, precise control | More code |
| Tika | Simple API, many formats | Java dependency, heavier |
| PyMuPDF | Fast, also handles PDFs | Less EPUB-specific features |

---

## Part 4: Efficient Inference & Production Deployment

### SpanMarker: Fine-Tunable Efficiency

[SpanMarker](https://github.com/tomaarsen/SpanMarkerNER) enables training powerful NER models on familiar encoders (BERT, RoBERTa, ELECTRA).

**Key Features:**
- Built on HuggingFace Transformers
- Supports IOB, IOB2, BIOES, BILOU schemes automatically
- Document-level context for improved accuracy
- 8-bit inference support
- Mixed precision training

**Performance Gains from Fine-Tuning:**

| Model | Before Fine-Tuning | After Fine-Tuning |
|-------|-------------------|-------------------|
| GLiNER-medium | 87.0% | 93.4% |
| SpanMarker | 47.0% | 90.1% |

**Cost Comparison:**

| Model | Hourly Cost | Relative Cost |
|-------|-------------|---------------|
| LLaMA 3.1-70B (GPU) | ~$8.00 | 80x |
| Compact models (GPU) | ~$0.50 | 5x |
| Compact models (CPU) | ~$0.10 | 1x |

**Source:** [HuggingFace CFM Case Study](https://huggingface.co/blog/cfm-case-study)

### Hybrid Pipeline Architecture (Recommended)

```
Document Input
      │
      ├─[PDF]──→ Docling (layout-aware) ─┐
      ├─[HTML]─→ Trafilatura ───────────┤
      ├─[EPUB]─→ EbookLib + BS4 ────────┤
      └─[Text]─→ Direct ────────────────┘
                      │
                      ▼
              Normalised Text + Structure Metadata
                      │
                      ▼
         ┌───────────────────────────────┐
         │     Entity Extraction Tier    │
         ├───────────────────────────────┤
         │ Tier 1: Pattern-based (fast)  │
         │   - Regex for emails, URLs    │
         │   - Date patterns             │
         │   - Known product codes       │
         ├───────────────────────────────┤
         │ Tier 2: spaCy (reliable)      │
         │   - PERSON, ORG, GPE, DATE    │
         │   - High precision standard   │
         ├───────────────────────────────┤
         │ Tier 3: GLiNER (flexible)     │
         │   - Custom entity types       │
         │   - Zero-shot capability      │
         ├───────────────────────────────┤
         │ Tier 4: LLM (optional)        │
         │   - Complex/ambiguous cases   │
         │   - Relation extraction       │
         └───────────────────────────────┘
                      │
                      ▼
              Entity Deduplication & Normalisation
                      │
                      ▼
              Storage (SQLite + Knowledge Graph)
```

### Entity Type Strategy

**Standard Types (spaCy - always extract):**
- PERSON, ORG, GPE (geo-political entity)
- DATE, TIME, MONEY, PERCENT
- PRODUCT, EVENT, WORK_OF_ART, LAW

**Custom Types (GLiNER - domain-specific):**
- TECHNOLOGY, CONCEPT, METHOD (technical docs)
- DISEASE, DRUG, GENE (biomedical)
- CASE_NUMBER, STATUTE, COURT (legal)
- METRIC, KPI, STRATEGY (business)

---

## Part 5: Best Practices Summary

### Do's

1. **Layer extraction methods**: Pattern → spaCy → GLiNER → LLM (escalating cost/complexity)
2. **Preserve document structure**: Use layout-aware extractors before NER
3. **Batch process with spaCy**: `nlp.pipe()` for 10-100x speedup on large corpora
4. **Cache entity models**: Lazy-load and reuse across documents
5. **Normalise entities**: Deduplicate "Apple", "Apple Inc.", "Apple Inc" → canonical form
6. **Store positions**: Keep character offsets for citation and highlighting
7. **Use document context**: SpanMarker's document-level context improves F1 by ~2-3%

### Don'ts

1. **Don't use LLMs for simple entities**: spaCy is 100x faster for PERSON/ORG/DATE
2. **Don't ignore layout**: Forms and tables need structure-aware extraction
3. **Don't fine-tune prematurely**: GLiNER zero-shot often sufficient; fine-tune only with enough data
4. **Don't extract from HTML directly**: Main content extraction first (Trafilatura)
5. **Don't assume OCR quality**: Verify extraction quality before NER on scanned docs

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Precision | >90% | Correct entities / Total extracted |
| Recall | >85% | Correct entities / Total in document |
| F1 Score | >87% | Harmonic mean |
| Latency | <100ms/page | Time for extraction + NER |
| Memory | <2GB | Model + document in memory |

---

## Part 6: Comparison with ragd's Current Implementation

### Already Implemented (v0.2-v0.3)

| Component | Status | Implementation |
|-----------|--------|----------------|
| spaCy NER | Implemented | `src/ragd/knowledge/entities.py` |
| Pattern extraction | Implemented | `PatternEntityExtractor` class |
| KeyBERT keywords | Implemented | `src/ragd/metadata/extractor.py` |
| Language detection | Implemented | langdetect/fast-langdetect |
| PDF extraction | Implemented | PyMuPDF + Docling |
| HTML extraction | Implemented | Trafilatura + selectolax |
| Knowledge graph | Implemented | SQLite-based (ADR-0031) |
| PII detection | Implemented | Presidio + spaCy + regex |

### Enhancement Opportunities

| Gap | Priority | Recommendation |
|-----|----------|----------------|
| GLiNER integration | High | Add for zero-shot custom entities |
| EPUB support | Medium | Add EbookLib extractor |
| SpanMarker fine-tuning | Low | For domain-specific deployments |
| Layout-aware NER | Low | LayoutLMv3 for form-heavy use cases |
| Entity normalisation | Medium | Canonical form mapping |
| Cross-document entity linking | Low | Entity disambiguation across corpus |

---

## References

### Papers

- [Recent Advances in NER Survey (2024)](https://arxiv.org/abs/2401.10825)
- [GLiNER (NAACL 2024)](https://aclanthology.org/2024.naacl-long.300.pdf)
- [UniversalNER (NAACL 2024)](https://aclanthology.org/2024.naacl-long.243.pdf)
- [GoLLIE (ICLR 2024)](https://arxiv.org/abs/2310.03668)
- [NuNER (EMNLP 2024)](https://aclanthology.org/2024.emnlp-main.660.pdf)
- [DocLLM (ACL 2024)](https://aclanthology.org/2024.acl-long.463/)
- [LayoutLLM (CVPR 2024)](https://arxiv.org/abs/2404.05225)

### Tools & Libraries

- [GLiNER GitHub](https://github.com/urchade/GLiNER)
- [SpanMarker](https://github.com/tomaarsen/SpanMarkerNER)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [EbookLib](https://github.com/aerkalov/ebooklib)
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities)

### Benchmarks

- [Papers with Code NER Leaderboard](https://paperswithcode.com/task/named-entity-recognition-ner/latest)
- [HuggingFace CFM Case Study](https://huggingface.co/blog/cfm-case-study)
- [Sandia MCE Evaluation (2024)](https://www.osti.gov/servlets/purl/2429881)
- [Trafilatura Evaluation](https://trafilatura.readthedocs.io/en/latest/evaluation.html)

---

## Related Documentation

- [NLP Library Integration Guide](./nlp-library-integration.md) - Implementation patterns for spaCy, KeyBERT, langdetect
- [State-of-the-Art Metadata](./state-of-the-art-metadata.md) - Metadata extraction research
- [State-of-the-Art Knowledge Graphs](./state-of-the-art-knowledge-graphs.md) - Entity extraction for graph construction
- [F-030: Metadata Extraction](../features/completed/F-030-metadata-extraction.md) - Current NER implementation
- [ADR-0034: GLiNER Zero-Shot NER](../decisions/adrs/0034-gliner-zero-shot-ner.md) - Architecture decision for GLiNER adoption

---

**Status**: Research complete
