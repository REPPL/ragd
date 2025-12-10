# F-040: Long-Term Memory Store

## Overview

**Research**: [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md)
**Milestone**: v2.0-alpha
**Priority**: P0

## Problem Statement

Current RAG systems are stateless - each query starts fresh with no context from previous interactions. Users must repeatedly provide context, preferences, and background information. A persistent memory layer enables ragd to:

1. Remember user preferences across sessions
2. Track query history and interaction patterns
3. Build contextual understanding over time
4. Provide personalised retrieval based on past behaviour

## Design Approach

### Architecture

Mem0-inspired hybrid storage combining multiple specialised stores:

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ SEMANTIC STORE  │  │ EPISODIC STORE  │  │ PROCEDURAL STORE│  │
│  │   (VectorDB)    │  │   (VectorDB)    │  │   (Key-Value)   │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  │
│  │ Facts & prefs   │  │ Past events     │  │ Patterns        │  │
│  │ "Prefers metric"│  │ "Query on date" │  │ "Searches AM"   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│            │                   │                   │             │
│            └───────────────────┼───────────────────┘             │
│                                ▼                                 │
│                    ┌─────────────────────┐                       │
│                    │    GRAPH STORE      │                       │
│                    │      (Kuzu)         │                       │
│                    │ Memory relationships│                       │
│                    └─────────────────────┘                       │
│                                │                                 │
│                                ▼                                 │
│                    ┌─────────────────────┐                       │
│                    │   WORKING MEMORY    │                       │
│                    │    (In-Memory)      │                       │
│                    │  Current session    │                       │
│                    └─────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Types

| Type | Storage | Purpose | Example |
|------|---------|---------|---------|
| **Semantic** | ChromaDB | Facts, knowledge, preferences | "User prefers British English" |
| **Episodic** | ChromaDB | Past interactions, events | "Searched 'OAuth' on 15 Nov" |
| **Procedural** | SQLite KV | Patterns, workflows | "Often searches before meetings" |
| **Working** | In-memory | Current session context | Active conversation state |
| **Graph** | Kuzu | Memory relationships | Entity connections across memories |

### Technologies

- **ChromaDB**: Semantic and episodic memory (vector similarity)
- **SQLite**: Procedural memory (key-value patterns)
- **Kuzu**: Memory relationship graph (from F-022)
- **SQLCipher**: Encryption at rest (from F-015)

## Implementation Tasks

### Core Infrastructure
- [ ] Design memory schema (Pydantic models)
- [ ] Implement MemoryStore base class
- [ ] Create SemanticMemoryStore (facts, preferences)
- [ ] Create EpisodicMemoryStore (interactions, events)
- [ ] Create ProceduralMemoryStore (patterns, workflows)
- [ ] Create WorkingMemoryStore (session context)
- [ ] Implement memory graph integration (Kuzu)

### Memory Operations
- [ ] Implement `add_memory(content, type, metadata)`
- [ ] Implement `search_memory(query, types, limit)`
- [ ] Implement `update_memory(id, content)`
- [ ] Implement `forget(criteria)` (GDPR deletion)
- [ ] Implement memory deduplication
- [ ] Implement automatic memory extraction from queries

### Persistence & Security
- [ ] Integrate with F-015 encryption
- [ ] Implement memory export/import
- [ ] Add memory backup/restore
- [ ] Implement cross-session persistence

### CLI Commands
- [ ] Implement `ragd memory show`
- [ ] Implement `ragd memory search <query>`
- [ ] Implement `ragd memory add <content>`
- [ ] Implement `ragd memory forget <criteria>`
- [ ] Implement `ragd memory stats`
- [ ] Implement `ragd memory export/import`

### Testing
- [ ] Write unit tests for each memory store
- [ ] Write integration tests for memory operations
- [ ] Test encryption integration
- [ ] Test memory search accuracy

## Success Criteria

- [ ] Memory persists across sessions
- [ ] Semantic search finds relevant memories (>80% precision)
- [ ] Memory retrieval latency < 100ms
- [ ] GDPR-compliant deletion removes all traces
- [ ] Memory encrypted at rest
- [ ] Works with existing F-022 knowledge graph
- [ ] Memory improves retrieval relevance (measurable)

## Dependencies

### Required (P0)
- F-015 Database Encryption (v0.7)
- F-022 Knowledge Graph (v0.8)
- ChromaDB (existing)
- Kuzu (existing)

### Optional
- F-041 User Profile Management (v2.0-beta)
- F-042 Persona Agent System (v2.0-beta)

## Technical Notes

### Memory Schema

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class MemoryType(str, Enum):
    SEMANTIC = "semantic"      # Facts, preferences
    EPISODIC = "episodic"      # Events, interactions
    PROCEDURAL = "procedural"  # Patterns, workflows
    WORKING = "working"        # Session context

class Memory(BaseModel):
    """Base memory model."""
    id: str
    content: str
    type: MemoryType
    created_at: datetime
    updated_at: datetime
    confidence: float = 1.0
    source: str | None = None  # Where memory came from
    metadata: dict = {}

class SemanticMemory(Memory):
    """Fact or preference."""
    type: MemoryType = MemoryType.SEMANTIC
    category: str  # e.g., "preference", "fact", "knowledge"
    subject: str | None = None

class EpisodicMemory(Memory):
    """Past interaction or event."""
    type: MemoryType = MemoryType.EPISODIC
    event_type: str  # e.g., "query", "feedback", "session"
    timestamp: datetime
    context: dict = {}

class ProceduralMemory(Memory):
    """Pattern or workflow."""
    type: MemoryType = MemoryType.PROCEDURAL
    pattern_type: str  # e.g., "search_pattern", "preference_pattern"
    frequency: int = 1
    last_observed: datetime
```

### Memory Store Interface

```python
from abc import ABC, abstractmethod

class MemoryStore(ABC):
    """Abstract base for memory stores."""

    @abstractmethod
    async def add(self, memory: Memory) -> str:
        """Add memory, return ID."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.5
    ) -> list[Memory]:
        """Search memories by semantic similarity."""
        pass

    @abstractmethod
    async def get(self, memory_id: str) -> Memory | None:
        """Get memory by ID."""
        pass

    @abstractmethod
    async def update(self, memory_id: str, content: str) -> bool:
        """Update memory content."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete memory (GDPR)."""
        pass

    @abstractmethod
    async def delete_by_criteria(self, criteria: dict) -> int:
        """Delete memories matching criteria, return count."""
        pass
```

### Memory Layer Orchestration

```python
class MemoryLayer:
    """Orchestrates all memory stores."""

    def __init__(self, config: MemoryConfig):
        self.semantic = SemanticMemoryStore(config)
        self.episodic = EpisodicMemoryStore(config)
        self.procedural = ProceduralMemoryStore(config)
        self.working = WorkingMemoryStore()
        self.graph = MemoryGraphStore(config)

    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        **kwargs
    ) -> str:
        """Add memory to appropriate store."""
        store = self._get_store(memory_type)
        memory_id = await store.add(content, **kwargs)

        # Update graph relationships
        await self.graph.add_memory_node(memory_id)

        return memory_id

    async def search_memory(
        self,
        query: str,
        types: list[MemoryType] | None = None,
        limit: int = 10
    ) -> list[Memory]:
        """Search across memory stores."""
        types = types or list(MemoryType)
        results = []

        for memory_type in types:
            store = self._get_store(memory_type)
            results.extend(await store.search(query, limit))

        # Rank by relevance and recency
        return self._rank_memories(results, query)[:limit]

    async def consolidate(self) -> int:
        """Consolidate and compress memories."""
        # Merge similar memories
        # Archive old episodic memories
        # Strengthen frequently accessed memories
        pass

    async def forget(self, criteria: dict) -> int:
        """GDPR-compliant deletion across all stores."""
        count = 0
        for store in [self.semantic, self.episodic, self.procedural]:
            count += await store.delete_by_criteria(criteria)
        await self.graph.remove_orphaned_nodes()
        return count
```

### Configuration

```yaml
memory:
  enabled: true
  database: ~/.ragd/memory.db

  semantic:
    collection: ragd_semantic_memory
    embedding_model: nomic-embed-text

  episodic:
    collection: ragd_episodic_memory
    retention_days: 365  # Auto-archive after
    max_entries: 10000

  procedural:
    database: ~/.ragd/procedural.db

  working:
    max_context_tokens: 4096
    session_timeout: 3600  # seconds

  consolidation:
    enabled: true
    schedule: daily
    similarity_threshold: 0.9  # Merge threshold

  graph:
    database: ~/.ragd/memory_graph.kuzu
    enabled: true
```

### CLI Commands

```bash
# Show recent memories
ragd memory show
ragd memory show --type semantic
ragd memory show --limit 20

# Search memories
ragd memory search "authentication preferences"
ragd memory search "what did I search for last week"

# Add explicit memory
ragd memory add "Prefer British English spelling" --type semantic
ragd memory add "Meeting notes from project sync" --type episodic

# Forget memories (GDPR)
ragd memory forget --older-than 30d
ragd memory forget --contains "sensitive topic"
ragd memory forget --id mem_abc123

# Memory statistics
ragd memory stats
# Output:
# Semantic memories: 156
# Episodic memories: 1,234
# Procedural patterns: 23
# Total size: 12.3 MB
# Oldest memory: 2024-01-15

# Export/import
ragd memory export memories.json
ragd memory import memories.json --merge
```

### Memory-Enhanced Retrieval

```python
async def memory_enhanced_search(
    query: str,
    memory_layer: MemoryLayer,
    k: int = 10
) -> list[SearchResult]:
    """Search with memory context."""

    # Get relevant memories
    memories = await memory_layer.search_memory(query, limit=5)

    # Extract context from memories
    context = build_memory_context(memories)

    # Enhance query with memory context
    enhanced_query = f"{context}\n\nQuery: {query}"

    # Perform retrieval with enhanced query
    results = await vector_search(enhanced_query, k)

    # Boost results matching user preferences
    preferences = await memory_layer.semantic.get_preferences()
    results = apply_preference_boost(results, preferences)

    return results
```

## Related Documentation

- [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) - Research basis
- [F-015: Database Encryption](../completed/F-015-database-encryption.md) - Security integration
- [F-022: Knowledge Graph](../completed/F-022-knowledge-graph.md) - Graph store reuse
- [F-041: User Profile Management](./F-041-user-profile-management.md) - Profile integration
- [v2.0.0 Milestone](../../milestones/v2.0.0.md) - Release planning

---

**Status**: Planned
