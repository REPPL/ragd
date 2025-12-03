# Development Process

Documentation of how things were built.

## Structure

| Directory/File | Purpose |
|----------------|---------|
| [workflow.md](./workflow.md) | Implementation workflow and AI transparency |
| [devlogs/](./devlogs/) | Development narrative (mandatory per release) |
| [retrospectives/](./retrospectives/) | Lessons learned (mandatory for major/minor releases) |

## Release Documentation Standard

### Tiered Documentation Requirements

**Major/Minor Releases (v0.X.0)** - Full documentation suite:

| Document | Location | When |
|----------|----------|------|
| Milestone | `milestones/vX.Y.0.md` | Before implementation |
| Implementation Record | `implementation/vX.Y.0.md` | After completion |
| Retrospective | `retrospectives/vX.Y.0-retrospective.md` | After completion |
| Devlog | `devlogs/YYYY-MM-DD-vX.Y.0-*.md` | During/after development |

**Patch Releases (v0.X.Y where Y > 0)** - Minimal documentation:

| Document | Location | When |
|----------|----------|------|
| Milestone | `milestones/vX.Y.Z.md` | Before implementation |
| Implementation Record | Optional (if substantial) | After completion |

## What Belongs Here

- Development narrative (devlogs)
- Process documentation
- Retrospectives and lessons learned
- Methodology notes

## What Doesn't Belong Here

- Technical implementation → [implementation/](../implementation/)
- Feature planning → [features/](../features/)
- Architecture decisions → [decisions/](../decisions/)

---

## Related Documentation

- [Development Hub](../README.md)
- [Implementation Records](../implementation/)
- [Milestones](../milestones/)
