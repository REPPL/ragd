# Implementation Workflow

## Overview

This document defines the implementation workflow for ragd, incorporating lessons learned from v0.1.0 and emphasising AI transparency.

---

## AI Transparency Commitment

ragd is developed with AI assistance, and we commit to transparent documentation of the AI coding process:

- **Thinking logs** accompany each significant commit
- **Retrospectives** are committed after each milestone
- **Decisions and reasoning** are preserved in the repository

This allows anyone reviewing the GitHub archive to understand not just *what* was built, but *how* the AI reasoned through each release.

---

## Phased Implementation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 0: Setup                                                   │
│ ├── Create branch: milestone/vX.Y.Z                             │
│ ├── Create session file: .work/agents/session.yaml              │
│ └── Run readiness assessment (≥80% to proceed)                  │
├─────────────────────────────────────────────────────────────────┤
│ Phase 1: Foundation                                              │
│ ├── Implement base components                                   │
│ ├── Tests + doc sync checkpoint                                 │
│ ├── Commit with thinking log                                    │
│ └── Tag: vX.Y.Z-alpha.1                                         │
├─────────────────────────────────────────────────────────────────┤
│ Phase 2: Core Features                                           │
│ ├── Implement features (respect dependencies)                   │
│ ├── Per-feature: tests + UAT + doc sync                         │
│ ├── Commit with thinking log for each feature                   │
│ └── Tag: vX.Y.Z-alpha.2                                         │
├─────────────────────────────────────────────────────────────────┤
│ Phase 3: Polish                                                  │
│ ├── Error handling, edge cases                                  │
│ ├── Full test suite (≥80% coverage)                             │
│ ├── Documentation audit (run documentation-auditor)             │
│ └── Tag: vX.Y.Z-beta.1                                          │
├─────────────────────────────────────────────────────────────────┤
│ Phase 4: Release                                                 │
│ ├── Thorough UAT (USER RUNS, USER CONFIRMS)                     │
│ ├── Security audit (run codebase-security-auditor)              │
│ ├── Commit retrospective                                        │
│ ├── Merge to main (USER APPROVES)                               │
│ └── Tag: vX.Y.Z                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation Sync Checkpoint

Before EVERY commit that changes functionality:

### 1. Command Audit (if CLI changed)
```bash
# Compare CLI help to documentation
ragd --help
ragd <command> --help
# Verify matches docs/guides/cli/reference.md
```

### 2. Feature Audit (if features added/changed)
- Verify feature spec matches implementation
- Update supported formats lists
- Update CLI reference

### 3. Status Audit (if milestone changed)
- Update milestone status to "Released"
- Move features from `planned/` to `completed/`
- Update roadmap tables

Use `/sync-docs` command to automate this verification.

---

## AI Thinking Logs

Each significant commit should include a thinking log documenting:

```markdown
# Thinking Log: [Feature/Fix Name]

## Context
[What prompted this change]

## Approach Considered
[Options evaluated]

## Decision Made
[What was chosen and why]

## Challenges Encountered
[Problems solved during implementation]

## Outcome
[Result and any follow-up needed]
```

Store in `docs/development/process/devlogs/` with format `YYYY-MM-DD-feature-name.md`.

---

## Session State Management

At start of EVERY implementation session:

1. Check for existing session file:
   ```bash
   cat .work/agents/session.yaml 2>/dev/null || echo "No session"
   ```

2. If exists: Resume from recorded state
3. If not: Create new session file

### Session File Template

```yaml
# .work/agents/session.yaml
version: "0.2.0"
phase: "foundation"  # setup | foundation | features | polish | release
started: "2025-11-26"
last_updated: "2025-11-26T18:00:00Z"

completed:
  - feature: "F-010"
    commit: "abc123"
    notes: "Base PDF extraction working"

in_progress:
  - feature: "F-011"
    status: "implementing tests"
    blockers: []

pending:
  - "F-012"
  - "F-013"

decisions:
  - question: "Use PyMuPDF or PDFPlumber?"
    answer: "PyMuPDF - faster, handles more edge cases"
    date: "2025-11-26"

known_issues:
  - "OCR not yet integrated"
```

On context limit approaching: Write comprehensive session state with "RESUME FROM HERE" marker.

---

## User Intervention Points

| Point | Type | When | Why |
|-------|------|------|-----|
| **Scope confirmation** | Decision | Phase 0 | Define what's in/out |
| **Architecture questions** | Decision | Phase 1 | Major design choices |
| **UAT for UI features** | Verification | Phase 2-3 | Visual inspection required |
| **Final UAT** | Verification | Phase 4 | Comprehensive acceptance |
| **Merge approval** | Approval | Phase 4 | Main branch protection |
| **Release confirmation** | Approval | Phase 4 | Tag and push |

### UAT Classification

**NEVER skip UAT for:**
- Any UI component (TUI, CLI output formatting)
- Any user-facing feature
- Any output visible to users

**May skip UAT for:**
- Internal refactoring (no output changes)
- Documentation-only changes
- Test additions

---

## Autonomous Implementation Gates

The agent CAN proceed autonomously when:
- ✅ Readiness score ≥80%
- ✅ All tests pass
- ✅ Doc sync checkpoint passes
- ✅ PII scan clean
- ✅ Security scan clean
- ✅ No UI-facing changes (or UAT already passed)

The agent MUST stop and ask when:
- ❌ Readiness score <80%
- ❌ Tests fail
- ❌ Doc sync shows drift
- ❌ PII found
- ❌ Security issues found
- ❌ UI changes need UAT
- ❌ Architectural ambiguity

---

## Version Numbering Policy

### Semantic Versioning (MAJOR.MINOR.PATCH)

| Version | When to Use | Example |
|---------|-------------|---------|
| **0.X.0** | Milestone release (planned features) | v0.1.0, v0.2.0 |
| **0.X.Y** | Bug fixes after milestone | v0.1.1, v0.1.2 |
| **X.0.0** | Breaking changes or major milestone | v1.0.0 |

### Version Locations (CRITICAL)

ragd defines version in **two places** that must stay synchronised:

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata (pip install) |
| `src/ragd/__init__.py` | Runtime `__version__` (CLI display) |

**Always update BOTH files when changing version.**

See project documentation for detailed version management instructions.

### Rules

1. **pyproject.toml** version = next planned version during development
2. **src/ragd/__init__.py** `__version__` = same as pyproject.toml
3. **Git tag** = version at release moment
4. **After release**: Bump BOTH files to next patch (0.1.0 → 0.1.1)
5. **Milestone tags**: Use pre-release suffixes during development
   - `v0.2.0-alpha.1` - Foundation complete
   - `v0.2.0-beta.1` - Features complete
   - `v0.2.0` - Release

---

## Milestone Retrospectives

After each milestone release, create a retrospective documenting:

1. **What happened** - Actual vs planned process
2. **Manual interventions** - What couldn't be automated
3. **Documentation drift** - What drifted and why
4. **Lessons learned** - Process improvements
5. **Action items** - Specific changes for next milestone

Commit retrospective to `docs/development/process/retrospectives/` before tagging release.

---

## Related Documentation

- [Development Hub](../README.md)
- [Implementation Records](../implementation/)
- [AI Contributions](../ai-contributions.md)

---

**Status**: Active
