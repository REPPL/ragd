# Understanding Chunking Strategies

When ragd indexes a document, it splits it into smaller pieces called "chunks." The way text is divided significantly affects search quality. This document explains ragd's chunking strategies and when to use each.

## Why Chunking Matters

### The Chunking Trade-off

**Smaller chunks:**
- More precise retrieval (find exactly what you need)
- Less context in each chunk (may lose meaning)
- More chunks to search and store

**Larger chunks:**
- More context preserved
- Less precise (may retrieve too much irrelevant text)
- Fewer chunks to manage

The goal is finding the right balance for your content.

### How Chunks Affect Search

When you search, ragd:
1. Converts your query to a vector
2. Finds chunks with similar vectors
3. Returns the most relevant chunks

If chunks are too large, relevant information gets diluted by surrounding text. If too small, important context is lost.

## ragd's Chunking Strategies

ragd offers four chunking strategies:

| Strategy | Best For | How It Works |
|----------|----------|--------------|
| **sentence** | General text | Groups complete sentences |
| **fixed** | Uniform content | Fixed token count |
| **recursive** | Structured docs | Respects document hierarchy |
| **structure** | Complex layouts | Preserves tables, lists |

### Sentence Chunking (Default)

**How it works:**
1. Splits text at sentence boundaries (periods, question marks, etc.)
2. Groups sentences until reaching the target chunk size
3. Adds overlap from the previous chunk

**Example:**
```
Original:
"AI is transforming industries. Machine learning enables automation.
Natural language processing powers chatbots. These technologies
are becoming mainstream."

Chunks (target: 50 tokens):
[1] "AI is transforming industries. Machine learning enables automation."
[2] "Machine learning enables automation. Natural language processing
     powers chatbots."
[3] "Natural language processing powers chatbots. These technologies
     are becoming mainstream."
```

Notice the overlap—"Machine learning enables automation" appears in chunks 1 and 2.

**Best for:**
- Prose documents (reports, articles)
- Text where sentences are complete thoughts
- General-purpose indexing

**Configuration:**
```yaml
chunking:
  strategy: sentence
  chunk_size: 512      # Target tokens per chunk
  overlap: 50          # Tokens to repeat between chunks
  min_chunk_size: 100  # Minimum chunk size
```

### Fixed Chunking

**How it works:**
1. Divides text into equal-sized pieces (by token count)
2. Tries to break at word boundaries
3. Adds overlap from the previous chunk

**Best for:**
- Logs and data files
- Content without clear sentence structure
- When consistent chunk sizes matter

**Configuration:**
```yaml
chunking:
  strategy: fixed
  chunk_size: 512
  overlap: 50
```

**Limitations:**
- May split mid-sentence
- Doesn't respect document structure
- Can separate related information

### Recursive Chunking

**How it works:**
1. First tries to split at document structure (headings, sections)
2. If chunks are too large, splits at paragraphs
3. If still too large, splits at sentences
4. Finally splits at word boundaries if needed

**Separator hierarchy:**
1. `## ` — Markdown H2 headings
2. `# ` — Markdown H1 headings
3. `\n\n\n` — Multiple blank lines
4. `\n\n` — Paragraph breaks
5. `\n` — Line breaks
6. `. ` — Sentence endings
7. ` ` — Word boundaries

**Example:**
```markdown
# Introduction
Some intro text here.

## Background
Background information that explains context.

## Methods
Detailed methodology section with multiple paragraphs.
```

Recursive chunking keeps "Introduction," "Background," and "Methods" as separate chunks when possible, preserving document structure.

**Best for:**
- Markdown documents
- Technical documentation
- Code with comments
- Any structured text

**Configuration:**
```yaml
chunking:
  strategy: recursive
  chunk_size: 512
  overlap: 50
```

### Structure-Aware Chunking

**How it works:**
1. Uses document layout analysis (from Docling)
2. Keeps tables intact as single chunks
3. Preserves list items together
4. Respects visual structure

**Best for:**
- PDFs with complex layouts
- Documents with tables
- Forms and structured data

**Note:** Structure-aware chunking is applied automatically for PDFs processed with Docling. The `strategy` config primarily affects plain text processing.

## Chunk Size Guidelines

### Recommended Sizes by Content Type

| Content Type | Chunk Size | Overlap | Rationale |
|-------------|------------|---------|-----------|
| Technical docs | 512 | 50 | Balance detail and context |
| Legal documents | 768 | 100 | Longer, interconnected clauses |
| Short notes | 256 | 25 | Preserve granularity |
| Academic papers | 512 | 75 | Section-based retrieval |
| Code files | 256 | 50 | Function-level chunks |

### Tokens vs Characters

ragd measures chunks in **tokens**, not characters:
- 1 token ≈ 4 characters (rough average)
- 512 tokens ≈ 2000 characters
- A token is typically a word or word piece

**Why tokens?**
- Embedding models have token limits
- LLMs process tokens
- More consistent across languages

## Overlap Explained

Overlap repeats content between adjacent chunks:

```
Chunk 1: [A B C D E F G H I J]
Chunk 2:         [G H I J K L M N O P]
                  ↑ overlap ↑
```

**Why overlap?**
- Prevents information loss at chunk boundaries
- Helps with queries that span chunk edges
- Improves semantic continuity

**How much overlap?**
- Default: 50 tokens (~10% of chunk size)
- More overlap: Better boundary handling, more storage
- Less overlap: Less redundancy, potential boundary issues

**Rule of thumb:** 10-15% of chunk size works well for most content.

## Automatic Strategy Selection

ragd can automatically choose the best strategy based on file type:

| File Type | Default Strategy | Reason |
|-----------|-----------------|--------|
| `.md`, `.rst` | recursive | Respects heading structure |
| `.py`, `.js`, `.ts` | recursive | Respects function boundaries |
| `.txt` | sentence | General prose |
| `.pdf` | structure (via Docling) | Complex layouts |
| `.html` | recursive | Respects DOM structure |

## Viewing Chunk Information

### Check How Documents Were Chunked

```bash
# Show detailed statistics including chunk info
ragd info --detailed
```

### During Indexing

```bash
# Verbose output shows chunking decisions
ragd index ~/Documents/ --verbose
```

## Troubleshooting Chunking Issues

### "Search results miss relevant content"

**Possible cause:** Chunks too large, relevant text diluted.

**Solution:** Reduce chunk size:
```yaml
chunking:
  chunk_size: 256  # Smaller chunks
```

### "Results lack context"

**Possible cause:** Chunks too small, context lost.

**Solution:** Increase chunk size and overlap:
```yaml
chunking:
  chunk_size: 768
  overlap: 100
```

### "Tables are split across chunks"

**Possible cause:** Document processed without layout analysis.

**Solution:** Ensure Docling is available for PDF processing, or reindex:
```bash
ragd reindex --force
```

### "Markdown headings not respected"

**Possible cause:** Using sentence strategy instead of recursive.

**Solution:** Switch to recursive:
```yaml
chunking:
  strategy: recursive
```

## Advanced: Custom Chunking

For specialised needs, ragd's chunking can be extended programmatically. See the [Developer Documentation](../development/) for details on implementing custom chunkers.

---

## Related Documentation

- [Configuration Reference](../reference/configuration.md) — Chunking configuration options
- [Contextual Retrieval](./contextual-retrieval.md) — Adding context to chunks
- [Hybrid Search](./hybrid-search.md) — How chunks are searched

