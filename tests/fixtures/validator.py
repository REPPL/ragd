"""Golden answer validation for test fixtures.

Validates extracted text against expected golden answers defined in sources.yaml.
Supports exact matching, fuzzy matching (for OCR errors), and pattern matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Sequence

# Optional dependency - graceful degradation if not installed
try:
    from rapidfuzz import fuzz

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of validating a single golden answer."""

    passed: bool
    score: float
    check_type: str
    details: dict[str, object] = field(default_factory=dict)
    message: str = ""


@dataclass
class DocumentValidationReport:
    """Complete validation report for a document."""

    document_id: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Return the percentage of checks that passed."""
        if self.total_checks == 0:
            return 1.0
        return self.passed_checks / self.total_checks


class GoldenAnswerValidator:
    """Validate extracted text against golden answers from sources.yaml."""

    def __init__(self, sources_path: Path | None = None) -> None:
        """Initialise validator with sources.yaml path.

        Args:
            sources_path: Path to sources.yaml. Defaults to same directory.
        """
        if sources_path is None:
            sources_path = Path(__file__).parent / "sources.yaml"
        self.sources_path = sources_path
        self._sources: dict | None = None

    @property
    def sources(self) -> dict:
        """Lazy-load sources.yaml."""
        if self._sources is None:
            with open(self.sources_path) as f:
                self._sources = yaml.safe_load(f)
        return self._sources

    def get_document_config(self, document_id: str) -> dict | None:
        """Get configuration for a specific document by ID."""
        for doc in self.sources.get("documents", []):
            if doc.get("id") == document_id:
                return doc
        return None

    def validate_must_contain(
        self,
        extracted_text: str,
        golden: dict,
    ) -> ValidationResult:
        """Validate that required text is present in extraction.

        Args:
            extracted_text: The text extracted from the document.
            golden: Golden answer config with 'text', 'confidence', etc.

        Returns:
            ValidationResult with pass/fail status and details.
        """
        text = golden["text"]
        confidence = golden.get("confidence", "exact")
        description = golden.get("description", "")

        if confidence == "exact":
            passed = text in extracted_text
            score = 1.0 if passed else 0.0
            message = f"Exact match for '{text}': {'found' if passed else 'not found'}"
        else:
            # Fuzzy matching
            if not RAPIDFUZZ_AVAILABLE:
                # Fall back to substring search
                passed = text.lower() in extracted_text.lower()
                score = 1.0 if passed else 0.0
                message = f"Substring match for '{text}' (rapidfuzz not available)"
            else:
                threshold = golden.get("fuzzy_threshold", 0.85)
                ratio = fuzz.partial_ratio(text, extracted_text) / 100
                passed = ratio >= threshold
                score = ratio
                message = (
                    f"Fuzzy match for '{text}': {ratio:.2%} "
                    f"(threshold: {threshold:.0%})"
                )

        return ValidationResult(
            passed=passed,
            score=score,
            check_type="must_contain",
            details={
                "text": text,
                "confidence": confidence,
                "description": description,
            },
            message=message,
        )

    def validate_pattern(
        self,
        extracted_text: str,
        pattern_config: dict,
    ) -> ValidationResult:
        """Validate that a regex pattern matches in the extraction.

        Args:
            extracted_text: The text extracted from the document.
            pattern_config: Config with 'pattern', 'min_matches', etc.

        Returns:
            ValidationResult with pass/fail status and match count.
        """
        pattern = pattern_config["pattern"]
        min_matches = pattern_config.get("min_matches", 1)
        description = pattern_config.get("description", "")

        try:
            matches = re.findall(pattern, extracted_text)
            match_count = len(matches)
            passed = match_count >= min_matches
            score = min(match_count / min_matches, 1.0) if min_matches > 0 else 1.0
            message = (
                f"Pattern '{pattern}': {match_count} matches "
                f"(required: {min_matches})"
            )
        except re.error as e:
            passed = False
            score = 0.0
            match_count = 0
            message = f"Invalid regex pattern: {e}"

        return ValidationResult(
            passed=passed,
            score=score,
            check_type="pattern",
            details={
                "pattern": pattern,
                "min_matches": min_matches,
                "actual_matches": match_count,
                "description": description,
            },
            message=message,
        )

    def validate_structure(
        self,
        chunk_count: int,
        structure_config: dict,
    ) -> ValidationResult:
        """Validate structural expectations (chunk counts, etc.).

        Args:
            chunk_count: Number of chunks produced from the document.
            structure_config: Config with 'min_chunks', 'max_chunks', etc.

        Returns:
            ValidationResult with pass/fail status.
        """
        min_chunks = structure_config.get("min_chunks", 0)
        max_chunks = structure_config.get("max_chunks", float("inf"))

        passed = min_chunks <= chunk_count <= max_chunks
        if max_chunks == float("inf"):
            score = 1.0 if chunk_count >= min_chunks else chunk_count / min_chunks
        else:
            if passed:
                score = 1.0
            elif chunk_count < min_chunks:
                score = chunk_count / min_chunks
            else:
                score = max_chunks / chunk_count

        message = (
            f"Chunk count: {chunk_count} "
            f"(expected: {min_chunks}-{max_chunks})"
        )

        return ValidationResult(
            passed=passed,
            score=score,
            check_type="structure",
            details={
                "min_chunks": min_chunks,
                "max_chunks": max_chunks,
                "actual_chunks": chunk_count,
            },
            message=message,
        )

    def validate_quality(
        self,
        pages_with_text: int,
        total_pages: int,
        quality_config: dict,
    ) -> ValidationResult:
        """Validate extraction quality metrics.

        Args:
            pages_with_text: Number of pages that yielded text.
            total_pages: Total number of pages in document.
            quality_config: Config with 'min_text_extraction_ratio', etc.

        Returns:
            ValidationResult with pass/fail status.
        """
        min_ratio = quality_config.get("min_text_extraction_ratio", 0.0)

        if total_pages == 0:
            actual_ratio = 0.0
        else:
            actual_ratio = pages_with_text / total_pages

        passed = actual_ratio >= min_ratio
        score = min(actual_ratio / min_ratio, 1.0) if min_ratio > 0 else 1.0
        message = (
            f"Text extraction ratio: {actual_ratio:.1%} "
            f"(minimum: {min_ratio:.0%})"
        )

        return ValidationResult(
            passed=passed,
            score=score,
            check_type="quality",
            details={
                "min_ratio": min_ratio,
                "actual_ratio": actual_ratio,
                "pages_with_text": pages_with_text,
                "total_pages": total_pages,
            },
            message=message,
        )

    def validate_document(
        self,
        document_id: str,
        extracted_text: str,
        chunk_count: int = 0,
        pages_with_text: int = 0,
        total_pages: int = 0,
    ) -> DocumentValidationReport:
        """Run all golden answer validations for a document.

        Args:
            document_id: ID from sources.yaml.
            extracted_text: Full extracted text from document.
            chunk_count: Number of chunks produced.
            pages_with_text: Pages that yielded text (for quality check).
            total_pages: Total pages in document.

        Returns:
            DocumentValidationReport with all check results.
        """
        config = self.get_document_config(document_id)
        if config is None:
            return DocumentValidationReport(
                document_id=document_id,
                passed=False,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                results=[
                    ValidationResult(
                        passed=False,
                        score=0.0,
                        check_type="config",
                        message=f"No configuration found for document: {document_id}",
                    )
                ],
            )

        results: list[ValidationResult] = []
        golden_answers = config.get("golden_answers", {})

        # Validate must_contain entries
        for must_contain in golden_answers.get("must_contain", []):
            result = self.validate_must_contain(extracted_text, must_contain)
            results.append(result)

        # Validate patterns
        for pattern in golden_answers.get("patterns", []):
            result = self.validate_pattern(extracted_text, pattern)
            results.append(result)

        # Validate structure
        structure = golden_answers.get("structure")
        if structure:
            result = self.validate_structure(chunk_count, structure)
            results.append(result)

        # Validate quality
        quality = golden_answers.get("quality")
        if quality and total_pages > 0:
            result = self.validate_quality(pages_with_text, total_pages, quality)
            results.append(result)

        passed_checks = sum(1 for r in results if r.passed)
        failed_checks = len(results) - passed_checks

        return DocumentValidationReport(
            document_id=document_id,
            passed=failed_checks == 0,
            total_checks=len(results),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            results=results,
        )


def get_documents_by_category(
    category_type: str,
    category_value: str,
    sources_path: Path | None = None,
) -> list[dict]:
    """Get all documents matching a specific category.

    Args:
        category_type: One of 'complexity', 'language', 'document_type'.
        category_value: The value to match (e.g., 'simple', 'english').
        sources_path: Optional path to sources.yaml.

    Returns:
        List of document configurations matching the category.
    """
    validator = GoldenAnswerValidator(sources_path)
    matching = []

    for doc in validator.sources.get("documents", []):
        categories = doc.get("categories", {})
        if categories.get(category_type) == category_value:
            matching.append(doc)

    return matching


def list_all_document_ids(sources_path: Path | None = None) -> list[str]:
    """Get list of all document IDs in the registry.

    Args:
        sources_path: Optional path to sources.yaml.

    Returns:
        List of document ID strings.
    """
    validator = GoldenAnswerValidator(sources_path)
    return [doc["id"] for doc in validator.sources.get("documents", [])]
