"""Entity extraction for knowledge graph construction.

Provides multiple extraction strategies:
- Pattern-based: Fast, no external dependencies
- spaCy-based: Higher quality, requires spacy model
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities that can be extracted."""

    PERSON = "PERSON"
    ORGANISATION = "ORG"
    LOCATION = "LOC"
    TECHNOLOGY = "TECH"
    CONCEPT = "CONCEPT"
    PRODUCT = "PRODUCT"
    DATE = "DATE"
    OTHER = "OTHER"


@dataclass
class Entity:
    """An extracted entity from text.

    Attributes:
        name: The entity text/name
        type: Entity classification
        start: Start character offset in source text
        end: End character offset in source text
        confidence: Extraction confidence (0-1)
        source_text: Original text context (optional)
    """

    name: str
    type: EntityType
    start: int = 0
    end: int = 0
    confidence: float = 1.0
    source_text: str = ""

    def __post_init__(self):
        """Normalise entity name."""
        self.name = self.name.strip()

    @property
    def normalised_name(self) -> str:
        """Return normalised version of name for comparison."""
        return self.name.lower().replace("-", " ").replace("_", " ")

    def to_dict(self) -> dict:
        """Serialise to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Entity:
        """Deserialise from dictionary."""
        return cls(
            name=data["name"],
            type=EntityType(data["type"]),
            start=data.get("start", 0),
            end=data.get("end", 0),
            confidence=data.get("confidence", 1.0),
        )


class EntityExtractor(Protocol):
    """Protocol for entity extractors."""

    def extract(self, text: str) -> list[Entity]:
        """Extract entities from text."""
        ...

    @property
    def available(self) -> bool:
        """Check if extractor is ready."""
        ...


class PatternEntityExtractor:
    """Pattern-based entity extractor using regex.

    Fast and dependency-free, but lower quality than ML-based extractors.
    """

    # Technology patterns
    TECH_PATTERNS = [
        r"\b(Python|JavaScript|TypeScript|Rust|Go|Java|C\+\+|Ruby|PHP)\b",
        r"\b(React|Angular|Vue|Django|Flask|FastAPI|Express|Rails)\b",
        r"\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|SQLite)\b",
        r"\b(Docker|Kubernetes|AWS|Azure|GCP|Terraform)\b",
        r"\b(GraphQL|REST|gRPC|WebSocket|HTTP|HTTPS)\b",
        r"\b(JWT|OAuth|SAML|SSO|LDAP|Kerberos)\b",
        r"\b(Git|GitHub|GitLab|Bitbucket)\b",
        r"\b(Linux|macOS|Windows|Ubuntu|Debian)\b",
        r"\b(TensorFlow|PyTorch|Keras|scikit-learn|spaCy)\b",
        r"\b(LLM|GPT|BERT|Transformer|RAG|NLP)\b",
    ]

    # Concept patterns
    CONCEPT_PATTERNS = [
        r"\b(machine learning|deep learning|neural network)\b",
        r"\b(authentication|authorisation|encryption)\b",
        r"\b(microservice|monolith|serverless)\b",
        r"\b(CI/CD|DevOps|SRE)\b",
        r"\b(API|SDK|CLI|GUI)\b",
    ]

    # Organisation patterns (common tech companies)
    ORG_PATTERNS = [
        r"\b(Google|Microsoft|Amazon|Apple|Meta|Facebook)\b",
        r"\b(OpenAI|Anthropic|DeepMind|Hugging Face)\b",
        r"\b(Netflix|Spotify|Uber|Airbnb|Stripe)\b",
    ]

    def __init__(self, min_confidence: float = 0.7) -> None:
        """Initialise extractor.

        Args:
            min_confidence: Minimum confidence threshold
        """
        self.min_confidence = min_confidence

        # Compile patterns
        self._tech_regex = re.compile(
            "|".join(self.TECH_PATTERNS),
            re.IGNORECASE,
        )
        self._concept_regex = re.compile(
            "|".join(self.CONCEPT_PATTERNS),
            re.IGNORECASE,
        )
        self._org_regex = re.compile(
            "|".join(self.ORG_PATTERNS),
            re.IGNORECASE,
        )

    @property
    def available(self) -> bool:
        """Always available (no external dependencies)."""
        return True

    def extract(self, text: str) -> list[Entity]:
        """Extract entities using pattern matching.

        Args:
            text: Text to extract entities from

        Returns:
            List of extracted entities
        """
        entities = []
        seen = set()  # Avoid duplicates

        # Extract technologies
        for match in self._tech_regex.finditer(text):
            name = match.group(0)
            key = name.lower()
            if key not in seen:
                seen.add(key)
                entities.append(
                    Entity(
                        name=name,
                        type=EntityType.TECHNOLOGY,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,
                    )
                )

        # Extract concepts
        for match in self._concept_regex.finditer(text):
            name = match.group(0)
            key = name.lower()
            if key not in seen:
                seen.add(key)
                entities.append(
                    Entity(
                        name=name,
                        type=EntityType.CONCEPT,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8,
                    )
                )

        # Extract organisations
        for match in self._org_regex.finditer(text):
            name = match.group(0)
            key = name.lower()
            if key not in seen:
                seen.add(key)
                entities.append(
                    Entity(
                        name=name,
                        type=EntityType.ORGANISATION,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9,
                    )
                )

        # Sort by position
        entities.sort(key=lambda e: e.start)

        return entities


class SpacyEntityExtractor:
    """spaCy-based entity extractor.

    Higher quality extraction using ML models.
    Requires spacy and a language model to be installed.
    """

    # Map spaCy labels to our EntityType
    LABEL_MAP = {
        "PERSON": EntityType.PERSON,
        "ORG": EntityType.ORGANISATION,
        "GPE": EntityType.LOCATION,
        "LOC": EntityType.LOCATION,
        "PRODUCT": EntityType.PRODUCT,
        "DATE": EntityType.DATE,
        "TIME": EntityType.DATE,
    }

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        min_confidence: float = 0.7,
    ) -> None:
        """Initialise extractor.

        Args:
            model_name: spaCy model name
            min_confidence: Minimum confidence threshold
        """
        self.model_name = model_name
        self.min_confidence = min_confidence
        self._nlp = None
        self._loaded = False
        self._available = None

    def _load_model(self) -> None:
        """Lazy-load spaCy model."""
        if self._loaded:
            return

        try:
            import spacy

            self._nlp = spacy.load(self.model_name)
            self._available = True
            logger.info("Loaded spaCy model: %s", self.model_name)
        except ImportError:
            logger.warning("spaCy not installed, extractor unavailable")
            self._available = False
        except OSError:
            logger.warning(
                "spaCy model '%s' not found, extractor unavailable",
                self.model_name,
            )
            self._available = False

        self._loaded = True

    @property
    def available(self) -> bool:
        """Check if spaCy model is available."""
        if self._available is None:
            self._load_model()
        return self._available or False

    def extract(self, text: str) -> list[Entity]:
        """Extract entities using spaCy NER.

        Args:
            text: Text to extract entities from

        Returns:
            List of extracted entities
        """
        self._load_model()

        if self._nlp is None:
            return []

        doc = self._nlp(text)
        entities = []
        seen = set()

        for ent in doc.ents:
            key = ent.text.lower()
            if key in seen:
                continue
            seen.add(key)

            entity_type = self.LABEL_MAP.get(ent.label_, EntityType.OTHER)

            entities.append(
                Entity(
                    name=ent.text,
                    type=entity_type,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85,  # spaCy doesn't provide confidence
                )
            )

        return entities


def get_entity_extractor(
    prefer_spacy: bool = True,
    spacy_model: str = "en_core_web_sm",
) -> EntityExtractor:
    """Get the best available entity extractor.

    Args:
        prefer_spacy: Try spaCy first if available
        spacy_model: spaCy model name if using spaCy

    Returns:
        EntityExtractor instance
    """
    if prefer_spacy:
        spacy_extractor = SpacyEntityExtractor(model_name=spacy_model)
        if spacy_extractor.available:
            return spacy_extractor
        logger.info("spaCy unavailable, falling back to pattern extractor")

    return PatternEntityExtractor()
