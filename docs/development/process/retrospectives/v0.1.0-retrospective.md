# v0.1.0 Retrospective

## Overview

**Milestone:** v0.1.0 - Core RAG Pipeline
**Agent:** Claude (claude-opus-4-5-20251101)
**Sessions:** 5+ conversation sessions

---

## What Happened

| Phase | Plan | Actual | Notes |
|-------|------|--------|-------|
| **Branch Strategy** | Work on `feature/` or `milestone/` branch | Worked directly on main | No rollback safety |
| **Doc Audit** | Assess readiness before implementing | Docs existed but weren't formally audited | Started with incomplete understanding |
| **Implementation** | Follow phased plan with quality gates | Iterative implementation across sessions | Multiple rounds needed |
| **Testing** | Run tests + UAT before each commit | Tests ran, but UAT was ad-hoc | Bugs found late |
| **Thinking Logs** | Create AI log for every commit | No thinking logs created | Lost reasoning context |
| **Doc Sync** | Verify docs match implementation | Significant drift discovered post-implementation | Required manual fix session |
| **Version Tags** | Tag phases (alpha.1, beta.1, release) | Tagged only at end (v0.1.0) | Missing intermediate checkpoints |

## Manual Interventions Required

| Intervention | Cause | Could Be Automated? |
|--------------|-------|---------------------|
| **TUI inline mode bug** | UI testing requires visual inspection | No - requires human eyes |
| **TUI subtitle missing** | Rich/Textual rendering edge case | No - visual verification |
| **TUI layout preferences** | UX design decision (left/centre/right alignment) | No - requires user preference |
| **health→doctor rename** | Doc drift from implementation | **Yes** - doc sync checkpoint |
| **HTML support missing from docs** | Feature added without doc update | **Yes** - doc sync checkpoint |
| **F-009 scope decision** | Ambiguous feature boundary | Partially - better spec upfront |
| **Commit organisation** | Multiple related changes | **Yes** - follow phased commits |

**Key Finding:** 3 of 7 interventions were UX/visual issues requiring human judgement. The other 4 could have been caught by automation.

## Documentation Drift

| Drift Type | Files Affected | Root Cause |
|------------|----------------|------------|
| Command rename | 6 CLI docs | Implementation changed after docs written |
| Feature addition | 3 docs | HTML support added without doc update |
| Status mismatch | 4 docs | v0.1.0 still "Planned" after release |
| Link rot | 10+ docs | Features in `planned/` after completion |

**Pattern:** Documentation was written speculatively (before implementation), then implementation diverged. No checkpoint verified consistency before release.

## Context Loss Issues

The v0.1.0 implementation spanned multiple conversation sessions:

1. Initial implementation (core modules)
2. TUI implementation
3. Bug fixes (3 TUI bugs)
4. Documentation sync
5. Release tagging

Each context switch required summarisation, leading to:
- Lost details about decisions made
- Repeated work to re-understand state
- No persistent record of reasoning

## Lessons Learned

### What Worked Well

- Feature-centric documentation structure made scope clear
- Test coverage was comprehensive (98 tests)
- Rich/Textual TUI provided excellent UX
- Privacy-first architecture validated

### What Needs Improvement

- **Documentation sync**: Need automated verification before commits
- **Session state**: Need persistent state across conversation sessions
- **Thinking logs**: Need AI reasoning documented for transparency
- **UAT for UI**: Never skip user acceptance testing for visual features
- **Branch isolation**: Work on feature branches, not directly on main

## Process Improvements Implemented

Based on this retrospective, the following improvements were made:

### 1. Documentation Sync Checkpoint

Added to `implement-autonomously` agent and created `/sync-docs` command:
- Compare CLI help output to documentation
- Verify feature status matches implementation
- Flag and fix drift before committing

### 2. Mandatory UAT for UI Features

Clarified in workflow documentation:
- **NEVER skip UAT** for TUI, CLI output, or user-facing features
- **May skip UAT** only for internal refactoring, docs-only, or tests

### 3. Session State Persistence

Emphasised `.work/agents/session.yaml` usage:
- Track current phase and completed features
- Record decisions made and rationale
- Enable resume from known state

### 4. Version Numbering Policy

Added to project CLAUDE.md:
- `0.X.0` for milestone releases
- `0.X.Y` for bug fixes after milestone
- Pre-release suffixes (`-alpha.1`, `-beta.1`) during development

### 5. Milestone Retrospectives

This document itself is part of the improvement:
- Create retrospective for every milestone
- Commit to `docs/development/process/retrospectives/`
- Ensure no PII in retrospective content

## Gap Analysis vs implement-autonomously Agent

The `implement-autonomously` agent already prescribes most of what went wrong:

| Agent Prescription | v0.1.0 Reality | Now Fixed? |
|-------------------|----------------|------------|
| Branch isolation | Direct to main | Will use branches for v0.2.0 |
| Readiness assessment | Skipped | Agent reminder added |
| Single clarification rule | Multiple rounds | Better understood |
| AI thinking logs | None created | Template and guidance added |
| Per-commit UAT | Ad-hoc | Workflow clarified |
| Doc verification gate | Skipped | `/sync-docs` command added |
| Session state file | Not created | Guidance emphasised |

## Action Items for v0.2.0

1. [ ] Create `milestone/v0.2.0` branch at start
2. [ ] Run readiness assessment before implementation
3. [ ] Create session state file from day one
4. [ ] Write thinking log for each significant commit
5. [ ] Run `/sync-docs` before every commit
6. [ ] UAT for all TUI/CLI changes (no skipping)
7. [ ] Tag intermediate versions (`v0.2.0-alpha.1`, etc.)
8. [ ] Create retrospective before final release tag

---

🤖 Generated by Claude during autonomous implementation of v0.1.0

**Status**: Complete
