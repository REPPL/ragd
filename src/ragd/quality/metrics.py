"""Quality metrics for document extraction.

Provides functions to compute quality scores for extracted text.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class QualityMetrics:
    """Quality metrics for a document extraction.

    All scores are in range 0.0 - 1.0 where 1.0 is best quality.

    Attributes:
        completeness: Text extraction completeness (text length vs file size)
        character_quality: Character quality (absence of garbled/mojibake)
        structure: Structure preservation (headings, lists, formatting)
        images: Image handling quality (placeholders with captions)
        tables: Table recognition quality (detected or placeholder)
        overall: Weighted composite score
        computed_at: When metrics were computed
        details: Additional diagnostic information
    """

    completeness: float = 0.0
    character_quality: float = 0.0
    structure: float = 0.0
    images: float = 0.0
    tables: float = 0.0
    overall: float = 0.0
    computed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for storage."""
        return {
            "completeness": self.completeness,
            "character_quality": self.character_quality,
            "structure": self.structure,
            "images": self.images,
            "tables": self.tables,
            "overall": self.overall,
            "computed_at": self.computed_at,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityMetrics:
        """Create metrics from dictionary."""
        return cls(
            completeness=data.get("completeness", 0.0),
            character_quality=data.get("character_quality", 0.0),
            structure=data.get("structure", 0.0),
            images=data.get("images", 0.0),
            tables=data.get("tables", 0.0),
            overall=data.get("overall", 0.0),
            computed_at=data.get("computed_at", datetime.now().isoformat()),
            details=data.get("details", {}),
        )


# Common mojibake patterns (encoding issues)
MOJIBAKE_PATTERNS = [
    r"[\ufffd]+",  # Replacement characters
    r"â€[™œ]",  # UTF-8 interpreted as Windows-1252 (curly quotes)
    r"Ã[\x80-\xbf]",  # Common UTF-8 double-encoding (using hex escapes)
    r"ï»¿",  # BOM artifacts
    r"[\x00-\x08\x0b\x0c\x0e-\x1f]",  # Control characters (except tab, newline, CR)
]

# Structure markers for markdown
STRUCTURE_PATTERNS = {
    "headings": r"^#{1,6}\s+\S",  # Markdown headings
    "lists": r"^\s*[-*+]\s+\S|^\s*\d+\.\s+\S",  # Bullet or numbered lists
    "links": r"\[.+?\]\(.+?\)",  # Markdown links
    "emphasis": r"\*\*.+?\*\*|__.+?__|_[^_]+_|\*[^*]+\*",  # Bold/italic
    "code_blocks": r"```[\s\S]*?```|`[^`]+`",  # Code blocks/inline
}

# Image placeholder patterns (what good extraction looks like)
IMAGE_PATTERNS = {
    "placeholder": r"\[(?:Image|Figure|Fig\.?)\s*(?:\d+)?[:\s]*([^\]]*)\]",
    "caption": r"(?:Caption|Figure|Image)\s*\d*[:\s]+.{10,}",
    "markdown_image": r"!\[([^\]]*)\]\([^)]+\)",
}

# Table patterns
TABLE_PATTERNS = {
    "markdown_table": r"\|[^|]+\|",  # Markdown table rows
    "table_header": r"\|[-:]+\|",  # Table header separator
    "placeholder": r"\[(?:Table)\s*(?:\d+)?[:\s]*([^\]]*)\]",
}


def compute_completeness(
    text: str,
    file_size: int,
    file_type: str,
) -> tuple[float, dict[str, Any]]:
    """Compute text extraction completeness score.

    Estimates how much of the document content was extracted based on
    the ratio of text length to file size, adjusted by file type.

    Args:
        text: Extracted text
        file_size: Original file size in bytes
        file_type: File type (pdf, html, txt, etc.)

    Returns:
        Tuple of (score, details dict)
    """
    if file_size == 0:
        return 0.0, {"reason": "Empty file"}

    text_len = len(text)

    # Expected text-to-file ratios vary by file type
    # These are rough estimates based on typical content
    expected_ratios = {
        "pdf": (0.02, 0.5),  # PDFs can be very binary-heavy (images, fonts)
        "html": (0.1, 0.8),  # HTML has tags but mostly text
        "txt": (0.8, 1.0),   # Plain text should be near 1:1
        "md": (0.7, 1.0),    # Markdown is mostly text
    }

    min_ratio, max_ratio = expected_ratios.get(file_type, (0.05, 0.5))
    actual_ratio = text_len / file_size

    details = {
        "text_length": text_len,
        "file_size": file_size,
        "text_ratio": round(actual_ratio, 4),
        "expected_range": f"{min_ratio:.2f}-{max_ratio:.2f}",
    }

    # Score based on how well the ratio fits expected range
    if actual_ratio < min_ratio * 0.1:
        # Very low extraction - likely failed
        score = actual_ratio / (min_ratio * 0.1) * 0.3
        details["assessment"] = "Very low extraction - likely image-only or encrypted"
    elif actual_ratio < min_ratio:
        # Below expected but some content extracted
        score = 0.3 + (actual_ratio - min_ratio * 0.1) / (min_ratio * 0.9) * 0.4
        details["assessment"] = "Below expected - partial extraction"
    elif actual_ratio <= max_ratio:
        # Within expected range - good
        score = 0.7 + (actual_ratio - min_ratio) / (max_ratio - min_ratio) * 0.3
        details["assessment"] = "Good extraction ratio"
    else:
        # Above expected - could indicate noise or repetition
        excess = actual_ratio - max_ratio
        score = max(0.5, 1.0 - excess)
        details["assessment"] = "Above expected - may contain extraction artifacts"

    return min(1.0, max(0.0, score)), details


def compute_character_quality(text: str) -> tuple[float, dict[str, Any]]:
    """Compute character quality score detecting encoding issues.

    Checks for mojibake, control characters, and other encoding problems.

    Args:
        text: Text to analyse

    Returns:
        Tuple of (score, details dict)
    """
    if not text:
        return 0.0, {"reason": "Empty text"}

    total_chars = len(text)
    problems = {}
    problem_count = 0

    # Check for mojibake patterns
    for pattern in MOJIBAKE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            count = sum(len(m) for m in matches)
            problems[f"mojibake_{pattern[:20]}"] = count
            problem_count += count

    # Check for unusual character distribution
    categories = {}
    for char in text[:10000]:  # Sample first 10k chars for performance
        cat = unicodedata.category(char)
        categories[cat] = categories.get(cat, 0) + 1

    # High ratio of "other" categories may indicate problems
    sample_size = min(len(text), 10000)
    other_chars = sum(v for k, v in categories.items() if k.startswith("C"))
    other_ratio = other_chars / sample_size if sample_size > 0 else 0

    details = {
        "total_chars": total_chars,
        "problem_chars": problem_count,
        "problem_ratio": round(problem_count / total_chars, 4) if total_chars > 0 else 0,
        "control_char_ratio": round(other_ratio, 4),
        "problems": problems,
    }

    # Score: penalise for problems
    problem_ratio = problem_count / total_chars if total_chars > 0 else 0

    if problem_ratio == 0 and other_ratio < 0.01:
        score = 1.0
        details["assessment"] = "Clean text, no encoding issues detected"
    elif problem_ratio < 0.001:
        score = 0.95
        details["assessment"] = "Minor issues, mostly clean"
    elif problem_ratio < 0.01:
        score = 0.8
        details["assessment"] = "Some encoding issues detected"
    elif problem_ratio < 0.05:
        score = 0.5
        details["assessment"] = "Significant encoding problems"
    else:
        score = max(0.0, 0.3 - problem_ratio)
        details["assessment"] = "Severe encoding issues - text may be unusable"

    return score, details


def compute_structure_score(text: str, file_type: str) -> tuple[float, dict[str, Any]]:
    """Compute structure preservation score.

    Checks for preservation of headings, lists, links, formatting.

    Args:
        text: Extracted text
        file_type: Original file type

    Returns:
        Tuple of (score, details dict)
    """
    if not text:
        return 0.0, {"reason": "Empty text"}

    # Count structure elements
    found = {}
    for name, pattern in STRUCTURE_PATTERNS.items():
        matches = re.findall(pattern, text, re.MULTILINE)
        found[name] = len(matches)

    details = {
        "elements_found": found,
        "total_elements": sum(found.values()),
    }

    # Plain text files aren't expected to have markdown structure
    if file_type == "txt":
        # For plain text, check for basic paragraph structure
        paragraphs = len(re.findall(r"\n\n+", text))
        details["paragraphs"] = paragraphs
        score = min(1.0, 0.5 + paragraphs * 0.05)
        details["assessment"] = "Plain text - paragraph structure assessed"
        return score, details

    # For other file types, expect some structure
    total = sum(found.values())
    text_length = len(text)

    # Rough expectation: 1 structure element per 500-1000 chars
    expected_min = text_length / 1000
    expected_good = text_length / 500

    if total == 0 and text_length > 500:
        score = 0.3
        details["assessment"] = "No structure detected - may be flattened"
    elif total < expected_min:
        score = 0.5 + (total / expected_min) * 0.3
        details["assessment"] = "Limited structure preserved"
    elif total < expected_good:
        score = 0.8 + (total - expected_min) / (expected_good - expected_min) * 0.15
        details["assessment"] = "Good structure preservation"
    else:
        score = 0.95
        details["assessment"] = "Excellent structure preservation"

    return min(1.0, score), details


def compute_image_handling(text: str, file_type: str) -> tuple[float, dict[str, Any]]:
    """Compute image handling quality score.

    Checks for proper image placeholders with captions.
    Images should be clearly marked, not confused with text.

    Args:
        text: Extracted text
        file_type: Original file type

    Returns:
        Tuple of (score, details dict)
    """
    if not text:
        return 0.0, {"reason": "Empty text"}

    # Count image-related patterns
    found = {}
    for name, pattern in IMAGE_PATTERNS.items():
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        found[name] = len(matches)

    total_images = sum(found.values())

    details = {
        "patterns_found": found,
        "total_image_refs": total_images,
    }

    # Plain text files typically don't have images
    if file_type == "txt":
        score = 1.0  # N/A, so perfect
        details["assessment"] = "Plain text - image handling not applicable"
        return score, details

    # PDFs often have images, HTML may or may not
    if file_type == "pdf":
        # For PDFs, we expect some image handling
        if total_images > 0:
            # Check if placeholders have captions (quality indicator)
            has_captions = found.get("caption", 0) > 0 or found.get("placeholder", 0) > 0
            if has_captions:
                score = 0.9
                details["assessment"] = "Images detected with captions/placeholders"
            else:
                score = 0.7
                details["assessment"] = "Images detected but limited caption info"
        else:
            # No images found - could be text-only PDF or images lost
            score = 0.5
            details["assessment"] = "No image references - may be text-only or images lost"
    else:
        # For HTML and other formats
        if total_images > 0:
            score = 0.85
            details["assessment"] = "Image references preserved"
        else:
            score = 0.7  # May not have had images
            details["assessment"] = "No images detected - may not have had any"

    return score, details


def compute_table_handling(text: str, file_type: str) -> tuple[float, dict[str, Any]]:
    """Compute table recognition quality score.

    Checks for proper table formatting or placeholders.

    Args:
        text: Extracted text
        file_type: Original file type

    Returns:
        Tuple of (score, details dict)
    """
    if not text:
        return 0.0, {"reason": "Empty text"}

    # Count table-related patterns
    found = {}
    for name, pattern in TABLE_PATTERNS.items():
        matches = re.findall(pattern, text, re.MULTILINE)
        found[name] = len(matches)

    # Check for markdown tables specifically
    has_markdown_table = found.get("markdown_table", 0) > 0 and found.get("table_header", 0) > 0
    has_placeholder = found.get("placeholder", 0) > 0

    details = {
        "patterns_found": found,
        "has_markdown_table": has_markdown_table,
        "has_placeholder": has_placeholder,
    }

    if file_type == "txt":
        score = 1.0  # N/A
        details["assessment"] = "Plain text - table handling not applicable"
        return score, details

    if has_markdown_table:
        score = 0.95
        details["assessment"] = "Tables preserved in markdown format"
    elif has_placeholder:
        score = 0.7
        details["assessment"] = "Table placeholders found - content may be simplified"
    else:
        # No tables detected - may not have had any
        score = 0.6
        details["assessment"] = "No tables detected - may not have had any or lost"

    return score, details


def compute_overall_score(metrics: QualityMetrics) -> float:
    """Compute weighted overall quality score.

    Weights:
    - Completeness: 30% (most important - did we get the content?)
    - Character quality: 25% (critical for usability)
    - Structure: 20% (important for navigation)
    - Images: 15% (important for comprehension)
    - Tables: 10% (less common but important)

    Args:
        metrics: Individual quality metrics

    Returns:
        Weighted overall score 0.0 - 1.0
    """
    weights = {
        "completeness": 0.30,
        "character_quality": 0.25,
        "structure": 0.20,
        "images": 0.15,
        "tables": 0.10,
    }

    weighted_sum = (
        metrics.completeness * weights["completeness"]
        + metrics.character_quality * weights["character_quality"]
        + metrics.structure * weights["structure"]
        + metrics.images * weights["images"]
        + metrics.tables * weights["tables"]
    )

    return round(weighted_sum, 4)
