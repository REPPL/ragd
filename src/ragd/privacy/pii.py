"""PII detection for ragd.

This module provides PII (Personally Identifiable Information) detection
using multiple engines:
- Presidio: Microsoft's PII detection framework (primary)
- spaCy: NER-based detection (fallback)
- Regex: Pattern-based detection (always available)

All detection runs locally with no external API calls.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


def is_presidio_available() -> bool:
    """Check if Presidio is available.

    Returns:
        True if presidio-analyzer is installed.
    """
    try:
        import presidio_analyzer  # noqa: F401

        return True
    except ImportError:
        return False


def is_spacy_available() -> bool:
    """Check if spaCy is available with a language model.

    Returns:
        True if spaCy and an English model are available.
    """
    try:
        import spacy

        # Try to load English model
        try:
            spacy.load("en_core_web_sm")
            return True
        except OSError:
            # Model not installed
            return False
    except ImportError:
        return False


class PIIEngine(Enum):
    """PII detection engine types."""

    PRESIDIO = "presidio"
    SPACY = "spacy"
    REGEX = "regex"
    HYBRID = "hybrid"  # Use multiple engines


class PIIEntityType(Enum):
    """Standard PII entity types."""

    # Personal identifiers
    PERSON = "PERSON"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"

    # Financial
    CREDIT_CARD = "CREDIT_CARD"
    IBAN_CODE = "IBAN_CODE"
    BANK_ACCOUNT = "BANK_ACCOUNT"

    # Government IDs
    US_SSN = "US_SSN"
    UK_NINO = "UK_NINO"
    US_PASSPORT = "US_PASSPORT"
    UK_PASSPORT = "UK_PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"

    # Location
    LOCATION = "LOCATION"
    ADDRESS = "ADDRESS"
    IP_ADDRESS = "IP_ADDRESS"

    # Medical
    MEDICAL_RECORD = "MEDICAL_RECORD"
    NHS_NUMBER = "NHS_NUMBER"

    # Other
    DATE = "DATE"
    URL = "URL"
    ORGANIZATION = "ORGANIZATION"
    CUSTOM = "CUSTOM"


@dataclass
class PIIEntity:
    """Detected PII entity.

    Attributes:
        entity_type: Type of PII entity.
        value: The detected PII value.
        start: Start position in text.
        end: End position in text.
        confidence: Detection confidence (0-1).
        engine: Detection engine used.
    """

    entity_type: PIIEntityType | str
    value: str
    start: int
    end: int
    confidence: float
    engine: PIIEngine

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary."""
        return {
            "entity_type": (
                self.entity_type.value
                if isinstance(self.entity_type, PIIEntityType)
                else self.entity_type
            ),
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "engine": self.engine.value,
        }


@dataclass
class PIIResult:
    """Result of PII detection on text.

    Attributes:
        entities: List of detected PII entities.
        text_length: Length of analysed text.
        engine_used: Primary engine used.
    """

    entities: list[PIIEntity] = field(default_factory=list)
    text_length: int = 0
    engine_used: PIIEngine = PIIEngine.REGEX

    @property
    def has_pii(self) -> bool:
        """Check if any PII was detected."""
        return len(self.entities) > 0

    @property
    def entity_count(self) -> int:
        """Count of detected entities."""
        return len(self.entities)

    def by_type(self) -> dict[str, int]:
        """Count entities by type."""
        return dict(
            Counter(
                e.entity_type.value
                if isinstance(e.entity_type, PIIEntityType)
                else e.entity_type
                for e in self.entities
            )
        )

    def high_confidence(self, threshold: float = 0.85) -> list[PIIEntity]:
        """Get high-confidence entities."""
        return [e for e in self.entities if e.confidence >= threshold]

    def low_confidence(self, threshold: float = 0.85) -> list[PIIEntity]:
        """Get low-confidence entities."""
        return [e for e in self.entities if e.confidence < threshold]


@dataclass
class PIIReport:
    """Comprehensive PII report for a document.

    Attributes:
        document_path: Path to analysed document.
        total_pii_found: Total PII entities detected.
        by_type: Count by entity type.
        high_confidence_count: High-confidence detections.
        low_confidence_count: Low-confidence detections.
        results: Detailed results per chunk/section.
        summary: Human-readable summary.
    """

    document_path: str
    total_pii_found: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    high_confidence_count: int = 0
    low_confidence_count: int = 0
    results: list[PIIResult] = field(default_factory=list)
    summary: str = ""

    @classmethod
    def from_results(
        cls,
        document_path: str,
        results: list[PIIResult],
        confidence_threshold: float = 0.85,
    ) -> PIIReport:
        """Create report from detection results.

        Args:
            document_path: Path to document.
            results: List of PIIResult from detection.
            confidence_threshold: Threshold for high confidence.

        Returns:
            PIIReport summarising all results.
        """
        all_entities = [e for r in results for e in r.entities]
        by_type = Counter(
            e.entity_type.value
            if isinstance(e.entity_type, PIIEntityType)
            else e.entity_type
            for e in all_entities
        )

        high = sum(1 for e in all_entities if e.confidence >= confidence_threshold)
        low = len(all_entities) - high

        # Generate summary
        if not all_entities:
            summary = "No PII detected"
        else:
            top_types = by_type.most_common(3)
            type_str = ", ".join(f"{t}: {c}" for t, c in top_types)
            summary = f"Found {len(all_entities)} PII entities ({type_str})"

        return cls(
            document_path=document_path,
            total_pii_found=len(all_entities),
            by_type=dict(by_type),
            high_confidence_count=high,
            low_confidence_count=low,
            results=results,
            summary=summary,
        )


class RegexDetector:
    """Regex-based PII detector.

    Provides reliable detection for structured PII patterns.
    """

    # Common PII patterns
    PATTERNS: dict[PIIEntityType, list[re.Pattern]] = {
        PIIEntityType.EMAIL_ADDRESS: [
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        ],
        PIIEntityType.PHONE_NUMBER: [
            # UK phone numbers (+44 or 0 prefix)
            re.compile(r"(?:\+44|0)\s?(?:\d\s?){9,10}"),
            # US phone numbers (area code + number)
            re.compile(r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"),
            # Generic international (+ prefix)
            re.compile(r"\+\d{1,3}[-.\s]?\d{6,14}"),
        ],
        PIIEntityType.CREDIT_CARD: [
            # Major card patterns
            re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        ],
        PIIEntityType.US_SSN: [
            re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
        ],
        PIIEntityType.UK_NINO: [
            re.compile(
                r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
                re.IGNORECASE,
            ),
        ],
        PIIEntityType.IBAN_CODE: [
            re.compile(r"\b[A-Z]{2}\d{2}[\s]?(?:[A-Z0-9][\s]?){11,30}\b"),
        ],
        PIIEntityType.IP_ADDRESS: [
            # IPv4
            re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            # IPv6 (simplified)
            re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}\b"),
        ],
        PIIEntityType.URL: [
            re.compile(r"\bhttps?://[^\s<>\"{}|\\^`\[\]]+\b"),
        ],
        PIIEntityType.DATE: [
            # DD/MM/YYYY or MM/DD/YYYY
            re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"),
            # YYYY-MM-DD
            re.compile(r"\b\d{4}[-]\d{2}[-]\d{2}\b"),
        ],
    }

    # Patterns that might indicate false positives
    ALLOWLIST_PATTERNS = [
        re.compile(r"\(555\)\s?\d{3}"),  # 555 phone numbers (test numbers)
        re.compile(r"555[-.\s]\d{3}"),  # 555 phone numbers without parens
        re.compile(r"@example\.(com|org|net)$"),  # Example domains (exact match at end)
    ]

    def __init__(
        self,
        enabled_types: list[PIIEntityType] | None = None,
        confidence: float = 0.9,
    ) -> None:
        """Initialise regex detector.

        Args:
            enabled_types: Types to detect (None = all).
            confidence: Confidence score for regex matches.
        """
        self._enabled_types = enabled_types or list(self.PATTERNS.keys())
        self._confidence = confidence

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect PII using regex patterns.

        Args:
            text: Text to analyse.

        Returns:
            List of detected PII entities.
        """
        entities = []

        for entity_type in self._enabled_types:
            patterns = self.PATTERNS.get(entity_type, [])
            for pattern in patterns:
                for match in pattern.finditer(text):
                    value = match.group()

                    # Check allowlist
                    if self._is_allowlisted(value):
                        continue

                    entities.append(
                        PIIEntity(
                            entity_type=entity_type,
                            value=value,
                            start=match.start(),
                            end=match.end(),
                            confidence=self._confidence,
                            engine=PIIEngine.REGEX,
                        )
                    )

        return entities

    def _is_allowlisted(self, value: str) -> bool:
        """Check if value matches allowlist."""
        return any(p.search(value) for p in self.ALLOWLIST_PATTERNS)


class PresidioDetector:
    """Presidio-based PII detector.

    Uses Microsoft Presidio for comprehensive PII detection.
    """

    def __init__(
        self,
        entities: list[str] | None = None,
        confidence_threshold: float = 0.7,
        language: str = "en",
    ) -> None:
        """Initialise Presidio detector.

        Args:
            entities: Entity types to detect.
            confidence_threshold: Minimum confidence score.
            language: Language for analysis.

        Raises:
            ImportError: If Presidio not available.
        """
        if not is_presidio_available():
            raise ImportError(
                "Presidio not available. Install with: pip install presidio-analyzer"
            )

        from presidio_analyzer import AnalyzerEngine

        self._analyzer = AnalyzerEngine()
        self._entities = entities
        self._threshold = confidence_threshold
        self._language = language

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect PII using Presidio.

        Args:
            text: Text to analyse.

        Returns:
            List of detected PII entities.
        """
        results = self._analyzer.analyze(
            text=text,
            entities=self._entities,
            language=self._language,
        )

        entities = []
        for r in results:
            if r.score < self._threshold:
                continue

            # Map Presidio entity type to our enum
            entity_type = self._map_entity_type(r.entity_type)

            entities.append(
                PIIEntity(
                    entity_type=entity_type,
                    value=text[r.start : r.end],
                    start=r.start,
                    end=r.end,
                    confidence=r.score,
                    engine=PIIEngine.PRESIDIO,
                )
            )

        return entities

    def _map_entity_type(self, presidio_type: str) -> PIIEntityType | str:
        """Map Presidio entity type to our enum."""
        mapping = {
            "PERSON": PIIEntityType.PERSON,
            "EMAIL_ADDRESS": PIIEntityType.EMAIL_ADDRESS,
            "PHONE_NUMBER": PIIEntityType.PHONE_NUMBER,
            "CREDIT_CARD": PIIEntityType.CREDIT_CARD,
            "IBAN_CODE": PIIEntityType.IBAN_CODE,
            "US_SSN": PIIEntityType.US_SSN,
            "UK_NINO": PIIEntityType.UK_NINO,
            "IP_ADDRESS": PIIEntityType.IP_ADDRESS,
            "LOCATION": PIIEntityType.LOCATION,
            "DATE_TIME": PIIEntityType.DATE,
            "NRP": PIIEntityType.PERSON,  # Nationality/Religion/Political group
            "ORGANIZATION": PIIEntityType.ORGANIZATION,
            "URL": PIIEntityType.URL,
        }
        return mapping.get(presidio_type, presidio_type)


class SpacyDetector:
    """spaCy NER-based PII detector.

    Uses spaCy's named entity recognition for PII detection.
    """

    def __init__(
        self,
        model: str = "en_core_web_sm",
        confidence: float = 0.8,
    ) -> None:
        """Initialise spaCy detector.

        Args:
            model: spaCy model name.
            confidence: Default confidence for NER entities.

        Raises:
            ImportError: If spaCy not available.
        """
        if not is_spacy_available():
            raise ImportError(
                "spaCy not available. Install with: pip install spacy && "
                "python -m spacy download en_core_web_sm"
            )

        import spacy

        self._nlp = spacy.load(model)
        self._confidence = confidence

    def detect(self, text: str) -> list[PIIEntity]:
        """Detect PII using spaCy NER.

        Args:
            text: Text to analyse.

        Returns:
            List of detected PII entities.
        """
        doc = self._nlp(text)

        entities = []
        for ent in doc.ents:
            entity_type = self._map_entity_type(ent.label_)
            if entity_type is None:
                continue

            entities.append(
                PIIEntity(
                    entity_type=entity_type,
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=self._confidence,
                    engine=PIIEngine.SPACY,
                )
            )

        return entities

    def _map_entity_type(self, spacy_label: str) -> PIIEntityType | None:
        """Map spaCy entity label to our enum."""
        mapping = {
            "PERSON": PIIEntityType.PERSON,
            "GPE": PIIEntityType.LOCATION,  # Geo-political entity
            "LOC": PIIEntityType.LOCATION,
            "ORG": PIIEntityType.ORGANIZATION,
            "DATE": PIIEntityType.DATE,
            "TIME": PIIEntityType.DATE,
        }
        return mapping.get(spacy_label)


class PIIDetector:
    """Main PII detection interface.

    Orchestrates multiple detection engines for comprehensive coverage.

    Usage:
        detector = PIIDetector()
        result = detector.detect("Contact John at john@example.com")

        if result.has_pii:
            print(f"Found {result.entity_count} PII entities")
            for entity in result.entities:
                print(f"  {entity.entity_type}: {entity.value}")
    """

    def __init__(
        self,
        engine: PIIEngine = PIIEngine.HYBRID,
        confidence_threshold: float = 0.7,
        entities: list[PIIEntityType | str] | None = None,
    ) -> None:
        """Initialise PII detector.

        Args:
            engine: Detection engine to use.
            confidence_threshold: Minimum confidence score.
            entities: Specific entity types to detect.
        """
        self._engine = engine
        self._threshold = confidence_threshold
        self._entities = entities

        # Initialise detectors based on engine selection
        self._regex_detector = RegexDetector(
            enabled_types=[
                e for e in (entities or [])
                if isinstance(e, PIIEntityType)
            ] or None,
            confidence=0.9,
        )

        self._presidio_detector: PresidioDetector | None = None
        self._spacy_detector: SpacyDetector | None = None

        if engine in (PIIEngine.PRESIDIO, PIIEngine.HYBRID):
            try:
                entity_strs = (
                    [
                        e.value if isinstance(e, PIIEntityType) else e
                        for e in (entities or [])
                    ]
                    or None
                )
                self._presidio_detector = PresidioDetector(
                    entities=entity_strs,
                    confidence_threshold=confidence_threshold,
                )
            except ImportError:
                logger.warning("Presidio not available, falling back to regex")

        if engine in (PIIEngine.SPACY, PIIEngine.HYBRID):
            try:
                self._spacy_detector = SpacyDetector(
                    confidence=confidence_threshold,
                )
            except ImportError:
                logger.warning("spaCy not available, falling back to regex")

    @property
    def available_engines(self) -> list[PIIEngine]:
        """Get list of available engines."""
        engines = [PIIEngine.REGEX]  # Always available
        if self._presidio_detector:
            engines.append(PIIEngine.PRESIDIO)
        if self._spacy_detector:
            engines.append(PIIEngine.SPACY)
        return engines

    def detect(self, text: str) -> PIIResult:
        """Detect PII in text.

        Args:
            text: Text to analyse.

        Returns:
            PIIResult with detected entities.
        """
        all_entities: list[PIIEntity] = []
        engine_used = PIIEngine.REGEX

        # Presidio detection (primary for PRESIDIO/HYBRID)
        if self._presidio_detector and self._engine in (
            PIIEngine.PRESIDIO,
            PIIEngine.HYBRID,
        ):
            entities = self._presidio_detector.detect(text)
            all_entities.extend(entities)
            engine_used = PIIEngine.PRESIDIO

        # spaCy detection (primary for SPACY, fallback for HYBRID)
        if self._spacy_detector and self._engine in (
            PIIEngine.SPACY,
            PIIEngine.HYBRID,
        ):
            entities = self._spacy_detector.detect(text)
            all_entities.extend(entities)
            if self._engine == PIIEngine.SPACY:
                engine_used = PIIEngine.SPACY

        # Regex detection (always for REGEX, fallback for others)
        if self._engine == PIIEngine.REGEX or (
            self._engine == PIIEngine.HYBRID
            and not self._presidio_detector
            and not self._spacy_detector
        ):
            entities = self._regex_detector.detect(text)
            all_entities.extend(entities)
            engine_used = PIIEngine.REGEX

        # Deduplicate overlapping entities
        unique_entities = self._deduplicate_entities(all_entities)

        return PIIResult(
            entities=unique_entities,
            text_length=len(text),
            engine_used=engine_used if self._engine != PIIEngine.HYBRID else PIIEngine.HYBRID,
        )

    def _deduplicate_entities(
        self, entities: list[PIIEntity]
    ) -> list[PIIEntity]:
        """Remove duplicate/overlapping entities.

        Keeps the entity with higher confidence when overlapping.

        Args:
            entities: List of potentially overlapping entities.

        Returns:
            Deduplicated list.
        """
        if not entities:
            return []

        # Sort by start position, then by confidence (descending)
        sorted_entities = sorted(
            entities, key=lambda e: (e.start, -e.confidence)
        )

        result = []
        last_end = -1

        for entity in sorted_entities:
            # Skip if overlapping with previous
            if entity.start < last_end:
                continue
            result.append(entity)
            last_end = entity.end

        return result

    def generate_report(
        self,
        document_path: str,
        texts: list[str],
    ) -> PIIReport:
        """Generate PII report for document.

        Args:
            document_path: Path to document.
            texts: Text chunks to analyse.

        Returns:
            Comprehensive PIIReport.
        """
        results = [self.detect(text) for text in texts]
        return PIIReport.from_results(
            document_path=document_path,
            results=results,
            confidence_threshold=self._threshold,
        )


def redact_pii(
    text: str,
    entities: list[PIIEntity],
    redaction_char: str = "█",
) -> str:
    """Redact PII from text.

    Replaces detected PII with redaction characters.

    Args:
        text: Original text.
        entities: Detected PII entities.
        redaction_char: Character to use for redaction.

    Returns:
        Text with PII redacted.
    """
    if not entities:
        return text

    # Sort in reverse order to preserve positions
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

    redacted = text
    for entity in sorted_entities:
        replacement = redaction_char * len(entity.value)
        redacted = redacted[: entity.start] + replacement + redacted[entity.end :]

    return redacted
