# Personal RAG & Memory Systems - State-of-the-Art

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

State-of-the-art research on adding personal information to RAG systems: memory architectures, user context, personalisation, and privacy-preserving techniques.

## Executive Summary

Personal RAG systems extend traditional document retrieval with:
1. **Persistent memory** - Retaining context across sessions
2. **User profiles** - Adapting retrieval to individual preferences
3. **Personal data vaults** - Secure storage for sensitive personal information
4. **Persona agents** - User-centric agents that personalise interactions

This analysis covers memory architectures (Mem0, Letta, LangMem), personalisation frameworks (PersonaRAG), personal data ingestion approaches, and privacy-preserving techniques for handling sensitive user information.

---

## 1. Memory Architectures

### 1.1 Memory System Categories

Research identifies four distinct memory types for personal RAG:

| Type | Description | Example Data |
|------|-------------|--------------|
| **Semantic Memory** | Facts and knowledge | "User prefers metric units" |
| **Episodic Memory** | Past experiences | "Last week's conversation about X" |
| **Procedural Memory** | How-to knowledge | "User's preferred coding style" |
| **Working Memory** | Current session context | Active conversation state |

**Source:** [Survey: From RAG to Agent](https://arxiv.org/html/2504.10147v1)

### 1.2 Leading Open-Source Memory Frameworks

#### Mem0

- **Stars:** 41,000+ GitHub | **Downloads:** 13M+ PyPI
- **Architecture:** Hybrid data store combining:
  - Vector database (semantic similarity)
  - Graph database (relationship modelling)
  - Key-value store (fast fact retrieval)
- **Memory Levels:** User / Session / Agent state
- **Benchmark Performance:** 66.9% accuracy, 1.4s latency, 90% token savings

Mem0 addresses challenges through an innovative hybrid data store combining multiple specialised storage systems. The framework employs three complementary storage technologies for different memory operations.

**Use Case:** Best for complex research assistants needing relational memory across weeks of sessions.

**Source:** [Mem0 GitHub](https://github.com/mem0ai/mem0), [AI Memory Benchmark](https://mem0.ai/blog/benchmarked-openai-memory-vs-langmem-vs-memgpt-vs-mem0-for-long-term-memory-here-s-how-they-stacked-up)

#### Letta (formerly MemGPT)

- **Origin:** UC Berkeley research
- **Architecture:** "LLM Operating System" with memory tiers that swap information in/out
- **Key Concepts:**
  - Memory Hierarchy (in-context vs out-of-context)
  - Persistent editable Memory Blocks
  - Agentic Context Engineering (agents control their context window)

Letta treats the LLM like an operating system, with memory tiers that swap information in and out. Agents control the context window by using tools to edit, delete, or search for memory.

**Use Case:** Best for document analysis exceeding context windows through intelligent memory swapping.

**Source:** [Letta GitHub](https://github.com/letta-ai/letta)

#### LangMem (LangChain)

- **Integration:** Native LangChain/LangGraph ecosystem
- **Memory Types:** Semantic, Procedural, Episodic
- **Weakness:** Vector scan can stall at ~60s for large memories
- **Strengths:** Developer-friendly if already using LangChain

### 1.3 Memory Benchmark Comparison

| Framework | Accuracy | Latency | Token Savings | Best For |
|-----------|----------|---------|---------------|----------|
| **Mem0** | 66.9% | 1.4s | 90% | Relational memory |
| **MemGPT/Letta** | Good | Variable | High | Document analysis |
| **LangMem** | Moderate | ~60s (large) | Moderate | LangChain users |
| **OpenAI Memory** | 40.7% | Higher | Lower | Simple use cases |

Mem0 achieved 26% higher accuracy compared to OpenAI's memory system while maintaining 91% lower latency than full-context approaches.

**Source:** [AI Memory Systems Benchmark 2025](https://guptadeepak.com/the-ai-memory-wars-why-one-system-crushed-the-competition-and-its-not-openai/)

---

## 2. PersonaRAG Architecture

University of Passau's PersonaRAG introduces user-centric agents into the retrieval process.

### 2.1 Multi-Agent System

PersonaRAG employs a multi-agent system where each agent specialises in different aspects:

| Agent | Function |
|-------|----------|
| **User Profile Agent** | Manages historical interactions and preferences |
| **Context Retrieval Agent** | Personalised document selection |
| **Session Analysis Agent** | Current interaction patterns |
| **Document Ranking Agent** | User-specific relevance scoring |
| **Feedback Agent** | Continuous preference learning |

### 2.2 Performance

- **5-10% accuracy improvement** over vanilla RAG
- Robust performance regardless of number of retrieved passages
- Fewer passages suffice due to efficient extraction by user-centric agents
- Generalises across LLMs (GPT-3.5, LLaMA 3 70B, MoE 8x7B)

### 2.3 Key Innovation

Dynamic, real-time user data refinement rather than static profiles. The User Profile Agent monitors click-through rates, navigation paths, and interaction patterns to continuously adapt retrieval.

**Source:** [PersonaRAG Paper](https://arxiv.org/abs/2407.09394), [MarkTechPost Analysis](https://www.marktechpost.com/2024/07/28/is-the-future-of-agentic-ai-personal-meet-personarag-a-new-ai-method-that-extends-traditional-rag-frameworks-by-incorporating-user-centric-agents-into-the-retrieval-process/)

---

## 3. Personalisation Data Sources

The survey "From RAG to Agent" identifies four personalisation data categories:

### 3.1 Data Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Explicit User Profiles** | Biographical data | Age, location, education, stated preferences |
| **Behavioural Histories** | Interaction patterns | Browsing, clicks, purchases, search history |
| **User-Generated Content** | Created by user | Chats, emails, reviews, documents |
| **Persona-Based Simulation** | LLM-generated | Interaction patterns based on user model |

### 3.2 Personalisation Techniques

**Pre-retrieval Methods:**
- Query rewriting (direct and auxiliary mechanisms)
- Query expansion (tagging-based and semantic approaches)

**Retrieval Methods:**
- Dense retrieval using vector embeddings
- Sparse retrieval employing term-based matching
- Prompt-based retrieval with contextual guidance
- Reinforcement learning-adapted strategies

**Generation Methods:**
- Explicit preference integration through prompting
- Implicit preference encoding via parameter fine-tuning (LoRA)
- Reinforcement learning-based alignment

**Source:** [Survey: From RAG to Agent](https://arxiv.org/html/2504.10147v1)

---

## 4. Personal Information Ingestion

### 4.1 Data Type-Specific Solutions

| Data Type | Tools/Approaches | Notes |
|-----------|-----------------|-------|
| **Medical Records** | Fasten Health, FHIR protocol | Self-hosted, offline-capable |
| **Financial Data** | Custom parsers, PDF extraction | Bank statement parsing |
| **Browser History** | ScreenPipe, Memex | Screen capture + local storage |
| **Conversations** | Rewind AI, Recall | Audio transcription + summaries |
| **Documents** | RAGFlow, Dify, Verba | Multi-format ingestion |

### 4.2 Open-Source Personal Data Projects

#### Rewind AI

- **Platform:** macOS/iOS only
- **Features:** Screen recording, conversation transcription, meeting summaries
- **Privacy:** Entirely offline, local storage, user-controlled exclusions
- **Integration:** ChatGPT for generic knowledge + personal context

Rewind is a memory extension device that transforms recall by recording screen activity, conversations, and digital interactions, building a searchable archive.

**Source:** [Rewind AI](https://www.rewind.ai/)

#### ScreenPipe

- **Platform:** Windows, macOS, Linux
- **Features:** Continuous screen capture, audio transcription, plugin-based AI analysis
- **Privacy:** Open-source, privacy-first, local data collection

#### Memex (WorldBrain.io)

- **Platform:** Browser extension
- **Features:** Web content annotation, full-text search, knowledge organisation
- **Privacy:** Local-first data storage

#### Fasten Health

- **Purpose:** Personal/family electronic medical record aggregator
- **Protocol:** FHIR + Smart-on-FHIR (OAuth2)
- **Privacy:** Self-hosted, offline operation

Designed to integrate with thousands of insurance companies, hospital networks, clinics, and labs while keeping medical history private and secure.

**Source:** [Fasten Health](https://blog.fastenhealth.com/introducing-fasten-health)

#### RAGFlow

- **Features:** Deep document understanding, "needle in haystack" retrieval
- **Document Support:** PDFs, PPTs, complex formats
- **Architecture:** RAG + Agent capabilities for superior context layer

**Source:** [RAGFlow GitHub](https://github.com/infiniflow/ragflow)

---

## 5. Privacy-Preserving Techniques

### 5.1 PII Detection & Redaction

#### Microsoft Presidio

- Detects: Names, emails, phones, SSN, addresses, medical data
- Integrated into LlamaIndex as post-processor
- Local detection, no external APIs

**Source:** [PII Detection in RAG (LlamaIndex)](https://www.llamaindex.ai/blog/pii-detector-hacking-privacy-in-rag)

#### OneShield Privacy Guard (2025)

- Framework to detect and scrub sensitive entities
- High accuracy on names, dates, phone numbers

#### Pre/Post Processing Pattern

```
Input → Mask PII ([PERSON], [DATE]) → Process → Re-insert masked values
```

Some organisations mask secrets or personal info before processing, then post-process to re-insert masked info, ensuring raw personal data never leaves premises unencrypted.

**Source:** [Protecting PII in RAG (Elasticsearch)](https://www.elastic.co/search-labs/blog/rag-security-masking-pii)

### 5.2 Privacy-Preserving RAG Frameworks

#### LPRAG (Locally Private RAG)

Novel privacy-preserving RAG framework based on local differential privacy techniques. Ensures strict privacy guarantees for protecting private entities such as words, numbers, and phrases in private texts.

**Source:** [ScienceDirect: Mitigating privacy risks in RAG](https://www.sciencedirect.com/science/article/abs/pii/S0306457325000913)

#### Privacy-Aware Decoding

- Token-level noise injection
- Response-level RDP accounting
- First decoding-time defence specifically designed for RAG

**Source:** [Privacy-Aware Decoding for RAG](https://arxiv.org/html/2508.03098)

### 5.3 Local LLM Deployment

Running an LLM within company infrastructure ensures full control over data:
- Self-hosted open-source models (LLaMA, etc.)
- Enterprise hardware deployment via PyTorch or TensorFlow
- Full data control within infrastructure

A 2024 study presented a compact LLM framework for local use on electronic health records to meet strict privacy requirements in hospitals.

### 5.4 Enterprise Privacy Statistics (2024-2025)

| Statistic | Value |
|-----------|-------|
| AI privacy incidents increase | 56.4% in 2024 |
| Breaches involving cloud | 82% |
| Organisations admitting sensitive data reaches public AI | 26% |
| Organisations using technical controls to block/scan | 17% |

**Source:** [AI Data Privacy Concerns 2025](https://www.protecto.ai/blog/ai-data-privacy-concerns-risk-breaches)

---

## 6. Multi-Vector Store Architecture

State-of-the-art systems use specialised vector stores rather than monolithic storage:

```
┌─────────────────────────────────────────────────┐
│              Multi-Vector Architecture           │
├─────────────────────────────────────────────────┤
│  Conversation Store  → Context and chat history │
│  Knowledge Base Store → Documents and procedures│
│  User Preference Store → Behavioural patterns   │
│  Tool-Specific Stores → Domain-specialised data │
└─────────────────────────────────────────────────┘
```

### 6.1 Hybrid Retrieval Strategy

- **Vector similarity** - Semantic matching
- **Metadata filtering** - Context boundaries
- **Keyword search** - Precise term matching
- **Temporal weighting** - Recent information priority

This prevents the "wrong memory problem" where irrelevant but semantically similar information contaminates responses.

**Source:** [AI Memory Revolution 2025](https://ragwalla.com/blog/the-ai-memory-revolution-how-rag-powered-memory-systems-will-transform-enterprise-ai-in-2025)

---

## 7. Key Research Papers & Frameworks

| Paper/Framework | Key Contribution | Year |
|-----------------|------------------|------|
| **PersonaRAG** | User-centric agents in retrieval | 2024 |
| **Mem0** | Hybrid memory (vector + graph + KV) | 2024 |
| **MemGPT/Letta** | LLM OS with memory tiers | 2023 |
| **EMG-RAG** | Editable memory graphs | 2024 |
| **PEARL** | Generation-calibrated retrievers | 2024 |
| **LPRAG** | Local differential privacy for RAG | 2024 |
| **Survey: From RAG to Agent** | Comprehensive personalisation taxonomy | 2025 |

---

## 8. Implementation Recommendations for ragd

### 8.1 Memory Layer (v2.0-alpha)

**Recommended:** Mem0-inspired hybrid storage

```python
# Conceptual Memory Architecture
class MemoryLayer:
    semantic_store: VectorDB     # Facts: "User prefers metric units"
    episodic_store: VectorDB     # Events: "Query about X on date Y"
    procedural_store: KeyValue   # Patterns: "User searches before meetings"
    working_memory: InMemory     # Session: Current conversation context
    graph_store: Kuzu            # Relationships between memories
```

**Operations:**
- `add_memory(content, type)` - Store new memory
- `search_memory(query, types)` - Semantic retrieval
- `consolidate()` - Periodic memory compression
- `forget(criteria)` - GDPR-compliant deletion

### 8.2 Personal Information Vault (v2.0)

**Architecture:** Separate, highly-encrypted store

| Type | Connector | Priority |
|------|-----------|----------|
| Browser history | Web archive importer | P2 |
| Communications | Email/chat parsers | P3 |
| Health records | FHIR protocol | P3 |
| Financial data | Statement parsers | P3 |

**Security Requirements:**
- Higher encryption tier than document library
- Separate encryption keys
- Stricter PII handling (auto-redaction by default)
- Audit logging for all access

### 8.3 Persona Agent System (v2.0-beta)

**Recommended:** Multi-agent system inspired by PersonaRAG

| Agent | Function | Implementation |
|-------|----------|----------------|
| **User Profile Agent** | Manages preferences & history | Pydantic models + KV store |
| **Context Retrieval Agent** | Personalised document selection | Vector search + ranking weights |
| **Session Analysis Agent** | Tracks interaction patterns | In-memory state machine |
| **Feedback Agent** | Learns from implicit signals | Reinforcement learning (future) |

---

## Related Documentation

- [state-of-the-art-privacy.md](./state-of-the-art-privacy.md) - Privacy architecture for local RAG
- [state-of-the-art-knowledge-graphs.md](./state-of-the-art-knowledge-graphs.md) - Graph integration for memory
- [state-of-the-art-data-schemas.md](./state-of-the-art-data-schemas.md) - Data models for RAG
- [ADR-0009](../decisions/adrs/0009-security-architecture.md) - Layered security architecture

---

**Status**: Complete
