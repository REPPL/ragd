"""Document reference resolution for chat queries.

Resolves partial document references (e.g., "the hummel paper", "2021 paper")
to exact filenames using citation metadata from the current conversation.

This enables deterministic matching before LLM-based query rewriting,
solving the problem where smaller LLMs fail to match author names to
long academic filenames.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragd.citation import Citation

logger = logging.getLogger(__name__)


@dataclass
class ResolvedReference:
    """A resolved document reference.

    Attributes:
        original_text: The matched text from the query (e.g., "hummel paper")
        matched_filename: The resolved filename
        confidence: Match confidence (0.0-1.0)
        match_type: How the match was made (author, year, combined, filename)
    """

    original_text: str
    matched_filename: str
    confidence: float
    match_type: str


class DocumentReferenceResolver:
    """Resolves partial document references to exact filenames.

    Uses citation metadata (author_hint, year) to match user references
    like "the hummel paper" or "the 2021 paper" to documents that were
    cited in the current conversation.

    Example:
        resolver = DocumentReferenceResolver(recent_citations)
        resolutions = resolver.resolve("summarise the hummel paper")
        # Returns: [ResolvedReference(original_text="hummel paper",
        #           matched_filename="hummel-et-al-2021-data-sovereignty.pdf", ...)]
    """

    # Reference patterns to match in queries
    # Pattern: <author/year> + optional "paper"/"document"/"article"
    REFERENCE_PATTERNS = [
        # "the hummel paper", "hummel's paper", "the hummel 2021 paper"
        r"\b(?:the\s+)?(\w+)(?:'s)?\s+(?:(\d{4})\s+)?(?:paper|document|article|study)\b",
        # "the 2021 paper", "2021 study"
        r"\b(?:the\s+)?(\d{4})\s+(?:paper|document|article|study)\b",
        # "hummel et al", "hummel et al."
        r"\b(\w+)\s+et\s+al\.?\b",
        # "by hummel", "from hummel"
        r"\b(?:by|from)\s+(\w+)\b",
    ]

    # Minimum confidence to report a match
    MIN_CONFIDENCE = 0.6

    def __init__(self, citations: list["Citation"]) -> None:
        """Initialise with recently cited documents.

        Args:
            citations: List of Citation objects from recent conversation
        """
        self.citations = citations
        # Build lookup indices for fast matching
        self._author_index: dict[str, list["Citation"]] = {}
        self._year_index: dict[str, list["Citation"]] = {}
        self._build_indices()

    def _build_indices(self) -> None:
        """Build lookup indices from citations."""
        for citation in self.citations:
            # Index by author_hint (lowercase)
            if citation.author_hint:
                hint = citation.author_hint.lower()
                if hint not in self._author_index:
                    self._author_index[hint] = []
                self._author_index[hint].append(citation)

            # Index by year
            if citation.year:
                year = citation.year
                if year not in self._year_index:
                    self._year_index[year] = []
                self._year_index[year].append(citation)

    def resolve(self, query: str) -> list[ResolvedReference]:
        """Resolve document references in a query.

        Searches for patterns like "the hummel paper", "2021 study",
        "hummel et al" and matches them against recent citations.

        Args:
            query: User's query text

        Returns:
            List of resolved references with confidence scores
        """
        if not self.citations:
            return []

        resolutions: list[ResolvedReference] = []
        query_lower = query.lower()

        # Try each pattern
        for pattern in self.REFERENCE_PATTERNS:
            for match in re.finditer(pattern, query_lower, re.IGNORECASE):
                resolution = self._match_reference(match, query_lower)
                if resolution and resolution.confidence >= self.MIN_CONFIDENCE:
                    # Avoid duplicates
                    if not any(
                        r.matched_filename == resolution.matched_filename
                        for r in resolutions
                    ):
                        resolutions.append(resolution)

        # Also try direct filename token matching as fallback
        if not resolutions:
            resolution = self._match_by_filename_tokens(query_lower)
            if resolution:
                resolutions.append(resolution)

        return resolutions

    def _match_reference(
        self, match: re.Match, query: str
    ) -> ResolvedReference | None:
        """Match a regex result to a citation.

        Args:
            match: Regex match object
            query: Original query (lowercase)

        Returns:
            ResolvedReference if match found, None otherwise
        """
        groups = match.groups()

        # Extract author name and year from groups
        author_name: str | None = None
        year: str | None = None

        for group in groups:
            if group:
                if group.isdigit() and len(group) == 4:
                    year = group
                elif not group.isdigit():
                    author_name = group.lower()

        # Try to match
        candidates: list[tuple["Citation", float, str]] = []

        # Match by author
        if author_name and author_name in self._author_index:
            for citation in self._author_index[author_name]:
                confidence = 0.8
                match_type = "author"
                # Boost confidence if year also matches
                if year and citation.year == year:
                    confidence = 0.95
                    match_type = "author+year"
                candidates.append((citation, confidence, match_type))

        # Match by year only (if no author match)
        elif year and year in self._year_index:
            # Year-only match is lower confidence (could be ambiguous)
            for citation in self._year_index[year]:
                candidates.append((citation, 0.65, "year"))

        if not candidates:
            return None

        # Return highest confidence match
        best = max(candidates, key=lambda x: x[1])
        citation, confidence, match_type = best

        return ResolvedReference(
            original_text=match.group(0),
            matched_filename=citation.filename,
            confidence=confidence,
            match_type=match_type,
        )

    def _match_by_filename_tokens(self, query: str) -> ResolvedReference | None:
        """Match query words against filename tokens.

        Fallback matching when author_hint/year aren't available.

        Args:
            query: Query text (lowercase)

        Returns:
            ResolvedReference if match found, None otherwise
        """
        query_words = set(re.findall(r"\b\w+\b", query))
        # Remove common words
        stopwords = {"the", "a", "an", "this", "that", "paper", "document", "article"}
        query_words -= stopwords

        best_match: tuple["Citation", float] | None = None

        for citation in self.citations:
            # Tokenise filename (lowercase, remove extension, split on separators)
            filename_base = re.sub(r"\.[^.]+$", "", citation.filename.lower())
            filename_tokens = set(re.findall(r"\b\w+\b", filename_base))

            # Calculate overlap
            overlap = query_words & filename_tokens
            if overlap:
                # Score based on overlap ratio
                score = len(overlap) / max(len(query_words), 1)
                if best_match is None or score > best_match[1]:
                    best_match = (citation, score)

        if best_match and best_match[1] >= 0.3:
            citation, score = best_match
            return ResolvedReference(
                original_text="",  # No specific text matched
                matched_filename=citation.filename,
                confidence=min(score + 0.3, 0.7),  # Cap at 0.7 for token matching
                match_type="filename_tokens",
            )

        return None


def resolve_document_references(
    query: str,
    citations: list["Citation"],
) -> list[ResolvedReference]:
    """Convenience function to resolve document references.

    Args:
        query: User's query text
        citations: List of recently cited documents

    Returns:
        List of resolved references
    """
    resolver = DocumentReferenceResolver(citations)
    return resolver.resolve(query)
