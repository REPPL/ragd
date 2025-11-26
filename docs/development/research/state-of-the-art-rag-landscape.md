# State-of-the-Art RAG Tool Landscape

Comprehensive analysis of open-source RAG tools and frameworks to inform ragd's differentiation strategy.

## Executive Summary

The open-source RAG ecosystem has exploded since 2023, with dozens of tools competing for developers' attention. This analysis maps the landscape across four categories:

1. **Local Document Chat** - Privacy-focused tools for querying personal documents
2. **Enterprise Search** - Multi-user platforms with governance and integrations
3. **RAG Frameworks** - Developer libraries for building custom RAG systems
4. **Model Runners** - Local LLM inference engines with RAG capabilities

**Key market insight**: The market for RAG frameworks is estimated at $1.85 billion in 2025, with rapid growth driven by demand for real-time, accurate data retrieval.

**ragd's opportunity**: Most tools optimise for either simplicity (desktop apps) or enterprise scale (cloud-first). Few serve the **CLI-native developer** who wants programmatic control without a web interface.

---

## Category 1: Local Document Chat

Tools designed for individuals to query their documents privately.

### PrivateGPT

**GitHub**: [zylon-ai/private-gpt](https://github.com/zylon-ai/private-gpt) | **Stars**: ~54K

**Positioning**: "Interact with your documents using the power of GPT, 100% privately"

**Architecture**:
- Built on FastAPI + LlamaIndex
- OpenAI-compatible API
- Zero-trust, fully offline capable
- Modular: swap LLM, embeddings, or vector store independently

**Key Features**:
- High-level API abstracting RAG complexity (ingestion, retrieval, generation)
- Document parsing for PDF, DOCX, TXT, Markdown
- Streaming responses
- Enterprise edition (Zylon) for on-premise deployment

**Strengths**:
- Simplest path from "I have documents" to "I can chat with them"
- Strong privacy narrative (no data leaves device)
- Large community (25+ merged PRs monthly, 4,000+ Discord members)

**Weaknesses**:
- Single-user focus (no workspace/team features)
- Limited agent capabilities
- Web UI only (no CLI interface)

**What ragd can learn**:
- The High-level API design that "just works" for common use cases
- Privacy-first messaging resonates strongly
- The modular swap-any-component architecture

---

### AnythingLLM

**GitHub**: [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | **Stars**: ~45K

**Positioning**: "The all-in-one Desktop & Docker AI application with built-in RAG, AI agents, No-code agent builder, MCP compatibility"

**Architecture**:
- Full-stack application (React + Node.js)
- LanceDB as default vector store (bundled, zero-config)
- Supports 40+ LLM providers (local and cloud)
- Desktop app, Docker, or cloud deployment

**Key Features**:
- Multi-user workspaces with role-based access
- No-code agent builder
- MCP (Model Context Protocol) compatibility
- Document chat with workspace isolation

**Strengths**:
- Best-in-class onboarding experience (desktop app "just works")
- Multi-user and team governance features
- Extensive LLM provider support
- Active development cadence

**Weaknesses**:
- Heavy stack (Electron desktop app)
- No CLI interface for automation
- Docker networking often causes "can't reach model" errors

**What ragd can learn**:
- LanceDB bundling eliminates vector store setup friction
- Workspace concept for document organisation
- The "no frustrating setup required" promise

---

### Khoj

**GitHub**: [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | **Stars**: ~31K

**Positioning**: "Your AI second brain. Self-hostable. Get answers from the web or your docs."

**Architecture**:
- Python backend with FastAPI
- Supports Ollama, OpenAI, Anthropic, local GGUF models
- Web, Desktop, Mobile, Obsidian, Emacs, WhatsApp integrations

**Key Features**:
- Multi-platform presence (browser, Obsidian, Emacs, mobile, WhatsApp)
- Custom agents with scheduled automations
- "Deep research" mode for complex queries
- Image generation capabilities

**Strengths**:
- Broadest platform coverage (from Emacs to WhatsApp)
- Strong Obsidian integration (knowledge management sweet spot)
- Scheduled automations differentiate from pure chat tools

**Weaknesses**:
- Complexity from supporting many platforms
- AGPLv3 licence may concern some enterprise users
- Less focus on document processing quality

**What ragd can learn**:
- Obsidian/note-taking integration is high-value
- Scheduled automations extend utility beyond chat
- The "second brain" positioning

---

### GPT4All

**GitHub**: [nomic-ai/gpt4all](https://github.com/nomic-ai/gpt4all) | **Stars**: ~75K+

**Positioning**: "Run Large Language Models Locally and Privately"

**Architecture**:
- Qt desktop application (replaced Electron in v3.0)
- llama.cpp backend with auto GPU detection (CUDA, Metal, Vulkan)
- LocalDocs for RAG (HNSW index with SPECTRE embeddings)

**Key Features**:
- LocalDocs: drag-and-drop PDF/Markdown ingestion
- Watch-folder daemon (auto-index new files)
- Hot-swap model gallery (v3.0, July 2024)
- Native Windows ARM support (v3.7, January 2025)

**Roadmap Focus**:
- NPU acceleration (Apple, Qualcomm silicon)
- No-code LoRA fine-tuning UI
- Structured outputs (JSON, XML)

**Strengths**:
- Lightweight Qt app (not Electron bloat)
- LocalDocs adds minimal latency (~0.1s on modern hardware)
- Strong nomic.ai integration (their embedding models)

**Weaknesses**:
- RAG features less sophisticated than dedicated tools
- Desktop-only (no web interface option)
- Limited document type support

**What ragd can learn**:
- Watch-folder for automatic re-indexing
- GPU auto-detection and allocation strategies
- Qt > Electron for desktop performance

---

## Category 2: Enterprise Search

Tools designed for team collaboration with governance, integrations, and scale.

### Onyx (formerly Danswer)

**GitHub**: [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | **Stars**: ~15K+

**Positioning**: "Open Source AI Platform - AI Chat with advanced features that works with every LLM"

**Background**: YC W24 company, rebranded from Danswer to Onyx

**Architecture**:
- Vespa as search backend (replaced earlier vector DB)
- Hybrid search + knowledge graphs
- 40+ connectors for enterprise data sources
- MIT licence (Community Edition), proprietary (Enterprise)

**Key Features**:
- Enterprise-grade: SSO (OIDC/SAML/OAuth2), RBAC, credential encryption
- Connectors to Slack, Confluence, Google Drive, GitHub, etc.
- Knowledge graph extraction from documents
- Citation tracking (traces claims to source docs)

**Scale Target**: Tens of millions of documents

**Strengths**:
- Vespa backend enables true enterprise scale
- Most comprehensive connector ecosystem
- Strong governance features (access control, audit trails)

**Weaknesses**:
- Complex deployment (many moving parts)
- Primarily cloud/Docker focused
- Overkill for individual use

**What ragd can learn**:
- Citation/source tracking is essential for trust
- Multi-vector embeddings (Vespa capability) for chunk-level retrieval
- Connector architecture for extensibility

---

### Quivr

**GitHub**: [QuivrHQ/quivr](https://github.com/QuivrHQ/quivr) | **Stars**: ~28K

**Positioning**: "Opinionated RAG for integrating GenAI in your apps"

**Background**: YC W24 company, pivoted from consumer "second brain" to developer RAG framework

**Architecture**:
- Modular: any LLM (GPT-4, Groq, Llama), any vectorstore (PGVector, Faiss)
- Megaparse for document ingestion
- Le Juge for RAG evaluation

**Ecosystem**:
- **Megaparse**: Open-source document parsing (handles complex PDFs, tables)
- **Quivr Core**: RAG engine
- **Le Juge**: Evaluation framework for RAG quality

**Key Features**:
- Internet search integration
- Tool/plugin system for extending capabilities
- Offline mode
- Multi-format support (PDF, CSV, Excel, Word, Audio, Video)

**Strengths**:
- Clean separation of concerns (parsing, RAG, evaluation)
- Strong PDF/document parsing with Megaparse
- Both consumer and developer positioning

**Weaknesses**:
- Direction unclear after pivot
- Less active recently compared to peak
- Complex stack for simple use cases

**What ragd can learn**:
- Megaparse approach to document parsing
- Building evaluation into the ecosystem (Le Juge)
- Audio/video ingestion as future capability

---

## Category 3: RAG Frameworks

Developer libraries for building custom RAG systems.

### RAGFlow

**GitHub**: [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | **Stars**: ~40K+

**Positioning**: "Leading open-source RAG engine that fuses cutting-edge RAG with Agent capabilities"

**Background**: Open-sourced April 2024, rapid growth to 40K+ stars

**Architecture**:
- Visual DAG editor for pipeline construction
- Deep document understanding (tables, layouts, images from PDFs)
- GraphRAG support for knowledge graphs
- RAPTOR for hierarchical document summarisation

**Key Features**:
- Text2SQL for querying structured databases
- Citation tracking with source document links
- Slim (2GB) and full (9GB) Docker images
- Visual workflow builder (no-code friendly)

**Technical Capabilities**:
- RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval
- GraphRAG: Knowledge graph extraction and traversal
- Agentic reasoning with tool use

**Strengths**:
- "Quality-in, quality-out" philosophy
- Best-in-class document parsing (especially complex PDFs)
- Visual pipeline builder lowers barrier to entry
- Comprehensive feature set

**Weaknesses**:
- Docker-heavy deployment
- Web UI required (no pure CLI option)
- Resource-intensive for full features

**What ragd can learn**:
- Deep document understanding is a differentiator
- GraphRAG integration patterns
- RAPTOR for long documents

---

### LlamaIndex

**Repository**: [run-llama/llama_index](https://github.com/run-llama/llama_index) | **Stars**: ~40K+

**Positioning**: "Data framework for LLM applications"

**Architecture**:
- Python-first library
- Extensive indexing strategies (vector, tree, keyword, knowledge graph)
- First-class streaming support
- Integrations with 100+ data sources

**Key Features**:
- PropertyGraphIndex for knowledge graph RAG
- Advanced retrieval: HyDE, sentence-window, auto-merging
- Production-ready with LlamaCloud option
- Comprehensive evaluation toolkit

**Strengths**:
- Most sophisticated indexing and retrieval strategies
- Strong documentation and tutorials
- Active core team and community
- Clean abstractions for extension

**Weaknesses**:
- Library, not application (requires coding)
- Can be overwhelming for beginners
- Some abstractions add complexity

**What ragd can learn**:
- PropertyGraphIndex architecture
- Advanced retrieval strategies (HyDE, sentence-window)
- Abstraction design for extensibility

---

### LangChain

**Repository**: [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | **Stars**: ~100K+

**Positioning**: "Build context-aware reasoning applications"

**Architecture**:
- Chain abstraction for composing LLM operations
- 700+ tool integrations
- LangGraph for agentic workflows
- LangSmith for observability

**Key Features**:
- LCEL (LangChain Expression Language) for pipeline composition
- Extensive retriever implementations
- Memory management for conversations
- Agent frameworks (ReAct, OpenAI functions, etc.)

**Strengths**:
- Largest ecosystem and community
- Most integrations available
- Strong observability with LangSmith
- Rapid feature development

**Weaknesses**:
- Abstraction overhead can hurt performance
- Frequent breaking changes
- "Framework lock-in" concerns

**What ragd can learn**:
- The value of extensive integrations
- LangSmith-style observability for debugging
- Memory management patterns

---

## Category 4: Model Runners with RAG

LLM inference tools that have added RAG capabilities.

### LM Studio

**Website**: [lmstudio.ai](https://lmstudio.ai) | **Closed source (free)**

**Positioning**: "Local AI on your computer"

**Architecture**:
- Desktop application (Mac, Windows, Linux)
- llama.cpp backend with MLX for Apple Silicon
- OpenAI-compatible API server
- Built-in model discovery and download

**Key Features**:
- Built-in naive RAG (v0.3.0, 2024)
- Drag-and-drop document chat (PDF, DOCX, TXT, MD)
- Structured outputs API (JSON schema)
- Multi-GPU support with allocation strategies
- Python and TypeScript SDKs (v1.0.0)

**Strengths**:
- Polished UI/UX for model management
- Fast inference (MLX on Apple Silicon)
- OpenAI API compatibility enables ecosystem tools
- Active development with frequent updates

**Weaknesses**:
- Not open source
- RAG is "naive" (basic chunking, no advanced retrieval)
- Desktop only

**What ragd can learn**:
- Model discovery and download UX
- OpenAI API compatibility is essential
- SDK-first developer experience

---

### Jan

**GitHub**: [janhq/jan](https://github.com/janhq/jan) | **Stars**: ~30K+

**Positioning**: "Open-source ChatGPT replacement that runs 100% offline"

**Architecture**:
- Powered by Cortex.cpp (multi-engine: llama.cpp, ONNX, TensorRT-LLM)
- OpenAI-compatible local API
- Desktop application (Electron)
- MCP server support

**Key Features**:
- 70+ pre-configured models
- Context retention (email, files, calendar integration)
- Extension system (VSCode/Obsidian-like)
- AGPLv3 open source

**Strengths**:
- Multi-engine support (not just llama.cpp)
- MCP integration for tool use
- Extension architecture for customisation
- Strong privacy stance

**Weaknesses**:
- Electron app (heavier than Qt)
- AGPLv3 may concern some users
- Less focus on RAG (more on chat)

**What ragd can learn**:
- Multi-engine architecture (llama.cpp, ONNX, TensorRT)
- Extension system design
- Context retention across sessions

---

### Ollama

**Repository**: [ollama/ollama](https://github.com/ollama/ollama) | **Stars**: ~130K+

**Positioning**: "Get up and running with large language models"

**Architecture**:
- Go-based CLI and server
- Custom Modelfile format for model configuration
- OpenAI-compatible API
- Native GPU support (CUDA, Metal, ROCm)

**Key Features**:
- One-command model download and run
- Modelfile for custom model configuration
- Embedding API for RAG integrations
- Excellent performance on Apple Silicon

**Strengths**:
- Simplest UX in the space (`ollama run llama3`)
- Strong ecosystem integration (used by many RAG tools)
- Active development, frequent updates
- Small binary, fast startup

**Weaknesses**:
- No built-in RAG (requires external tools)
- Limited model customisation UI
- CLI only (which is a feature for some)

**What ragd can learn**:
- The power of one-command simplicity
- Modelfile format for configuration
- CLI-native design can win

---

### Perplexica

**GitHub**: [ItzCrazyKns/Perplexica](https://github.com/ItzCrazyKns/Perplexica) | **Stars**: ~20K+

**Positioning**: "Open-source alternative to Perplexity AI"

**Architecture**:
- SearxNG for web search
- Supports local LLMs (Ollama) and cloud providers
- TypeScript/Next.js stack
- Docker deployment

**Key Features**:
- Six focus modes (Academic, YouTube, Reddit, Wolfram, Writing, Web)
- File upload for document Q&A
- Source citation with links
- Balanced/Fast/Quality search modes

**Strengths**:
- Web search integration (not just document RAG)
- Focus modes for specialised queries
- Clean, modern UI

**Weaknesses**:
- More search engine than document RAG
- Requires SearxNG setup
- Less active than leading tools

**What ragd can learn**:
- Focus modes for query specialisation
- Web search integration patterns
- Search quality vs speed trade-offs

---

## Community Health Comparison

| Tool | Stars | Last Commit | Discord/Community | Licence |
|------|-------|-------------|-------------------|---------|
| **Ollama** | ~130K | Daily | Active | MIT |
| **LangChain** | ~100K | Daily | Very Active | MIT |
| **GPT4All** | ~75K | Weekly | Active | MIT |
| **PrivateGPT** | ~54K | Weekly | 4,000+ Discord | Apache-2.0 |
| **AnythingLLM** | ~45K | Daily | Active | MIT |
| **LlamaIndex** | ~40K | Daily | Very Active | MIT |
| **RAGFlow** | ~40K | Daily | Growing | Apache-2.0 |
| **Khoj** | ~31K | Weekly | Active | AGPL-3.0 |
| **Jan** | ~30K | Weekly | Active | AGPL-3.0 |
| **Quivr** | ~28K | Monthly | Moderate | AGPL-3.0 |
| **Perplexica** | ~20K | Weekly | Moderate | MIT |
| **Onyx** | ~15K | Daily | Active | MIT/Proprietary |

---

## Feature Matrix

| Feature | PrivateGPT | AnythingLLM | Khoj | RAGFlow | Ollama |
|---------|-----------|-------------|------|---------|--------|
| **CLI Interface** | No | No | Limited | No | Yes |
| **Web UI** | Yes | Yes | Yes | Yes | No |
| **Desktop App** | No | Yes | Yes | No | No |
| **Multi-user** | No | Yes | Yes | Yes | No |
| **Knowledge Graphs** | No | No | No | Yes | No |
| **Agent Support** | Limited | Yes | Yes | Yes | No |
| **Offline-first** | Yes | Yes | Yes | Yes | Yes |
| **API Server** | Yes | Yes | Yes | Yes | Yes |
| **Document Parsing** | Good | Good | Basic | Excellent | N/A |
| **Embedding Models** | Pluggable | Pluggable | Pluggable | Built-in | Built-in |

---

## Gap Analysis: Where ragd Fits

### Underserved Needs

1. **CLI-Native Workflow**
   - Ollama proves CLI-first can win (~130K stars)
   - No RAG tool offers true CLI-native experience
   - Developers want scripting, piping, automation

2. **Progressive Complexity**
   - Most tools are either too simple (GPT4All) or too complex (LangChain)
   - Few offer smooth progression from beginner to expert

3. **Transparent Operations**
   - Black-box RAG frustrates debugging
   - Need visibility into retrieval, ranking, generation

4. **Lightweight Local-First**
   - Many tools require Docker, databases, complex setup
   - Developers want `pip install && ragd init && ragd query`

5. **Framework + Application**
   - Most tools are either library (LlamaIndex) or application (AnythingLLM)
   - Few bridge both effectively

### ragd's Differentiation Strategy

| Dimension | Current Tools | ragd Opportunity |
|-----------|---------------|------------------|
| **Interface** | Web UI primary | CLI-first, TUI optional |
| **Complexity** | Fixed level | Progressive (user → expert modes) |
| **Transparency** | Black-box | Verbose/debug modes, explain retrieval |
| **Setup** | Docker/complex | Single binary, uv install |
| **Extensibility** | Plugins/apps | Unix philosophy (pipes, scripts) |
| **Target User** | End users | Developers and power users |

### Recommended Positioning

> **ragd**: The CLI-native RAG toolkit for developers who want control, transparency, and Unix-philosophy composability.

**Not competing with**:
- AnythingLLM (desktop app for teams)
- RAGFlow (enterprise visual workflows)
- LangChain (framework for custom apps)

**Directly competing with**:
- PrivateGPT (but CLI instead of web)
- Khoj (but developer-focused instead of consumer)
- Custom LlamaIndex scripts (but batteries-included)

---

## Key Takeaways for ragd

### Design Principles from the Landscape

1. **Ollama's Simplicity**: One command to get started (`ragd query "what is X"`)
2. **PrivateGPT's Modularity**: Swap embeddings, LLM, or vector store independently
3. **AnythingLLM's Zero-Config**: Bundle LanceDB, auto-detect hardware
4. **GPT4All's Watch-Folder**: Automatic re-indexing on file changes
5. **RAGFlow's Citation**: Always show sources for trust
6. **Khoj's Scheduling**: Extend beyond chat to automation
7. **LM Studio's SDKs**: Python/TypeScript SDKs for developers

### Technical Choices Validated

| Choice | Validation |
|--------|------------|
| **Typer + Rich** | CLI tools dominate (Ollama 130K stars) |
| **LanceDB** | Bundled by AnythingLLM, zero-config |
| **Ollama integration** | Ecosystem standard for local LLMs |
| **nomic embeddings** | GPT4All uses SPECTRE, nomic ecosystem strong |
| **Progressive disclosure** | Addresses complexity gap in market |

### Features to Prioritise

**v0.1 (Core)**:
- CLI document ingestion and query
- Ollama + nomic integration
- LanceDB vector store
- Source citations in responses

**v0.2 (Developer Experience)**:
- Verbose/debug mode (show retrieval process)
- Python SDK
- Watch-folder for auto-indexing
- OpenAI-compatible API server

**v0.3+ (Differentiation)**:
- Expert mode with retrieval tuning
- Pipeline composition (Unix pipes)
- GraphRAG integration (Kuzu)
- Evaluation toolkit

---

## References

### Tool Repositories

- [PrivateGPT](https://github.com/zylon-ai/private-gpt)
- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm)
- [Khoj](https://github.com/khoj-ai/khoj)
- [GPT4All](https://gpt4all.io)
- [Onyx/Danswer](https://github.com/onyx-dot-app/onyx)
- [Quivr](https://github.com/QuivrHQ/quivr)
- [RAGFlow](https://github.com/infiniflow/ragflow)
- [LlamaIndex](https://github.com/run-llama/llama_index)
- [LangChain](https://github.com/langchain-ai/langchain)
- [LM Studio](https://lmstudio.ai)
- [Jan](https://github.com/janhq/jan)
- [Ollama](https://github.com/ollama/ollama)
- [Perplexica](https://github.com/ItzCrazyKns/Perplexica)

### Analysis Sources

- [15 Best Open-Source RAG Frameworks in 2025](https://www.firecrawl.dev/blog/best-open-source-rag-frameworks)
- [10 Best RAG Tools and Platforms: Full Comparison 2025](https://www.meilisearch.com/blog/rag-tools)
- [Why Danswer uses Vespa](https://blog.vespa.ai/why-danswer-users-vespa/)
- [LocalGPT vs PrivateGPT](https://www.chatbees.ai/blog/localgpt-vs-privategpt)
- [Top 10 RAG Frameworks GitHub Repos 2025](https://rowanblackwoon.medium.com/top-10-rag-frameworks-github-repos-2025-dba899ae0355)

---

## Related Documentation

- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Model selection
- [State-of-the-Art CLI Modes](./state-of-the-art-cli-modes.md) - Interface design
- [State-of-the-Art User Interfaces](./state-of-the-art-user-interfaces.md) - TUI/WebUI options

---

**Status**: Research complete
