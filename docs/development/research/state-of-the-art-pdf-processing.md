# State-of-the-Art PDF Processing for RAG Systems

Cutting-edge techniques for processing difficult/messy PDFs in RAG pipelines.

## Executive Summary

Processing "messy" PDFs—scanned documents, complex layouts, tables, multi-column text, and poor-quality images—remains one of the most challenging problems in document understanding. Recent advances (2024-2025) introduce two paradigm shifts:

1. **Vision-first approaches** that bypass OCR entirely (ColPali, ColQwen2)
2. **Hybrid document understanding** combining layout analysis with structured extraction (Docling, SmolDocling)

The key insight from [OHRBench](https://github.com/opendatalab/OHR-Bench) (ICCV 2025) is that **OCR noise cascades through RAG systems**, reducing accuracy by up to 50%. This informs our approach: prioritise document understanding over raw text extraction.

---

## The OCR Problem: OHRBench Findings

**What OHRBench Discovered:**

The [OCR Hinders RAG paper](https://arxiv.org/abs/2412.02592) (Zhang et al., Dec 2024) introduces the first benchmark specifically measuring OCR's impact on RAG systems.

**Two Types of OCR Noise:**

| Noise Type | Description | Impact |
|------------|-------------|--------|
| **Semantic Noise** | Misspellings, misrecognised characters, symbol errors | Reduces retrieval accuracy by ~50% |
| **Formatting Noise** | Disrupted structure (tables, formulas, reading order) | Affects tables/formulas most severely |

**Key Finding:** Even state-of-the-art OCR solutions show 14% F1-score degradation. No current OCR solution is sufficient for building high-quality RAG knowledge bases from complex documents.

**Implication for ragd:** We must design for OCR failure—either by bypassing OCR entirely (vision approaches) or by using document understanding models that preserve structure.

---

## Approach 1: Vision-Based Retrieval (OCR-Free)

### ColPali / ColQwen2

**What It Is:**
- [ColPali](https://arxiv.org/abs/2407.01449) (Faysse et al., Jul 2024) embeds document page images directly using Vision Language Models
- Produces multi-vector representations (inspired by ColBERT) from visual patches
- Retrieves based on visual similarity—no text extraction required

**Why It Matters:**
- **Completely bypasses OCR** and its cascading errors
- Preserves visual layout, charts, tables as visual features
- 81.3 nDCG@5 on ViDoRe benchmark vs 65-75 for traditional pipelines

**Technical Approach:**
```
Page Image → Vision Encoder (PaliGemma-3B / Qwen2-VL) → Patch Embeddings → Multi-Vector Index
Query → Text Encoder → Query Embeddings → Late Interaction Retrieval
```

**Limitations:**
- High storage requirements (multi-vector per page)
- Computationally expensive at scale
- Cannot extract text for downstream processing

**Source:** [HuggingFace ColPali Blog](https://huggingface.co/blog/manu/colpali)

**Ecosystem Tools:**
- [ColiVara](https://github.com/tjmlabs/ColiVara) - REST API for ColPali retrieval
- [Byaldi](https://github.com/AnswerDotAI/byaldi) - RAGatouille-style library for ColPali
- [VARAG](https://github.com/adithya-s-k/VARAG) - Hybrid vision+text RAG pipeline

**Roadmap Position:** **v0.4 (Multi-modal)** or experimental v0.2 enhancement
- Best for image-heavy documents (slides, diagrams, infographics)
- Consider as fallback when text extraction fails

---

## Approach 2: Hybrid Document Understanding

### Docling (IBM Research)

**What It Is:**
- [Docling](https://github.com/docling-project/docling) is IBM's open-source document conversion toolkit
- Uses specialised AI models: DocLayNet (layout) + TableFormer (tables)
- Outputs structured JSON/Markdown preserving document hierarchy

**Why It Matters:**
- **Sidesteps traditional OCR** when possible (uses computer vision for layout)
- Processed 2.1M PDFs from Common Crawl for Granite training
- 97.9% cell accuracy on table extraction
- Integrates directly with LlamaIndex and LangChain

**Technical Approach:**
```
PDF → Layout Analysis (DocLayNet) → Element Detection
                                        ↓
    [Text Blocks] [Tables] [Figures] [Formulas] [Code]
           ↓          ↓
    Direct Extract  TableFormer → HTML/Markdown Table
           ↓
    Structured Output (JSON/Markdown) → RAG Pipeline
```

**Key Features:**
- Multi-format support: PDF, DOCX, PPTX, XLSX, HTML, images
- Reading order detection (critical for multi-column)
- Formula recognition
- Code block detection

**Source:** [IBM Research Blog](https://research.ibm.com/blog/docling-generative-AI), [Docling GitHub](https://github.com/docling-project/docling)

**Roadmap Position:** **v0.2 (Core PDF Processing)**
- Primary recommendation for ragd's messy PDF pipeline
- MIT licensed, production-ready
- LF AI & Data Foundation hosted

### Granite-Docling / SmolDocling

**What It Is:**
- [SmolDocling](https://arxiv.org/abs/2503.11576) (Nassar et al., Mar 2025) - 256M parameter document understanding model
- Holistic document understanding vs character-by-character OCR
- Outputs structured data directly

**Why It Matters:**
- Better accuracy than models 27x larger
- 28x less memory, 0.35s per page
- Dramatically improves downstream RAG performance

**Roadmap Position:** Evaluate alongside Docling for v0.2

---

## Approach 3: Traditional OCR (When Necessary)

For truly scanned documents where vision approaches are insufficient:

### OCR Engine Comparison (2024-2025)

| Engine | Confidence Score | Best For | Notes |
|--------|-----------------|----------|-------|
| **PaddleOCR** | 0.93 | Complex layouts, multi-language | Highest accuracy, active development |
| **Tesseract** | 0.89 | Simple layouts, Tamil/Hindi/Malayalam | Free, well-established, CPU-friendly |
| **EasyOCR** | 0.85 | Scene text, GPU environments | Balance of ease and accuracy |
| **Surya** | N/A (new) | 90+ languages, line-level detection | Outperforms Tesseract on speed/accuracy |

**Source:** [OCR Comparison Study](https://toon-beerten.medium.com/ocr-comparison-tesseract-versus-easyocr-vs-paddleocr-vs-mmocr-a362d9c79e66)

**Recommendation for ragd:**
1. **Primary:** PaddleOCR for scanned document fallback
2. **Alternative:** Surya for lighter deployments
3. **Avoid:** Tesseract alone for complex documents

### Mistral OCR (Commercial Option)

**What It Is:**
- [Mistral OCR](https://mistral.ai/news/mistral-ocr) (launched early 2025)
- Multimodal document understanding (not just text extraction)
- Handles LaTeX, tables, complex layouts

**Performance:**
- 94.89% overall accuracy (vs GPT-4o 89.77%, Gemini-1.5-Pro 89.92%)
- Best-in-class for mathematical expressions

**Roadmap Position:** Optional commercial tier for ragd users requiring highest accuracy

---

## Approach 4: Python Extraction Libraries

For well-formed PDFs (not scanned), direct extraction often outperforms OCR:

### PyMuPDF4LLM

**What It Is:**
- [PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) - extension of PyMuPDF for LLM/RAG workflows
- Direct PDF text extraction with structure preservation
- Outputs GitHub-compatible Markdown

**Why It Matters:**
- **0.12s processing** (vs 11.3s for marker-pdf)
- Multi-column layout support with correct reading order
- Header detection via font size → proper Markdown hierarchy
- Page chunking support (`page_chunks=True`)

**Best For:**
- Digital-native PDFs (not scanned)
- Speed-critical pipelines
- Documents with clear text layers

**Source:** [PyMuPDF RAG Documentation](https://pymupdf.readthedocs.io/en/latest/rag.html)

### Unstructured.io

**What It Is:**
- [Unstructured](https://docs.unstructured.io/) - comprehensive document processing platform
- Element-based chunking (title-to-title) vs token-based
- Chipper model for visual element detection

**Why It Matters:**
- Semantic chunking improves RAG retrieval
- Handles 10+ document formats
- SaaS and self-hosted options

**Best For:**
- Enterprise RAG pipelines
- Multi-format document processing
- When semantic chunking is critical

**Source:** [Unstructured Blog](https://unstructured.io/blog/unstructured-s-preprocessing-pipelines-enable-enhanced-rag-performance)

---

## Recommended Architecture for ragd v0.2

Based on this research, the recommended pipeline for UC-004 (Process Messy PDFs):

```
Input PDF
    ↓
┌─────────────────────────────────────────────────┐
│ Quality Detection (F-019?)                      │
│  - Is PDF digital-native or scanned?            │
│  - Does it have text layer?                     │
│  - Complexity score (tables, multi-column, etc) │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Route by Quality                                │
│                                                 │
│  Digital + Simple → PyMuPDF4LLM (fast path)     │
│  Digital + Complex → Docling (structure-aware)  │
│  Scanned → Docling + PaddleOCR fallback         │
│  Image-heavy → ColPali (vision retrieval)       │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Structured Output                               │
│  - Markdown with preserved structure            │
│  - Tables as HTML/Markdown                      │
│  - Metadata (page numbers, sections)            │
└─────────────────────────────────────────────────┘
    ↓
Standard RAG Pipeline (v0.1)
```

### Proposed v0.2 Features

| Feature ID | Name | Description |
|------------|------|-------------|
| F-019 | PDF Quality Detection | Classify PDFs: digital/scanned, complexity score |
| F-020 | Docling Integration | Primary document understanding pipeline |
| F-021 | OCR Fallback Pipeline | PaddleOCR for scanned documents |
| F-022 | Table Extraction | Structured table → Markdown/HTML output |
| F-023 | Multi-Column Handling | Correct reading order for complex layouts |

---

## Key Takeaways

1. **OCR is not enough.** OHRBench proves that OCR errors cascade through RAG systems. Design for document understanding, not text extraction.

2. **Docling is the best starting point.** MIT-licensed, production-ready, integrates with existing RAG frameworks.

3. **Vision approaches are the future.** ColPali shows that bypassing text entirely can improve retrieval. Consider for v0.4 multi-modal support.

4. **Quality detection is critical.** Route documents through appropriate pipelines based on their characteristics.

5. **Table extraction deserves special attention.** TableFormer in Docling achieves 97.9% cell accuracy—use it.

---

## References

### Papers
- [OCR Hinders RAG (OHRBench)](https://arxiv.org/abs/2412.02592) - Zhang et al., Dec 2024
- [ColPali](https://arxiv.org/abs/2407.01449) - Faysse et al., Jul 2024
- [SmolDocling](https://arxiv.org/abs/2503.11576) - Nassar et al., Mar 2025

### Tools & Libraries
- [Docling](https://github.com/docling-project/docling) - IBM Research
- [PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Unstructured](https://docs.unstructured.io/)
- [ColPali/Byaldi](https://github.com/AnswerDotAI/byaldi)

### Benchmarks
- [OHRBench](https://github.com/opendatalab/OHR-Bench) - OCR impact on RAG
- [ViDoRe](https://huggingface.co/vidore) - Visual document retrieval
- [LangChain Table RAG Benchmark](https://blog.langchain.com/benchmarking-rag-on-tables/)

---

## Related Documentation

- [ADR-0019: PDF Processing](../decisions/adrs/0019-pdf-processing.md) - Library selection decision
- [State-of-the-Art RAG](./state-of-the-art-rag.md) - Advanced retrieval techniques
- [UC-004: Process Messy PDFs](../../use-cases/briefs/UC-004-process-messy-pdfs.md) - Use case brief
- [F-002: Text Extraction](../features/completed/F-002-text-extraction.md) - Basic extraction (v0.1)
- [F-025: PDF Quality Detection](../features/completed/F-025-pdf-quality-detection.md) - Quality routing
- [F-026: Docling Integration](../features/completed/F-026-docling-integration.md) - Primary processor

---

**Status**: Research complete, ready for v0.2 feature specification

