"""Metadata extraction orchestrator.

This module provides the main MetadataExtractor class that coordinates
extraction of metadata from documents using various optional backends:
- PDF properties via PyMuPDF
- Language detection via langdetect
- Keywords via KeyBERT (optional)
- Named entities via spaCy (optional)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

from ragd.features import (
    KEYBERT_AVAILABLE,
    LANGDETECT_AVAILABLE,
    SPACY_AVAILABLE,
    get_detector,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedKeyword:
    """A keyword extracted from document text."""

    keyword: str
    score: float  # 0.0-1.0, relevance score
    source: str = "keybert"  # Extraction method

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.keyword} ({self.score:.2f})"


@dataclass
class ExtractedEntity:
    """A named entity extracted from document text."""

    text: str
    label: str  # PERSON, ORG, GPE, DATE, etc.
    start_char: int
    end_char: int
    confidence: float = 1.0

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.text} [{self.label}]"


@dataclass
class ExtractedMetadata:
    """All metadata extracted from a document.

    Combines metadata from multiple sources:
    - PDF native metadata (title, author, dates)
    - NLP extraction (keywords, entities, language)
    """

    # From PDF metadata
    pdf_title: str | None = None
    pdf_author: str | None = None
    pdf_subject: str | None = None
    pdf_creation_date: datetime | None = None
    pdf_modification_date: datetime | None = None

    # From NLP extraction
    keywords: list[ExtractedKeyword] = field(default_factory=list)
    entities: list[ExtractedEntity] = field(default_factory=list)
    detected_language: str = "en"
    language_confidence: float = 0.0

    # Extraction metadata
    extraction_time_ms: int = 0
    sources_used: list[str] = field(default_factory=list)

    @property
    def has_pdf_metadata(self) -> bool:
        """Check if PDF metadata was extracted."""
        return bool(self.pdf_title or self.pdf_author)

    @property
    def has_nlp_metadata(self) -> bool:
        """Check if NLP extraction was performed."""
        return bool(self.keywords or self.entities)

    def __str__(self) -> str:
        """Human-readable summary."""
        parts = []
        if self.pdf_title:
            parts.append(f"Title: {self.pdf_title}")
        if self.keywords:
            parts.append(f"Keywords: {len(self.keywords)}")
        if self.entities:
            parts.append(f"Entities: {len(self.entities)}")
        parts.append(f"Language: {self.detected_language}")
        return " | ".join(parts) if parts else "(No metadata)"


class MetadataExtractor:
    """Orchestrates metadata extraction from documents.

    Combines multiple extraction methods:
    - PDF properties (always available via PyMuPDF)
    - Language detection (requires langdetect)
    - Keyword extraction (requires KeyBERT)
    - Entity extraction (requires spaCy)

    The extractor gracefully degrades when optional dependencies are
    not available, extracting what it can with available tools.

    Example:
        >>> extractor = MetadataExtractor()
        >>> metadata = extractor.extract(text, pdf_path=Path("doc.pdf"))
        >>> print(metadata.keywords)
        >>> print(metadata.detected_language)
    """

    def __init__(
        self,
        *,
        enable_keywords: bool = True,
        enable_entities: bool = True,
        enable_language: bool = True,
        keyword_model: str = "all-MiniLM-L6-v2",
        spacy_model: str = "en_core_web_sm",
    ) -> None:
        """Initialise the metadata extractor.

        Args:
            enable_keywords: Enable keyword extraction (requires KeyBERT)
            enable_entities: Enable entity extraction (requires spaCy)
            enable_language: Enable language detection (requires langdetect)
            keyword_model: KeyBERT model to use
            spacy_model: spaCy model to use
        """
        self._enable_keywords = enable_keywords and KEYBERT_AVAILABLE
        self._enable_entities = enable_entities and SPACY_AVAILABLE
        self._enable_language = enable_language and LANGDETECT_AVAILABLE

        self._keyword_model = keyword_model
        self._spacy_model = spacy_model

        # Lazy-loaded models
        self._keybert: Any = None
        self._nlp: Any = None

        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def extract(
        self,
        text: str,
        pdf_path: Path | None = None,
        *,
        top_keywords: int = 10,
        keyword_diversity: float = 0.5,
        entity_types: list[str] | None = None,
    ) -> ExtractedMetadata:
        """Extract metadata from text and optionally PDF file.

        Args:
            text: Document text content
            pdf_path: Optional path to PDF for native metadata
            top_keywords: Number of keywords to extract
            keyword_diversity: Diversity of keywords (0-1, higher = more diverse)
            entity_types: Entity types to extract (None = all)

        Returns:
            ExtractedMetadata with all extracted information
        """
        import time

        start_time = time.perf_counter()
        sources_used: list[str] = []

        result = ExtractedMetadata()

        # Extract PDF metadata
        if pdf_path and pdf_path.exists():
            pdf_meta = self._extract_pdf_metadata(pdf_path)
            result.pdf_title = pdf_meta.get("title")
            result.pdf_author = pdf_meta.get("author")
            result.pdf_subject = pdf_meta.get("subject")
            result.pdf_creation_date = pdf_meta.get("creation_date")
            result.pdf_modification_date = pdf_meta.get("modification_date")
            if pdf_meta:
                sources_used.append("pdf_metadata")

        # Detect language
        if self._enable_language and text.strip():
            lang, confidence = self.detect_language(text)
            result.detected_language = lang
            result.language_confidence = confidence
            sources_used.append("langdetect")

        # Extract keywords
        if self._enable_keywords and text.strip():
            result.keywords = self.extract_keywords(
                text,
                top_n=top_keywords,
                diversity=keyword_diversity,
            )
            if result.keywords:
                sources_used.append("keybert")

        # Extract entities
        if self._enable_entities and text.strip():
            result.entities = self.extract_entities(text, entity_types=entity_types)
            if result.entities:
                sources_used.append("spacy")

        result.extraction_time_ms = int((time.perf_counter() - start_time) * 1000)
        result.sources_used = sources_used

        return result

    def extract_keywords(
        self,
        text: str,
        top_n: int = 10,
        diversity: float = 0.5,
    ) -> list[ExtractedKeyword]:
        """Extract keywords using KeyBERT.

        Uses Maximal Marginal Relevance (MMR) for diverse keywords.

        Args:
            text: Document text
            top_n: Number of keywords to extract
            diversity: Diversity parameter (0-1)

        Returns:
            List of ExtractedKeyword objects
        """
        if not self._enable_keywords:
            return []

        try:
            keybert = self._get_keybert()
            keywords = keybert.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words="english",
                top_n=top_n,
                use_mmr=True,
                diversity=diversity,
            )

            return [
                ExtractedKeyword(keyword=kw, score=score, source="keybert")
                for kw, score in keywords
            ]
        except Exception as e:
            self._logger.warning("Keyword extraction failed: %s", e)
            return []

    def extract_entities(
        self,
        text: str,
        entity_types: list[str] | None = None,
    ) -> list[ExtractedEntity]:
        """Extract named entities using spaCy.

        Args:
            text: Document text
            entity_types: Entity types to extract (None = all)
                Common types: PERSON, ORG, GPE, DATE, MONEY, EVENT

        Returns:
            List of ExtractedEntity objects
        """
        if not self._enable_entities:
            return []

        try:
            nlp = self._get_spacy()

            # Limit text length for performance
            max_length = 100000  # spaCy default
            doc = nlp(text[:max_length])

            entities = []
            for ent in doc.ents:
                if entity_types is None or ent.label_ in entity_types:
                    entities.append(
                        ExtractedEntity(
                            text=ent.text,
                            label=ent.label_,
                            start_char=ent.start_char,
                            end_char=ent.end_char,
                            confidence=1.0,  # spaCy doesn't provide confidence
                        )
                    )

            return entities
        except Exception as e:
            self._logger.warning("Entity extraction failed: %s", e)
            return []

    def detect_language(self, text: str) -> tuple[str, float]:
        """Detect language of text.

        Args:
            text: Text to analyse

        Returns:
            Tuple of (language_code, confidence)
        """
        if not self._enable_language:
            return "en", 0.0

        try:
            from langdetect import detect_langs

            # Use a sample of text for efficiency
            sample = text[:5000]
            results = detect_langs(sample)

            if results:
                top = results[0]
                return top.lang, top.prob

            return "en", 0.0
        except Exception as e:
            self._logger.warning("Language detection failed: %s", e)
            return "en", 0.0

    def _extract_pdf_metadata(self, pdf_path: Path) -> dict[str, Any]:
        """Extract metadata from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary of extracted metadata
        """
        try:
            doc = fitz.open(pdf_path)
            try:
                meta = doc.metadata or {}
                result: dict[str, Any] = {}

                if meta.get("title"):
                    result["title"] = meta["title"]
                if meta.get("author"):
                    result["author"] = meta["author"]
                if meta.get("subject"):
                    result["subject"] = meta["subject"]

                # Parse dates
                if meta.get("creationDate"):
                    result["creation_date"] = self._parse_pdf_date(meta["creationDate"])
                if meta.get("modDate"):
                    result["modification_date"] = self._parse_pdf_date(meta["modDate"])

                return result
            finally:
                doc.close()
        except Exception as e:
            self._logger.warning("PDF metadata extraction failed: %s", e)
            return {}

    def _parse_pdf_date(self, date_str: str) -> datetime | None:
        """Parse PDF date string to datetime.

        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'

        Args:
            date_str: PDF date string

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # Remove D: prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]

            # Extract basic components (YYYYMMDD)
            if len(date_str) >= 8:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])

                hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
                minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
                second = int(date_str[12:14]) if len(date_str) >= 14 else 0

                return datetime(year, month, day, hour, minute, second)

            return None
        except (ValueError, IndexError):
            return None

    def _get_keybert(self) -> Any:
        """Get or initialise KeyBERT model."""
        if self._keybert is None:
            self._logger.info("Loading KeyBERT model: %s", self._keyword_model)
            from keybert import KeyBERT

            self._keybert = KeyBERT(model=self._keyword_model)
        return self._keybert

    def _get_spacy(self) -> Any:
        """Get or initialise spaCy model."""
        if self._nlp is None:
            self._logger.info("Loading spaCy model: %s", self._spacy_model)
            import spacy

            self._nlp = spacy.load(self._spacy_model)
        return self._nlp

    def get_capabilities(self) -> dict[str, bool]:
        """Get current extraction capabilities.

        Returns:
            Dictionary of capability name to availability
        """
        detector = get_detector()
        return {
            "pdf_metadata": True,  # Always available via PyMuPDF
            "language_detection": detector.langdetect.available,
            "keyword_extraction": detector.keybert.available,
            "entity_extraction": detector.spacy_model.available,
        }
