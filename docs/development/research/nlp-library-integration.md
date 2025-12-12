# NLP Library Integration Guide

Implementation-specific guidance for integrating KeyBERT, spaCy, and langdetect into ragd v0.2 for F-030 (Metadata Extraction).

---

## Overview

This guide documents NLP library integration for automatic metadata extraction:

| Library | Purpose | Feature |
|---------|---------|---------|
| **KeyBERT** | Keyword extraction | F-030: Metadata Extraction |
| **spaCy** | Named Entity Recognition | F-030: Metadata Extraction |
| **langdetect** | Language detection | F-030: Metadata Extraction |

---

## KeyBERT

### Installation

```bash
pip install keybert
```

KeyBERT reuses sentence-transformers, which ragd already depends on.

### Basic Usage

```python
from keybert import KeyBERT

# Use same model as ragd embeddings (no extra memory)
kw_model = KeyBERT(model='all-MiniLM-L6-v2')

doc = """
Supervised learning is the machine learning task of learning a function
that maps an input to an output based on example input-output pairs.
"""

# Extract keywords
keywords = kw_model.extract_keywords(doc)
# Returns: [('supervised', 0.5), ('learning', 0.45), ...]
```

### Configuration Options

```python
keywords = kw_model.extract_keywords(
    doc,
    keyphrase_ngram_range=(1, 2),  # Unigrams and bigrams
    stop_words='english',           # Remove stop words
    top_n=10,                       # Number of keywords
    use_mmr=True,                   # Maximal Marginal Relevance (diversity)
    diversity=0.5,                  # Diversity threshold (0-1)
)
```

### Recommended Models

| Model | Use Case | Memory |
|-------|----------|--------|
| `all-MiniLM-L6-v2` | English documents (default) | ~80MB |
| `paraphrase-multilingual-MiniLM-L12-v2` | Multi-lingual | ~120MB |
| `all-mpnet-base-v2` | Higher accuracy | ~420MB |

### Reusing ragd Embedding Model

KeyBERT can share the sentence-transformer model with ragd's embedder to avoid loading duplicate models:

```python
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

# Reuse ragd's embedding model
sentence_model = SentenceTransformer("all-MiniLM-L6-v2")

# Use for KeyBERT
kw_model = KeyBERT(model=sentence_model)

# Also use for ragd embeddings
embeddings = sentence_model.encode(["text"])
```

### ragd Integration Pattern

```python
class KeywordExtractor:
    """Extract keywords using KeyBERT."""

    def __init__(self, model: SentenceTransformer | None = None):
        self._kw_model: KeyBERT | None = None
        self._shared_model = model

    def _ensure_model(self) -> KeyBERT:
        """Lazy load KeyBERT."""
        if self._kw_model is None:
            from keybert import KeyBERT

            if self._shared_model:
                self._kw_model = KeyBERT(model=self._shared_model)
            else:
                self._kw_model = KeyBERT(model='all-MiniLM-L6-v2')
        return self._kw_model

    def extract(
        self,
        text: str,
        top_n: int = 10,
        diversity: float = 0.5,
    ) -> list[tuple[str, float]]:
        """Extract keywords from text."""
        kw_model = self._ensure_model()
        return kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n,
            use_mmr=True,
            diversity=diversity,
        )
```

---

## spaCy

### Installation

```bash
pip install spacy

# Download model
python -m spacy download en_core_web_sm
```

### Model Options

| Model | Size | Accuracy | Use Case |
|-------|------|----------|----------|
| `en_core_web_sm` | ~13MB | Good | Fast, low memory |
| `en_core_web_md` | ~40MB | Better | Balanced |
| `en_core_web_lg` | ~560MB | Best | High accuracy |
| `en_core_web_trf` | ~400MB | Highest | Transformer-based |

**Recommendation:** Use `en_core_web_sm` by default, offer `en_core_web_trf` for high-accuracy needs.

### Basic NER Usage

```python
import spacy

# Load model
nlp = spacy.load('en_core_web_sm')

# Process text
text = "Apple Inc. is headquartered in Cupertino, California."
doc = nlp(text)

# Extract entities
for ent in doc.ents:
    print(f"{ent.text}: {ent.label_}")
# Apple Inc.: ORG
# Cupertino: GPE
# California: GPE
```

### Entity Types

| Label | Description | Example |
|-------|-------------|---------|
| `PERSON` | People | "John Smith" |
| `ORG` | Organisations | "Apple Inc." |
| `GPE` | Geopolitical entities | "London" |
| `DATE` | Dates | "January 2025" |
| `MONEY` | Monetary values | "$1 million" |
| `PRODUCT` | Products | "iPhone" |
| `EVENT` | Events | "World Cup" |
| `WORK_OF_ART` | Titles | "Mona Lisa" |
| `LAW` | Laws/Acts | "GDPR" |
| `LANGUAGE` | Languages | "English" |

### ragd Integration Pattern

```python
from dataclasses import dataclass

@dataclass
class Entity:
    """Extracted named entity."""
    text: str
    label: str
    start: int
    end: int

class EntityExtractor:
    """Extract named entities using spaCy."""

    def __init__(self, model: str = 'en_core_web_sm'):
        self._nlp = None
        self._model_name = model

    def _ensure_nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load(self._model_name)
            except OSError:
                # Model not downloaded
                from spacy.cli import download
                download(self._model_name)
                self._nlp = spacy.load(self._model_name)
        return self._nlp

    def extract(self, text: str) -> list[Entity]:
        """Extract named entities from text."""
        nlp = self._ensure_nlp()
        doc = nlp(text)
        return [
            Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
            )
            for ent in doc.ents
        ]

    def extract_by_type(
        self,
        text: str,
        labels: list[str],
    ) -> list[Entity]:
        """Extract entities of specific types."""
        entities = self.extract(text)
        return [e for e in entities if e.label in labels]
```

### Batch Processing

```python
def extract_entities_batch(texts: list[str]) -> list[list[Entity]]:
    """Process multiple texts efficiently."""
    nlp = spacy.load('en_core_web_sm')
    results = []
    for doc in nlp.pipe(texts, batch_size=50):
        entities = [
            Entity(ent.text, ent.label_, ent.start_char, ent.end_char)
            for ent in doc.ents
        ]
        results.append(entities)
    return results
```

---

## Language Detection

### langdetect (Simple)

```bash
pip install langdetect
```

```python
from langdetect import detect, detect_langs, DetectorFactory

# Ensure consistent results
DetectorFactory.seed = 0

# Simple detection
lang = detect("This is an English sentence.")  # 'en'

# With probabilities
probs = detect_langs("This is English text.")
# [en:0.999...]
```

### fast-langdetect (Faster, More Accurate)

```bash
pip install fast-langdetect
```

```python
from fast_langdetect import detect

# Returns language code
result = detect("This is English text.")
# {'lang': 'en', 'score': 0.98}
```

**Recommendation:** Use `fast-langdetect` for better accuracy and speed.

### ragd Integration Pattern

```python
class LanguageDetector:
    """Detect document language."""

    def __init__(self, use_fast: bool = True):
        self._use_fast = use_fast
        self._detector = None

    def detect(self, text: str) -> tuple[str, float]:
        """Detect language of text.

        Returns:
            Tuple of (language_code, confidence)
        """
        if self._use_fast:
            try:
                from fast_langdetect import detect
                result = detect(text)
                return result['lang'], result.get('score', 1.0)
            except ImportError:
                pass

        # Fallback to langdetect
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0
        lang = detect(text)
        return lang, 1.0  # langdetect doesn't provide confidence

    def detect_with_fallback(
        self,
        text: str,
        default: str = 'en',
    ) -> str:
        """Detect language with fallback for short/ambiguous text."""
        if len(text.strip()) < 20:
            return default

        try:
            lang, confidence = self.detect(text)
            if confidence < 0.5:
                return default
            return lang
        except Exception:
            return default
```

---

## Combined Metadata Extractor

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ExtractedMetadata:
    """Metadata extracted from document content."""

    # Keywords (KeyBERT)
    keywords: list[tuple[str, float]] = field(default_factory=list)

    # Named entities (spaCy)
    entities: list[Entity] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    organisations: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)

    # Language (langdetect)
    language: str = 'en'
    language_confidence: float = 1.0


class MetadataExtractor:
    """Extract metadata from document content using NLP."""

    def __init__(
        self,
        embedding_model: SentenceTransformer | None = None,
        spacy_model: str = 'en_core_web_sm',
    ):
        self._keyword_extractor = KeywordExtractor(model=embedding_model)
        self._entity_extractor = EntityExtractor(model=spacy_model)
        self._language_detector = LanguageDetector()

    def extract(
        self,
        text: str,
        extract_keywords: bool = True,
        extract_entities: bool = True,
        detect_language: bool = True,
    ) -> ExtractedMetadata:
        """Extract all metadata from text."""
        metadata = ExtractedMetadata()

        if detect_language:
            lang, conf = self._language_detector.detect(text)
            metadata.language = lang
            metadata.language_confidence = conf

        if extract_keywords:
            metadata.keywords = self._keyword_extractor.extract(text)

        if extract_entities:
            entities = self._entity_extractor.extract(text)
            metadata.entities = entities

            # Categorise by type
            metadata.people = [e.text for e in entities if e.label == 'PERSON']
            metadata.organisations = [e.text for e in entities if e.label == 'ORG']
            metadata.locations = [e.text for e in entities if e.label in ('GPE', 'LOC')]
            metadata.dates = [e.text for e in entities if e.label == 'DATE']

        return metadata
```

---

## Memory and Performance

### Memory Usage

| Component | Memory |
|-----------|--------|
| KeyBERT (shared model) | ~0 (reuses embedding model) |
| KeyBERT (standalone) | ~80-420MB |
| spaCy en_core_web_sm | ~13MB |
| spaCy en_core_web_trf | ~400MB |
| langdetect | ~2MB |
| fast-langdetect | ~10MB |

### Performance Tips

1. **Share embedding model** between ragd embedder and KeyBERT
2. **Use batch processing** for spaCy on multiple documents
3. **Lazy load** all models to avoid CLI startup delay
4. **Cache results** for documents already processed

---

## Testing Strategy

### Mocking KeyBERT

```python
@pytest.fixture
def mock_keybert():
    with patch("keybert.KeyBERT") as mock:
        instance = Mock()
        instance.extract_keywords.return_value = [
            ("machine learning", 0.65),
            ("data science", 0.52),
        ]
        mock.return_value = instance
        yield mock
```

### Mocking spaCy

```python
@pytest.fixture
def mock_spacy():
    with patch("spacy.load") as mock:
        nlp = Mock()
        doc = Mock()
        doc.ents = [
            Mock(text="Apple", label_="ORG", start_char=0, end_char=5),
            Mock(text="California", label_="GPE", start_char=20, end_char=30),
        ]
        nlp.return_value = doc
        mock.return_value = nlp
        yield mock
```

### Integration Tests

```python
@pytest.mark.slow
def test_real_keyword_extraction():
    """Integration test with real KeyBERT."""
    from keybert import KeyBERT

    kw_model = KeyBERT(model='all-MiniLM-L6-v2')
    text = "Machine learning and artificial intelligence are transforming technology."

    keywords = kw_model.extract_keywords(text, top_n=5)

    assert len(keywords) == 5
    assert any("learning" in kw[0].lower() for kw in keywords)
```

---

## ragd Dependency Group

```toml
# pyproject.toml
[project.optional-dependencies]
metadata = [
    "keybert>=0.8.0",
    "spacy>=3.7.0",
    "langdetect>=1.0.9",
    # Or: "fast-langdetect>=1.0.0",
]
```

---

## Related Documentation

- [State-of-the-Art NER](./state-of-the-art-ner.md) - Named entity recognition research
- [State-of-the-Art Metadata](./state-of-the-art-metadata.md) - Research context
- [F-030: Metadata Extraction](../features/completed/F-030-metadata-extraction.md) - Feature spec
- [F-029: Metadata Storage](../features/completed/F-029-metadata-storage.md) - Dublin Core schema

---

## Sources

- [KeyBERT GitHub](https://github.com/MaartenGr/KeyBERT)
- [KeyBERT Documentation](https://maartengr.github.io/KeyBERT/)
- [spaCy NER Documentation](https://spacy.io/usage/linguistic-features#named-entities)
- [langdetect PyPI](https://pypi.org/project/langdetect/)
- [fast-langdetect GitHub](https://github.com/LlmKira/fast-langdetect)

---

**Status**: Research complete
