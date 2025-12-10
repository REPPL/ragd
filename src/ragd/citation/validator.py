"""Citation validation engine for ragd.

Validates that LLM-generated citations actually match the source content,
detecting potential hallucinations where claims are attributed to documents
that don't contain supporting information.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragd.citation import Citation
    from ragd.citation.extractor import ExtractedCitation

logger = logging.getLogger(__name__)


class ValidationResult(str, Enum):
    """Result of validating a citation."""

    VALID = "valid"  # Content clearly supports the claim
    WEAK = "weak"  # Low confidence match - may or may not support
    INVALID = "invalid"  # No supporting content found
    OUT_OF_RANGE = "out_of_range"  # Citation index doesn't exist


class ValidationMode(str, Enum):
    """How to handle validation results."""

    WARN = "warn"  # Keep all citations, add confidence scores
    FILTER = "filter"  # Remove invalid citations from the list
    STRICT = "strict"  # Flag response as potentially hallucinated


@dataclass
class CitationValidation:
    """Validation result for a single citation usage."""

    citation_index: int
    result: ValidationResult
    confidence: float  # 0.0-1.0 confidence score
    claim_text: str
    source_preview: str | None
    keyword_overlap: float
    semantic_similarity: float | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report for a response."""

    validations: list[CitationValidation]
    unused_citations: list[int]  # Citation indices not referenced in response
    overall_confidence: float

    @property
    def valid_count(self) -> int:
        """Count of citations validated as VALID."""
        return sum(1 for v in self.validations if v.result == ValidationResult.VALID)

    @property
    def weak_count(self) -> int:
        """Count of citations validated as WEAK."""
        return sum(1 for v in self.validations if v.result == ValidationResult.WEAK)

    @property
    def invalid_count(self) -> int:
        """Count of citations validated as INVALID."""
        return sum(
            1
            for v in self.validations
            if v.result in (ValidationResult.INVALID, ValidationResult.OUT_OF_RANGE)
        )

    @property
    def has_hallucinations(self) -> bool:
        """Check if any citations appear to be hallucinated."""
        return self.invalid_count > 0


# Common English stopwords to exclude from keyword matching
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "then",
        "once",
        "and",
        "but",
        "or",
        "nor",
        "so",
        "yet",
        "both",
        "either",
        "neither",
        "not",
        "only",
        "own",
        "same",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "such",
        "can",
        "about",
    }
)


class CitationValidator:
    """Validates citation accuracy in LLM responses.

    Uses a tiered validation approach:
    1. Keyword overlap (fast) - checks for content word matches
    2. Semantic similarity (if enabled) - embedding-based matching

    Example:
        validator = CitationValidator()
        report = validator.validate(response_text, citations, extracted_markers)
        if report.has_hallucinations:
            logger.warning("Potential hallucination detected")
    """

    # Thresholds for classification
    KEYWORD_VALID_THRESHOLD = 0.3  # Min keyword overlap for VALID
    KEYWORD_WEAK_THRESHOLD = 0.15  # Min keyword overlap for WEAK
    SEMANTIC_VALID_THRESHOLD = 0.7  # Min semantic similarity for VALID
    SEMANTIC_WEAK_THRESHOLD = 0.5  # Min semantic similarity for WEAK

    def __init__(
        self,
        mode: ValidationMode = ValidationMode.WARN,
        use_semantic: bool = False,  # Disabled by default for performance
        embedder: Any | None = None,
    ):
        """Initialise the validator.

        Args:
            mode: How to handle validation results
            use_semantic: Whether to use embedding-based similarity
            embedder: Optional embedder instance (lazy-loaded if not provided)
        """
        self.mode = mode
        self.use_semantic = use_semantic
        self._embedder = embedder

    def validate(
        self,
        response_text: str,
        citations: list["Citation"],
        extracted: list["ExtractedCitation"],
    ) -> ValidationReport:
        """Validate all citations in a response.

        Args:
            response_text: LLM-generated response text
            citations: List of available citations (1-indexed in response)
            extracted: Extracted citation markers from response

        Returns:
            ValidationReport with results for each citation usage
        """
        validations = []
        used_indices: set[int] = set()

        for ext in extracted:
            for idx in ext.citation_indices:
                used_indices.add(idx)

                # Validate this citation usage
                validation = self._validate_citation(
                    idx, ext.claim_text, citations
                )
                validations.append(validation)

        # Find unused citations (provided but never referenced)
        all_indices = set(range(1, len(citations) + 1))
        unused = sorted(all_indices - used_indices)

        # Calculate overall confidence
        if validations:
            overall = sum(v.confidence for v in validations) / len(validations)
        else:
            overall = 1.0  # No citations = nothing to validate

        return ValidationReport(
            validations=validations,
            unused_citations=unused,
            overall_confidence=overall,
        )

    def _validate_citation(
        self,
        index: int,
        claim: str,
        citations: list["Citation"],
    ) -> CitationValidation:
        """Validate a single citation usage.

        Args:
            index: 1-based citation index
            claim: The claim text being attributed to this citation
            citations: List of available citations

        Returns:
            CitationValidation with result and confidence
        """
        # Check if citation index is valid
        if index < 1 or index > len(citations):
            return CitationValidation(
                citation_index=index,
                result=ValidationResult.OUT_OF_RANGE,
                confidence=0.0,
                claim_text=claim,
                source_preview=None,
                keyword_overlap=0.0,
                details={"error": f"Citation [{index}] out of range (1-{len(citations)})"},
            )

        citation = citations[index - 1]
        source_text = citation.content_preview or ""

        # Tier 1: Keyword overlap (always performed)
        keyword_score = self._compute_keyword_overlap(claim, source_text)

        # Short-circuit if keyword match is strong
        if keyword_score >= self.KEYWORD_VALID_THRESHOLD:
            return CitationValidation(
                citation_index=index,
                result=ValidationResult.VALID,
                confidence=min(1.0, keyword_score + 0.3),
                claim_text=claim,
                source_preview=source_text[:100] if source_text else None,
                keyword_overlap=keyword_score,
            )

        # Tier 2: Semantic similarity (if enabled)
        semantic_score = None
        if self.use_semantic and source_text:
            semantic_score = self._compute_semantic_similarity(claim, source_text)

            if semantic_score is not None:
                if semantic_score >= self.SEMANTIC_VALID_THRESHOLD:
                    return CitationValidation(
                        citation_index=index,
                        result=ValidationResult.VALID,
                        confidence=semantic_score,
                        claim_text=claim,
                        source_preview=source_text[:100] if source_text else None,
                        keyword_overlap=keyword_score,
                        semantic_similarity=semantic_score,
                    )
                elif semantic_score >= self.SEMANTIC_WEAK_THRESHOLD:
                    return CitationValidation(
                        citation_index=index,
                        result=ValidationResult.WEAK,
                        confidence=semantic_score * 0.8,
                        claim_text=claim,
                        source_preview=source_text[:100] if source_text else None,
                        keyword_overlap=keyword_score,
                        semantic_similarity=semantic_score,
                    )

        # Check for weak keyword match
        if keyword_score >= self.KEYWORD_WEAK_THRESHOLD:
            return CitationValidation(
                citation_index=index,
                result=ValidationResult.WEAK,
                confidence=keyword_score + 0.2,
                claim_text=claim,
                source_preview=source_text[:100] if source_text else None,
                keyword_overlap=keyword_score,
                semantic_similarity=semantic_score,
            )

        # Invalid: No supporting evidence found
        return CitationValidation(
            citation_index=index,
            result=ValidationResult.INVALID,
            confidence=max(keyword_score, semantic_score or 0.0) * 0.3,
            claim_text=claim,
            source_preview=source_text[:100] if source_text else None,
            keyword_overlap=keyword_score,
            semantic_similarity=semantic_score,
            details={"reason": "No keyword or semantic match found"},
        )

    def _compute_keyword_overlap(self, claim: str, source: str) -> float:
        """Compute keyword overlap ratio between claim and source.

        Args:
            claim: The claim text
            source: The source document content

        Returns:
            Overlap ratio (0.0-1.0)
        """
        # Tokenise and normalise
        claim_words = self._tokenise(claim)
        source_words = self._tokenise(source)

        if not claim_words:
            return 0.0

        # Calculate overlap
        overlap = claim_words & source_words
        return len(overlap) / len(claim_words)

    def _tokenise(self, text: str) -> set[str]:
        """Tokenise text into content words (excluding stopwords).

        Args:
            text: Text to tokenise

        Returns:
            Set of normalised content words
        """
        # Extract words (alphanumeric only)
        words = set(re.findall(r"\b[a-z]+\b", text.lower()))
        # Remove stopwords and very short words
        return {w for w in words if w not in _STOPWORDS and len(w) > 2}

    def _compute_semantic_similarity(self, claim: str, source: str) -> float | None:
        """Compute semantic similarity using embeddings.

        Args:
            claim: The claim text
            source: The source document content

        Returns:
            Cosine similarity (0.0-1.0) or None if unavailable
        """
        if self._embedder is None:
            try:
                from ragd.embedding import get_embedder

                self._embedder = get_embedder()
            except Exception as e:
                logger.debug("Failed to load embedder: %s", e)
                return None

        try:
            embeddings = self._embedder.embed([claim, source])
            if len(embeddings) < 2:
                return None

            claim_emb = embeddings[0]
            source_emb = embeddings[1]

            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(claim_emb, source_emb))
            norm_claim = sum(a * a for a in claim_emb) ** 0.5
            norm_source = sum(b * b for b in source_emb) ** 0.5

            if norm_claim == 0 or norm_source == 0:
                return 0.0

            return dot_product / (norm_claim * norm_source)
        except Exception as e:
            logger.debug("Semantic similarity failed: %s", e)
            return None


def validate_citations(
    response_text: str,
    citations: list["Citation"],
    mode: ValidationMode = ValidationMode.WARN,
    use_semantic: bool = False,
) -> ValidationReport:
    """Convenience function to validate citations in a response.

    Args:
        response_text: LLM-generated response text
        citations: List of available citations
        mode: How to handle validation results
        use_semantic: Whether to use embedding-based similarity

    Returns:
        ValidationReport with results
    """
    from ragd.citation.extractor import extract_citation_markers

    extracted = extract_citation_markers(response_text)
    validator = CitationValidator(mode=mode, use_semantic=use_semantic)
    return validator.validate(response_text, citations, extracted)
