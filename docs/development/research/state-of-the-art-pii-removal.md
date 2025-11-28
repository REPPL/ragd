# State-of-the-Art: PII Removal in RAG Systems

Comprehensive research on detecting, removing, and protecting Personally Identifiable Information (PII) in Retrieval-Augmented Generation systems.

## Executive Summary

PII removal in RAG systems is a critical challenge that spans three interconnected domains: **detection** (identifying PII in documents), **removal** (redacting or anonymising PII before storage), and **protection** (securing data after embedding). This research surveys current approaches and identifies practical solutions aligned with ragd's privacy-first architecture.

**Key Findings:**

1. **Hybrid detection** (NER + regex + rules) achieves the best balance of accuracy (F1: 91-94%) and performance
2. **Pre-vectorisation sanitisation** is more practical than post-embedding protection
3. **Embedding inversion attacks** can recover 92% of original text—embeddings require protection
4. **Microsoft Presidio** emerges as the leading open-source solution for local PII detection
5. **GDPR compliance** requires audit trails and complete cascade deletion capabilities

---

## 1. Privacy Threat Landscape

### 1.1 Attacks on RAG Systems

RAG systems face unique privacy risks due to their architecture—private data is both stored and actively retrieved during generation.

#### DEAL Attack (2024)

The [Documents Extraction Attack via LLM-Optimizer (DEAL)](https://openreview.net/forum?id=sx8dtyZT41) leverages LLMs to iteratively refine attack strings that induce RAG models to reveal private data in responses.

- **Effectiveness**: Close to 99% accuracy in extracting PII from retrieved documents
- **Tested on**: Qwen2, Llama3.1, GPT-4o
- **Implication**: Retrieved context can leak to end users through adversarial prompts

#### Embedding Inversion Attacks

Research demonstrates that [text embeddings reveal almost as much as the original text](https://ironcorelabs.com/ai-encryption/). Attackers can reconstruct sensitive information from vector representations.

- **Recovery rate**: 92% exact text recovery including full names and health diagnoses ([Morris et al., 2023](https://aclanthology.org/2024.acl-long.230/))
- **Attack method**: Transferable attacks work even without access to the original embedding model
- **Implication**: Embeddings must be treated with the same security as raw text

#### Privacy Leakage Through Retrieval

[Zeng et al. (ACL 2024)](https://aclanthology.org/2024.findings-acl.267/) demonstrate that RAG "reshapes the inherent behaviors of LLM generation, posing new privacy issues":

- Retrieved documents may contain PII from other users
- LLMs can memorise and disclose sensitive information from context
- Current privacy-preserving methods lack formal guarantees

### 1.2 Threat Model for Local RAG

For ragd's local-only architecture, the primary threats are:

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Physical device access | Critical | Encryption at rest (ADR-0010) |
| Embedding inversion | High | Pre-vectorisation sanitisation |
| Accidental indexing | Medium | PII detection before ingestion |
| Forensic recovery | Medium | Secure deletion (F-017) |

---

## 2. PII Detection Techniques

### 2.1 Named Entity Recognition (NER)

NER identifies entities like persons, locations, and organisations in text. Modern approaches use transformer-based models for context-aware detection.

#### spaCy NER Models

[spaCy](https://spacy.io/) provides multiple model sizes with different accuracy/performance trade-offs:

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `en_core_web_sm` | 12MB | Fast | Quick screening |
| `en_core_web_lg` | 560MB | Medium | Balanced (Presidio default) |
| `en_core_web_trf` | 438MB | Slow | Maximum accuracy |

**Entities detected**: PERSON, ORG, GPE (geo-political), LOC, DATE, MONEY, etc.

**Limitation**: NER alone misses structured PII like credit cards, SSNs, and IBANs.

#### Transformer-Based NER

Hugging Face transformers like [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) offer higher accuracy:

```python
# Example: Using transformers with Presidio
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import TransformersNlpEngine

nlp_engine = TransformersNlpEngine(models=[{
    "lang_code": "en",
    "model_name": {
        "spacy": "en_core_web_sm",
        "transformers": "dslim/bert-base-NER"
    }
}])
```

**Source**: [Presidio Transformers Recognizer](https://microsoft.github.io/presidio/samples/python/transformers_recognizer/)

### 2.2 Pattern-Based Detection

Regular expressions and validation logic detect structured PII:

| PII Type | Detection Method | Example Pattern |
|----------|------------------|-----------------|
| Email | Regex | `\b[\w.-]+@[\w.-]+\.\w+\b` |
| Phone (UK) | Regex + validation | `(\+44|0)\s?\d{4}\s?\d{6}` |
| Credit Card | Regex + Luhn checksum | `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}` |
| National Insurance | Regex + format | `[A-Z]{2}\d{6}[A-Z]` |
| IBAN | Regex + checksum | Country-specific patterns |

**Strength**: High precision for well-defined formats
**Limitation**: Cannot detect context-dependent PII (e.g., "my mother's name is...")

### 2.3 Hybrid Approaches

The most effective solutions combine multiple detection methods:

#### Microsoft Presidio

[Presidio](https://github.com/microsoft/presidio) is Microsoft's open-source PII detection framework supporting 24+ entity types out of the box.

**Architecture**:
```
Text Input
    ↓
┌─────────────────────────────────────┐
│ Presidio Analyzer                   │
│  ├─ Pattern Recognizers (regex)     │
│  ├─ NER (spaCy/transformers)        │
│  ├─ Custom Recognizers              │
│  └─ Context Enhancement             │
└─────────────────────────────────────┘
    ↓
Detection Results (entity, position, confidence)
```

**Key Features**:
- Configurable recognizers per entity type
- Multi-language support
- Context-aware scoring (e.g., "name:" prefix increases confidence)
- Extensible with custom recognizers
- Local execution (no cloud required)

**Installation**:
```bash
pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg
```

**Source**: [Microsoft Presidio Documentation](https://microsoft.github.io/presidio/)

#### Research Hybrid Model

A [hybrid rule-based NLP and ML approach](https://www.nature.com/articles/s41598-025-04971-9) achieved:

| Metric | Score |
|--------|-------|
| Precision | 94.7% |
| Recall | 89.4% |
| F1-Score | 91.1% |
| Accuracy (financial docs) | 93% |

### 2.4 LLM-Based Detection

Large language models offer context-aware PII detection but with trade-offs:

**Strengths**:
- Understands context ("My SSN is" vs "SSN format is")
- Handles paraphrased PII ("reached me at my mobile")
- [82% improvement](https://arxiv.org/html/2501.09765v1) over fine-tuned NER in some benchmarks

**Weaknesses**:
- Inconsistent—may hallucinate or miss structured PII
- Slower than rule-based approaches
- Requires LLM availability (conflicts with offline-first)
- Difficult to audit/verify decisions

**Performance Comparison**:

| Model | General Text F1 | Clinical Text F1 |
|-------|-----------------|------------------|
| GLiNER PII | 0.62 | 0.41 |
| OpenPipe PII-Redact | 0.98 | 0.42 |
| Hybrid NER+Rules | 0.91 | 0.89+ |

**Source**: [John Snow Labs Comparison](https://www.johnsnowlabs.com/how-good-are-open-source-llm-based-de-identification-tools-in-a-medical-context/)

**Recommendation**: Use LLM-based detection as optional enhancement, not primary method.

---

## 3. PII Removal Strategies

Once PII is detected, several strategies exist for handling it:

### 3.1 Redaction

Replace PII with placeholder tokens indicating the entity type.

```
Original: "Contact John Smith at john@example.com"
Redacted: "Contact [PERSON] at [EMAIL_ADDRESS]"
```

**Advantages**:
- Preserves document structure
- Clear what was removed
- Reversible with mapping table

**Disadvantages**:
- Loses semantic meaning
- May affect retrieval relevance

**Implementation**:
```python
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

anonymizer = AnonymizerEngine()
result = anonymizer.anonymize(
    text=text,
    analyzer_results=analyzer_results,
    operators={"DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})}
)
```

### 3.2 Synthesis (Fake Data Generation)

Replace PII with realistic fake values that preserve statistical properties.

```
Original: "Contact John Smith at john@example.com"
Synthesised: "Contact Jane Doe at user@domain.org"
```

**Advantages**:
- Preserves semantic meaning
- Better for analytics/ML training
- Document remains readable

**Disadvantages**:
- May introduce incorrect information
- **Not recommended for RAG** (fake PII could appear in search results)

**Source**: [Tonic Textual](https://www.tonic.ai/textual) provides synthesis capabilities but notes: "For RAG, it's crucial to redact rather than synthesise the entities. Redacting avoids inserting fake PII into the chunks, which could interfere with the retrieval process."

### 3.3 Generalisation

Replace specific values with broader categories.

```
Original: "John Smith, 45, from Manchester"
Generalised: "Male, 40-50, from North West England"
```

**Use Case**: Analytics where demographic patterns matter but individuals don't.

### 3.4 Suppression

Remove the PII entirely without replacement.

```
Original: "Contact John Smith for details"
Suppressed: "Contact for details"
```

**Use Case**: When PII is truly unnecessary for the document's purpose.

### 3.5 Pseudonymisation

Replace PII with consistent tokens that allow re-identification with a key.

```
Original: "John Smith called John Smith's office"
Pseudonymised: "PERSON_001 called PERSON_001's office"
```

**Advantages**:
- Maintains relationships between entities
- Reversible with key
- GDPR-compliant (pseudonymised data has reduced requirements)

---

## 4. Embedding-Level Protection

### 4.1 The Problem

Even after redacting PII from text, embeddings can leak information:

1. **Semantic encoding**: Embeddings capture meaning, potentially revealing PII
2. **Inversion attacks**: 92% text recovery from embeddings demonstrated
3. **Nearest-neighbour inference**: Similar embeddings may reveal relationships

### 4.2 Eguard Defence

[Eguard](https://arxiv.org/abs/2411.05034) is a novel defence mechanism using transformer-based projection networks:

**How it works**:
```
Original Embedding
    ↓
┌─────────────────────────────────────┐
│ Eguard Transformation               │
│  ├─ Sensitive Feature Detachment    │
│  ├─ Mutual Information Optimisation │
│  └─ Functionality Preservation      │
└─────────────────────────────────────┘
    ↓
Protected Embedding (same dimensions, protected content)
```

**Performance**:
- Protects 95%+ of tokens from inversion
- Maintains 98% consistency with original embeddings for downstream tasks
- Tested on T5, RoBERTa, MPNet, LLaMA, Gemma

**Trade-off**: Requires additional computation during embedding generation.

### 4.3 Differential Privacy for Embeddings

Add calibrated noise to embeddings to prevent information leakage:

**Word-Level DP**:
```python
# Conceptual approach
noisy_embedding = original_embedding + laplace_noise(sensitivity, epsilon)
```

**Challenges**:
- Large noise required for meaningful privacy (reduces utility)
- Affects retrieval accuracy significantly
- Complex to tune epsilon parameter

**Source**: [ACM TOPS: Metric DP for Sentence Embeddings](https://dl.acm.org/doi/10.1145/3708321)

### 4.4 Practical Recommendation

For ragd, a **defence-in-depth** approach:

1. **Primary**: Sanitise text before embedding (most practical)
2. **Secondary**: Encrypt embeddings at rest (SQLCipher)
3. **Optional**: Eguard-style transformation for high-security use cases

---

## 5. Privacy-Preserving Retrieval

### 5.1 LPRAG (Locally Private RAG)

[LPRAG](https://www.sciencedirect.com/science/article/abs/pii/S0306457325000913) applies Local Differential Privacy at the entity level rather than document level.

**Three-Phase Pipeline**:

1. **Preprocessing**: Identify entities (names, ages, medical terms), allocate privacy budgets
2. **DP Perturbation**: Apply tailored mechanisms per entity type:
   - Words: Synonym replacement with DP
   - Numbers: Bounded noise addition
   - Phrases: Semantic perturbation
3. **RAG Generation**: Use perturbed text for retrieval and generation

**Key Innovation—Adaptive Privacy Budget (APB)**:
- Allocate more noise to sensitive entities (SSN, diagnoses)
- Less noise to less sensitive entities (general locations)
- Preserves utility while protecting privacy

**Results**: Maintains high BLEU/ROUGE-L scores while preventing entity extraction.

### 5.2 SAGE (Synthetic Data for RAG)

[SAGE](https://arxiv.org/abs/2406.14773) proposes using synthetic data as a privacy-preserving alternative for retrieval.

**Two-Stage Paradigm**:

1. **Stage 1—Attribute Extraction and Generation**:
   - Extract key contextual attributes from original data
   - Generate synthetic documents preserving those attributes
   - Original PII is not transferred

2. **Stage 2—Agent-Based Refinement**:
   - Privacy Assessment Agent evaluates synthetic data for PII leakage
   - Rewriting Agent refines data based on feedback
   - Iterates until privacy agent deems it safe

**Results**: Comparable RAG performance to original data with substantially reduced privacy risks.

**Applicability to ragd**: More relevant for multi-user/shared RAG systems than personal RAG.

---

## 6. GDPR Compliance

### 6.1 Right to Erasure (Article 17)

The [GDPR right to be forgotten](https://gdpr-info.eu/art-17-gdpr/) requires:

1. Complete deletion of personal data on request
2. Deletion from all systems including backups
3. Notification to third parties who received the data

### 6.2 Challenges for RAG Systems

| Challenge | Description | Mitigation |
|-----------|-------------|------------|
| **Embedded PII** | PII encoded in embeddings | Pre-vectorisation sanitisation |
| **Distributed storage** | Data in SQLite + ChromaDB | Cascade deletion |
| **Backup retention** | PII persists in backups | Time-limited backups |
| **Session history** | PII in chat/search history | Session purge capability |
| **Model memorisation** | LLMs may memorise PII | Not applicable for RAG retrieval |

### 6.3 Implementation Requirements

From [AWS Knowledge Bases GDPR guide](https://aws.amazon.com/blogs/machine-learning/implementing-knowledge-bases-for-amazon-bedrock-in-support-of-gdpr-right-to-be-forgotten-requests/):

1. **Audit Framework**: Record all right-to-be-forgotten requests
2. **Cascade Deletion**: Remove from source, vector store auto-syncs
3. **Backup Handling**: 29-day retention or explicit snapshot purge
4. **Verification**: Confirm deletion across all storage layers

**ragd Implementation**:
```bash
# Proposed CLI
ragd purge --document <id> --reason "GDPR request" --cascade
# Actions:
# 1. Remove from ChromaDB (chunks + embeddings)
# 2. Remove from metadata SQLite
# 3. Log deletion in audit table
# 4. Note: User responsible for source file deletion
```

---

## 7. Tool Comparison

### 7.1 Feature Matrix

| Feature | Presidio | spaCy | Tonic Textual | GLiNER |
|---------|----------|-------|---------------|--------|
| **Open Source** | Yes | Yes | Partial | Yes |
| **Local/Offline** | Yes | Yes | Yes (SDK) | Yes |
| **Entity Types** | 24+ | 18 | 50+ | Variable |
| **Regex Support** | Built-in | Manual | Built-in | No |
| **Custom Entities** | Yes | Yes | Yes | Limited |
| **Multi-language** | Yes | Yes | Yes | Yes |
| **Anonymisation** | Built-in | Manual | Built-in | No |
| **Active Development** | Yes | Yes | Yes | Yes |
| **Python Support** | Native | Native | SDK | HuggingFace |

### 7.2 Performance Benchmarks

| Tool | Precision | Recall | F1-Score | Speed |
|------|-----------|--------|----------|-------|
| Presidio (default) | ~85% | ~80% | ~82% | Fast |
| Presidio (transformers) | ~92% | ~88% | ~90% | Medium |
| spaCy `en_core_web_lg` | ~83% | ~78% | ~80% | Fast |
| spaCy `en_core_web_trf` | ~90% | ~85% | ~87% | Slow |
| Hybrid NER+Rules | 94.7% | 89.4% | 91.1% | Fast |

**Note**: Performance varies significantly by domain (general vs medical vs financial).

### 7.3 Recommendation for ragd

**Primary**: Microsoft Presidio with spaCy `en_core_web_lg`

**Rationale**:
- Open source with active community
- Local/offline operation aligns with privacy-first
- Extensible for custom PII types
- Built-in anonymisation engine
- Good default performance with upgrade path (transformers)

---

## 8. Implementation Recommendations for ragd

### 8.1 Architecture

```
Document Ingestion
    ↓
┌─────────────────────────────────────┐
│ PII Detection Pipeline              │
│  ├─ Presidio Analyzer               │
│  │   ├─ Pattern Recognizers         │
│  │   ├─ spaCy NER                   │
│  │   └─ Custom Recognizers          │
│  │                                  │
│  └─ Confidence Scoring              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ User Decision Point                 │
│  ├─ View PII Report                 │
│  ├─ Index as-is                     │
│  ├─ Redact and index                │
│  ├─ Skip document                   │
│  └─ Configure per-entity handling   │
└─────────────────────────────────────┘
    ↓
Text Processing → Chunking → Embedding → Storage
```

### 8.2 Phased Implementation

#### Phase 1: Detection (F-023 - Existing)
- Integrate Presidio for detection
- Generate PII reports before indexing
- CLI flags: `--scan-pii`, `--pii-action`

#### Phase 2: Removal (F-055 - New)
- Add redaction capabilities
- Per-entity-type handling configuration
- Batch processing support

#### Phase 3: Embedding Protection (F-056 - New)
- Optional Eguard-style transformation
- Configuration for security/performance trade-off
- Metrics for protection effectiveness

#### Phase 4: Compliance (F-057 - New)
- GDPR-compliant deletion
- Audit trail
- Cascade purge across storage layers

### 8.3 Configuration Schema

```yaml
# ~/.ragd/config.yaml
pii:
  enabled: true
  scan_on_index: prompt  # always, never, prompt

  detection:
    engine: presidio  # presidio, spacy, hybrid
    model: en_core_web_lg  # spaCy model
    confidence_threshold: 0.7

    entities:
      - PERSON
      - EMAIL_ADDRESS
      - PHONE_NUMBER
      - CREDIT_CARD
      - UK_NINO  # National Insurance Number
      - LOCATION
      - DATE_TIME
      - IBAN_CODE

    custom_patterns:
      - name: PROJECT_CODE
        pattern: "PRJ-\\d{6}"
        score: 0.9

  handling:
    default_action: prompt  # index, skip, redact, prompt
    redaction_char: "█"

    per_entity:
      PERSON: redact
      EMAIL_ADDRESS: redact
      PHONE_NUMBER: redact
      LOCATION: index  # Less sensitive

  allowlist:
    patterns:
      - "example\\.com$"  # Test domains
      - "^555-"  # US fictional numbers
    values:
      - "John Doe"  # Placeholder name

  embedding_protection:
    enabled: false  # Performance impact
    method: eguard  # eguard, none

  audit:
    enabled: true
    log_detections: true
    log_actions: true
```

### 8.4 CLI Integration

```bash
# Scan documents for PII (no indexing)
ragd scan ~/Documents/contracts/
# Output: PII report per document

# Index with PII scanning
ragd index ~/Documents/ --scan-pii
# Interactive: prompts for each document with PII

# Index with automatic redaction
ragd index ~/Documents/ --scan-pii --pii-action redact

# Index with automatic skip of PII documents
ragd index ~/Documents/ --scan-pii --pii-action skip

# GDPR-compliant purge
ragd purge --document <id> --cascade --audit "GDPR request #123"

# View audit log
ragd audit --type pii --since "2024-01-01"
```

---

## 9. Research Sources

### Academic Papers

| Paper | Authors | Venue | Year |
|-------|---------|-------|------|
| [The Good and The Bad: Exploring Privacy Issues in RAG](https://aclanthology.org/2024.findings-acl.267/) | Zeng et al. | ACL Findings | 2024 |
| [DEAL: Privacy Attack on RAG](https://openreview.net/forum?id=sx8dtyZT41) | -- | OpenReview | 2024 |
| [Transferable Embedding Inversion Attack](https://aclanthology.org/2024.acl-long.230/) | -- | ACL | 2024 |
| [Eguard: Defending LLM Embeddings](https://arxiv.org/abs/2411.05034) | Liu et al. | arXiv | 2024 |
| [SAGE: Synthetic Data for Privacy-Preserving RAG](https://arxiv.org/abs/2406.14773) | Zeng et al. | EMNLP | 2025 |
| [LPRAG: Locally Private RAG](https://www.sciencedirect.com/science/article/abs/pii/S0306457325000913) | -- | IPM | 2025 |
| [Hybrid PII Detection in Financial Docs](https://www.nature.com/articles/s41598-025-04971-9) | -- | Scientific Reports | 2025 |

### Tools and Frameworks

| Tool | Organisation | URL |
|------|--------------|-----|
| Microsoft Presidio | Microsoft | [github.com/microsoft/presidio](https://github.com/microsoft/presidio) |
| spaCy | Explosion | [spacy.io](https://spacy.io/) |
| Tonic Textual | Tonic.ai | [tonic.ai/textual](https://www.tonic.ai/textual) |
| LlamaIndex PII | LlamaIndex | [llamaindex.ai](https://www.llamaindex.ai/blog/pii-detector-hacking-privacy-in-rag) |

### Regulatory Guidance

| Regulation | Article | URL |
|------------|---------|-----|
| GDPR | Article 17 (Right to Erasure) | [gdpr-info.eu/art-17-gdpr](https://gdpr-info.eu/art-17-gdpr/) |
| AWS GDPR for RAG | Implementation Guide | [aws.amazon.com](https://aws.amazon.com/blogs/machine-learning/implementing-knowledge-bases-for-amazon-bedrock-in-support-of-gdpr-right-to-be-forgotten-requests/) |

---

## Related Documentation

- [State-of-the-Art Privacy](./state-of-the-art-privacy.md) - Encryption and threat models
- [F-023: PII Detection](../features/planned/F-023-pii-detection.md) - Detection feature spec
- [F-059: Embedding Privacy Protection](../features/planned/F-059-embedding-privacy-protection.md) - Embedding defence
- [F-060: GDPR-Compliant Deletion](../features/planned/F-060-gdpr-compliant-deletion.md) - Compliance deletion
- [F-015: Database Encryption](../features/planned/F-015-database-encryption.md) - Data-at-rest protection
- [F-017: Secure Deletion](../features/planned/F-017-secure-deletion.md) - Data removal
- [ADR-0003: Privacy-First Architecture](../decisions/adrs/0003-privacy-first-architecture.md) - Core privacy principles
- [ADR-0028: PII Handling Architecture](../decisions/adrs/0028-pii-handling-architecture.md) - PII architecture
- [ADR-0029: Privacy-Preserving Embedding Strategy](../decisions/adrs/0029-embedding-privacy-strategy.md) - Embedding protection

---

**Status:** Research complete
