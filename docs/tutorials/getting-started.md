# Getting Started with ragd

Learn to index documents and search your personal knowledge base.

**Time:** 15 minutes
**Prerequisites:** ragd installed, sample documents ready
**Validates:** UC-001, UC-002, UC-003

> **Note:** This tutorial is a DRAFT for v0.1 specification validation. Implementation may differ.

---

## What You'll Learn

By the end of this tutorial, you'll know how to:
1. Check that ragd is working correctly
2. Index your first document
3. Search for information
4. View your knowledge base status

---

## Before You Start

Make sure you have:
- ragd installed (`pip install ragd`)
- A sample document to index (PDF, TXT, or Markdown)

Don't have a sample document? Create one:

```bash
echo "# My First Document

This is a sample document about artificial intelligence.
AI systems can process natural language and find patterns in data.
Machine learning is a subset of AI that learns from examples." > sample.md
```

---

## Step 1: Verify Installation

First, check that ragd is installed correctly:

```bash
ragd health
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✅ Storage          ChromaDB accessible                     │
│ ✅ Embedding        Model loaded successfully               │
│ ✅ Configuration    Valid configuration                     │
│ ✅ Dependencies     All packages installed                  │
└─────────────────────────────────────────────────────────────┘
```

If you see any ❌ errors, check the [Troubleshooting Guide](../guides/troubleshooting.md).

**Checkpoint:** All health checks show ✅

---

## Step 2: Check Initial Status

See the current state of your knowledge base:

```bash
ragd status
```

**Expected output (empty knowledge base):**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 0                       │          │
│ │ Chunks              │ 0                       │          │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ 💡 Get started: ragd index <path-to-documents>              │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Status shows 0 documents

---

## Step 3: Index Your First Document

Now, let's add a document to your knowledge base:

```bash
ragd index sample.md
```

**Expected output:**
```
Indexing: sample.md
  ├─ Extracting text... done
  ├─ Creating chunks... 3 chunks
  ├─ Generating embeddings... done
  └─ Storing in database... done

✅ Indexed 1 document (3 chunks)
```

**What happened?**
1. ragd read the contents of your document
2. Split the text into searchable chunks
3. Created vector embeddings for semantic search
4. Stored everything locally in ChromaDB

**Checkpoint:** Document indexed successfully with chunks created

---

## Step 4: Search Your Knowledge Base

Let's find information in your indexed document:

```bash
ragd search "what is machine learning"
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search Results for: "what is machine learning"           │
├─────────────────────────────────────────────────────────────┤
│ 1. sample.md (Score: 0.89)                                  │
│    Chunk 3 of 3                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Machine learning is a subset of AI that learns from     │ │
│ │ examples.                                               │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Notice how ragd found the relevant section even though your query ("what is machine learning") doesn't exactly match the text. This is **semantic search** - ragd understands the meaning of your query.

**Checkpoint:** Search returns relevant results with source attribution

---

## Step 5: Verify the Index Updated

Check your status again:

```bash
ragd status
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 1                       │          │
│ │ Chunks              │ 3                       │          │
│ └─────────────────────┴─────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Status shows 1 document and 3 chunks

---

## Step 6: Index More Documents

Index an entire directory of documents:

```bash
ragd index ~/Documents/notes/
```

ragd will:
- Recursively find all supported documents
- Skip duplicates automatically
- Show progress as it processes

---

## What You Learned

Congratulations! You've completed the getting started tutorial. You now know how to:

| Task | Command |
|------|---------|
| Check system health | `ragd health` |
| View knowledge base status | `ragd status` |
| Index a document | `ragd index <path>` |
| Search your knowledge | `ragd search "<query>"` |

---

## Next Steps

- **Index more documents:** Add your PDFs, notes, and research papers
- **Learn about metadata:** Organising Your Knowledge Base (v0.2)
- **Handle difficult PDFs:** Processing Difficult PDFs (v0.2)

---

## Troubleshooting

### "No results found"

- Make sure you've indexed documents first (`ragd status` to check)
- Try broader search terms
- Verify the document contains relevant content

### "Model failed to load"

- Check internet connection (model downloads on first use)
- Verify sufficient disk space (~500MB for default model)

### Other issues

See the [Troubleshooting Guide](../guides/troubleshooting.md) for more help.

---

## Related Documentation

- [UC-001: Index Documents](../use-cases/briefs/UC-001-index-documents.md)
- [UC-002: Search Knowledge](../use-cases/briefs/UC-002-search-knowledge.md)
- [UC-003: View System Status](../use-cases/briefs/UC-003-view-system-status.md)

---
