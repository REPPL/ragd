# Planned Features

Features planned for future development. See [features/README.md](../README.md) for the complete roadmap.

## v0.8.6 Features (Security Focus)

| ID | Feature | Description |
|----|---------|-------------|
| F-082 | Security Hardening | Input validation, path traversal prevention |
| F-083 | Secrets Management | Environment variables, encrypted config |
| F-084 | Error Resilience | Graceful degradation, safe error messages |
| F-085 | Test Coverage Boost | Target 85% coverage |
| F-086 | Dependency Audit | Security scan, SBOM generation |

## v0.8.7 Features (CLI Polish & Documentation I)

| ID | Feature | Description |
|----|---------|-------------|
| F-087 | Shell Completion | Bash/Zsh/Fish auto-completion |
| F-088 | Interactive Config | CLI wizard for configuration |
| F-089 | Help System Enhancement | Better --help, examples, man pages |
| F-090 | Output Mode Consistency | JSON/plain/rich everywhere |
| F-091 | Tutorial Suite | Getting started to advanced guides |
| F-092 | Configuration Reference | Complete config.yaml documentation |
| F-093 | Troubleshooting Guide | Common issues and solutions |
| F-094 | Use Case Gallery | Real-world examples |
| F-095 | Video/GIF Demo Specs | Voice-over scripts, storyboards |
| F-096 | Config Migration Tool | Migrate configs between versions |
| F-097 | Config Debugging | `ragd config show --effective` |

## v0.9.0 Features (Enhanced Indexing)

| ID | Feature | Description |
|----|---------|-------------|
| F-098 | Advanced HTML Engine | JavaScript rendering, SPAs |
| F-099 | PDF Layout Intelligence | Forms, annotations, multi-column |
| F-100 | New File Type Support | EPUB, DOCX, XLSX |
| F-101 | Smart Chunking v2 | Content-aware chunking |
| F-102 | Indexing Resume | Resume interrupted operations |
| F-103 | Content Hashing | Detect file changes |
| F-104 | Duplicate Detection | Handle duplicate content |
| F-105 | Indexing Self-Evaluation | Automated testing with feedback |

## v0.9.1-v0.9.6 Features (CLI Polish & Stability)

| ID | Feature | Version | Description |
|----|---------|---------|-------------|
| F-106 to F-109 | CLI Polish II | v0.9.1 | Docs, refinements, config, statistics |
| [F-110](./F-110-structured-logging.md) | Structured Logging | v0.9.5 | JSON logs, third-party suppression, rotation |
| [F-111](./F-111-error-logging-recovery.md) | Error Logging & Recovery | v0.9.5 | Per-document stats, failure categories |
| F-112 to F-113 | Audit & Exit Codes | v0.9.5 | Operation audit, consistent exit codes |
| [F-114](./F-114-cli-user-feedback.md) | CLI User Feedback | v0.9.5 | Clean progress, quality stats, named failures |
| F-115 to F-118 | Stability Features | v0.9.5 | Quality scoring, `ragd doctor`, dry-run |
| F-119 to F-122 | CLI Polish III | v0.9.6 | Final polish for 1.0 |

## v1.x Features (Production & Platform)

| ID | Feature | Version | Description |
|----|---------|---------|-------------|
| F-123 to F-127 | Performance & Polish | v1.0 | Profiling, memory, benchmarks |
| [F-057](./F-057-model-comparison.md) | Model Comparison | v1.0 | Evaluate models side-by-side |
| [F-075](./F-075-backend-migration-tool.md) | Backend Migration | v1.0 | Move between vector stores |
| F-128 to F-132 | Graph & Automation | v1.1 | Knowledge graph CLI, batch ops |
| F-133 to F-137 | API & Onboarding | v1.5 | REST API, guided setup |
| [F-024](./F-024-basic-webui.md) | Basic WebUI | v1.8 | FastAPI + HTMX + Tailwind |
| F-138 to F-141 | WebUI Features | v1.8 | Search, chat, index in browser |

## v2.0+ Features (Extensibility & Privacy)

| ID | Feature | Version | Research |
|----|---------|---------|----------|
| F-200 to F-205 | Extensibility | v2.0 | Plugins, workflows, dashboard |
| [F-058](./F-058-fine-tuning-pipeline.md) | Fine-Tuning Pipeline | v3.0 | [State-of-the-Art Fine-Tuning](../../research/state-of-the-art-fine-tuning.md) |
| [F-059](./F-059-embedding-privacy-protection.md) | Embedding Privacy | v3.0 | [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md) |
| [F-060](./F-060-gdpr-compliant-deletion.md) | GDPR-Compliant Deletion | v3.0 | [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md) |
| F-300 to F-302 | Privacy Foundation | v3.0 | Dashboard, lineage, anonymisation |

## v3.5+ Features (Personal Knowledge Assistant)

| ID | Feature | Research |
|----|---------|----------|
| [F-040](./F-040-long-term-memory.md) | Long-Term Memory | [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) |
| [F-041](./F-041-user-profile-management.md) | User Profiles | [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) |
| F-042 to F-044 | Persona & Vault | [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) |
| F-045 to F-048 | Data Connectors | Browser, email, health, financial |

## v4.0-v5.0 Features (Agents & Multi-User)

| ID | Feature | Version | Description |
|----|---------|---------|-------------|
| F-400 to F-407 | Autonomous Agents | v4.0 | Tool use, MCP, reasoning |
| F-500 to F-506 | Multi-User | v5.0 | Teams, RBAC, SSO |

## Recently Completed (Moved to completed/)

The following features were previously planned and have been implemented:

| ID | Feature | Implemented In |
|----|---------|----------------|
| F-018 | Data Sensitivity Tiers | v0.8.0 |
| F-022 | Knowledge Graph Integration | v0.8.5 |
| F-061 | Auto-Tag Suggestions | v0.8.1 |
| F-062 | Tag Library | v0.8.1 |
| F-063 | Smart Collections | v0.8.1 |
| F-064 | Tag Provenance | v0.8.0 |
| F-080 | Cross-Encoder Reranking | v0.8.2 |
| F-081 | Query Decomposition | v0.8.2 |

## Workflow

1. Create feature document here when feature is scoped
2. Prioritise features in roadmap discussions
3. Move to `active/` when development begins
4. Move to `completed/` when shipped

## What Belongs Here

- Scoped but not started features
- Features awaiting prioritisation
- Features pending design decisions

## What Doesn't Belong Here

- Active features -> [active/](../active/)
- Completed features -> [completed/](../completed/)
- Vague ideas -> Issues/discussions first

---

## Related Documentation

- [Feature Roadmap](../README.md)
- [Active Features](../active/)
- [Completed Features](../completed/)
