# Devlog: v0.8.5 Knowledge Graph Foundation

**Date:** 2025-12-03
**Version:** 0.8.5
**Theme:** Intelligence & Organisation - Knowledge Graph Foundation

## The Story

The original v0.8.x plan called for Kuzu graph database integration, LLM-based relationship extraction, and dual-index architecture. Reality check: that's easily a week's work done right.

Instead, we built the foundation: entity extraction and graph storage that works today.

## What We Built

### Entity Extraction

Two extractors, one interface:

**PatternEntityExtractor** - Fast, dependency-free:
```python
extractor = PatternEntityExtractor()
entities = extractor.extract("Building a REST API with Python and Django")
# [Entity(name="REST", type=CONCEPT),
#  Entity(name="Python", type=TECHNOLOGY),
#  Entity(name="Django", type=TECHNOLOGY)]
```

Works out of the box. Covers:
- Programming languages (Python, JavaScript, Rust...)
- Frameworks (Django, React, FastAPI...)
- Databases (PostgreSQL, MongoDB, Redis...)
- Cloud platforms (AWS, Azure, GCP...)
- Concepts (machine learning, authentication...)
- Companies (Google, Microsoft, OpenAI...)

**SpacyEntityExtractor** - Higher quality, optional:
```python
extractor = SpacyEntityExtractor("en_core_web_sm")
if extractor.available:
    entities = extractor.extract(text)  # People, orgs, locations, dates...
```

Graceful degradation. If spaCy isn't installed, pattern extraction handles it.

### Knowledge Graph Storage

SQLite-backed graph with three tables:

```sql
entities (name, type, doc_count, chunk_count)
relationships (source, target, type, weight)
entity_mentions (entity_name, doc_id, chunk_id)
```

No Kuzu needed. SQLite is everywhere, battle-tested, and performs well for local use.

### Co-occurrence Relationships

Entities mentioned together in a chunk? They're probably related:

```python
entities = [python, django, rest]
graph.add_entities_batch(entities, doc_id)
# Creates: python-django, python-rest, django-rest relationships
```

Simple heuristic, surprisingly effective. More mentions together = stronger relationship.

### Graph Traversal

Multi-hop exploration:

```python
related = graph.get_related("python", hops=2)
# 1-hop: django, flask, fastapi
# 2-hop: postgresql, jwt, rest (connected through frameworks)
```

Relevance scores decay with distance, keeping results focussed.

## What We Didn't Build

- **CLI commands** - No `ragd graph build` yet
- **Graph-enhanced retrieval** - The graph exists but doesn't boost search yet
- **LLM relationship extraction** - Co-occurrence is enough for now
- **Kuzu integration** - SQLite works fine

These aren't missing - they're deferred. The foundation is solid.

## The v0.8.x Series

One day, four releases:

| Version | Features | Tests |
|---------|----------|-------|
| v0.8.0 | Tag Provenance, Data Sensitivity | 53 |
| v0.8.1 | Collections, Suggestions, Library | 77 |
| v0.8.2 | Reranking, Query Decomposition | 44 |
| v0.8.5 | Knowledge Graph Foundation | 34 |

**Total: 208 new tests, 1235 passing**

The "Intelligence & Organisation" theme is complete. Documents can be:
- Tagged with provenance tracking
- Classified into sensitivity tiers
- Organised into smart collections
- Auto-suggested for tags
- Reranked for precision
- Decomposed for complex queries
- Connected via entity relationships

---

*~2 hours of pragmatic implementation*
