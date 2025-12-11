# CLI Essentials

The 6 core commands you need to be productive with ragd.

**Time:** 20 minutes
**Prerequisite:** ragd installed

---

## The Essential Commands

### Setup & Status

| Command | Purpose |
|---------|---------|
| `ragd doctor` | Run health checks |
| `ragd info` | View statistics |

### Document Management

| Command | Purpose |
|---------|---------|
| `ragd index` | Add documents |

### Query Commands

| Command | Purpose | Requires LLM |
|---------|---------|--------------|
| `ragd search` | Find document excerpts | No |
| `ragd ask` | Get AI-generated answer | Yes |
| `ragd chat` | Interactive conversation | Yes |

> **Not sure which query command to use?** See [Choosing the Right Command](./command-comparison.md).

---

## 1. ragd doctor

**Run health checks on ragd components.**

```bash
ragd doctor
```

**What it does:**
- Verifies ChromaDB storage is accessible
- Checks embedding model loads correctly
- Validates configuration
- Confirms dependencies are installed

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│ ✅ Storage          ChromaDB accessible                     │
│ ✅ Embedding        Model loaded successfully               │
│ ✅ Configuration    Valid configuration                     │
│ ✅ Dependencies     All packages installed                  │
└─────────────────────────────────────────────────────────────┘
```

**If something fails:** See [Troubleshooting Guide](../troubleshooting.md)

---

## 2. ragd index

**Add documents to your knowledge base.**

```bash
# Index a single file
ragd index document.pdf

# Index a directory
ragd index ~/Documents/notes/

# Index with verbose output
ragd index report.pdf --verbose
```

**What it does:**
1. Reads document content
2. Splits text into searchable chunks
3. Creates vector embeddings
4. Stores in local database

**Expected output:**
```
Indexing: document.pdf
  ├─ Extracting text... done
  ├─ Creating chunks... 47 chunks
  ├─ Generating embeddings... done
  └─ Storing in database... done

✅ Indexed 1 document (47 chunks)
```

**Supported formats:** PDF, Markdown, Plain text, HTML

---

## 3. ragd search

**Find information in your knowledge base.** Returns document excerpts directly - no AI generation.

```bash
# Basic search
ragd search "your question here"

# Limit results
ragd search "machine learning" --limit 5

# JSON output for scripts
ragd search "neural networks" --format json --no-interactive
```

**What it does:**
1. Converts your query to a vector embedding
2. Finds semantically similar chunks
3. Returns ranked results with sources

### Interactive Navigator

By default, search opens an interactive navigator:

| Key | Action |
|-----|--------|
| `j` or `↓` | Next result |
| `k` or `↑` | Previous result |
| `Enter` | View full content |
| `q` or `Esc` | Exit navigator |

To print results directly without the navigator:

```bash
ragd search "query" --no-interactive
```

**Tip:** Search understands meaning, not just keywords. Ask natural questions!

---

## 4. ragd ask

**Get an AI-generated answer from your documents.** Requires Ollama to be running.

```bash
# Basic question
ragd ask "What are the main findings?"

# With a specific model
ragd ask "Summarise the report" --model llama3.2:8b

# Complex question with agentic mode
ragd ask "Compare the three approaches" --agentic
```

**What it does:**
1. Retrieves relevant document chunks (like search)
2. Sends chunks + question to Ollama LLM
3. Generates an answer grounded in your documents
4. Returns answer with source citations

**Expected output:**
```
Based on the indexed documents, the main findings are:

1. Revenue increased by 15% year-over-year [1]
2. Customer satisfaction improved to 4.2/5 [2]
3. Operational costs decreased by 8% [1]

Sources:
[1] quarterly-report.pdf, p. 3
[2] customer-survey.pdf, p. 12
```

**Key options:**
- `--agentic`: Enable advanced retrieval with query rewriting
- `--cite none`: Disable citations
- `--show-confidence`: Display confidence score

---

## 5. ragd chat

**Interactive conversation with your knowledge base.** Requires Ollama to be running.

```bash
ragd chat
```

**What it does:**
- Maintains conversation history
- Retrieves context for each question
- Remembers previous Q&A for follow-ups

**Example session:**
```
You: What does the report say about authentication?
Assistant: The report recommends multi-factor authentication... [1]

You: What alternatives does it mention?
Assistant: It also discusses biometric options and... [2]

You: /quit
```

**Chat commands:**

| Command | Action |
|---------|--------|
| `/search <query>` | Search documents (use `-n N` to limit) |
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/quit` or `/exit` | Exit chat |
| `Ctrl+C` | Exit chat |

---

## 6. ragd info

**View the state of your knowledge base.**

```bash
ragd info
```

**What it does:**
- Shows document count
- Shows chunk/embedding count
- Displays storage usage
- Shows configuration summary

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Status Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│ ✅ System Ready                                             │
├─────────────────────────────────────────────────────────────┤
│ 📚 Index Statistics                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Documents           │ 42                      │          │
│ │ Chunks              │ 1,247                   │          │
│ └─────────────────────┴─────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Options

These flags work with most commands:

| Flag | Short | Purpose |
|------|-------|---------|
| `--help` | `-h` | Show help for command |
| `--format` | `-f` | Output format (rich/plain/json) |
| `--no-color` | | Disable coloured output |

**Examples:**
```bash
ragd search --help          # Help for search command
ragd --version              # Show version
ragd info --format json     # JSON output
```

---

## What's Next?

You've learned the essentials! When you're ready:

- **[Command Comparison](./command-comparison.md)** - When to use search vs ask vs chat
- **[Intermediate Guide](./intermediate.md)** - Task-specific workflows
- **[Advanced Guide](./advanced.md)** - Configuration and debugging
- **[Reference](./reference.md)** - Complete command specifications

---

## Related Documentation

- [What is RAG?](../../explanation/what-is-rag.md) - Understanding retrieval-augmented generation
- [CLI Reference](../../reference/cli-reference.md) - Complete command specifications
- [Getting Started Tutorial](../../tutorials/01-getting-started.md) - First-time setup
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and solutions

---
