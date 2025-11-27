# ADR-0004: Hybrid Specification Approach

## Status

Accepted

## Context

ragd needs a specification approach that:
- Supports autonomous agent implementation
- Maintains human oversight at key milestones
- Captures user intent (not just technical details)
- Validates features through user experience
- Scales from v0.1 to v1.0+

Traditional approaches have limitations:
- **Requirements documents:** Often disconnect from implementation
- **User stories only:** Lack technical depth for autonomous agents
- **Technical specs only:** Miss user experience validation

## Decision

Use a **hybrid specification approach** combining three layers:

```
Layer 1: USE CASES (Why)
    ↓ derive
Layer 2: FEATURE SPECS (What)
    ↓ validate
Layer 3: TUTORIALS (How users experience it)
```

### Layer 1: Use Cases

**Purpose:** Define what users want to accomplish

**Format:** Use case briefs (lightweight)
- Summary
- User story
- Trigger
- Preconditions
- Success criteria (testable)
- Derived features

**Location:** `docs/use-cases/briefs/`

**Example:** UC-001 defines "Index Documents" - what the user wants, not how it's implemented.

### Layer 2: Feature Specifications

**Purpose:** Define what to build (agent-executable)

**Format:** Feature specs (detailed)
- Problem statement
- Design approach
- Implementation tasks (checkable)
- Success criteria (measurable)
- Dependencies
- Technical notes

**Location:** `docs/development/features/`

**Example:** F-001 through F-007 and F-035-F-036 detail exactly how to implement UC-001.

### Layer 3: Tutorials

**Purpose:** Validate features through user experience

**Format:** Step-by-step guides
- Prerequisites
- Expected outputs
- Checkpoints
- Troubleshooting

**Location:** `docs/tutorials/`

**Example:** "Getting Started" tutorial validates UC-001, UC-002, UC-003.

### Workflow

```
1. Define Use Case (human)
    ↓
2. Derive Feature Specs (human + agent)
    ↓
3. Draft Tutorial (agent)
    ↓
4. Implement Features (agent)
    ↓
5. Validate via Tutorial (human)
    ↓
6. Milestone Review (human)
```

## Consequences

### Positive

- Clear traceability: Use Case → Features → Tutorial
- Agents have detailed specs for implementation
- Humans validate through user experience
- Specification and validation are interlinked
- Supports autonomous implementation with oversight

### Negative

- More documentation to maintain
- Three places to update for changes
- Requires discipline to keep in sync

### Mitigations

- Traceability matrix links all three layers
- Use case changes trigger feature/tutorial reviews
- Tutorials serve as integration tests

## Alternatives Considered

### Use Case Driven Only (Jacobson)

- **Pros:** User-focused, proven methodology
- **Cons:** Insufficient detail for autonomous agents
- **Rejected:** Agents need more technical guidance

### Feature-First Only

- **Pros:** Direct, efficient for experienced teams
- **Cons:** May lose user perspective, harder to validate
- **Rejected:** Need user experience validation

### Tutorial-Driven Development

- **Pros:** Excellent user focus, validates assumptions
- **Cons:** Doesn't scale, slow for large projects
- **Rejected:** Too slow for comprehensive systems

### BDD (Behaviour-Driven Development)

- **Pros:** Executable specifications, clear acceptance
- **Cons:** Gherkin syntax overhead, tool dependency
- **Considered:** May adopt Given-When-Then for criteria

## Related Documentation

- [Use Cases](../../../use-cases/)
- [Feature Specifications](../../features/)
- [Tutorials](../../../tutorials/)
- [ragged Analysis](../../lineage/ragged-analysis.md) - Lessons learned

