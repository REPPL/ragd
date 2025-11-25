# ragd Planning Prompt

This document preserves the original planning conversation that shaped ragd's specification approach.

## Original Request

> Review the entire documentation for the ragged project and ultrathink best practice of how to transfer what's useful from ragged to ragd, which will be the new reference platform. I do not wish to begin implementation of ragd, but to agree on how to specify what's needed (e.g. functionality, features, priorities) following from what we have learned implementing ragged. For example, does it make sense to begin with use cases, or guides, or tutorials? What is the current best practice here? Once we're done, I'd like to specify a roadmap and have the implementation executed autonomously by an agent -- from start to finish. But for now, I need to understand what's the current best practice setting up ragd.

## Clarifying Questions & Answers

### Q1: What is ragd's relationship to ragged?
**Answer**: Clean rewrite - Reimplement ragged's full feature set with better architecture

### Q2: Who is the primary audience for ragd?
**Answer**: End users - People wanting a working RAG tool for personal use

### Q3: For autonomous agent implementation, what level of human oversight?
**Answer**: Fully autonomous - Agent implements everything, user reviews at milestones

### Q4: Which specification approach?
**Answer**: Hybrid (recommended) - Use cases + Feature specs + Tutorial validation combined

### Q5: What scope should ragd's roadmap target?
**Answer**: Personal platform (v0.1-v1.0) - Full personal knowledge tool matching ragged's v1.0 vision

### Q6: How to document the ragged→ragd knowledge transfer?
**Answer**: Research report - Store the planning conversation as a research report

### Q7: Missing features/priorities?
**Answer**:
- Advanced chunking (semantic, hierarchical, contextual)
- Query processing (decomposition, HyDE, classification, routing)
- Processing messy PDFs (killer feature)
- Earlier multi-modal (Vision/ColPali before v0.6)

### Q8: WebUI scope?
**Answer**: Basic but good-looking WebUI included in v1.0 (chat interface + document upload), following ragged wireframe design. Advanced features deferred to v1.1+.

## Date

2025-11-25

## Planning Session Context

### Research Conducted
1. **ragged Documentation Structure** - Explored full docs hierarchy
2. **ragged Features** - Catalogued 35+ CLI commands, 70K lines
3. **ragged Lessons Learned** - Reviewed devlogs, implementation records
4. **Long-Term Roadmap** - Analysed v0.7-v2.0 planned features
5. **Vision Documents** - Reviewed product vision, design principles
6. **LEANN Integration** - Understood 97% storage savings technology
7. **WebUI Wireframes** - Reviewed design at docs/design/webUI/wireframe/

### Approaches Evaluated
1. **Use Case-Driven** - Start with user stories, derive features
2. **Feature-First** - Catalogue features, create detailed specs
3. **Tutorial-Driven** - Write tutorials first, implement to satisfy them

### Decision: Hybrid Approach
Combines all three in layers:
- Layer 1: Use Cases (Why) → derive
- Layer 2: Feature Specs (What) → validate
- Layer 3: Tutorials (How users experience it)

### Key Design Decisions
- **Killer Feature**: Messy PDF processing at v0.2
- **Earlier Multi-Modal**: ColPali at v0.4 (not v0.6)
- **CLI-First**: Comprehensive CLI through v1.0
- **Basic WebUI**: Simple chat + upload at v1.0
- **Research Acknowledgements**: Preserve sources for LEANN, HyDE, etc.

---

**Purpose**: This document enables reproducibility - others can understand how ragd's specification decisions were made.
