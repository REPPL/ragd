# State-of-the-Art Document Tagging for RAG Systems

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

Techniques for implementing automated and manual document tagging to enable organisation, filtering, and collection-based navigation in RAG knowledge bases.

## Executive Summary

Document tagging in RAG systems operates at two levels: **automated** (LLM/ML-driven) and **manual** (user-defined). The current best practice is a **hybrid approach** where automated tagging provides a baseline, and users can refine, override, or supplement with their own taxonomy.

Key insights (2024-2025):
- **LLM-based tagging** via zero-shot classification enables dynamic tag assignment without training
- **Controlled vocabularies** with user extensions balance consistency and flexibility
- **Provenance tracking** (distinguishing auto vs manual tags) builds user trust
- **Tags enable virtual collections** without duplicating files or rigid folder hierarchies

ragd's existing `TagManager` and `LLMMetadataEnhancer` provide the technical foundation. The main enhancement opportunities are provenance tracking, tag libraries, and user documentation.

---

## Automated Tagging Approaches

### Technique Comparison

| Approach | Technique | Pros | Cons | Local? |
|----------|-----------|------|------|--------|
| **Zero-Shot Classification** | BART/MNLI models via Hugging Face | No training needed, works with any tag set | Slower, requires LLM calls | ✅ |
| **KeyBERT Keywords** | BERT embeddings extract semantically relevant phrases | Fast, no training | Keywords, not categories | ✅ |
| **LLM Classification** | Local LLMs (Ollama) classify into predefined categories | Rich understanding, context-aware | Requires LLM infrastructure | ✅ |
| **Named Entity Recognition** | spaCy/transformers extract entities (people, orgs, places) | Structured, consistent | Limited to entity types | ✅ |
| **Supervised Classification** | Train models on labelled examples | High accuracy for known categories | Requires training data | ✅ |

**Source:** [Hugging Face Zero-Shot Classification](https://huggingface.co/tasks/zero-shot-classification)

### Zero-Shot Classification with Hugging Face

Zero-shot classification allows models to categorise text into labels not seen during training—ideal for dynamic tag vocabularies:

```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

text = "The quarterly revenue increased by 15% compared to last year."
candidate_labels = ["finance", "technology", "legal", "marketing", "hr"]

result = classifier(text, candidate_labels)
# {'labels': ['finance', 'technology', ...], 'scores': [0.89, 0.05, ...]}
```

**Why Zero-Shot for RAG:**
- No fine-tuning required—works with any tag vocabulary
- Tag library can evolve without retraining
- Supports multi-label classification (document can have multiple tags)

**Source:** [Mastering Zero-Shot Classification with Hugging Face](https://medium.com/@durgeshgurnani/mastering-zero-shot-classification-with-hugging-face-a-comprehensive-guide-a2e1c188c064)

### LLM-Based Tagging (LlamaIndex/LangChain)

**LlamaIndex MetadataExtractor:**

```python
from llama_index.core.extractors import KeywordExtractor
from llama_index.core.node_parser import SentenceSplitter

extractors = [
    KeywordExtractor(keywords=10),  # Extract key topics as tags
]

pipeline = IngestionPipeline(transformations=[SentenceSplitter(), *extractors])
nodes = pipeline.run(documents=documents)
# Each node now has metadata["excerpt_keywords"]
```

**LangChain OpenAI Metadata Tagger:**

```python
from langchain.document_transformers import OpenAIMetadataTagger
from pydantic import BaseModel

class DocumentTags(BaseModel):
    category: str  # report, article, documentation, etc.
    topics: list[str]  # Key themes
    sensitivity: str  # public, internal, confidential

tagger = OpenAIMetadataTagger(schema=DocumentTags)
tagged_docs = tagger.transform_documents(documents)
```

**Source:** [LangChain OpenAI Metadata Tagger](https://python.langchain.com/docs/integrations/document_transformers/openai_metadata_tagger/)

---

## Manual Tagging Patterns

### Tagging Paradigms

| Pattern | Description | Pros | Cons |
|---------|-------------|------|------|
| **Folksonomy** | Users create any tag freely | Maximum flexibility | Inconsistent, tag sprawl |
| **Controlled Vocabulary** | Tags from predefined list only | Consistent, searchable | Rigid, may miss concepts |
| **Hierarchical Taxonomy** | Parent/child tag relationships | Structured navigation | Complex to maintain |
| **Hybrid** | Controlled core + user suggestions | Balanced approach | Requires governance |

**Source:** [NN/g Taxonomy 101](https://www.nngroup.com/articles/taxonomy-101/)

### Controlled Vocabulary Best Practices

From enterprise document management systems:

1. **Governance:** Dedicated team manages tag vocabulary; new tags require approval
2. **Normalisation:** Lowercase, hyphens for spaces, consistent pluralisation
3. **Hierarchy limit:** Maximum 3-4 levels deep to prevent over-complexity
4. **Regular review:** Quarterly audits to merge synonyms, retire unused tags
5. **User suggestions:** Allow users to propose tags for review

**Source:** [Picturepark Taxonomy Best Practices](https://picturepark.com/content-management-blog/best-practices-for-dam-taxonomy-metadata-tags-and-controlled-vocabularies)

### Hierarchical Tag Structure

```python
# Tag hierarchy using path notation
tags = [
    "work",
    "work/project-alpha",
    "work/project-beta",
    "personal",
    "personal/health",
    "personal/finance",
]

# Querying: find all "work/*" tags
work_docs = tag_manager.find_by_tags(["work"], match_prefix=True)
```

**Benefits:**
- Enables drill-down navigation in WebUI
- Supports inheritance (tagging "work" implicitly includes sub-tags)
- Compatible with folder-like mental models

---

## Tag Libraries and Controlled Vocabularies

### Existing Vocabularies to Draw From

| Source | Type | Use Case | URL |
|--------|------|----------|-----|
| **Dublin Core Subject** | General vocabulary | Document classification | [dublincore.org](https://www.dublincore.org/) |
| **Library of Congress (LCSH)** | Hierarchical taxonomy | Academic/research | [loc.gov](https://www.loc.gov/aba/publications/FreeLCSH/freelcsh.html) |
| **IPTC Media Topics** | News/media taxonomy | Journalism, articles | [iptc.org](https://iptc.org/standards/media-topics/) |
| **Schema.org Types** | Structured vocabulary | Web content, technical | [schema.org](https://schema.org/) |
| **Industry Taxonomies** | Domain-specific | Legal, medical, financial | Various |

### User-Editable Tag Library Pattern

```python
@dataclass
class TagLibrary:
    """Manages available tags with controlled vocabulary + user extensions."""

    # System tags (curated, cannot be deleted)
    system_namespaces: dict[str, list[str]] = field(default_factory=lambda: {
        "document-type": ["report", "article", "documentation", "legal", "financial", "academic"],
        "sensitivity": ["public", "internal", "confidential"],
        "status": ["draft", "review", "approved", "archived"],
    })

    # User-defined namespaces (fully customisable)
    user_namespaces: dict[str, list[str]] = field(default_factory=dict)

    # Pending suggestions from auto-tagging (user can promote)
    suggestions: list[TagSuggestion] = field(default_factory=list)

    def is_valid_tag(self, tag: str) -> bool:
        """Check if tag exists in library (system or user)."""
        ...

    def suggest_tag(self, tag: str, source: str = "auto") -> None:
        """Add tag to suggestions for user review."""
        ...

    def promote_suggestion(self, tag: str, namespace: str) -> None:
        """Move suggestion to official user namespace."""
        ...
```

**SharePoint Managed Metadata Pattern:**

Following [SharePoint's approach](https://learn.microsoft.com/en-us/sharepoint/managed-metadata):
- **Closed term sets:** Curated lists for critical categories (document type, sensitivity)
- **Open term sets:** Users can contribute new terms (projects, topics)
- **Local vs global:** Some tags apply organisation-wide, others are project-specific

---

## Differentiating Automated vs Manual Tags

### Visual Differentiation in UI

From [Brandfolder](https://brandfolder.com/resources/metadata-tag/):
> "Manual tags are shown with a solid line, and AI tags have a dotted line. This makes it easy to review the tags Brand Intelligence added."

**UI Patterns:**

| Tag Type | Visual Indicator | Interaction |
|----------|-----------------|-------------|
| Manual | Solid border, user icon | Edit, delete freely |
| Auto (confirmed) | Solid border, checkmark | Same as manual |
| Auto (unconfirmed) | Dotted border, sparkle icon | Confirm/reject/edit |
| Suggested | Faded, plus icon | Click to add |

### Provenance Metadata Pattern

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class TagEntry:
    """Tag with provenance tracking."""

    name: str
    source: Literal["manual", "auto-llm", "auto-keybert", "auto-ner", "imported"]
    confidence: float | None = None  # For auto-generated tags (0.0-1.0)
    confirmed: bool = True  # False for unreviewed auto-tags
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str | None = None  # User ID for manual, model name for auto

@dataclass
class DocumentMetadata:
    # ... other fields ...

    # Enhanced tag storage with provenance
    ragd_tags: list[TagEntry] = field(default_factory=list)

    # Convenience property for simple tag list
    @property
    def tag_names(self) -> list[str]:
        return [t.name for t in self.ragd_tags if t.confirmed]
```

### Benefits of Provenance Tracking

1. **User trust:** Users see which tags they added vs system-generated
2. **Quality assessment:** Track auto-tag accuracy over time
3. **Feedback loop:** Users "confirm" or "reject" auto-tags → improves ML
4. **Audit trail:** Required for compliance in regulated industries
5. **Rollback:** Can remove all auto-tags without affecting manual ones

**Source:** [Kontent.ai AI Auto-Tagging](https://kontent.ai/blog/ai-based-auto-tagging-of-content-what-you-need-to-know/)

---

## WebUI Benefits of Tagging

### Navigation and Discovery Features

| Feature | How Tags Enable It |
|---------|-------------------|
| **Tag cloud** | Visual overview of knowledge base themes (font size = frequency) |
| **Faceted search** | Filter results by multiple tags simultaneously |
| **Breadcrumb navigation** | Hierarchical tags create drill-down paths |
| **Related documents** | "Also tagged with..." suggestions |
| **Quick filters** | One-click to filter by frequently used tags |

### Productivity Features

| Feature | Implementation |
|---------|---------------|
| **Bulk operations** | Select all documents with tag, apply action |
| **Smart collections** | Saved tag combinations (e.g., "finance + Q3 + reviewed") |
| **Tag-based workflows** | Auto-actions based on tags (e.g., "draft" → review queue) |
| **Access control** | Restrict access by tag (e.g., "confidential" = admin only) |

### UI Design Patterns

From [WebAppHuddle](https://webapphuddle.com/design-tags-feature-in-web-apps/) and [UI-Patterns](https://ui-patterns.com/patterns/Tag):

- **Pill-style tags** with × to remove
- **Autocomplete** when typing new tags
- **Colour-coding** by namespace/category
- **Drag-and-drop** to tag documents
- **Tag input** with comma/enter to add multiple

**Source:** [Tags: From UX to Implementation](https://schof.co/tags-ux-to-implementation/)

---

## Tags for Automatic Collections

### Smart Collections Pattern

Tags enable **virtual folders** without moving files:

```python
@dataclass
class Collection:
    """A saved tag query that auto-collects matching documents."""

    id: str
    name: str
    description: str
    query: TagQuery
    auto_update: bool = True  # New documents matching query auto-join
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TagQuery:
    """Boolean combination of tags for collection membership."""

    include_all: list[str] = field(default_factory=list)  # AND logic
    include_any: list[str] = field(default_factory=list)  # OR logic
    exclude: list[str] = field(default_factory=list)      # NOT logic

    def matches(self, doc_tags: list[str]) -> bool:
        """Check if document tags match this query."""
        doc_set = set(doc_tags)

        # Must have ALL include_all tags
        if self.include_all and not set(self.include_all) <= doc_set:
            return False

        # Must have at least ONE include_any tag (if specified)
        if self.include_any and not set(self.include_any) & doc_set:
            return False

        # Must NOT have any exclude tags
        if self.exclude and set(self.exclude) & doc_set:
            return False

        return True
```

### Example Collections

| Collection Name | Tag Query | Description |
|-----------------|-----------|-------------|
| "Q3 Finance Reports" | `include_all: [finance, q3-2024]` | Quarterly review |
| "Active Projects" | `include_any: [project/*], exclude: [archived]` | All non-archived projects |
| "Needs Review" | `include_any: [draft, needs-review]` | Awaiting review |
| "Research Papers" | `include_any: [academic, research]` | Academic materials |
| "Confidential" | `include_all: [confidential]` | Access-controlled |

### Benefits Over Folder Hierarchies

From [Shelf.io](https://shelf.io/blog/why-knowledge-management-must-include-a-tagging-system/):

1. **Dynamic membership:** New documents auto-join matching collections
2. **Multiple membership:** One document can be in many collections
3. **No duplication:** Unlike folders, no copy/move required
4. **Cross-cutting views:** Collections can span hierarchies
5. **Flexible reorganisation:** Change tag = change membership instantly

**Source:** [Forte Labs: Tagging for PKM](https://fortelabs.com/blog/a-complete-guide-to-tagging-for-personal-knowledge-management/)

---

## Documentation Strategy for Non-Technical Users

### Recommended Documentation Types

| Doc Type | Purpose | Audience | Location |
|----------|---------|----------|----------|
| **Tutorial** | "Learn tagging in 10 minutes" | New users | `docs/tutorials/tagging-basics.md` |
| **Guide** | "How to organise your knowledge base" | Regular users | `docs/guides/organising-with-tags.md` |
| **Reference** | Tag command syntax, API | Power users | `docs/reference/metadata-commands.md` |
| **Explanation** | Why tagging matters, concepts | Curious users | `docs/explanation/tagging-system.md` |
| **In-app Help** | Contextual tooltips | WebUI users | Embedded in UI |

### Key Content for Non-Technical Users

**Tutorial content should cover:**
1. **Why tags matter:** "Tags help you find documents faster"
2. **Auto vs manual:** "ragd automatically suggests tags. You can accept, reject, or add your own."
3. **Hierarchies:** "Use `/` to create folders: `work/project-alpha`"
4. **Collections:** "Tags create virtual folders without moving files"

**Guide content should cover:**
1. **Organising by project:** Tag workflow for project-based work
2. **Research workflows:** Academic tagging patterns
3. **Review workflows:** Using status tags (draft → review → approved)
4. **Bulk operations:** Tagging multiple documents at once

---

## Recommendations for ragd

### Current State

ragd already has:
- **TagManager** (`src/ragd/metadata/tags.py`): Full CRUD for user tags
- **LLMMetadataEnhancer** (`src/ragd/llm/metadata.py`): Classification via Ollama
- **DocumentMetadata** (`src/ragd/metadata/schema.py`): `ragd_tags` field
- **find_by_tags()**: Query documents by tag with AND/OR logic

### Enhancement Opportunities

| Enhancement | Effort | Impact | Informs Feature |
|-------------|--------|--------|-----------------|
| **Tag provenance** (source, confidence, confirmed) | Medium | High | New feature |
| **Tag library** (controlled vocabulary + suggestions) | Medium | Medium | New feature |
| **Auto-tag suggestions** (surface KeyBERT/LLM as suggestions) | Low | Medium | Extends F-030 |
| **Collection queries** (saved tag combinations) | Medium | High | Extends F-031 |
| **User documentation** (tutorial, guide, explanation) | Medium | High | User docs |

### Proposed Features

**F-061: Auto-Tag Suggestions**
- Surface KeyBERT keywords and LLM classifications as "suggested tags"
- Users can confirm/reject/edit suggestions
- Confirmed tags become manual tags

**F-062: Tag Library Management**
- System namespaces (document-type, sensitivity, status)
- User-defined namespaces
- Tag suggestion queue with approval workflow

**F-063: Smart Collections**
- Saved tag queries
- Auto-updating membership
- Collection-based navigation in WebUI

---

## References

### Best Practices and Architecture
- [Unstructured: Metadata in RAG](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results)
- [Haystack: Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)
- [NN/g: Taxonomy 101](https://www.nngroup.com/articles/taxonomy-101/)
- [Docsie: Tagging System Guide](https://www.docsie.io/blog/glossary/tagging-system/)

### Libraries and Tools
- [LlamaIndex Metadata Extraction](https://docs.llamaindex.ai/en/stable/module_guides/loading/documents_and_nodes/usage_metadata_extractor/)
- [LangChain OpenAI Metadata Tagger](https://python.langchain.com/docs/integrations/document_transformers/openai_metadata_tagger/)
- [Hugging Face Zero-Shot Classification](https://huggingface.co/tasks/zero-shot-classification)
- [KeyBERT](https://github.com/MaartenGr/KeyBERT)

### UX and WebUI Patterns
- [WebAppHuddle: Tags Feature Design](https://webapphuddle.com/design-tags-feature-in-web-apps/)
- [UI-Patterns: Tagging](https://ui-patterns.com/patterns/Tag)
- [Tags: From UX to Implementation](https://schof.co/tags-ux-to-implementation/)

### Knowledge Management
- [Shelf.io: Why Tags Matter](https://shelf.io/blog/why-knowledge-management-must-include-a-tagging-system/)
- [Forte Labs: Tagging for PKM](https://fortelabs.com/blog/a-complete-guide-to-tagging-for-personal-knowledge-management/)
- [Picturepark: Taxonomy Best Practices](https://picturepark.com/content-management-blog/best-practices-for-dam-taxonomy-metadata-tags-and-controlled-vocabularies)

### Automated Tagging
- [Brandfolder: Automated Metadata Tagging](https://brandfolder.com/resources/metadata-tag/)
- [Kontent.ai: AI Auto-Tagging](https://kontent.ai/blog/ai-based-auto-tagging-of-content-what-you-need-to-know/)
- [PoolParty: Auto Classification](https://poolparty.biz/tagging-101-what-is-auto-classification)

### Enterprise Standards
- [SharePoint Managed Metadata](https://learn.microsoft.com/en-us/sharepoint/managed-metadata)
- [Adobe Experience Manager Smart Tagging](https://business.adobe.com/products/experience-manager/assets/smart-tagging.html)
- [TagSpaces: Local File Tagging](https://www.tagspaces.org/)

---

## Related Documentation

- [State-of-the-Art Metadata](./state-of-the-art-metadata.md) - Metadata extraction, storage, provenance
- [State-of-the-Art User Interfaces](./state-of-the-art-user-interfaces.md) - WebUI patterns
- [F-031: Tag Management](../features/completed/F-031-tag-management.md) - Current tag feature
- [F-030: Metadata Extraction](../features/completed/F-030-metadata-extraction.md) - Auto-extraction pipeline

---

**Status**: Research complete
