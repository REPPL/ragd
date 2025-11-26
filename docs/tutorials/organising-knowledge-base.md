# Organising Your Knowledge Base

Learn to use metadata and tags to organise and find your documents.

**Time:** 15 minutes
**Prerequisites:** ragd with metadata extras installed, some documents indexed
**Validates:** UC-005, F-029, F-030, F-031

> **Note:** This tutorial is a DRAFT for v0.2 specification validation. Implementation may differ.

---

## What You'll Learn

By the end of this tutorial, you'll know how to:
1. View automatically extracted metadata
2. Edit document metadata
3. Create and apply tags
4. Search with metadata filters
5. Organise documents into projects

---

## Before You Start

### Install Metadata Dependencies

```bash
# Install metadata extras
pip install "ragd[metadata]"

# Download NLP model for entity extraction
python -m spacy download en_core_web_sm
```

### Index Some Documents

If you haven't already, index a few documents:

```bash
ragd index ~/Documents/research/
```

---

## Step 1: View Automatic Metadata

When you index documents, ragd automatically extracts metadata. View it:

```bash
ragd meta show research-paper.pdf
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Document Metadata: research-paper.pdf                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Core Metadata (Dublin Core):                                │
│ ┌─────────────────────┬─────────────────────────────────┐  │
│ │ Title               │ Machine Learning in Healthcare   │  │
│ │ Creator             │ Dr. Jane Smith, Dr. John Doe     │  │
│ │ Subject             │ machine learning, healthcare,    │  │
│ │                     │ medical diagnosis, AI            │  │
│ │ Date                │ 2024-06-15                       │  │
│ │ Type                │ Research Paper                   │  │
│ │ Language            │ en (99% confidence)              │  │
│ └─────────────────────┴─────────────────────────────────┘  │
│                                                             │
│ Extracted Keywords:                                         │
│   machine learning (0.82), healthcare (0.78),               │
│   medical diagnosis (0.71), neural networks (0.65),         │
│   patient outcomes (0.58)                                   │
│                                                             │
│ Named Entities:                                             │
│   People: Dr. Jane Smith, Dr. John Doe                      │
│   Organisations: Stanford Medical Center, NIH               │
│   Locations: California, United States                      │
│                                                             │
│ RAG Metadata:                                               │
│ ┌─────────────────────┬─────────────────────────────────┐  │
│ │ Source Path         │ ~/Documents/research/paper.pdf   │  │
│ │ Indexed             │ 2025-11-26 10:15:32              │  │
│ │ Chunks              │ 45                               │  │
│ │ Embedding Model     │ all-MiniLM-L6-v2                 │  │
│ └─────────────────────┴─────────────────────────────────┘  │
│                                                             │
│ Tags: (none)                                                │
│ Project: (none)                                             │
└─────────────────────────────────────────────────────────────┘
```

**What's automatically extracted:**
- **Title**: From PDF metadata or first heading
- **Creator**: From PDF author field or extracted names
- **Subject**: Keywords extracted by KeyBERT
- **Language**: Detected by langdetect
- **Named Entities**: People, organisations, locations via spaCy

**Checkpoint:** View automatic metadata for an indexed document

---

## Step 2: Edit Metadata

Automatic extraction isn't always perfect. Edit metadata manually:

```bash
ragd meta edit research-paper.pdf --title "ML Applications in Healthcare Diagnostics"
```

**Expected output:**
```
Updated metadata for: research-paper.pdf
  Title: Machine Learning in Healthcare
      → ML Applications in Healthcare Diagnostics
```

**Edit multiple fields:**

```bash
ragd meta edit research-paper.pdf \
  --title "ML Applications in Healthcare Diagnostics" \
  --creator "Smith, J.; Doe, J." \
  --date "2024-06-15"
```

**Interactive editing:**

```bash
ragd meta edit research-paper.pdf --interactive
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Edit Metadata: research-paper.pdf                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Title [ML Applications in Healthcare Diagnostics]:          │
│ > _                                                         │
│                                                             │
│ Creator [Smith, J.; Doe, J.]:                               │
│ > _                                                         │
│                                                             │
│ (Press Enter to keep current value, Ctrl+C to cancel)       │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Successfully edit document metadata

---

## Step 3: Add Tags

Tags help you categorise documents. Add your first tag:

```bash
ragd tag add research-paper.pdf "machine-learning"
```

**Expected output:**
```
Added tag 'machine-learning' to: research-paper.pdf
```

**Add multiple tags:**

```bash
ragd tag add research-paper.pdf "healthcare" "priority:high" "status:reading"
```

**Expected output:**
```
Added tags to: research-paper.pdf
  + healthcare
  + priority:high
  + status:reading
```

**View tags on a document:**

```bash
ragd tag list research-paper.pdf
```

**Expected output:**
```
Tags for research-paper.pdf:
  machine-learning
  healthcare
  priority:high
  status:reading
```

**Checkpoint:** Add and view tags on a document

---

## Step 4: Use Hierarchical Tags

Tags can be hierarchical using colons:

```bash
# Add hierarchical tags
ragd tag add paper.pdf "topic:ml:neural-networks"
ragd tag add paper.pdf "topic:ml:transformers"
ragd tag add report.pdf "topic:finance:quarterly"
```

**List all tags in your knowledge base:**

```bash
ragd tag list --all
```

**Expected output:**
```
Tags in knowledge base:

topic: (3 documents)
├── ml: (2 documents)
│   ├── neural-networks (1)
│   └── transformers (1)
└── finance: (1 document)
    └── quarterly (1)

healthcare (1 document)
machine-learning (1 document)
priority:
├── high (1)
└── low (0)
status:
├── reading (1)
└── done (0)
```

**Checkpoint:** Understand hierarchical tag structure

---

## Step 5: Batch Tagging

Tag multiple documents at once:

```bash
# Tag all PDFs in a directory
ragd tag add ~/Documents/research/*.pdf "source:research"

# Tag by search results
ragd search "machine learning" --tag "topic:ml"
```

**Expected output:**
```
Tagged 5 documents matching "machine learning" with: topic:ml
  + research-paper.pdf
  + ml-intro.pdf
  + neural-nets-guide.pdf
  + transformer-paper.pdf
  + deep-learning-book.pdf
```

**Checkpoint:** Batch tag documents efficiently

---

## Step 6: Search with Filters

Combine semantic search with metadata filters:

```bash
# Search within tagged documents
ragd search "neural networks" --tag "priority:high"
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search Results                                           │
│    Query: "neural networks"                                 │
│    Filter: tag:priority:high                                │
├─────────────────────────────────────────────────────────────┤
│ 1. research-paper.pdf (Score: 0.91)                         │
│    Tags: machine-learning, healthcare, priority:high        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Deep neural networks have shown remarkable results in    │ │
│ │ medical image analysis, particularly in detecting...     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**More filter examples:**

```bash
# Search by author
ragd search "diagnosis" --creator "Smith"

# Search by date range
ragd search "quarterly results" --date-from "2024-01-01" --date-to "2024-12-31"

# Search by language
ragd search "machine learning" --language "en"

# Combine multiple filters
ragd search "revenue" --tag "topic:finance" --date-from "2024-01-01"
```

**Checkpoint:** Filter search results by metadata

---

## Step 7: Create Projects

Group related documents into projects:

```bash
# Assign documents to a project
ragd project add "ML Research" research-paper.pdf ml-intro.pdf
```

**Expected output:**
```
Created project: ML Research
Added 2 documents:
  + research-paper.pdf
  + ml-intro.pdf
```

**View project contents:**

```bash
ragd project show "ML Research"
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Project: ML Research                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Documents: 2                                                │
│ Total Chunks: 89                                            │
│ Last Updated: 2025-11-26                                    │
│                                                             │
│ Contents:                                                   │
│   1. research-paper.pdf (45 chunks)                         │
│      Tags: machine-learning, healthcare                     │
│   2. ml-intro.pdf (44 chunks)                               │
│      Tags: machine-learning, tutorial                       │
└─────────────────────────────────────────────────────────────┘
```

**Search within a project:**

```bash
ragd search "neural networks" --project "ML Research"
```

**Checkpoint:** Organise documents into projects

---

## Step 8: List and Filter Documents

View all documents with filters:

```bash
# List all documents
ragd list

# Filter by tag
ragd list --tag "priority:high"

# Filter by project
ragd list --project "ML Research"

# Sort by date
ragd list --sort date --desc
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Documents (showing 5 of 12)                                 │
│ Filter: tag:priority:high                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  #  Document              Chunks  Tags              Date    │
│ ─── ──────────────────── ─────── ───────────────── ──────── │
│  1  research-paper.pdf      45   ml, healthcare    Jun 2024 │
│  2  urgent-report.pdf       23   finance, urgent   Nov 2025 │
│  3  action-items.md         12   tasks, urgent     Nov 2025 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Filter and list documents effectively

---

## Step 9: Remove Tags

Clean up tags you no longer need:

```bash
# Remove a tag from a document
ragd tag remove research-paper.pdf "status:reading"
```

**Expected output:**
```
Removed tag 'status:reading' from: research-paper.pdf
```

**Remove a tag from all documents:**

```bash
ragd tag remove --all "deprecated-tag"
```

**Delete unused tags:**

```bash
ragd tag prune
```

**Expected output:**
```
Removed 3 unused tags:
  - old-project
  - temp
  - draft
```

**Checkpoint:** Manage and clean up tags

---

## What You Learned

Congratulations! You've completed the organising tutorial. You now know how to:

| Task | Command |
|------|---------|
| View document metadata | `ragd meta show <file>` |
| Edit metadata | `ragd meta edit <file> --title "..."` |
| Add tags | `ragd tag add <file> "tag"` |
| List all tags | `ragd tag list --all` |
| Search with filters | `ragd search "<query>" --tag "..."` |
| Create projects | `ragd project add "Name" <files>` |
| List documents | `ragd list --tag "..." --project "..."` |
| Remove tags | `ragd tag remove <file> "tag"` |

---

## Metadata Schema (Dublin Core)

ragd uses Dublin Core metadata fields:

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Document title | "Machine Learning Guide" |
| `creator` | Author(s) | "Jane Smith; John Doe" |
| `subject` | Keywords/topics | "ML, AI, neural networks" |
| `description` | Summary | "An introduction to..." |
| `date` | Publication date | "2024-06-15" |
| `type` | Document type | "Research Paper", "Report" |
| `format` | File format | "application/pdf" |
| `language` | ISO language code | "en" |

---

## Next Steps

- **Back up your data:** [Backing Up Your Data](./backing-up-data.md)
- **Advanced search:** [Search Guide](../guides/search.md)
- **Automate tagging:** [Tag Automation Guide](../guides/tag-automation.md)

---

## Troubleshooting

### "Metadata extraction failed"

Install NLP dependencies:
```bash
pip install "ragd[metadata]"
python -m spacy download en_core_web_sm
```

### Keywords not relevant

- KeyBERT works best with longer documents
- Try adjusting diversity: `ragd config set metadata.keyword_diversity 0.7`

### Entity extraction missing names

- spaCy's small model may miss some entities
- For better accuracy: `python -m spacy download en_core_web_trf`
- Configure: `ragd config set metadata.spacy_model en_core_web_trf`

### Tags not syncing

- Run `ragd meta rebuild` to reindex metadata
- Check storage: `ragd doctor`

---

## Related Documentation

- [UC-005: Manage Metadata](../use-cases/briefs/UC-005-manage-metadata.md)
- [F-029: Metadata Storage](../development/features/planned/F-029-metadata-storage.md)
- [F-030: Metadata Extraction](../development/features/planned/F-030-metadata-extraction.md)
- [F-031: Tag Management](../development/features/planned/F-031-tag-management.md)
- [Dublin Core Schema](../reference/metadata-schema.md)

---
