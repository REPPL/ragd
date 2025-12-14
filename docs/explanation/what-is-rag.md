# What is RAG?

RAG (Retrieval-Augmented Generation) lets AI answer questions using your documents.

## The Problem RAG Solves

AI chatbots like ChatGPT are trained on public internet data. They can't know about:
- Your personal notes
- Your company's documents
- Research papers you've collected
- Meeting notes from last week

You could paste documents into the chat, but that's tedious and limited by context windows.

**RAG solves this** by automatically finding relevant parts of your documents and giving them to the AI as context.

## How RAG Works

Think of it like asking a librarian who:
1. Understands your question
2. Finds relevant books and pages
3. Reads those pages
4. Answers based on what they read

RAG follows the same three steps:

### 1. Retrieval
Find relevant pieces of your documents. ragd splits your documents into chunks and uses semantic search to find the ones most related to your question.

### 2. Augmentation
Add those pieces to the AI's context. The AI receives your question plus the relevant chunks as background information.

### 3. Generation
Create an answer grounded in your documents. The AI generates a response based on the retrieved context, often with citations.

## ragd's Query Commands

ragd provides three ways to query your documents:

| Command | What it does | Needs AI? |
|---------|-------------|-----------|
| `ragd search` | Find relevant excerpts | No |
| `ragd ask` | Get an AI-generated answer | Yes |
| `ragd chat` | Have a conversation | Yes |

**Not sure which to use?** See [Choosing the Right Command](../guides/cli/command-comparison.md).

## Why Local RAG?

ragd runs entirely on your machine:

- **Privacy**: Your documents never leave your computer
- **No API costs**: Uses local AI models via Ollama
- **Works offline**: No internet required after setup
- **You own your data**: No cloud services, no subscriptions

## Technical Details

For those who want to understand more:

- **Embeddings**: Documents are converted to vectors that capture meaning
- **Vector search**: Finds similar vectors using cosine similarity
- **Hybrid search**: Combines vector search with keyword matching
- **Chunking**: Documents are split into overlapping pieces for better retrieval

See [Hybrid Search](./hybrid-search.md) and [Chunking Strategies](./chunking-strategies.md) for deeper explanations.

---

## Related Documentation

- [Choosing the Right Command](../guides/cli/command-comparison.md) - search vs ask vs chat
- [Hybrid Search](./hybrid-search.md) - How retrieval works
- [Model Purposes](./model-purposes.md) - Understanding the different AI models
- [Getting Started Tutorial](../tutorials/01-getting-started.md) - Hands-on introduction
- [RAG Alternatives](./alternatives.md) - Other tools if ragd doesn't fit your needs
