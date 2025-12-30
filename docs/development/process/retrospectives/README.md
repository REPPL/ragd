# Milestone Retrospectives

AI transparency documentation for each milestone release.

## Purpose

These retrospectives document the AI-assisted development process, including:
- What happened vs what was planned
- Manual interventions required
- Documentation drift discovered
- Lessons learned
- Process improvements made

## Structure

Each milestone has its own directory with a README.md:

| Directory | Milestone | Notes |
|-----------|-----------|-------|
| [v0.1.0/](./v0.1.0/) | Core RAG Pipeline | |
| [v0.2.0/](./v0.2.0/) | Killer Feature | PDF, metadata, export backends |
| [v0.2.5/](./v0.2.5/) | F-039 HTML Processing | Now released in v0.3.0 |
| [v0.3.0/](./v0.3.0/) | Advanced Search & CLI | Includes F-039, F-051-054 |
| [v0.4.0/](./v0.4.0/) | Multi-Modal | ColPali vision embeddings (F-019) |
| [v0.4.1/](./v0.4.1/) | Boolean Search | Query parser, operators |
| [v0.5.0/](./v0.5.0/) | Chat & LLM | Ollama, Agentic RAG, RAGAS |
| [v0.6.0/](./v0.6.0/) | Storage | Backend abstraction, FAISS |
| [v0.6.5/](./v0.6.5/) | Polish & Stability | Backfilled |
| [v0.7.0/](./v0.7.0/) | Privacy Core | Encryption, sessions, PII |
| [v0.8.0/](./v0.8.0/) | Intelligence Foundation | Tag provenance, data tiers |
| [v0.8.1/](./v0.8.1/) | Intelligent Tagging | Auto-tags, tag library |
| [v0.8.2/](./v0.8.2/) | Retrieval Enhancements | Cross-encoder, query decomposition |
| [v0.8.5/](./v0.8.5/) | Knowledge Graph | Graph integration |
| [v0.8.6/](./v0.8.6/) | Security Focus | Hardening, audit |
| [v0.8.7/](./v0.8.7/) | CLI Polish & Docs I | Config, tutorials |
| [v0.9.0/](./v0.9.0/) | Enhanced Indexing | HTML/PDF improvements |
| [v0.9.1/](./v0.9.1/) | CLI Polish II | Refinements |
| [v0.9.5/](./v0.9.5/) | Stability & Logging | Early adopter |
| [v0.9.6/](./v0.9.6/) | Alpha Testing | Error handling |
| [v1.0.0/](./v1.0.0/) | Performance & Polish | Production ready |

**Note:** Retrospectives are historical records documenting actual development sessions. The v0.2.5 retrospective documents F-039 work that is now released as part of v0.3.0.

## PII Requirements

**CRITICAL**: All retrospectives must be free of personal information:

- No file paths containing usernames (`/Users/...`, `/home/...`)
- No personal email addresses
- No real names
- Use relative paths only

## Template

See `implement-autonomously` agent for the retrospective template.

---

## Related Documentation

- [Development Process](../README.md)
- [Devlogs](../devlogs/)
- [AI Contributions](../../ai-contributions.md)
