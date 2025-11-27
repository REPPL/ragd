# F-019: Multi-Modal Support

## Overview

**Research**: [State-of-the-Art Multi-Modal](../../research/state-of-the-art-multi-modal.md)
**Milestone**: v0.4
**Priority**: P1

## Problem Statement

Documents contain valuable visual information: diagrams, charts, screenshots, and images. Traditional RAG systems ignore this content, losing significant knowledge. Users should be able to search for and retrieve visual content as naturally as text.

## Design Approach

### Architecture

```
Document with Images
    ↓
Image Extraction (PyMuPDF/Docling)
    ↓
Vision Embedding (ColPali/ColQwen)
    ↓
Multi-Modal Vector Store
    ↓
Unified Search (text + images)
```

### Technologies

- **ColPali/ColQwen2**: Vision embeddings for images
- **PyMuPDF/Docling**: Image extraction from documents
- **ChromaDB**: Multi-modal collection support
- **Ollama LLaVA** (optional): Caption generation

### Query Modes

| Mode | Description |
|------|-------------|
| **Text → Text** | Standard semantic search |
| **Text → Image** | Find images matching description |
| **Image → Text** | Find text related to image |
| **Image → Image** | Find similar images |

## Implementation Tasks

- [ ] Add image extraction to ingestion pipeline
- [ ] Integrate ColPali/ColQwen for vision embeddings
- [ ] Create multi-modal ChromaDB collection
- [ ] Implement unified search across modalities
- [ ] Add image display in CLI (via Rich or external viewer)
- [ ] Implement optional caption generation
- [ ] Add image-specific metadata (dimensions, format)
- [ ] Write unit tests for image extraction
- [ ] Write integration tests for multi-modal search

## Success Criteria

- [ ] Images extracted from PDFs automatically
- [ ] Visual content searchable by description
- [ ] Mixed results (text + images) ranked correctly
- [ ] Processing time < 1s per image for embedding
- [ ] Works offline with local models
- [ ] Image results display usefully in CLI

## Dependencies

- PyMuPDF (image extraction)
- ColPali/ColQwen2 (vision embeddings)
- Ollama (optional, for captions)
- F-001 to F-007, F-035 (core pipeline)

## Technical Notes

### Configuration

```yaml
multi_modal:
  enabled: true
  vision_model: colpali-v1.0
  extract_images: true
  min_image_size: 100  # pixels, skip tiny images
  generate_captions: false  # requires Ollama
  caption_model: llava:7b
```

### Image Extraction

```python
import fitz  # PyMuPDF

def extract_images(pdf_path: str) -> list[Image]:
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        for img in page.get_images():
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append(Image(
                data=base_image["image"],
                format=base_image["ext"],
                page=page.number,
                metadata={"width": img[2], "height": img[3]}
            ))
    return images
```

### Vision Embedding

```python
from colpali import ColPali

model = ColPali.from_pretrained("vidore/colpali-v1.0")

def embed_image(image: Image) -> list[float]:
    return model.encode_image(image.data)

def embed_text_for_image_search(query: str) -> list[float]:
    return model.encode_text(query)
```

### Unified Search

```python
def multi_modal_search(query: str, k: int = 10) -> list[Result]:
    # Embed query for both modalities
    text_query_emb = text_model.encode(query)
    vision_query_emb = vision_model.encode_text(query)

    # Search both collections
    text_results = text_collection.search(text_query_emb, k)
    image_results = image_collection.search(vision_query_emb, k)

    # Merge and rerank
    return merge_results(text_results, image_results, k)
```

## Related Documentation

- [State-of-the-Art Multi-Modal](../../research/state-of-the-art-multi-modal.md) - Research basis
- [v0.4.0 Milestone](../../milestones/v0.4.0.md) - Release planning
- [F-002: Text Extraction](../completed/F-002-text-extraction.md) - Extended for images

---
