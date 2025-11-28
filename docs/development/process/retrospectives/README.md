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

Each milestone gets a retrospective file:

| File | Milestone | Notes |
|------|-----------|-------|
| [v0.1.0-retrospective.md](./v0.1.0-retrospective.md) | Core RAG Pipeline | |
| [v0.2.0-retrospective.md](./v0.2.0-retrospective.md) | Killer Feature | PDF, metadata, export backends |
| [v0.2.5-retrospective.md](./v0.2.5-retrospective.md) | F-039 HTML Processing | Now released in v0.3.0 |
| [v0.3.0-retrospective.md](./v0.3.0-retrospective.md) | Advanced Search & CLI | Includes F-039, F-051-054 |
| [v0.4.0-retrospective.md](./v0.4.0-retrospective.md) | Multi-Modal | ColPali vision embeddings (F-019) |
| [v0.4.1-retrospective.md](./v0.4.1-retrospective.md) | Boolean Search | Query parser, operators |

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
- [Workflow Documentation](../workflow.md)
- [AI Contributions](../../ai-contributions.md)
