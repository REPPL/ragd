# Feature Specifications

Feature-centric roadmap for ragd development.

## Purpose

Features are the primary unit of work. Each feature specification describes:
- **What** the feature does
- **Why** it matters
- **How** it will be implemented
- **When** it's considered done

## Status by Location

| Directory | Status | Meaning |
|-----------|--------|---------|
| [active/](./active/) | 🔄 In Progress | Currently being implemented |
| [planned/](./planned/) | 📅 Queued | Designed, awaiting implementation |
| [completed/](./completed/) | ✅ Done | Shipped and documented |

## Feature Index

### v0.1 Features (Core RAG)

| ID | Feature | Status | Use Case |
|----|---------|--------|----------|
| [F-001](./completed/F-001-document-ingestion.md) | Document Ingestion Pipeline | ✅ Complete | UC-001 |
| [F-002](./completed/F-002-text-extraction.md) | Text Extraction | ✅ Complete | UC-001 |
| [F-003](./completed/F-003-chunking-engine.md) | Chunking Engine | ✅ Complete | UC-001 |
| [F-004](./completed/F-004-embedding-generation.md) | Embedding Generation | ✅ Complete | UC-001 |
| [F-005](./completed/F-005-semantic-search.md) | Semantic Search | ✅ Complete | UC-002 |
| [F-006](./completed/F-006-result-formatting.md) | Result Formatting | ✅ Complete | UC-002 |
| [F-007](./completed/F-007-status-dashboard.md) | Status Dashboard | ✅ Complete | UC-003 |
| [F-035](./completed/F-035-health-check.md) | Health Check Command | ✅ Complete | UC-003 |
| [F-036](./completed/F-036-guided-setup.md) | Guided Setup | ✅ Complete | - |

### v0.2 Features (Killer Feature)

#### PDF Processing

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-025](./completed/F-025-pdf-quality-detection.md) | PDF Quality Detection | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-026](./completed/F-026-docling-integration.md) | Docling Integration | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-027](./completed/F-027-ocr-pipeline.md) | OCR Pipeline | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-028](./completed/F-028-table-extraction.md) | Table Extraction | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |

#### Metadata Management

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-029](./completed/F-029-metadata-storage.md) | Metadata Storage | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |
| [F-030](./completed/F-030-metadata-extraction.md) | Metadata Extraction | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |
| [F-031](./completed/F-031-tag-management.md) | Tag Management | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |

#### Export & Backup

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-032](./completed/F-032-export-engine.md) | Export Engine | ✅ Complete | - |
| [F-033](./completed/F-033-import-engine.md) | Import Engine | ✅ Complete | - |
| [F-034](./completed/F-034-archive-format.md) | Archive Format | ✅ Complete | - |

#### Watch Folder

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-037](./completed/F-037-watch-folder.md) | Watch Folder Auto-Indexing | ✅ Complete | [State-of-the-Art RAG Landscape](../research/state-of-the-art-rag-landscape.md) |

#### Web Archive

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-038](./completed/F-038-web-archive-support.md) | Web Archive Support | ✅ Complete | [State-of-the-Art HTML Processing](../research/state-of-the-art-html-processing.md) |

### v0.3 Features (Advanced Retrieval)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-009](./completed/F-009-citation-output.md) | Citation Output | ✅ Complete | - |
| [F-010](./completed/F-010-contextual-retrieval.md) | Contextual Retrieval | ✅ Complete | ADR-0007 |
| [F-011](./completed/F-011-late-chunking.md) | Late Chunking | ✅ Complete | ADR-0007 |
| [F-012](./completed/F-012-hybrid-search.md) | Hybrid Search | ✅ Complete | ADR-0007 |

### v0.4 Features (Multi-Modal)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-019](./completed/F-019-multi-modal-support.md) | Multi-Modal Support | ✅ Complete | State-of-the-Art Multi-Modal |

### v0.5 Features (Chat & Evaluation)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-013](./completed/F-013-ragas-evaluation.md) | RAGAS Evaluation | ✅ Complete | ADR-0008 |
| [F-014](./completed/F-014-agentic-rag.md) | Agentic RAG | ✅ Complete | State-of-the-Art RAG |
| [F-020](./completed/F-020-ollama-llm-integration.md) | Ollama LLM Integration | ✅ Complete | State-of-the-Art Local RAG |
| [F-055](./completed/F-055-multi-model-orchestration.md) | Multi-Model Orchestration | ✅ Complete | [State-of-the-Art Multi-Model RAG](../research/state-of-the-art-multi-model-rag.md) |

### v0.6.0 Features (Storage)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-021](./completed/F-021-vector-store-abstraction.md) | Vector Store Abstraction | ✅ Complete | ADR-0002 |
| [F-070](./completed/F-070-backend-recommendation.md) | Backend Recommendation | ✅ Complete | - |
| [F-071](./completed/F-071-metadata-proxy-layer.md) | Metadata Proxy Layer | ✅ Complete | - |
| [F-072](./completed/F-072-backend-health-checks.md) | Backend Health Checks | ✅ Complete | - |
| [F-073](./completed/F-073-performance-profiler.md) | Performance Profiler | ✅ Complete | - |
| [F-074](./completed/F-074-model-recommendation.md) | Model Recommendation | ✅ Complete | - |

### v0.6.5 Features (Polish & Stability)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-076](./completed/F-076-ragas-evaluation-metrics.md) | RAGAS Evaluation Metrics | ✅ Complete | - |
| [F-077](./completed/F-077-cli-visual-polish.md) | CLI Visual Polish | ✅ Complete | - |
| [F-078](./completed/F-078-configuration-validation.md) | Configuration Validation | ✅ Complete | - |
| [F-079](./completed/F-079-dependency-error-handling.md) | Dependency Error Handling | ✅ Complete | - |

### v0.7 Features (Privacy & Security)

#### Chat Improvements (Preliminary)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-065](./completed/F-065-chat-citation-display.md) | Chat Citation Display | ✅ Complete | - |
| [F-066](./completed/F-066-configurable-chat-prompts.md) | Configurable Chat Prompts | ✅ Complete | - |

#### Privacy Core

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-015](./completed/F-015-database-encryption.md) | Database Encryption | ✅ Complete | ADR-0009 |
| [F-016](./completed/F-016-session-management.md) | Session Management | ✅ Complete | ADR-0009 |
| [F-017](./completed/F-017-secure-deletion.md) | Secure Deletion | ✅ Complete | ADR-0009 |
| [F-023](./completed/F-023-pii-detection.md) | PII Detection | ✅ Complete | State-of-the-Art Privacy |

### v0.8 Features (Intelligence & Organisation)

#### v0.8.0 - Foundation

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-064](./completed/F-064-tag-provenance.md) | Tag Provenance | ✅ Complete | - |
| [F-018](./completed/F-018-data-tiers.md) | Data Sensitivity Tiers | ✅ Complete | ADR-0010 |

#### v0.8.1 - Intelligent Tagging

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-061](./completed/F-061-auto-tag-suggestions.md) | Auto-Tag Suggestions | ✅ Complete | - |
| [F-062](./completed/F-062-tag-library.md) | Tag Library | ✅ Complete | - |
| [F-063](./completed/F-063-smart-collections.md) | Smart Collections | ✅ Complete | - |

#### v0.8.2 - Retrieval Enhancements

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-080](./completed/F-080-cross-encoder-reranking.md) | Cross-Encoder Reranking | ✅ Complete | State-of-the-Art RAG |
| [F-081](./completed/F-081-query-decomposition.md) | Query Decomposition | ✅ Complete | State-of-the-Art RAG |

#### v0.8.5 - Knowledge Graph

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-022](./completed/F-022-knowledge-graph.md) | Knowledge Graph Integration | ✅ Complete | State-of-the-Art Knowledge Graphs |

### v0.8.6 Features (Security Focus)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-082](./completed/F-082-security-hardening.md) | Security Hardening | ✅ Complete | Input validation, path traversal prevention |
| [F-083](./completed/F-083-secrets-management.md) | Secrets Management | ✅ Complete | Environment variables, encrypted config |
| [F-084](./completed/F-084-error-resilience.md) | Error Resilience | ✅ Complete | Graceful degradation, safe error messages |
| [F-085](./completed/F-085-test-coverage-boost.md) | Test Coverage Boost | ✅ Complete | Target 85% coverage |
| [F-086](./completed/F-086-dependency-audit.md) | Dependency Audit | ✅ Complete | Security scan, SBOM generation |

### v0.8.7 Features (CLI Polish & Documentation I)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-087](./completed/F-087-shell-completion.md) | Shell Completion | ✅ Complete | Bash/Zsh/Fish auto-completion |
| [F-088](./completed/F-088-interactive-config.md) | Interactive Config | ✅ Complete | CLI wizard for configuration |
| [F-089](./completed/F-089-help-system.md) | Help System Enhancement | ✅ Complete | Better --help, examples, man pages |
| [F-090](./completed/F-090-output-modes.md) | Output Mode Consistency | ✅ Complete | JSON/plain/rich everywhere |
| [F-091](./completed/F-091-tutorial-suite.md) | Tutorial Suite | ✅ Complete | Getting started to advanced guides |
| [F-092](./completed/F-092-configuration-reference.md) | Configuration Reference | ✅ Complete | Complete config.yaml documentation |
| [F-093](./completed/F-093-troubleshooting-guide.md) | Troubleshooting Guide | ✅ Complete | Common issues and solutions |
| [F-094](./completed/F-094-use-case-gallery.md) | Use Case Gallery | ✅ Complete | Real-world examples |
| [F-095](./completed/F-095-demo-specs.md) | Video/GIF Demo Specs | ✅ Complete | Voice-over scripts, storyboards |
| [F-096](./completed/F-096-config-migration.md) | Config Migration Tool | ✅ Complete | Migrate configs between versions |
| [F-097](./completed/F-097-config-debugging.md) | Config Debugging | ✅ Complete | `ragd config show --effective` |

### v0.9.0 Features (Enhanced Indexing)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-098](./planned/F-098-advanced-html-engine.md) | Advanced HTML Engine | 📅 Deferred | JavaScript rendering, SPAs |
| [F-099](./planned/F-099-pdf-layout-intelligence.md) | PDF Layout Intelligence | 📅 Deferred | Forms, annotations, multi-column |
| [F-100](./completed/F-100-new-file-types.md) | New File Type Support | ✅ Complete | EPUB, DOCX, XLSX |
| [F-101](./completed/F-101-smart-chunking-v2.md) | Smart Chunking v2 | ✅ Complete | Content-aware chunking |
| [F-102](./completed/F-102-indexing-resume.md) | Indexing Resume | ✅ Complete | Resume interrupted operations |
| [F-103](./completed/F-103-content-hashing.md) | Content Hashing | ✅ Complete | Detect file changes |
| [F-104](./completed/F-104-duplicate-detection.md) | Duplicate Detection | ✅ Complete | Handle duplicate content |
| [F-105](./planned/F-105-indexing-self-evaluation.md) | Indexing Self-Evaluation | 📅 Deferred | Automated testing with feedback |

### v0.9.1 Features (CLI Polish II)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-106](./completed/F-106-indexing-documentation.md) | Indexing Documentation | ✅ Complete | Docs for new indexing features |
| [F-107](./completed/F-107-cli-refinements.md) | CLI Refinements I | ✅ Complete | UX improvements from v0.9.0 |
| [F-108](./completed/F-108-config-refinements.md) | Config Refinements | ✅ Complete | Additional config options |
| [F-109](./completed/F-109-index-statistics.md) | Index Statistics | ✅ Complete | `ragd status --detailed` |

### v0.9.5 Features (Stability & Logging)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-110](./completed/F-110-structured-logging.md) | Structured Logging | ✅ Complete | JSON logs, log rotation |
| F-111 | Error Logging & Recovery | 📅 Deferred | Detailed error logs |
| F-112 | Operation Audit Trail | 📅 Deferred | Timestamps, durations |
| [F-113](./completed/F-113-exit-codes.md) | Exit Codes & Status | ✅ Complete | Consistent exit codes |
| F-114 | CLI User Feedback | 📅 Deferred | Progress, errors, hints |
| F-115 | Source Quality Scoring | 📅 Deferred | Confidence scores |
| [F-116](./completed/F-116-index-integrity.md) | Index Integrity Checks | ✅ Complete | `ragd doctor` |
| [F-117](./completed/F-117-self-healing.md) | Self-Healing Index | ✅ Complete | Auto-repair issues |
| F-118 | Dry-Run Mode | 📅 Deferred | `--dry-run` for destructive ops |

### v0.9.6 Features (CLI Polish III)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-119 | Early Adopter Doc Fixes | 📅 Planned | Address feedback |
| F-120 | CLI Refinements II | 📅 Planned | Final UX polish |
| F-121 | Troubleshooting Updates | 📅 Planned | Real issues encountered |
| F-122 | Tutorial Refinements | 📅 Planned | User confusion points |

### v1.0 Features (Performance & Polish)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-123 | Performance Profiling | 📅 Planned | Identify bottlenecks |
| F-124 | Memory Optimisation | 📅 Planned | Reduce RAM usage |
| F-125 | Startup Time | 📅 Planned | Faster CLI startup |
| F-126 | Final Bug Fixes | 📅 Planned | Last fixes and polish |
| F-127 | Performance Benchmarks | 📅 Planned | Published benchmarks |
| [F-057](./planned/F-057-model-comparison.md) | Model Comparison Mode | 📅 Planned | Evaluate models side-by-side |
| [F-075](./planned/F-075-backend-migration-tool.md) | Backend Migration Tool | 📅 Planned | Move between vector stores |

### v1.1 Features (Graph & Automation)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-128 | Knowledge Graph CLI | 📅 Planned | `ragd graph query/explore/visualise` |
| F-129 | Comparison Framework | 📅 Planned | A/B testing models/configs |
| F-130 | Batch Operations | 📅 Planned | Process multiple queries |
| F-131 | Results Export | 📅 Planned | Export to JSON/CSV |
| F-132 | Timing & Metrics Output | 📅 Planned | `--timing` flag |

### v1.5 Features (API & Onboarding)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-133 | API Server | 📅 Planned | REST API with OpenAPI |
| F-134 | Onboarding Flow | 📅 Planned | Guided first-run |
| F-135 | API Authentication | 📅 Planned | API keys, rate limiting |
| F-136 | Webhooks | 📅 Planned | Event notifications |
| F-137 | Health Endpoints | 📅 Planned | `/health`, `/ready`, `/metrics` |

### v1.8 Features (WebUI Foundation)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| [F-024](./planned/F-024-basic-webui.md) | Basic WebUI | 📅 Planned | FastAPI + HTMX + Tailwind |
| F-138 | WebUI Search | 📅 Planned | Search interface with filters |
| F-139 | WebUI Chat | 📅 Planned | Chat in browser |
| F-140 | WebUI Index | 📅 Planned | Upload and index documents |
| F-141 | Mobile Responsive | 📅 Planned | Works on all devices |

### v2.0 Features (Extensibility)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-200 | Plugin System | 📅 Planned | Extensibility framework |
| F-201 | Workflow Automation | 📅 Planned | Scheduled indexing, triggers |
| F-202 | Advanced Dashboard | 📅 Planned | Analytics, visualisations |
| F-203 | Knowledge Graph Explorer | 📅 Planned | Visual graph navigation |
| F-204 | Saved Searches | 📅 Planned | Bookmarks, history |
| F-205 | Export Templates | 📅 Planned | Custom export formats |

### v3.0 Features (Privacy Foundation)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-058](./planned/F-058-fine-tuning-pipeline.md) | Fine-Tuning Pipeline | 📅 Planned | Local model fine-tuning |
| [F-059](./planned/F-059-embedding-privacy-protection.md) | Embedding Privacy Protection | 📅 Planned | Differential privacy |
| [F-060](./planned/F-060-gdpr-compliant-deletion.md) | GDPR-Compliant Deletion | 📅 Planned | Right to be forgotten |
| F-300 | Privacy Dashboard | 📅 Planned | Privacy settings UI |
| F-301 | Data Lineage Tracking | 📅 Planned | Data origin tracking |
| F-302 | Anonymisation Engine | 📅 Planned | Auto-redact PII |

### v3.5 Features (Memory & Profiles)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-040](./planned/F-040-long-term-memory.md) | Long-Term Memory Store | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| [F-041](./planned/F-041-user-profile-management.md) | User Profile Management | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-042 | Persona Agent System | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-043 | Memory Consolidation | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| [F-044](./planned/F-044-personal-vault.md) | Personal Information Vault | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

### v3.x Features (Personal Data Connectors)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| F-045 | Browser History Connector | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-046 | Communication Parser | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-047 | Health Record Import (FHIR) | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-048 | Financial Data Import | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

### v4.0 Features (Autonomous Agents)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-400 | Agent Framework | 📅 Planned | Core agent loop with planning |
| F-401 | Tool Use System | 📅 Planned | File ops, web search, APIs |
| F-402 | Multi-Step Reasoning | 📅 Planned | Complex task decomposition |
| F-403 | Agent Collaboration | 📅 Planned | Multiple agents working together |
| F-404 | MCP Integration | 📅 Planned | Model Context Protocol |
| F-405 | Task Planning Engine | 📅 Planned | Break down goals into steps |
| F-406 | Agent Memory | 📅 Planned | Persistent context |
| F-407 | Safety Guardrails | 📅 Planned | Sandboxing, approval workflows |

### v5.0 Features (Multi-User)

| ID | Feature | Status | Description |
|----|---------|--------|-------------|
| F-500 | Multi-User Support | 📅 Planned | User accounts, authentication |
| F-501 | Team Workspaces | 📅 Planned | Shared knowledge bases |
| F-502 | Role-Based Access Control | 📅 Planned | Fine-grained permissions |
| F-503 | SSO Integration | 📅 Planned | OAuth2, SAML, LDAP |
| F-504 | Federated Search | 📅 Planned | Search across instances |
| F-505 | API v2 | 📅 Planned | GraphQL, webhooks, SDK |
| F-506 | Compliance Features | 📅 Planned | Audit reports, retention |

## Workflow

1. **Plan:** Create feature document in `planned/`
2. **Start:** Move to `active/` when development begins
3. **Complete:** Move to `completed/` when feature is released

## Feature Numbering Convention

Features are numbered sequentially with milestone-based ranges:

| Range | Milestone | Theme |
|-------|-----------|-------|
| F-001 to F-007, F-035-F-036 | v0.1 | Core RAG |
| F-025 to F-034, F-037-F-038 | v0.2 | Killer Feature (PDFs, Metadata, Export, Watch, Web) |
| F-009 to F-012 | v0.3 | Advanced Search (Citation, Contextual, Late Chunking, Hybrid) |
| F-019 | v0.4 | Multi-Modal |
| F-013, F-014, F-020, F-055 | v0.5 | Chat & Evaluation |
| F-021, F-070 to F-074 | v0.6.0 | Storage |
| F-076 to F-079 | v0.6.5 | Polish & Stability |
| F-065, F-066 | v0.7 | Chat Improvements |
| F-015 to F-017, F-023 | v0.7 | Privacy & Security |
| F-064, F-018 | v0.8.0 | Intelligence Foundation |
| F-061, F-062, F-063 | v0.8.1 | Intelligent Tagging |
| F-080, F-081 | v0.8.2 | Retrieval Enhancements |
| F-022 | v0.8.5 | Knowledge Graph |
| F-082 to F-086 | v0.8.6 | Security Focus |
| F-087 to F-097 | v0.8.7 | CLI Polish & Documentation I |
| F-098 to F-105 | v0.9.0 | Enhanced Indexing |
| F-106 to F-109 | v0.9.1 | CLI Polish II |
| F-110 to F-118 | v0.9.5 | Stability & Logging |
| F-119 to F-122 | v0.9.6 | CLI Polish III |
| F-123 to F-127 | v1.0 | Performance & Polish |
| F-128 to F-132 | v1.1 | Graph & Automation |
| F-133 to F-137 | v1.5 | API & Onboarding |
| F-138 to F-141 | v1.8 | WebUI Foundation |
| F-200 to F-205 | v2.0 | Extensibility |
| F-300 to F-302 | v3.0 | Privacy Foundation |
| F-040 to F-044 | v3.5 | Memory & Profiles |
| F-045 to F-048 | v3.x | Personal Data Connectors |
| F-400 to F-407 | v4.0 | Autonomous Agents |
| F-500 to F-506 | v5.0 | Multi-User |

**Guidelines:**
- Numbers are assigned sequentially as features are designed
- A feature keeps its number even if its milestone changes
- Gaps in numbering (e.g., no F-025) are expected as features are added over time
- Use the next available number for new features

## Feature Template

```markdown
# F-NNN: [Feature Name]

## Overview

**Use Case**: [UC-NNN](../../use-cases/briefs/UC-NNN-name.md)
**Milestone**: vX.Y
**Priority**: P0 | P1 | P2

## Problem Statement

[Why this feature matters - the pain point it solves]

## Design Approach

[How we solve the problem - architecture, patterns, technologies]

## Implementation Tasks

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Success Criteria

- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)

## Dependencies

- [Dependency 1]
- [Dependency 2]

## Technical Notes

[Implementation details, edge cases, considerations]

## Related Documentation

- [Link 1](./path) - Description
- [Link 2](./path) - Description

---
```

## What Belongs Here

- Feature specification documents (F-NNN-name.md)
- Technical design decisions
- Implementation task breakdowns

## What Doesn't Belong Here

- **Use case briefs** → `../../use-cases/briefs/`
- **Tutorials** → `../../tutorials/`
- **Architecture decisions** → `../decisions/adrs/`
- **Milestone planning** → `../milestones/`

## Related Documentation

- [Use Cases](../../use-cases/) - What users want to accomplish
- [Milestones](../milestones/) - When features ship
- [Tutorials](../../tutorials/) - How users experience features

---
