"""Source quality scoring for ragd (F-115).

Provides quality assessment for indexed content:
- Extraction confidence
- Text completeness
- Formatting quality
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QualityFlag(Enum):
    """Quality-related flags for content."""

    OCR_REQUIRED = "ocr_required"
    TABLES_DETECTED = "tables_detected"
    IMAGES_SKIPPED = "images_skipped"
    NATIVE_TEXT = "native_text"
    STRUCTURE_PRESERVED = "structure_preserved"
    FORMATTING_LOST = "formatting_lost"
    LOW_CONFIDENCE = "low_confidence"
    INCOMPLETE = "incomplete"


@dataclass
class QualityScore:
    """Quality assessment for indexed content.

    Scores range from 0.0 (lowest) to 1.0 (highest).
    """

    extraction_confidence: float = 1.0
    text_completeness: float = 1.0
    formatting_quality: float = 1.0
    flags: list[QualityFlag] = field(default_factory=list)

    # Weights for overall score calculation
    _WEIGHTS = {
        "extraction_confidence": 0.4,
        "text_completeness": 0.4,
        "formatting_quality": 0.2,
    }

    @property
    def overall(self) -> float:
        """Calculate weighted overall quality score."""
        return (
            self.extraction_confidence * self._WEIGHTS["extraction_confidence"]
            + self.text_completeness * self._WEIGHTS["text_completeness"]
            + self.formatting_quality * self._WEIGHTS["formatting_quality"]
        )

    @property
    def grade(self) -> str:
        """Return quality grade (A-F)."""
        score = self.overall
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    @property
    def is_high_quality(self) -> bool:
        """Check if content is high quality (>= 0.8)."""
        return self.overall >= 0.8

    @property
    def is_low_quality(self) -> bool:
        """Check if content is low quality (< 0.6)."""
        return self.overall < 0.6

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "extraction_confidence": round(self.extraction_confidence, 3),
            "text_completeness": round(self.text_completeness, 3),
            "formatting_quality": round(self.formatting_quality, 3),
            "overall": round(self.overall, 3),
            "grade": self.grade,
            "flags": [f.value for f in self.flags],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityScore:
        """Create from dictionary."""
        flags = [QualityFlag(f) for f in data.get("flags", [])]
        return cls(
            extraction_confidence=data.get("extraction_confidence", 1.0),
            text_completeness=data.get("text_completeness", 1.0),
            formatting_quality=data.get("formatting_quality", 1.0),
            flags=flags,
        )


def score_extraction_confidence(
    text: str,
    is_ocr: bool = False,
    ocr_confidence: float | None = None,
) -> tuple[float, list[QualityFlag]]:
    """Score extraction confidence.

    Args:
        text: Extracted text content
        is_ocr: Whether OCR was used
        ocr_confidence: OCR engine confidence (0.0-1.0)

    Returns:
        Tuple of (score, flags)
    """
    flags = []
    score = 1.0

    if is_ocr:
        flags.append(QualityFlag.OCR_REQUIRED)
        # Start with OCR baseline
        if ocr_confidence is not None:
            score = ocr_confidence
        else:
            score = 0.75  # Default OCR penalty
    else:
        flags.append(QualityFlag.NATIVE_TEXT)

    # Check for common OCR errors
    ocr_error_patterns = [
        r"\bl\d\b",  # l followed by digit (l1, l2)
        r"\bO\d\b",  # O followed by digit (O0, O1)
        r"[^\w\s]{3,}",  # Sequences of special chars
        r"\b[A-Z]{2,}[a-z]+[A-Z]+",  # Mixed case gibberish
    ]

    error_count = 0
    for pattern in ocr_error_patterns:
        error_count += len(re.findall(pattern, text))

    # Penalise for OCR errors
    if error_count > 0:
        penalty = min(0.3, error_count * 0.02)
        score = max(0.3, score - penalty)

    if score < 0.7:
        flags.append(QualityFlag.LOW_CONFIDENCE)

    return score, flags


def score_text_completeness(
    text: str,
    expected_length: int | None = None,
    has_missing_sections: bool = False,
) -> tuple[float, list[QualityFlag]]:
    """Score text completeness.

    Args:
        text: Extracted text content
        expected_length: Expected content length (if known)
        has_missing_sections: Whether sections were detected as missing

    Returns:
        Tuple of (score, flags)
    """
    flags = []
    score = 1.0

    # Check minimum viable content
    text_length = len(text.strip())
    if text_length < 50:
        score = 0.3
        flags.append(QualityFlag.INCOMPLETE)
    elif text_length < 200:
        score = 0.6

    # Compare to expected length
    if expected_length is not None and expected_length > 0:
        ratio = text_length / expected_length
        if ratio < 0.5:
            score = min(score, 0.5)
            flags.append(QualityFlag.INCOMPLETE)
        elif ratio < 0.8:
            score = min(score, 0.7)

    if has_missing_sections:
        score = min(score, 0.7)
        flags.append(QualityFlag.INCOMPLETE)

    return score, flags


def score_formatting_quality(
    text: str,
    has_structure: bool = False,
    has_tables: bool = False,
    images_skipped: int = 0,
) -> tuple[float, list[QualityFlag]]:
    """Score formatting preservation quality.

    Args:
        text: Extracted text content
        has_structure: Whether document structure was preserved
        has_tables: Whether tables were detected
        images_skipped: Number of images that couldn't be processed

    Returns:
        Tuple of (score, flags)
    """
    flags = []
    score = 1.0

    # Check for structure markers
    has_headers = bool(re.search(r"^#+\s|\n#{1,6}\s", text, re.MULTILINE))
    has_lists = bool(re.search(r"^\s*[-*•]\s|\n\s*\d+\.", text, re.MULTILINE))
    has_paragraphs = "\n\n" in text

    structure_indicators = sum([has_headers, has_lists, has_paragraphs])

    if has_structure or structure_indicators >= 2:
        flags.append(QualityFlag.STRUCTURE_PRESERVED)
    elif structure_indicators == 0 and len(text) > 500:
        score = 0.6
        flags.append(QualityFlag.FORMATTING_LOST)

    if has_tables:
        flags.append(QualityFlag.TABLES_DETECTED)
        # Tables often lose formatting, slight penalty
        score = min(score, 0.85)

    if images_skipped > 0:
        flags.append(QualityFlag.IMAGES_SKIPPED)
        # Penalty based on number of skipped images
        penalty = min(0.3, images_skipped * 0.05)
        score = max(0.5, score - penalty)

    return score, flags


def calculate_quality_score(
    text: str,
    is_ocr: bool = False,
    ocr_confidence: float | None = None,
    expected_length: int | None = None,
    has_missing_sections: bool = False,
    has_structure: bool = False,
    has_tables: bool = False,
    images_skipped: int = 0,
) -> QualityScore:
    """Calculate comprehensive quality score for content.

    Args:
        text: Extracted text content
        is_ocr: Whether OCR was used
        ocr_confidence: OCR engine confidence
        expected_length: Expected content length
        has_missing_sections: Whether sections were detected as missing
        has_structure: Whether document structure was preserved
        has_tables: Whether tables were detected
        images_skipped: Number of images that couldn't be processed

    Returns:
        QualityScore with all dimensions
    """
    all_flags = []

    extraction_score, extraction_flags = score_extraction_confidence(
        text, is_ocr=is_ocr, ocr_confidence=ocr_confidence
    )
    all_flags.extend(extraction_flags)

    completeness_score, completeness_flags = score_text_completeness(
        text,
        expected_length=expected_length,
        has_missing_sections=has_missing_sections,
    )
    all_flags.extend(completeness_flags)

    formatting_score, formatting_flags = score_formatting_quality(
        text,
        has_structure=has_structure,
        has_tables=has_tables,
        images_skipped=images_skipped,
    )
    all_flags.extend(formatting_flags)

    # Deduplicate flags
    unique_flags = list(dict.fromkeys(all_flags))

    return QualityScore(
        extraction_confidence=extraction_score,
        text_completeness=completeness_score,
        formatting_quality=formatting_score,
        flags=unique_flags,
    )


def format_quality_badge(score: QualityScore) -> str:
    """Format quality score as a display badge.

    Args:
        score: Quality score to format

    Returns:
        Formatted badge string
    """
    grade = score.grade
    overall = score.overall

    # Color-coded badge
    if overall >= 0.8:
        return f"[green]★ {grade}[/green]"
    elif overall >= 0.6:
        return f"[yellow]★ {grade}[/yellow]"
    else:
        return f"[red]★ {grade}[/red]"


def format_quality_summary(score: QualityScore) -> str:
    """Format quality score as a summary string.

    Args:
        score: Quality score to format

    Returns:
        Summary string
    """
    parts = [f"Quality: {score.grade} ({score.overall:.0%})"]

    if score.flags:
        flag_strs = [f.value.replace("_", " ") for f in score.flags[:3]]
        parts.append(f"[{', '.join(flag_strs)}]")

    return " ".join(parts)
