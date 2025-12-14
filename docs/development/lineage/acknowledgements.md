# Research Acknowledgements

This document acknowledges the research papers, projects, and sources that inform ragd's implementation.

## Document Processing

### Docling

**Source**: Docling - Document Processing Toolkit
**Organisation**: IBM Research
**Link**: https://github.com/DS4SD/docling
**Licence**: MIT
**How Used**: State-of-the-art document parsing for PDFs with complex layouts, tables, and figures
**Milestone**: v0.2.0

### PaddleOCR

**Source**: PaddleOCR
**Organisation**: PaddlePaddle (Baidu)
**Link**: https://github.com/PaddlePaddle/PaddleOCR
**Licence**: Apache 2.0
**How Used**: Primary OCR engine for scanned document text extraction
**Milestone**: v0.2.0

### EasyOCR

**Source**: EasyOCR
**Creator**: JaidedAI
**Link**: https://github.com/JaidedAI/EasyOCR
**Licence**: Apache 2.0
**How Used**: Fallback OCR engine for cross-platform compatibility
**Milestone**: v0.2.0

---

## Retrieval & Search

### HyDE (Hypothetical Document Embeddings)

**Source**: Precise Zero-Shot Dense Retrieval without Relevance Labels
**Authors**: Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan
**Link**: https://arxiv.org/abs/2212.10496
**Year**: 2022
**How Used**: Generate hypothetical documents from queries for improved retrieval
**Milestone**: v0.3.0

### ColPali

**Source**: ColPali: Efficient Document Retrieval with Vision Language Models
**Organisation**: Illuin Technology
**Link**: https://github.com/illuin-tech/colpali
**Licence**: MIT
**How Used**: Vision embeddings for image-based document retrieval
**Milestone**: v0.4.0

---

## Storage & Efficiency

### LEANN (Lightweight Embedding-Aware Neural Network)

**Source**: LEANN: Lightweight Embedding-Aware Neural Network for Efficient Vector Search
**Authors**: Yichuan Wang et al.
**Link**: https://arxiv.org/abs/2506.08276
**Repository**: https://github.com/yichuan-w/LEANN
**Licence**: MIT
**How Used**: Optional vector storage backend with 97% storage savings via graph-based selective recomputation
**Milestone**: v0.6.0 (optional backend)

### ChromaDB

**Source**: Chroma - The AI-native open-source embedding database
**Organisation**: Chroma
**Link**: https://github.com/chroma-core/chroma
**Licence**: Apache 2.0
**How Used**: Default vector storage backend
**Milestone**: v0.1.0

---

## Knowledge Graphs

### Kuzu

**Source**: Kuzu - Embeddable Property Graph Database
**Organisation**: Kuzu Inc
**Link**: https://github.com/kuzudb/kuzu
**Licence**: MIT
**How Used**: Embedded graph database for knowledge graphs and temporal reasoning
**Milestone**: v0.8.0

---

## Frameworks & Libraries

### Typer

**Source**: Typer - Build great CLIs with Python
**Creator**: Sebastián Ramírez
**Link**: https://github.com/tiangolo/typer
**Licence**: MIT
**How Used**: CLI framework for ragd commands
**Milestone**: v0.1.0

### Rich

**Source**: Rich - Python library for rich text and beautiful formatting
**Creator**: Will McGugan
**Link**: https://github.com/Textualize/rich
**Licence**: MIT
**How Used**: Terminal output formatting, progress bars, tables
**Milestone**: v0.1.0

### Sentence Transformers

**Source**: Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks
**Authors**: Nils Reimers, Iryna Gurevych
**Link**: https://github.com/UKPLab/sentence-transformers
**Paper**: https://arxiv.org/abs/1908.10084
**Licence**: Apache 2.0
**How Used**: Local text embedding generation
**Milestone**: v0.1.0

### Ollama

**Source**: Ollama - Run large language models locally
**Organisation**: Ollama
**Link**: https://github.com/ollama/ollama
**Licence**: MIT
**How Used**: Local LLM inference for chat and generation
**Milestone**: v0.5.0

---

## Predecessor Project

### ragged

**Source**: ragged - Privacy-first RAG system
**Versions Analysed**: v0.1-v0.6 (implemented), v0.7-v2.0 (planned)
**How Used**: Feature set, architecture patterns, lessons learned
**Relationship**: ragd is a clean rewrite incorporating ragged's learnings

---

## Adding New Acknowledgements

When integrating new research or projects, add an entry following this template:

```markdown
### [Feature/Technology Name]

**Source**: [Paper/Project Name]
**Creator/Organisation**: [Creator or Organisation]
**Link**: [URL to paper or repository]
**Licence**: [Licence type]
**How Used**: [Brief description of how ragd uses this]
**Milestone**: [Version where integrated]
```

## Licence Compatibility

All acknowledged sources have licences compatible with ragd's open-source nature:
- MIT: Compatible
- Apache 2.0: Compatible
- BSD: Compatible

