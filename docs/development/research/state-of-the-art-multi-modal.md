# State-of-the-Art Multi-Modal RAG

## Executive Summary

**Key Recommendations for ragd:**

1. **Vision Retrieval:** Use ColPali/ColQwen2 for document page retrieval - bypasses OCR pipeline entirely
2. **Image Embeddings:** SigLIP 2 outperforms CLIP for image-text similarity with better efficiency
3. **Hybrid Strategy:** Combine text summaries of images (for retrieval) with raw images (for generation)
4. **Chunking:** Use modality-specific chunking; preserve images/tables as independent retrievable units
5. **Generation:** Route to multimodal LLM (Llama 3.2 Vision, Qwen2-VL) when visual context is relevant

---

## Multi-Modal RAG Landscape

### Why Multi-Modal Matters

| Document Type | Text-Only RAG | Multi-Modal RAG |
|---------------|---------------|-----------------|
| Text documents | Excellent | Excellent |
| PDFs with diagrams | Poor (loses visual info) | Good |
| Presentations | Poor | Good |
| Technical manuals | Moderate | Excellent |
| Infographics | Very Poor | Good |
| Charts/graphs | Very Poor | Excellent |

### Key Challenges

1. **Alignment:** Different modalities have different semantic spaces
2. **Retrieval:** How to search across text, images, and tables
3. **Fusion:** When and how to combine modalities for generation
4. **Storage:** Multi-vector representations increase storage needs
5. **Latency:** Vision models add processing overhead

---

## Part 1: Vision Language Models for Retrieval

### Model Comparison

| Model | Architecture | Best For | Context |
|-------|--------------|----------|---------|
| **ColPali** | PaliGemma + ColBERT | Document pages | Multi-vector |
| **ColQwen2** | Qwen2-VL + ColBERT | Document pages | Multi-vector |
| **CLIP** | ViT + Text Encoder | General images | Single-vector |
| **SigLIP 2** | Improved CLIP | Image-text matching | Single-vector |
| **Voyage Multimodal-3** | Proprietary | Unified embedding | Single-vector |

### ColPali: The Document Retrieval Revolution

**What is ColPali:**
ColPali uses Vision Language Models to create multi-vector embeddings directly from document page images, bypassing OCR entirely.

**How it works:**
```
Document Page Image
        ↓
   PaliGemma-3B (VLM)
        ↓
   ViT Output Patches
        ↓
   Linear Projection
        ↓
Multi-Vector Embedding (128 vectors per page)
```

**Advantages:**
- No OCR pipeline needed
- Handles complex layouts automatically
- Understands charts, tables, diagrams
- Works with any language
- Outperforms traditional retrieval on ViDoRe benchmark

**Source:** [ColPali Paper](https://arxiv.org/abs/2407.01449)

### ColQwen2 Implementation

```python
from colpali_engine.models import ColQwen2, ColQwen2Processor
import torch

# Load model
model = ColQwen2.from_pretrained(
    "vidore/colqwen2-v1.0",
    torch_dtype=torch.float16,
    device_map="cuda"
)
processor = ColQwen2Processor.from_pretrained("vidore/colqwen2-v1.0")

# Process document pages
images = [Image.open(f"page_{i}.png") for i in range(10)]
inputs = processor(images=images, return_tensors="pt").to("cuda")

with torch.no_grad():
    page_embeddings = model(**inputs)

# Process query
query = "What are the quarterly revenue figures?"
query_inputs = processor(text=[query], return_tensors="pt").to("cuda")

with torch.no_grad():
    query_embedding = model(**query_inputs)

# Late interaction scoring (ColBERT-style)
scores = torch.einsum("bnd,csd->bcns", query_embedding, page_embeddings)
scores = scores.max(dim=-1).values.sum(dim=-1)
```

### SigLIP 2 for Image Embeddings

**When to use SigLIP:**
- General image retrieval (not document-specific)
- Product images, photos, artwork
- When you need single-vector embeddings
- Smaller batch sizes / limited compute

```python
from transformers import AutoProcessor, AutoModel
import torch

# Load SigLIP 2
model = AutoModel.from_pretrained("google/siglip2-base-patch16-256")
processor = AutoProcessor.from_pretrained("google/siglip2-base-patch16-256")

# Encode images
images = [Image.open(path) for path in image_paths]
inputs = processor(images=images, return_tensors="pt")

with torch.no_grad():
    image_features = model.get_image_features(**inputs)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

# Encode text query
text_inputs = processor(text=["a photo of a cat"], return_tensors="pt")

with torch.no_grad():
    text_features = model.get_text_features(**text_inputs)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)

# Compute similarity
similarity = (image_features @ text_features.T).softmax(dim=0)
```

**Source:** [SigLIP 2 on Hugging Face](https://huggingface.co/blog/siglip2)

---

## Part 2: Retrieval Strategies

### Three Approaches Compared

| Approach | Retrieval | Generation | Pros | Cons |
|----------|-----------|------------|------|------|
| **Unified Embedding** | Same space for all | Pass embeddings | Simplest | Limited models |
| **Text Summary** | Embed summaries | Pass summaries | Works with any LLM | Information loss |
| **Multi-Vector** | Separate per modality | Pass raw content | Best quality | Most complex |

### Approach 1: Unified Multimodal Embedding

```python
from voyageai import Client

client = Client()

# Embed text and images in same space
text_embedding = client.embed(
    ["What is machine learning?"],
    model="voyage-multimodal-3",
    input_type="query"
)

image_embedding = client.embed(
    [image_base64],
    model="voyage-multimodal-3",
    input_type="document"
)

# Direct cosine similarity
similarity = cosine_similarity(text_embedding, image_embedding)
```

### Approach 2: Text Summary Bridge

```python
from transformers import LlavaForConditionalGeneration, AutoProcessor

# Use VLM to generate text summaries of images
model = LlavaForConditionalGeneration.from_pretrained("llava-hf/llava-1.5-7b-hf")
processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")

def summarize_image(image: Image.Image) -> str:
    """Generate text summary of image for retrieval."""
    prompt = """<image>
    Describe this image in detail for document retrieval purposes.
    Include all text, data, and visual information."""

    inputs = processor(text=prompt, images=image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=500)
    return processor.decode(output[0], skip_special_tokens=True)

# Store summary for retrieval, keep raw image for generation
summaries = [summarize_image(img) for img in images]
summary_embeddings = embed_texts(summaries)

# At query time: retrieve summary, pass raw image to VLM
```

### Approach 3: Multi-Vector Retriever (Recommended)

```python
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma

# Separate stores for summaries (retrieval) and raw content (generation)
vectorstore = Chroma(
    collection_name="multi_modal_rag",
    embedding_function=embedding_model
)
docstore = InMemoryStore()

retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    id_key="doc_id"
)

# For each image:
# 1. Generate summary for retrieval
# 2. Store raw image in docstore
# 3. Link via doc_id

def index_image(image: Image.Image, doc_id: str):
    # Summary for vector search
    summary = summarize_image(image)

    # Add to vector store (searchable)
    retriever.vectorstore.add_documents([
        Document(page_content=summary, metadata={"doc_id": doc_id})
    ])

    # Store raw image in docstore (for generation)
    retriever.docstore.mset([(doc_id, image)])
```

**Source:** [LangChain Multi-Vector Retriever](https://blog.langchain.com/semi-structured-multi-modal-rag/)

---

## Part 3: Multi-Modal Chunking

### Modality-Specific Strategy

```
Document
    │
    ├── Text Content
    │   ├── Paragraph chunks (semantic)
    │   └── Headings (hierarchical)
    │
    ├── Images
    │   ├── Embedded images
    │   ├── Charts/graphs
    │   └── Diagrams
    │
    ├── Tables
    │   ├── Full table as unit
    │   └── Row-level for large tables
    │
    └── Code Blocks
        └── Function/class as unit
```

### Implementation with Unstructured

```python
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Image, Table, NarrativeText, Title
)

def chunk_multimodal_document(pdf_path: str) -> dict:
    """Extract and chunk different modalities from PDF."""

    # Partition with layout analysis
    elements = partition_pdf(
        pdf_path,
        strategy="hi_res",  # Use YOLOX for layout detection
        extract_images_in_pdf=True,
        extract_image_block_types=["Image", "Table"],
        infer_table_structure=True
    )

    chunks = {
        "text": [],
        "images": [],
        "tables": []
    }

    for element in elements:
        if isinstance(element, NarrativeText):
            chunks["text"].append({
                "content": element.text,
                "metadata": element.metadata.to_dict()
            })
        elif isinstance(element, Image):
            chunks["images"].append({
                "image": element.metadata.image_base64,
                "context": get_surrounding_text(element, elements)
            })
        elif isinstance(element, Table):
            chunks["tables"].append({
                "html": element.metadata.text_as_html,
                "text": element.text,
                "context": get_surrounding_text(element, elements)
            })

    return chunks

def get_surrounding_text(element, all_elements, window: int = 2):
    """Get text before/after element for context."""
    idx = all_elements.index(element)
    context = []

    for i in range(max(0, idx - window), min(len(all_elements), idx + window + 1)):
        if isinstance(all_elements[i], (NarrativeText, Title)):
            context.append(all_elements[i].text)

    return " ".join(context)
```

### Vision-Guided Chunking (Advanced)

Recent research shows that using VLMs for chunking decisions produces better results:

```python
async def vision_guided_chunk(pages: list[Image.Image]) -> list[dict]:
    """Use VLM to intelligently chunk document pages."""

    prompt = """Analyze this document page and identify semantic chunks.
    For each chunk, provide:
    1. Type: text, table, figure, or mixed
    2. Bounding box coordinates [x1, y1, x2, y2]
    3. A brief description
    4. Whether it continues on next page

    Return as JSON list."""

    chunks = []
    for i, page in enumerate(pages):
        response = await vlm.generate(prompt, images=[page])
        page_chunks = json.loads(response)

        for chunk in page_chunks:
            chunk["page"] = i
            chunks.append(chunk)

    # Merge chunks that span pages
    return merge_continuation_chunks(chunks)
```

**Source:** [Vision-Guided Chunking Paper](https://arxiv.org/html/2506.16035v1)

---

## Part 4: Generation with Multi-Modal Context

### Multimodal LLM Options

| Model | Parameters | Local | Context | Best For |
|-------|------------|-------|---------|----------|
| **Llama 3.2 Vision** | 11B/90B | Yes | 128K | General multi-modal |
| **Qwen2-VL** | 2B/7B/72B | Yes | 32K | Document understanding |
| **GPT-4V** | Unknown | No | 128K | Highest quality |
| **LLaVA** | 7B/13B | Yes | 4K | Research, fine-tuning |
| **Pixtral** | 12B | Yes | 128K | Long context vision |

### Context Assembly for Generation

```python
from typing import Union

def assemble_multimodal_context(
    query: str,
    retrieved_items: list[dict],
    max_images: int = 5,
    max_text_chars: int = 8000
) -> list[Union[str, Image.Image]]:
    """Assemble context for multimodal generation."""

    context = []
    text_budget = max_text_chars
    image_count = 0

    # Sort by relevance score
    retrieved_items.sort(key=lambda x: x["score"], reverse=True)

    for item in retrieved_items:
        if item["type"] == "text" and text_budget > 0:
            text = item["content"][:text_budget]
            context.append(f"[Text Context]\n{text}")
            text_budget -= len(text)

        elif item["type"] == "image" and image_count < max_images:
            context.append(item["image"])  # PIL Image
            context.append(f"[Image: {item.get('description', 'Relevant figure')}]")
            image_count += 1

        elif item["type"] == "table":
            table_text = f"[Table]\n{item['text']}"
            if len(table_text) <= text_budget:
                context.append(table_text)
                text_budget -= len(table_text)

    return context

async def generate_multimodal_response(
    query: str,
    context: list[Union[str, Image.Image]],
    model: str = "llama3.2-vision:11b"
) -> str:
    """Generate response using multimodal LLM."""

    # Separate text and images
    text_parts = [c for c in context if isinstance(c, str)]
    images = [c for c in context if isinstance(c, Image.Image)]

    prompt = f"""Based on the following context, answer the question.

Context:
{chr(10).join(text_parts)}

Question: {query}

Provide a comprehensive answer based on both text and visual information."""

    # Call multimodal LLM (implementation depends on backend)
    response = await vlm_generate(
        prompt=prompt,
        images=images,
        model=model
    )

    return response
```

### Routing to Multimodal Generation

```python
def should_use_multimodal(
    query: str,
    retrieved_items: list[dict]
) -> bool:
    """Decide if query needs multimodal generation."""

    # Check if retrieved items include images
    has_images = any(item["type"] == "image" for item in retrieved_items)

    # Check if query is about visual content
    visual_keywords = [
        "chart", "graph", "diagram", "figure", "image", "picture",
        "show", "visual", "display", "table", "screenshot", "plot"
    ]
    query_is_visual = any(kw in query.lower() for kw in visual_keywords)

    return has_images or query_is_visual
```

**Source:** [Together AI: Multimodal Document RAG](https://www.together.ai/blog/multimodal-document-rag-with-llama-3-2-vision-and-colqwen2)

---

## Part 5: Storage and Performance

### Storage Requirements

| Content Type | Storage per Item | Index Overhead |
|--------------|------------------|----------------|
| **Text chunk** | ~1KB | ~3KB (768-dim) |
| **Text embedding** | 3KB (768-dim float32) | - |
| **ColPali page** | ~200KB (image) | ~400KB (128×128-dim) |
| **Image summary** | ~2KB | ~3KB (embedding) |
| **Raw image** | 100KB-2MB | - |

### Optimisation Strategies

**For ColPali multi-vectors:**
```python
# Quantise embeddings for storage efficiency
from qdrant_client.models import VectorParams, Distance

# Use scalar quantisation for 4x reduction
collection_config = {
    "vectors": {
        "colpali": VectorParams(
            size=128,
            distance=Distance.COSINE,
            quantization_config={
                "scalar": {
                    "type": "int8",
                    "always_ram": True
                }
            }
        )
    }
}
```

**For image storage:**
```python
import io
from PIL import Image

def compress_image_for_storage(
    image: Image.Image,
    max_size: tuple = (1024, 1024),
    quality: int = 85
) -> bytes:
    """Compress image for efficient storage."""
    # Resize if too large
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Convert to WebP for better compression
    buffer = io.BytesIO()
    image.save(buffer, format="WebP", quality=quality)
    return buffer.getvalue()
```

### Latency Considerations

| Operation | Typical Latency | Notes |
|-----------|-----------------|-------|
| ColPali embedding (1 page) | 100-200ms | GPU required |
| SigLIP embedding (1 image) | 20-50ms | GPU or CPU |
| Text embedding (1 chunk) | 5-10ms | CPU efficient |
| Image summary generation | 2-5s | VLM inference |
| Multimodal generation | 3-10s | Depends on model |

**Optimisation: Pre-compute embeddings**
```python
async def index_document_batch(documents: list[Path]):
    """Index documents with parallel embedding."""
    import asyncio

    async def process_document(doc_path: Path):
        pages = extract_pages(doc_path)

        # Generate embeddings in parallel
        embeddings = await asyncio.gather(*[
            generate_page_embedding(page) for page in pages
        ])

        # Store in vector DB
        await vectorstore.add_documents(embeddings)

    # Process documents concurrently
    await asyncio.gather(*[
        process_document(doc) for doc in documents
    ])
```

---

## Recommended Architecture for ragd

### Multi-Modal Pipeline (v0.4+)

```
Document Input
      │
      ├── Text Documents
      │   └── Standard text pipeline
      │
      ├── PDFs with Images
      │   ├── ColPali page embeddings (retrieval)
      │   ├── Image extraction + summaries
      │   └── Text extraction (fallback)
      │
      └── Image Files
          ├── SigLIP embeddings
          └── VLM summaries

Query Processing
      │
      ├── Text Query
      │   └── Embed with text model
      │
      └── Visual Query ("show me the chart...")
          └── Embed with multimodal model

Retrieval
      │
      ├── Vector search (text + ColPali)
      │
      └── Re-ranking with cross-modal scores

Generation
      │
      ├── Text-only context → Text LLM
      │
      └── Contains images → Multimodal LLM
```

### Configuration

```yaml
# ~/.ragd/config.yaml

multimodal:
  enabled: true  # Enable in v0.4

  # Document processing
  document_processing:
    # Use ColPali for PDFs with visual content
    use_colpali: true
    colpali_model: "vidore/colqwen2-v1.0"

    # Fallback text extraction
    extract_text: true
    ocr_engine: "paddleocr"  # or "tesseract"

  # Image embedding
  image_embedding:
    model: "google/siglip2-base-patch16-256"
    generate_summaries: true
    summary_model: "llava-hf/llava-1.5-7b-hf"

  # Generation
  generation:
    multimodal_model: "llama3.2-vision:11b"
    text_model: "llama3:8b"
    auto_route: true  # Auto-select based on context

  # Storage
  storage:
    compress_images: true
    image_quality: 85
    max_image_size: [1024, 1024]
```

---

## References

### ColPali and Vision Retrieval
- [ColPali Paper (arXiv)](https://arxiv.org/abs/2407.01449)
- [ColPali GitHub](https://github.com/illuin-tech/colpali)
- [ColPali on Hugging Face](https://huggingface.co/blog/manu/colpali)
- [Vespa ColPali Implementation](https://blog.vespa.ai/retrieval-with-vision-language-models-colpali/)

### Vision Language Models
- [SigLIP 2 on Hugging Face](https://huggingface.co/blog/siglip2)
- [CLIP vs SigLIP Comparison](https://blog.ritwikraha.dev/choosing-between-siglip-and-clip-for-language-image-pretraining)
- [Llama 3.2 Vision](https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/)

### Multi-Modal RAG Architecture
- [NVIDIA Multi-Modal RAG Guide](https://developer.nvidia.com/blog/an-easy-introduction-to-multimodal-retrieval-augmented-generation/)
- [LangChain Multi-Vector Retriever](https://blog.langchain.com/semi-structured-multi-modal-rag/)
- [IBM: What is Multimodal RAG?](https://www.ibm.com/think/topics/multimodal-rag)

### Chunking Strategies
- [Vision-Guided Chunking Paper](https://arxiv.org/html/2506.16035v1)
- [Unstructured Documentation](https://docs.unstructured.io/)
- [Multi-Modal Chunking Guide](https://www.multimodal.dev/post/how-to-chunk-documents-for-rag)

---

## Related Documentation

- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Document extraction
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Text embedding models
- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [v0.4 Milestone](../milestones/v0.4.md) - Multi-modal support milestone

---

**Status:** Research complete
