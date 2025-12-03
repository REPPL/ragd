# Understanding ragd Chat: How Your Questions Find Answers

ragd uses **hybrid search** to find relevant content when you ask questions. This tutorial explains how it works and how to get better results.

## How Chat Works Internally

When you type a question in `ragd chat` or `ragd ask`, several things happen behind the scenes:

```
User Question: "What are the ethical concerns in machine learning?"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Query Embedding                                        │
│  Your question is converted to a 384-dimensional vector         │
│  using the sentence-transformers model                          │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Parallel Search                                        │
│  ┌─────────────────────┐   ┌─────────────────────┐             │
│  │   Semantic Search    │   │   Keyword Search    │             │
│  │   (ChromaDB)         │   │   (BM25)            │             │
│  │                      │   │                      │             │
│  │ Finds conceptually   │   │ Finds exact word    │             │
│  │ similar content      │   │ matches             │             │
│  └─────────────────────┘   └─────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Reciprocal Rank Fusion (RRF)                           │
│  Results from both searches are combined and re-ranked          │
│  Score = Σ 1/(k + rank) where k=60                              │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Context Assembly                                       │
│  Top results are formatted with source attribution              │
│  and sent to the LLM within a token budget                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: LLM Generation                                         │
│  The LLM generates an answer based ONLY on the retrieved        │
│  context, with citations to source documents                    │
└─────────────────────────────────────────────────────────────────┘
```

## Example: Seeing the Search in Action

### Step 1: Index some documents

```bash
ragd index ~/Documents/research-papers/
```

### Step 2: Search directly to preview results

Before asking a question via chat, you can preview exactly what ragd will find:

```bash
ragd search "machine learning ethics"
```

Output:
```
Search Results (5 of 23 matches):

1. [0.89] ethics-in-ai.pdf (p.12)
   "Machine learning systems must be designed with ethical
   considerations from the outset..."

2. [0.76] ml-guidelines.pdf (p.3)
   "Ethical AI development requires transparency in model
   training data and decision processes..."

3. [0.71] ai-governance-report.pdf (p.45)
   "The ethical implications of autonomous systems include
   accountability, fairness, and privacy..."
```

The score in brackets `[0.89]` is the hybrid relevance score.

### Step 3: Ask the same query via chat

```bash
ragd chat
> What are the ethical concerns in machine learning?
```

ragd runs the **same search** you just previewed, then sends the top results to the LLM. The LLM answers based on those specific documents.

## Why Hybrid Search?

ragd combines two search methods because each has strengths:

| Method | Good At | Weak At |
|--------|---------|---------|
| **Semantic** | Finding conceptually similar content even with different wording | Exact terminology, proper nouns |
| **Keyword (BM25)** | Exact matches, technical terms, names | Synonyms, paraphrasing |

### Example: "NLP challenges"

- **Semantic search** finds: "natural language processing difficulties", "text understanding problems"
- **Keyword search** finds: "NLP challenges" (exact match)
- **Hybrid** finds both!

## Tips for Better Results

### 1. Use specific keywords

```
Bad:  "Tell me about AI"
Good: "What are the privacy implications of facial recognition?"
```

Specific queries give both search methods more to work with.

### 2. Preview with ragd search

```bash
# See exactly what ragd will find
ragd search "your query here"

# If results look good, ask via chat
ragd ask "your query here"
```

### 3. Check what's indexed

```bash
ragd stats           # See topics and coverage
ragd search "term"   # Verify content exists
```

### 4. Understand no-context responses

If ragd says:
```
I don't have information about that in my indexed documents.
```

This means:
- No chunks scored high enough on hybrid search
- The topic may not be covered in your indexed documents
- Try different keywords or check if relevant documents are indexed

## Search Modes

ragd supports different search modes via the `--mode` flag:

```bash
# Default: hybrid (semantic + keyword)
ragd search "query"

# Semantic only (conceptual similarity)
ragd search "query" --mode semantic

# Keyword only (BM25 exact matching)
ragd search "query" --mode keyword
```

In chat, hybrid mode is always used for best results.

## Debugging Search Issues

### Low-quality results?

1. **Check the search results directly**:
   ```bash
   ragd search "your question" --limit 10
   ```

2. **Try different phrasings**:
   ```bash
   ragd search "machine learning ethics"
   ragd search "ethical AI considerations"
   ragd search "ML fairness accountability"
   ```

3. **Verify documents are indexed**:
   ```bash
   ragd status
   ```

### No results at all?

1. **Check if the topic exists in your documents**:
   ```bash
   ragd search "any keyword you expect to find"
   ```

2. **Re-index if needed**:
   ```bash
   ragd index --rebuild ~/Documents/
   ```

## Advanced: Understanding RRF Scores

The Reciprocal Rank Fusion (RRF) algorithm combines search results:

```
Score(doc) = Σ 1/(k + rank_i)
```

Where:
- `k=60` (constant to prevent division by zero)
- `rank_i` = position in each search result list

A document ranked #1 in both searches gets:
- Semantic: 1/(60+1) = 0.0164
- Keyword: 1/(60+1) = 0.0164
- **Total: 0.0328**

A document ranked #1 in one and #10 in another:
- Semantic: 1/(60+1) = 0.0164
- Keyword: 1/(60+10) = 0.0143
- **Total: 0.0307**

Documents appearing in both lists are boosted; those in only one list may still rank high if they score very well on that method.

---

## Related Documentation

- [Chatting with Your Knowledge Base](./chatting-with-your-knowledge.md) - How to use the chat interface
- [Powerful Searching](./powerful-searching.md) - Advanced search techniques
- [CLI Reference](../reference/cli-reference.md) - Complete command reference
