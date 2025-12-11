# Choosing the Right Command

ragd provides three ways to query your knowledge base. This guide helps you choose.

## Quick Decision

| I want to... | Use | Example |
|--------------|-----|---------|
| Find relevant document excerpts | `ragd search` | `ragd search "budget projections"` |
| Get an AI-generated answer | `ragd ask` | `ragd ask "What were the Q3 results?"` |
| Have a back-and-forth conversation | `ragd chat` | `ragd chat` |

## The Three Query Commands

### ragd search - Find Information

**What it does:** Returns relevant excerpts directly from your documents.

**Use when:**
- You want to see the actual text in your documents
- You're exploring what's in your knowledge base
- You don't need AI synthesis
- You want fast results without an LLM

**Output:** Document chunks with source references and relevance scores.

**Example:**
```bash
ragd search "machine learning techniques"
```

**Key features:**
- Interactive navigator (j/k to move, q to quit)
- Three search modes: hybrid (default), semantic, keyword
- Filter by tags
- No LLM required

### ragd ask - Get Answers

**What it does:** Retrieves relevant context, then uses an AI to generate an answer.

**Use when:**
- You want a synthesised answer, not raw excerpts
- You have a specific question
- You want citations to verify the answer
- You need one answer, not a conversation

**Output:** AI-generated response with source citations.

**Example:**
```bash
ragd ask "What are the main recommendations in the security report?"
```

**Key features:**
- Single question, single answer
- Source citations
- Agentic mode (`--agentic`) for complex questions
- Configurable model and temperature

### ragd chat - Conversation

**What it does:** Interactive multi-turn dialogue with your knowledge base.

**Use when:**
- You have follow-up questions
- You want to explore a topic in depth
- You need clarification or elaboration
- Context from earlier questions matters

**Output:** Ongoing conversation with citations.

**Example:**
```bash
ragd chat
You: What does the report say about authentication?
Assistant: The report recommends... [1]
You: What alternatives does it mention?
Assistant: It also discusses... [2]
```

**Key features:**
- Multi-turn memory
- In-chat commands (/help, /search, /clear)
- Session history
- Configurable citations

## Feature Comparison

| Feature | search | ask | chat |
|---------|:------:|:---:|:----:|
| Returns raw document excerpts | Yes | No | No |
| Generates AI answer | No | Yes | Yes |
| Remembers previous questions | No | No | Yes |
| Requires Ollama | No | Yes | Yes |
| Interactive mode | Navigator | No | REPL |
| Agentic mode available | No | Yes | No |
| In-session search | No | No | Yes (`/search`) |

## Progression: From Retrieval to Conversation

```
search          ask             chat
   |              |               |
   v              v               v
Retrieval    Retrieval +     Retrieval +
  only       Generation      Multi-turn
                             Generation
   |              |               |
   v              v               v
 Fast          Single          Dialogue
              question
```

## Common Workflows

### Quick Fact-Finding
```bash
ragd search "quarterly revenue"
```
Fast, no LLM needed. Browse results interactively.

### Research Question
```bash
ragd ask "What methodology was used in the Smith et al. study?"
```
Get a synthesised answer with citations.

### Deep Exploration
```bash
ragd chat
```
Ask questions, get answers, follow up, clarify.

### Complex Analysis
```bash
ragd ask "Compare the three proposed solutions" --agentic
```
Agentic mode evaluates retrieval quality and refines the answer.

## LLM Requirements

| Command | Ollama Required | Why |
|---------|-----------------|-----|
| `search` | No | Pure retrieval - no generation |
| `ask` | Yes | Needs LLM to generate answer |
| `chat` | Yes | Needs LLM for conversation |

If Ollama isn't running, `ask` and `chat` will show an error with setup instructions.

---

## Related Documentation

- [What is RAG?](../../explanation/what-is-rag.md) - Understanding retrieval-augmented generation
- [CLI Essentials](./essentials.md) - Core command reference
- [Chat Interface Tutorial](../../tutorials/03-chat-interface.md) - Hands-on chat guide
- [Searching Tutorial](../../tutorials/02-searching.md) - Master search queries
