"""Citation marker extraction from LLM responses.

Extracts [1], [2], [1;2] style citation markers from text along with
the surrounding claim context for validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExtractedCitation:
    """A citation marker extracted from response text.

    Attributes:
        marker_text: The full marker as it appears in text (e.g., "[1;2]")
        citation_indices: The 1-based citation numbers referenced (e.g., [1, 2])
        claim_text: The sentence or phrase containing the citation
        char_start: Start position of marker in response
        char_end: End position of marker in response
    """

    marker_text: str
    citation_indices: list[int]
    claim_text: str
    char_start: int
    char_end: int


# Pattern matches [N] or [N;M;...] format
_CITATION_PATTERN = re.compile(r"\[(\d+(?:;\d+)*)\]")


def extract_citation_markers(response_text: str) -> list[ExtractedCitation]:
    """Extract all citation markers from LLM response text.

    Handles formats:
    - Single: [1], [2], [3]
    - Multiple: [1;2], [1;2;3]
    - Adjacent: [1][2] (extracted as separate markers)

    Args:
        response_text: The LLM-generated response containing citation markers

    Returns:
        List of ExtractedCitation objects with marker info and claim context
    """
    citations = []

    for match in _CITATION_PATTERN.finditer(response_text):
        marker = match.group(0)  # Full marker e.g., "[1;2]"
        indices_str = match.group(1)  # Just the numbers e.g., "1;2"
        indices = [int(i) for i in indices_str.split(";")]

        # Extract surrounding context (sentence containing citation)
        claim = _extract_claim_context(response_text, match.start(), match.end())

        citations.append(
            ExtractedCitation(
                marker_text=marker,
                citation_indices=indices,
                claim_text=claim,
                char_start=match.start(),
                char_end=match.end(),
            )
        )

    return citations


def _extract_claim_context(text: str, marker_start: int, marker_end: int) -> str:
    """Extract the sentence or phrase containing a citation marker.

    Finds sentence boundaries (. ? ! or newlines) around the marker
    and returns the containing sentence with the marker removed.

    Args:
        text: Full response text
        marker_start: Start position of citation marker
        marker_end: End position of citation marker

    Returns:
        The sentence/phrase containing the citation (marker removed)
    """
    # Sentence-ending punctuation followed by space or newline
    sentence_endings = ".!?\n"

    # Find start of sentence (look backwards for sentence boundary)
    sentence_start = 0
    for i in range(marker_start - 1, -1, -1):
        if text[i] in sentence_endings:
            sentence_start = i + 1
            # Skip any whitespace after the boundary
            while sentence_start < marker_start and text[sentence_start].isspace():
                sentence_start += 1
            break

    # Find end of sentence (look forwards for sentence boundary)
    sentence_end = len(text)
    for i in range(marker_end, len(text)):
        if text[i] in sentence_endings:
            sentence_end = i + 1
            break

    # Extract sentence and remove the citation marker for cleaner claim text
    sentence = text[sentence_start:sentence_end].strip()

    # Remove all citation markers from the claim for cleaner validation
    claim = _CITATION_PATTERN.sub("", sentence).strip()

    # Normalise whitespace
    claim = " ".join(claim.split())

    return claim


def get_used_citation_indices(response_text: str) -> set[int]:
    """Get the set of citation indices actually used in a response.

    Useful for identifying unused citations that were provided in context.

    Args:
        response_text: The LLM-generated response

    Returns:
        Set of 1-based citation indices that appear in the response
    """
    used = set()
    for match in _CITATION_PATTERN.finditer(response_text):
        indices_str = match.group(1)
        for idx in indices_str.split(";"):
            used.add(int(idx))
    return used
