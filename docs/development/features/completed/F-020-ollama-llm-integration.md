# F-020: Ollama LLM Integration

## Overview

**Research**: [State-of-the-Art Local RAG](../../research/state-of-the-art-local-rag.md)
**Milestone**: v0.5
**Priority**: P1

## Problem Statement

ragd retrieves relevant content, but users want answers, not just sources. Integrating local LLMs via Ollama enables question-answering, summarisation, and conversation while maintaining the privacy-first principle.

## Design Approach

### Architecture

```
User Query
    ↓
Retrieval (existing pipeline)
    ↓
Context Assembly
    ↓
Ollama LLM Generation
    ↓
Response with Citations
```

### Technologies

- **Ollama**: Local LLM server
- **Models**: Llama 3.2, Qwen 2.5, Mistral
- **Streaming**: Real-time response output
- **Prompts**: RAG-optimised prompt templates

### Generation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Answer** | Single response | Quick questions |
| **Summarise** | Condense multiple sources | Overview queries |
| **Compare** | Analyse differences | Comparison queries |
| **Chat** | Multi-turn conversation | Exploration |

## Implementation Tasks

- [ ] Create Ollama client wrapper
- [ ] Implement context assembly from retrieved chunks
- [ ] Design RAG prompt templates
- [ ] Add streaming response support
- [ ] Implement citation tracking
- [ ] Create `ragd ask` command for single questions
- [ ] Create `ragd chat` command for conversation
- [ ] Add chat history persistence
- [ ] Handle Ollama unavailability gracefully
- [ ] Write unit tests for generation
- [ ] Write integration tests for full pipeline

## Success Criteria

- [ ] Natural language answers from knowledge base
- [ ] Responses cite source documents
- [ ] Streaming output for better UX
- [ ] Conversation context preserved
- [ ] Works fully offline
- [ ] Graceful degradation without Ollama

## Dependencies

- Ollama (external, must be installed)
- httpx (Ollama client)
- F-005: Semantic Search (retrieval)
- F-006: Result Formatting (output)

## Technical Notes

### Configuration

```yaml
llm:
  backend: ollama
  model: llama3.2:3b
  temperature: 0.7
  max_tokens: 1024
  ollama_url: http://localhost:11434

chat:
  history_enabled: true
  history_file: ~/.ragd/chat_history.json
  context_window: 5  # previous turns to include
```

### Ollama Client

```python
import httpx

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    def generate(
        self,
        prompt: str,
        model: str = "llama3.2:3b",
        stream: bool = True
    ) -> Iterator[str]:
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": stream},
            stream=True
        )
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("response", "")

    def is_available(self) -> bool:
        try:
            self.client.get(f"{self.base_url}/api/tags")
            return True
        except httpx.ConnectError:
            return False
```

### RAG Prompt Template

```python
RAG_PROMPT = """Answer the question based ONLY on the following context.
If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""

def generate_answer(question: str, chunks: list[Chunk]) -> str:
    context = "\n\n".join([
        f"[Source: {c.metadata['source']}]\n{c.content}"
        for c in chunks
    ])
    prompt = RAG_PROMPT.format(context=context, question=question)
    return ollama.generate(prompt)
```

### Citation Tracking

```python
@dataclass
class CitedAnswer:
    answer: str
    citations: list[Citation]

@dataclass
class Citation:
    source: str
    chunk_index: int
    relevance_score: float
    excerpt: str
```

### CLI Commands

```bash
# Single question
ragd ask "What authentication methods are recommended?"

# Chat mode
ragd chat
> How does JWT work?
> What are the security considerations?
> /exit

# Summarise topic
ragd summarise "authentication"
```

## Related Documentation

- [State-of-the-Art Local RAG](../../research/state-of-the-art-local-rag.md) - Research basis
- [State-of-the-Art RAG](../../research/state-of-the-art-rag.md) - General RAG patterns
- [v0.5.0 Milestone](../../milestones/v0.5.0.md) - Release planning
- [F-014: Agentic RAG](./F-014-agentic-rag.md) - Advanced generation

---
