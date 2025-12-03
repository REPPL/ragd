# Chatting with Your Knowledge Base

Learn to use ragd's chat interface to have natural conversations about your documents.

## Prerequisites

Before starting this tutorial, ensure you have:

1. **ragd installed and configured** - See [Getting Started](./getting-started.md)
2. **Documents indexed** - At least a few documents in your knowledge base
3. **Ollama installed and running** - Visit [ollama.ai](https://ollama.ai) for installation

## Step 1: Verify Ollama is Running

First, check that Ollama is available:

```bash
ollama list
```

You should see at least one model. If not, pull a recommended model:

```bash
ollama pull llama3.2:3b
```

Verify ragd can connect to Ollama:

```bash
ragd doctor
```

Look for:
```
LLM
  [OK] Ollama available
  [OK] Model llama3.2:3b ready
```

## Step 2: Ask a Single Question

The simplest way to query your knowledge is with `ragd ask`:

```bash
ragd ask "What is the main topic of my documents?"
```

You'll see:
1. A progress indicator while ragd searches
2. An AI-generated answer based on your documents
3. Sources cited at the end

### Understanding the Output

```
ragd ask "What authentication methods are discussed?"

Searching knowledge base...

Based on your documents, the authentication methods discussed include:

1. **OAuth 2.0** - For third-party service integration
2. **JWT tokens** - For stateless API authentication
3. **Session cookies** - For web application state

The security policy recommends using JWT for new APIs.

[Sources: security-policy.pdf:12, api-design.md:45]
```

## Step 3: Start an Interactive Chat

For a more conversational experience, start a chat session:

```bash
ragd chat
```

You'll enter an interactive mode:

```
Welcome to ragd chat! Type /help for commands, /exit to quit.
Model: llama3.2:3b

>
```

### Having a Conversation

Try asking follow-up questions:

```
> What authentication methods are discussed?

Based on your documents, the main authentication methods are...

> Which one is recommended for new projects?

According to the security policy (security-policy.pdf:15),
JWT tokens are recommended for new API projects because...

> What are the security considerations?

The documents highlight several security considerations for JWT:
1. Token expiry times should be kept short
2. Use HTTPS for all token transmission
3. Store tokens securely...
```

Notice how ragd remembers the conversation context and can answer follow-up questions naturally.

## Step 4: Use Chat Commands

While in chat mode, you can use special commands:

| Command | What it Does |
|---------|--------------|
| `/help` | Show all available commands |
| `/sources` | Show sources from the last response |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |
| `/exit` | Exit the chat |

Try it:

```
> /sources

Sources from last response:
  [1] security-policy.pdf, pages 15-17
  [2] api-design.md, section "Authentication"
  [3] best-practices.txt, lines 45-60

> /clear

Conversation cleared. Starting fresh!

> /exit

Session saved. Goodbye!
```

## Step 5: Enable Agentic Mode

For complex questions, ragd can use agentic RAG to improve results:

```bash
ragd ask "Compare the pros and cons of all approaches" --agentic --show-confidence
```

With agentic mode enabled:
- **CRAG** - Automatically rewrites queries if initial results aren't relevant
- **Self-RAG** - Evaluates its own answers and refines them

Output includes confidence scores:

```
Comparing the approaches discussed in your documents...

[Confidence: 0.87]

OAuth 2.0:
  Pros: Industry standard, wide library support
  Cons: Complex implementation, requires refresh tokens

JWT:
  Pros: Stateless, scales well, works offline
  Cons: Token size, cannot revoke individual tokens

Session Cookies:
  Pros: Simple, browser-native
  Cons: Stateful, CSRF vulnerability
```

## Step 6: Work with Named Sessions

Save and resume conversations:

```bash
# Start a named session
ragd chat --session security-review

# ... have your conversation ...

# Later, resume the same session
ragd chat --session security-review
```

Your conversation history is preserved between sessions.

## Tips and Best Practices

### Ask Specific Questions

**Good:** "What ports need to be open for the API server?"
**Less Good:** "Tell me about the network"

### Provide Context in Follow-ups

**Good:** "What about the authentication endpoint specifically?"
**Less Good:** "What about that?"

### Use Sources to Verify

Always check the sources to verify the AI's claims:

```
> /sources
```

Then you can read the original documents if needed.

## Troubleshooting

### "Cannot connect to Ollama"

Ensure Ollama is running:
```bash
ollama serve
```

### "Model not found"

Pull the required model:
```bash
ollama pull llama3.2:3b
```

### Slow Responses

Try a smaller model:
```bash
ragd chat --model llama3.2:1b
```

Or check if your system has GPU acceleration:
```bash
ragd status --detailed
```

## Next Steps

- Explore [CLI Reference](../reference/cli-reference.md) for all options
- Learn about [Evaluation](../reference/cli-reference.md#ragd-evaluate) to measure quality
- Try different models to find your preferred balance of speed and quality

---

## Related Documentation

- [Getting Started](./getting-started.md) - First steps with ragd
- [CLI Reference](../reference/cli-reference.md) - Complete command reference
- [F-020: Ollama LLM Integration](../development/features/completed/F-020-ollama-llm-integration.md)

