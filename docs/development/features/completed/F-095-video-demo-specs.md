# F-095: Video/GIF Demo Specs

**Status:** Planned
**Milestone:** v0.8.7

## Problem Statement

Video demos are effective for showing ragd in action, but require planning. Specs ensure consistent, high-quality recordings.

## Design Approach

Create detailed specifications for video/GIF demos that can be recorded later.

### Demo Categories
1. **Quick Start** (30s GIF) - Install, init, first search
2. **Feature Tours** (2-3min) - Deep dive into features
3. **Use Case Walkthroughs** (5min) - Complete workflows

### Spec Structure
```
docs/assets/demos/
├── README.md              # Demo index
├── 01-quick-start.md      # Quick start spec
├── 02-search-tour.md      # Search feature spec
├── 03-chat-tour.md        # Chat feature spec
└── scripts/               # Terminal recording scripts
    └── quick-start.sh
```

### Spec Format
Each spec includes:
1. **Title** - Demo name
2. **Duration** - Target length
3. **Audience** - Who it's for
4. **Storyboard** - Scene-by-scene breakdown
5. **Script** - Commands to run
6. **Annotations** - What to highlight
7. **Recording notes** - Terminal size, settings

## Implementation Tasks

- [ ] Create docs/assets/demos directory
- [ ] Write quick-start demo spec
- [ ] Write search-tour demo spec
- [ ] Write chat-tour demo spec
- [ ] Create recording script for quick-start
- [ ] Document recording tools (asciinema, vhs)
- [ ] Define terminal size and font standards

## Success Criteria

- [ ] 3+ demo specs with storyboards
- [ ] Recording scripts ready to execute
- [ ] Recording guidelines documented

## Dependencies

- v0.8.6 (Security Focus)
- F-091 Tutorial Suite (content alignment)

---

## Related Documentation

- [v0.8.7 Milestone](../../milestones/v0.8.7.md)
- [F-091 Tutorial Suite](./F-091-tutorial-suite.md)

---

**Status**: Planned
