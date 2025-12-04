# Chat Interface

Interactive Q&A with your knowledge base.

**Time:** 15 minutes
**Level:** Intermediate
**Prerequisites:** Indexed documents, Ollama installed

## What You'll Learn

- Starting chat sessions
- Asking questions with context
- Using citations
- Chat commands

## Prerequisites

Install and start Ollama:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server
ollama serve

# Pull a model
ollama pull llama3.2:3b
```

## Starting a Chat

```bash
ragd chat
```

You'll see a prompt where you can ask questions:

```
ragd> What are the main findings in my research papers?
```

## Chat Commands

While in chat mode:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/quit` or `/exit` | Exit chat |
| `Ctrl+C` | Exit chat |

## Using Citations

Enable citations to verify sources:

```bash
ragd chat --cite numbered
```

Responses will include numbered references:

```
The research shows significant improvements [1].
Further analysis confirms these findings [2].

References:
[1] research-paper.pdf, p. 12
[2] analysis-report.pdf, p. 5
```

## Chat Options

### Different Model

```bash
ragd chat --model llama3.2:8b
```

### Adjust Temperature

More creative (higher temperature):

```bash
ragd chat --temperature 0.9
```

More focused (lower temperature):

```bash
ragd chat --temperature 0.3
```

### More Context

Retrieve more documents for context:

```bash
ragd chat --limit 10
```

## Verification

You've succeeded if you can:
- [ ] Start a chat session
- [ ] Ask questions and get contextual answers
- [ ] Use chat commands
- [ ] Enable citations

## Next Steps

- [Organisation](04-organisation.md) - Tags and collections
- [Automation](06-automation.md) - Scripting

---

## Troubleshooting

**"Ollama not running"**
- Start Ollama: `ollama serve`
- Check port 11434 is available

**"Model not found"**
- Pull the model: `ollama pull llama3.2:3b`

**Slow responses**
- Try a smaller model
- Reduce `--limit` for less context
