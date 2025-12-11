"""Caption and photo credit removal.

Removes figure captions, table captions, photo credits, and media
attributions that pollute content text.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# Caption and attribution patterns
# Note: Patterns should be precise to avoid false positives on long lines
CAPTION_PATTERNS = [
    # Figure/table captions (academic style)
    r"^Figure\s+\d+[.:\-]\s*.+$",
    r"^Fig\.\s*\d+[.:\-]\s*.+$",
    r"^Table\s+\d+[.:\-]\s*.+$",
    r"^Chart\s+\d+[.:\-]\s*.+$",
    r"^Graph\s+\d+[.:\-]\s*.+$",
    r"^Exhibit\s+\d+[.:\-]\s*.+$",
    r"^Diagram\s+\d+[.:\-]\s*.+$",
    # Photo credits
    r"^Photo(?:\s+credit)?:\s*.+$",
    r"^Image:\s*.+$",
    r"^Credit:\s*.+$",
    r"^Source:\s*.+$",
    r"^Illustration(?:\s+by)?:\s*.+$",
    r"^Photograph(?:\s+by)?:\s*.+$",
    r"^Picture:\s*.+$",
    # Media attribution (inline) - use word boundaries and limit line length
    # Matches: "Photo / Getty Images", "Reuters/AP", etc.
    # Requires "/" within first 100 chars and word boundary on agency names
    r"^.{0,100}/\s*(?:Getty\s*Images?|Reuters|\bAP\b|\bAFP\b|\bEPA\b|Shutterstock|iStock|Alamy)(?:\s|$|[,.])",
    r"^\((?:Getty\s*Images?|Reuters|AP|AFP|EPA|Shutterstock|iStock|Alamy)\)$",
    r"^©\s*.+(?:Getty|Reuters|\bAP\b|\bAFP\b|\bEPA\b).*$",
    # Alt text leakage
    r"^Image\s+description:\s*.+$",
    r"^\[Image:.*\]$",
    r"^\[Photo:.*\]$",
    r"^\[Figure:.*\]$",
    # Video/multimedia captions
    r"^Video:\s*.+$",
    r"^Watch:\s*.+$",
    r"^Listen:\s*.+$",
    # Common caption markers
    r"^\(Image\)$",
    r"^\(Photo\)$",
    r"^\(Courtesy of .+\)$",
    r"^Courtesy of .+$",
]

# Compile patterns for efficiency
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CAPTION_PATTERNS]


def remove_captions(text: str) -> str:
    """Remove figure captions, photo credits, and media attributions.

    Args:
        text: Text potentially containing captions

    Returns:
        Text with captions removed
    """
    lines = text.split("\n")
    filtered = []

    for line in lines:
        line_stripped = line.strip()

        # Keep empty lines (preserve paragraph structure)
        if not line_stripped:
            filtered.append(line)
            continue

        # Check against caption patterns
        is_caption = any(pattern.match(line_stripped) for pattern in _COMPILED_PATTERNS)

        if not is_caption:
            # Additional heuristic: short lines with only attribution markers
            is_caption = _is_attribution_line(line_stripped)

        if not is_caption:
            filtered.append(line)

    result = "\n".join(filtered)

    # Safety check: don't remove more than 50% of content
    # This protects against overly aggressive pattern matching
    original_len = len(text.strip())
    result_len = len(result.strip())

    if original_len > 0 and result_len < original_len * 0.5:
        logger.warning(
            "Caption removal would delete >50%% of content (%d -> %d chars), skipping",
            original_len,
            result_len,
        )
        return text

    return result


def _is_attribution_line(line: str) -> bool:
    """Check if line appears to be a standalone attribution.

    Args:
        line: Line to check

    Returns:
        True if line looks like an attribution
    """
    # Very short lines ending with common agency names
    if len(line) < 50:
        agencies = ["Getty", "Reuters", "AP", "AFP", "EPA", "Shutterstock"]
        return any(line.endswith(agency) or line.endswith(f"({agency})") for agency in agencies)

    return False


def has_caption_content(text: str) -> bool:
    """Check if text contains caption-like content.

    Useful for diagnostics and testing.

    Args:
        text: Text to check

    Returns:
        True if captions detected
    """
    lines = text.split("\n")

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if any(pattern.match(line_stripped) for pattern in _COMPILED_PATTERNS):
            return True

    return False
