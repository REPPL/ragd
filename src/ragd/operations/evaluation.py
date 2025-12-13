"""Indexing self-evaluation for ragd (F-105).

Provides self-evaluation system that compares source to indexed content
and reports quality metrics.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EvaluationMetrics:
    """Metrics from source-to-index comparison."""

    completeness: float = 0.0  # Text coverage (0.0-1.0)
    accuracy: float = 0.0  # Character-level similarity (0.0-1.0)
    structure: float = 0.0  # Structure preservation (0.0-1.0)
    metadata: float = 0.0  # Metadata extraction quality (0.0-1.0)

    @property
    def overall(self) -> float:
        """Calculate weighted overall score."""
        return (
            self.completeness * 0.35
            + self.accuracy * 0.35
            + self.structure * 0.20
            + self.metadata * 0.10
        )

    @property
    def grade(self) -> str:
        """Return evaluation grade (A-F)."""
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "completeness": round(self.completeness, 3),
            "accuracy": round(self.accuracy, 3),
            "structure": round(self.structure, 3),
            "metadata": round(self.metadata, 3),
            "overall": round(self.overall, 3),
            "grade": self.grade,
        }


@dataclass
class EvaluationResult:
    """Result of indexing self-evaluation."""

    document_id: str | None = None
    source_path: str | None = None
    metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "source_path": self.source_path,
            "metrics": self.metrics.to_dict(),
            "issues": self.issues,
            "suggestions": self.suggestions,
            "evaluated_at": self.evaluated_at.isoformat(),
            "success": self.success,
            "error": self.error,
        }


def compute_completeness(source_text: str, indexed_text: str) -> float:
    """Compute text coverage completeness.

    Args:
        source_text: Original source text
        indexed_text: Text as indexed

    Returns:
        Completeness score (0.0-1.0)
    """
    if not source_text:
        return 0.0

    source_words = set(re.findall(r'\b\w+\b', source_text.lower()))
    indexed_words = set(re.findall(r'\b\w+\b', indexed_text.lower()))

    if not source_words:
        return 1.0 if not indexed_words else 0.0

    # Measure word coverage
    coverage = len(source_words & indexed_words) / len(source_words)

    return min(1.0, coverage)


def compute_accuracy(source_text: str, indexed_text: str) -> float:
    """Compute character-level accuracy.

    Args:
        source_text: Original source text
        indexed_text: Text as indexed

    Returns:
        Accuracy score (0.0-1.0)
    """
    if not source_text:
        return 0.0 if indexed_text else 1.0

    # Normalise whitespace
    source_norm = " ".join(source_text.split())
    indexed_norm = " ".join(indexed_text.split())

    # Use sequence matcher for similarity
    matcher = difflib.SequenceMatcher(None, source_norm, indexed_norm)
    return matcher.ratio()


def compute_structure_preservation(source_text: str, indexed_text: str) -> float:
    """Compute structure preservation score.

    Args:
        source_text: Original source text
        indexed_text: Text as indexed

    Returns:
        Structure score (0.0-1.0)
    """
    def count_structure(text: str) -> dict[str, int]:
        return {
            "headers": len(re.findall(r'^#+\s|\n#{1,6}\s', text, re.MULTILINE)),
            "lists": len(re.findall(r'^\s*[-*•]\s|\n\s*\d+\.', text, re.MULTILINE)),
            "paragraphs": text.count("\n\n"),
            "links": len(re.findall(r'\[.*?\]\(.*?\)', text)),
            "emphasis": len(re.findall(r'\*\*.*?\*\*|__.*?__|_.*?_|\*.*?\*', text)),
        }

    source_struct = count_structure(source_text)
    indexed_struct = count_structure(indexed_text)

    if not any(source_struct.values()):
        return 1.0  # No structure to preserve

    # Compare structure counts
    scores = []
    for key in source_struct:
        if source_struct[key] > 0:
            ratio = min(1.0, indexed_struct[key] / source_struct[key])
            scores.append(ratio)

    return sum(scores) / len(scores) if scores else 1.0


def compute_metadata_quality(
    expected_metadata: dict[str, Any],
    actual_metadata: dict[str, Any],
) -> float:
    """Compute metadata extraction quality.

    Args:
        expected_metadata: Expected metadata fields
        actual_metadata: Actually extracted metadata

    Returns:
        Metadata quality score (0.0-1.0)
    """
    if not expected_metadata:
        return 1.0

    # Check key metadata fields
    key_fields = ["title", "author", "date", "source", "format"]
    found = 0
    total = 0

    for field in key_fields:
        if field in expected_metadata:
            total += 1
            if field in actual_metadata and actual_metadata[field]:
                found += 1

    return found / total if total > 0 else 1.0


def evaluate_indexing(
    source_text: str,
    indexed_text: str,
    expected_metadata: dict[str, Any] | None = None,
    actual_metadata: dict[str, Any] | None = None,
    document_id: str | None = None,
    source_path: str | None = None,
) -> EvaluationResult:
    """Evaluate indexing quality by comparing source to indexed.

    Args:
        source_text: Original source text
        indexed_text: Text as indexed
        expected_metadata: Expected metadata
        actual_metadata: Actually extracted metadata
        document_id: ID of the document
        source_path: Path to source file

    Returns:
        EvaluationResult with metrics and suggestions
    """
    issues = []
    suggestions = []

    # Compute metrics
    completeness = compute_completeness(source_text, indexed_text)
    accuracy = compute_accuracy(source_text, indexed_text)
    structure = compute_structure_preservation(source_text, indexed_text)
    metadata_score = compute_metadata_quality(
        expected_metadata or {},
        actual_metadata or {},
    )

    metrics = EvaluationMetrics(
        completeness=completeness,
        accuracy=accuracy,
        structure=structure,
        metadata=metadata_score,
    )

    # Generate issues and suggestions
    if completeness < 0.7:
        issues.append("Low text coverage - some content may be missing")
        suggestions.append("Check if OCR is needed for scanned content")

    if accuracy < 0.8:
        issues.append("Low accuracy - text may have extraction errors")
        suggestions.append("Verify extraction method for this file type")

    if structure < 0.5:
        issues.append("Poor structure preservation")
        suggestions.append("Consider enabling structure-preserving extraction")

    if metadata_score < 0.5:
        issues.append("Incomplete metadata extraction")
        suggestions.append("Check metadata extraction configuration")

    return EvaluationResult(
        document_id=document_id,
        source_path=source_path,
        metrics=metrics,
        issues=issues,
        suggestions=suggestions,
    )


@dataclass
class BatchEvaluationResult:
    """Result of batch evaluation."""

    total: int = 0
    evaluated: int = 0
    high_quality: int = 0  # A or B grade
    medium_quality: int = 0  # C grade
    low_quality: int = 0  # D or F grade
    average_score: float = 0.0
    results: list[EvaluationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "evaluated": self.evaluated,
            "high_quality": self.high_quality,
            "medium_quality": self.medium_quality,
            "low_quality": self.low_quality,
            "average_score": round(self.average_score, 3),
        }


def evaluate_batch(
    evaluations: list[EvaluationResult],
) -> BatchEvaluationResult:
    """Aggregate batch evaluation results.

    Args:
        evaluations: List of individual evaluations

    Returns:
        BatchEvaluationResult with aggregated metrics
    """
    if not evaluations:
        return BatchEvaluationResult()

    high_quality = sum(1 for e in evaluations if e.metrics.grade in ["A", "B"])
    medium_quality = sum(1 for e in evaluations if e.metrics.grade == "C")
    low_quality = sum(1 for e in evaluations if e.metrics.grade in ["D", "F"])
    avg_score = sum(e.metrics.overall for e in evaluations) / len(evaluations)

    return BatchEvaluationResult(
        total=len(evaluations),
        evaluated=len(evaluations),
        high_quality=high_quality,
        medium_quality=medium_quality,
        low_quality=low_quality,
        average_score=avg_score,
        results=evaluations,
    )


def format_evaluation_report(result: EvaluationResult) -> str:
    """Format evaluation result as a report string.

    Args:
        result: Evaluation result

    Returns:
        Formatted report string
    """
    lines = [
        "Indexing Self-Evaluation Report",
        "=" * 30,
        "",
        f"Document: {result.document_id or 'Unknown'}",
        f"Source: {result.source_path or 'Unknown'}",
        f"Grade: {result.metrics.grade} ({result.metrics.overall:.0%})",
        "",
        "Metrics:",
        f"  Completeness: {result.metrics.completeness:.0%}",
        f"  Accuracy:     {result.metrics.accuracy:.0%}",
        f"  Structure:    {result.metrics.structure:.0%}",
        f"  Metadata:     {result.metrics.metadata:.0%}",
    ]

    if result.issues:
        lines.extend(["", "Issues:"])
        for issue in result.issues:
            lines.append(f"  - {issue}")

    if result.suggestions:
        lines.extend(["", "Suggestions:"])
        for suggestion in result.suggestions:
            lines.append(f"  - {suggestion}")

    return "\n".join(lines)
