# State-of-the-Art Text Chunking for RAG Systems

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

## Executive Summary

**Key Recommendations for ragd:**

1. **Default Chunk Size:** 256-512 tokens for general RAG, adjustable based on embedding model context window
2. **Primary Strategy:** Semantic chunking with sentence boundaries respected
3. **Overlap:** 10-20% of chunk size (50-100 tokens for 512-token chunks)
4. **Hybrid Approach:** Use recursive chunking for structured documents, sentence-based for prose
5. **Always Measure:** Optimal chunk size varies by domain - benchmark retrieval quality on your data

---

## Why Chunking Matters

### The Retrieval Quality Cascade

```
Document Quality → Chunking Quality → Retrieval Quality → Generation Quality
                        ↑
                  Critical bottleneck
```

Poor chunking causes:
- **Information fragmentation** - Key context split across chunks
- **Semantic dilution** - Irrelevant content mixed with relevant
- **Boundary artifacts** - Sentences cut mid-thought
- **Retrieval noise** - Wrong chunks returned for queries

### The Chunk Size Trade-off

| Size | Advantages | Disadvantages |
|------|------------|---------------|
| **Small (128-256)** | Precise retrieval, less noise | Loses context, fragmentation |
| **Medium (512-768)** | Balanced precision/context | Standard choice |
| **Large (1024-2048)** | More context, complete ideas | Dilutes relevance, retrieval noise |

---

## Chunk Size Research

### Academic Findings

#### LlamaIndex Study (2023)

Tested chunk sizes from 128 to 2048 tokens across multiple datasets:

| Chunk Size | Faithfulness | Relevancy | Retrieval Hit Rate |
|------------|--------------|-----------|-------------------|
| 128 | 0.82 | 0.78 | 0.71 |
| 256 | 0.85 | 0.83 | 0.76 |
| **512** | **0.87** | **0.86** | **0.79** |
| 1024 | 0.85 | 0.84 | 0.74 |
| 2048 | 0.81 | 0.80 | 0.68 |

**Conclusion:** 512 tokens provides the best balance for general-purpose RAG.

#### Pinecone Analysis (2024)

Analysed retrieval quality across different chunk sizes:

- **Short text (< 100 words):** Use as-is, don't chunk
- **Medium text (100-500 words):** Single chunk or 2-3 chunks
- **Long text (500+ words):** Chunk to 256-512 tokens

**Key Insight:** Chunk size should correlate with query complexity. Simple factual queries work better with smaller chunks; complex reasoning queries need larger context.

#### Weaviate Research (2024)

Compared fixed-size vs semantic chunking:

| Method | NDCG@10 | Processing Time |
|--------|---------|-----------------|
| Fixed (512 tokens) | 0.42 | 1.0x |
| Sentence-based | 0.48 | 1.2x |
| Recursive | 0.51 | 1.5x |
| **Semantic (LLM-assisted)** | **0.56** | 8-10x |

**Trade-off:** Semantic chunking improves quality but significantly increases processing time.

### Domain-Specific Recommendations

| Domain | Recommended Size | Rationale |
|--------|------------------|-----------|
| **Technical docs** | 512-768 | Complete code blocks, concepts |
| **Legal documents** | 1024+ | Long clauses, full context needed |
| **Q&A/FAQ** | 256-512 | Self-contained answers |
| **Academic papers** | 768-1024 | Section coherence |
| **Chat transcripts** | 256 | Turn-by-turn retrieval |
| **News articles** | 512 | Paragraph-level semantics |

---

## Chunking Strategies

### 1. Fixed-Size Chunking

**How it works:** Split text by character/token count with overlap.

```python
def fixed_chunk(text: str, size: int = 512, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

**Pros:**
- Simple, fast, deterministic
- Consistent chunk sizes
- Works with any text

**Cons:**
- Ignores semantic boundaries
- Cuts sentences mid-thought
- Poor for structured content

**When to use:** Fallback strategy, very long unstructured text.

### 2. Sentence-Based Chunking

**How it works:** Split on sentence boundaries, combine to target size.

```python
def sentence_chunk(
    text: str,
    target_tokens: int = 512,
    max_tokens: int = 1024
) -> list[str]:
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens > max_tokens and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_tokens = 0

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
```

**Pros:**
- Preserves sentence boundaries
- Semantically coherent chunks
- Good balance of quality and speed

**Cons:**
- Sentence detection can fail
- Variable chunk sizes
- Long sentences cause issues

**When to use:** Default for prose, documentation, articles.

### 3. Recursive/Hierarchical Chunking

**How it works:** Split on document structure (headers, paragraphs), then recursively on smaller units.

```python
SEPARATORS = [
    "\n## ",     # H2 headers
    "\n### ",    # H3 headers
    "\n\n",      # Paragraphs
    "\n",        # Lines
    ". ",        # Sentences
    " ",         # Words (last resort)
]

def recursive_chunk(
    text: str,
    separators: list[str],
    max_tokens: int = 512
) -> list[str]:
    if count_tokens(text) <= max_tokens:
        return [text]

    for separator in separators:
        if separator in text:
            parts = text.split(separator)
            chunks = []
            for part in parts:
                chunks.extend(
                    recursive_chunk(part, separators[1:], max_tokens)
                )
            return chunks

    # Fallback: hard split
    return fixed_chunk(text, max_tokens)
```

**Pros:**
- Respects document structure
- Keeps related content together
- Handles markdown/headers well

**Cons:**
- Structure detection varies
- More complex implementation
- May create uneven chunk sizes

**When to use:** Markdown, technical documentation, structured content.

### 4. Semantic Chunking

**How it works:** Use embeddings or LLMs to identify semantic boundaries.

```python
def semantic_chunk(
    text: str,
    embedding_model,
    threshold: float = 0.5
) -> list[str]:
    sentences = sent_tokenize(text)
    embeddings = embedding_model.encode(sentences)

    chunks = []
    current_chunk = [sentences[0]]

    for i in range(1, len(sentences)):
        similarity = cosine_similarity(embeddings[i-1], embeddings[i])

        if similarity < threshold:
            # Low similarity = topic shift = chunk boundary
            chunks.append(' '.join(current_chunk))
            current_chunk = []

        current_chunk.append(sentences[i])

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
```

**Pros:**
- Identifies natural topic boundaries
- Best retrieval quality
- Adapts to content

**Cons:**
- Computationally expensive (8-10x slower)
- Requires embedding model
- Harder to debug

**When to use:** High-value documents, quality-critical applications.

### 5. Agentic Chunking

**How it works:** LLM analyses document and proposes optimal chunks.

**Example Prompt:**
```
Analyse this text and identify natural sections that should stay together.
Consider:
- Topic coherence
- Self-contained information
- Reference dependencies

Text: {text}

Return JSON: [{"start": int, "end": int, "reason": str}, ...]
```

**Pros:**
- Highest quality boundaries
- Can explain chunk decisions
- Handles complex documents

**Cons:**
- Very expensive (LLM calls)
- Slow (seconds per document)
- Requires careful prompting

**When to use:** Very high-value content, complex documents.

---

## Overlap Strategies

### Why Overlap Matters

Without overlap, context at chunk boundaries is lost:

```
Chunk 1: "...the algorithm works by first sorting the input."
Chunk 2: "Then it iterates through each element to find..."

Query: "How does the algorithm work?"
→ Neither chunk has complete answer
```

With overlap:

```
Chunk 1: "...the algorithm works by first sorting the input. Then it..."
Chunk 2: "...sorting the input. Then it iterates through each element..."

Query: "How does the algorithm work?"
→ Either chunk provides context
```

### Overlap Recommendations

| Chunk Size | Recommended Overlap | Ratio |
|------------|---------------------|-------|
| 256 tokens | 25-50 tokens | 10-20% |
| 512 tokens | 50-100 tokens | 10-20% |
| 1024 tokens | 100-150 tokens | 10-15% |

**Research Finding:** 10-15% overlap is optimal. More overlap wastes storage and computation; less overlap risks losing boundary context.

### Overlap Methods

1. **Fixed overlap:** Always N tokens/chars
2. **Sentence-aware:** Include at least 1 complete sentence from previous chunk
3. **Semantic:** Include until topic similarity drops

**Recommendation:** Sentence-aware overlap provides best balance of context preservation and efficiency.

---

## Token Counting

### Why Token Counting Matters

Embedding models have token limits. Exceeding them causes:
- Truncation (lost information)
- Errors (model rejection)
- Degraded embeddings (context overflow)

### Embedding Model Token Limits

| Model | Token Limit | Recommended Chunk Size |
|-------|-------------|----------------------|
| nomic-embed-text-v1.5 | 8192 | 512-1024 |
| all-MiniLM-L6-v2 | 512 | 256-400 |
| all-mpnet-base-v2 | 384 | 200-300 |
| BAAI/bge-m3 | 8192 | 512-1024 |
| OpenAI text-embedding-3-* | 8191 | 512-2048 |

**Rule of Thumb:** Keep chunks at 50-75% of model token limit for safety margin.

### Token Counting Implementation

```python
import tiktoken

# For OpenAI-style models
def count_tokens_cl100k(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# For sentence-transformers models (approximate)
def count_tokens_approximate(text: str) -> int:
    # ~4 characters per token on average for English
    return len(text) // 4
```

**Important:** Different tokenisers produce different counts. Use the embedding model's tokeniser for accuracy.

---

## Late Chunking (Emerging Technique)

### Concept

Traditional chunking embeds each chunk independently. Late chunking embeds the full document first, then extracts chunk representations.

```
Traditional: Document → Chunks → Embed Each → Store
Late:        Document → Embed Full → Extract Chunk Vectors → Store
```

### Benefits

1. **Cross-chunk context:** Each chunk embedding "knows" about surrounding content
2. **Better boundary handling:** No information loss at chunk edges
3. **Improved coherence:** Semantic relationships preserved

### JinaAI Late Chunking Implementation

```python
from transformers import AutoModel

model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en')

# Get all token embeddings for full document
outputs = model(document_tokens)
all_embeddings = outputs.last_hidden_state

# Extract chunk embeddings by averaging token ranges
chunk_embeddings = []
for start, end in chunk_boundaries:
    chunk_emb = all_embeddings[start:end].mean(dim=0)
    chunk_embeddings.append(chunk_emb)
```

### Trade-offs

| Aspect | Traditional | Late Chunking |
|--------|-------------|---------------|
| Processing speed | Fast | Slower (full doc encoding) |
| Context awareness | None | High |
| Memory usage | Low | Higher |
| Retrieval quality | Good | Better (+5-10%) |
| Implementation | Simple | More complex |

**Recommendation:** Consider late chunking for v0.3+ as quality enhancement.

---

## Benchmarking Chunking Quality

### Metrics

1. **Retrieval Hit Rate:** Does correct chunk appear in top-K?
2. **NDCG@K:** Are relevant chunks ranked higher?
3. **Answer Quality:** Does retrieved context enable good generation?

### Testing Protocol

```python
def evaluate_chunking_strategy(
    strategy: ChunkingStrategy,
    test_set: list[QueryDocPair],
    retriever: Retriever,
    k: int = 5
) -> ChunkingMetrics:
    """Evaluate a chunking strategy on retrieval quality."""

    hits = 0
    ndcg_scores = []

    for query, relevant_doc in test_set:
        # Chunk the relevant document
        chunks = strategy.chunk(relevant_doc)

        # Index chunks
        retriever.index(chunks)

        # Retrieve for query
        results = retriever.search(query, k=k)

        # Check if any relevant chunk retrieved
        if any(chunk_contains_answer(r, query) for r in results):
            hits += 1

        # Compute NDCG
        ndcg_scores.append(compute_ndcg(results, relevant_doc, k))

    return ChunkingMetrics(
        hit_rate=hits / len(test_set),
        ndcg_mean=sum(ndcg_scores) / len(ndcg_scores)
    )
```

### ragd Benchmark Targets

| Metric | Minimum | Target |
|--------|---------|--------|
| Hit Rate @5 | 0.70 | 0.85 |
| NDCG@10 | 0.40 | 0.55 |
| Faithfulness | 0.70 | 0.85 |

---

## Recommended Architecture for ragd

### Default Configuration

```yaml
chunking:
  # Default strategy
  strategy: sentence

  # Size parameters
  target_tokens: 512
  max_tokens: 768
  min_tokens: 50

  # Overlap
  overlap_tokens: 50
  overlap_sentences: 1  # Ensure at least 1 sentence overlap

  # Token counting
  tokeniser: cl100k_base

  # Structure detection
  detect_markdown: true
  markdown_strategy: recursive
```

### Strategy Selection Logic

```python
def select_chunking_strategy(document: Document) -> ChunkingStrategy:
    """Select optimal chunking strategy based on document type."""

    if document.format == "markdown":
        return RecursiveChunker(separators=MARKDOWN_SEPARATORS)

    if document.format == "code":
        return RecursiveChunker(separators=CODE_SEPARATORS)

    if document.word_count < 200:
        return NoChunker()  # Keep short docs as-is

    # Default: sentence-based
    return SentenceChunker()
```

### Chunk Metadata

Every chunk should carry:

```python
@dataclass
class ChunkMetadata:
    # Identity
    chunk_id: str
    doc_id: str
    chunk_index: int

    # Position
    start_char: int
    end_char: int

    # Size
    token_count: int
    char_count: int

    # Context
    section_header: str | None  # If from structured doc
    overlap_prev: int  # Tokens from previous chunk
    overlap_next: int  # Tokens in next chunk
```

---

## Common Pitfalls

### 1. Ignoring Embedding Model Limits

**Problem:** Chunks exceed model token limit.
**Solution:** Always count tokens, not characters.

### 2. No Overlap

**Problem:** Boundary context lost.
**Solution:** Use 10-20% overlap.

### 3. Uniform Strategy

**Problem:** Same chunking for all document types.
**Solution:** Adapt strategy to content structure.

### 4. Chunks Too Small

**Problem:** High retrieval precision but lost context.
**Solution:** Ensure chunks are semantically complete.

### 5. Chunks Too Large

**Problem:** Retrieval noise, diluted relevance.
**Solution:** Keep chunks focused on single concepts.

---

## References

### Research Papers
- [Chunk Optimisation for RAG](https://arxiv.org/abs/2312.06648) - Size impact analysis
- [Semantic Text Chunking](https://arxiv.org/abs/2402.04095) - Embedding-based segmentation
- [Late Chunking](https://arxiv.org/abs/2409.04701) - JinaAI contextual chunking

### Industry Guides
- [LlamaIndex Chunking Guide](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5)
- [Pinecone Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/)
- [Weaviate: How to Choose Chunk Size](https://weaviate.io/blog/chunking-strategies)
- [Unstructured.io Chunking Guide](https://unstructured.io/blog/chunking-for-rag-best-practices)

### Implementation Examples
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [LlamaIndex Node Parsers](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/)
- [Semantic Chunking with NLTK](https://www.nltk.org/api/nltk.tokenize.html)

---

## Related Documentation

- [ADR-0018: Chunking Strategy](../decisions/adrs/0018-chunking-strategy.md) - Architecture decision
- [F-003: Chunking Engine](../features/completed/F-003-chunking-engine.md) - Feature specification
- [F-011: Late Chunking](../features/completed/F-011-late-chunking.md) - Advanced chunking feature
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Model selection and limits
- [State-of-the-Art Evaluation](./state-of-the-art-evaluation.md) - Measuring chunking quality
- [State-of-the-Art RAG](./state-of-the-art-rag.md) - Overall RAG architecture

---

**Status:** Research complete
