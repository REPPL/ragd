"""Tests for indexing self-evaluation (F-105)."""

import pytest

from ragd.operations.evaluation import (
    EvaluationMetrics,
    EvaluationResult,
    BatchEvaluationResult,
    compute_completeness,
    compute_accuracy,
    compute_structure_preservation,
    compute_metadata_quality,
    evaluate_indexing,
    evaluate_batch,
    format_evaluation_report,
)


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics."""

    def test_default_metrics(self):
        """Should have zero defaults."""
        metrics = EvaluationMetrics()
        assert metrics.completeness == 0.0
        assert metrics.overall == 0.0

    def test_overall_weighted(self):
        """Should compute weighted overall."""
        metrics = EvaluationMetrics(
            completeness=0.8,
            accuracy=0.8,
            structure=0.8,
            metadata=0.8,
        )
        assert metrics.overall == 0.8

    def test_grade_a(self):
        """High scores should get grade A."""
        metrics = EvaluationMetrics(
            completeness=0.95,
            accuracy=0.95,
            structure=0.95,
            metadata=0.95,
        )
        assert metrics.grade == "A"

    def test_grade_f(self):
        """Low scores should get grade F."""
        metrics = EvaluationMetrics(
            completeness=0.3,
            accuracy=0.3,
            structure=0.3,
            metadata=0.3,
        )
        assert metrics.grade == "F"

    def test_to_dict(self):
        """Should convert to dictionary."""
        metrics = EvaluationMetrics(completeness=0.75)
        d = metrics.to_dict()
        assert d["completeness"] == 0.75
        assert "grade" in d
        assert "overall" in d


class TestComputeCompleteness:
    """Tests for completeness computation."""

    def test_identical_text(self):
        """Identical text should be 100% complete."""
        source = "Hello world this is a test"
        indexed = "Hello world this is a test"
        assert compute_completeness(source, indexed) == 1.0

    def test_partial_coverage(self):
        """Partial coverage should be measured."""
        source = "Hello world this is a test document with words"
        indexed = "Hello world this"
        completeness = compute_completeness(source, indexed)
        assert 0.3 <= completeness <= 0.5

    def test_empty_source(self):
        """Empty source should return 0."""
        assert compute_completeness("", "some text") == 0.0

    def test_empty_indexed(self):
        """Empty indexed should return 0."""
        assert compute_completeness("some text", "") == 0.0


class TestComputeAccuracy:
    """Tests for accuracy computation."""

    def test_identical_text(self):
        """Identical text should have high accuracy."""
        source = "Hello world"
        indexed = "Hello world"
        assert compute_accuracy(source, indexed) == 1.0

    def test_similar_text(self):
        """Similar text should have moderate accuracy."""
        source = "Hello world"
        indexed = "Hello worlds"  # One char different
        accuracy = compute_accuracy(source, indexed)
        assert 0.9 <= accuracy < 1.0

    def test_different_text(self):
        """Very different text should have low accuracy."""
        source = "Hello world"
        indexed = "Goodbye universe"
        accuracy = compute_accuracy(source, indexed)
        assert accuracy < 0.5


class TestComputeStructurePreservation:
    """Tests for structure preservation computation."""

    def test_preserved_headers(self):
        """Should detect preserved headers."""
        source = "# Header\n\nContent here\n\n## Sub"
        indexed = "# Header\n\nContent here\n\n## Sub"
        score = compute_structure_preservation(source, indexed)
        assert score >= 0.9

    def test_lost_structure(self):
        """Should detect lost structure."""
        source = "# Header\n\n- List item\n- Another\n\n**Bold**"
        indexed = "Header List item Another Bold"
        score = compute_structure_preservation(source, indexed)
        assert score < 0.5

    def test_no_structure(self):
        """Plain text should have perfect preservation."""
        source = "Just plain text with no structure"
        indexed = "Just plain text with no structure"
        score = compute_structure_preservation(source, indexed)
        assert score == 1.0


class TestComputeMetadataQuality:
    """Tests for metadata quality computation."""

    def test_complete_metadata(self):
        """Complete metadata should score 1.0."""
        expected = {"title": "Test", "author": "Jane", "date": "2024"}
        actual = {"title": "Test", "author": "Jane", "date": "2024"}
        assert compute_metadata_quality(expected, actual) == 1.0

    def test_partial_metadata(self):
        """Partial metadata should score partially."""
        expected = {"title": "Test", "author": "Jane", "date": "2024"}
        actual = {"title": "Test"}  # Only title extracted
        score = compute_metadata_quality(expected, actual)
        assert 0.3 <= score <= 0.4

    def test_empty_expected(self):
        """No expected metadata should score 1.0."""
        assert compute_metadata_quality({}, {"some": "value"}) == 1.0


class TestEvaluateIndexing:
    """Tests for evaluate_indexing function."""

    def test_good_indexing(self):
        """Good indexing should score well."""
        source = "This is the source document with all the important content."
        indexed = "This is the source document with all the important content."

        result = evaluate_indexing(source, indexed)

        assert result.success is True
        assert result.metrics.grade in ["A", "B"]
        assert len(result.issues) == 0

    def test_poor_indexing(self):
        """Poor indexing should identify issues."""
        source = "This is a long document with lots of important information."
        indexed = "short"  # Almost nothing indexed

        result = evaluate_indexing(source, indexed)

        assert result.success is True
        assert result.metrics.grade in ["D", "F"]
        assert len(result.issues) > 0
        assert len(result.suggestions) > 0

    def test_includes_document_info(self):
        """Should include document info."""
        result = evaluate_indexing(
            "source",
            "indexed",
            document_id="doc-123",
            source_path="/path/to/doc.pdf",
        )

        assert result.document_id == "doc-123"
        assert result.source_path == "/path/to/doc.pdf"


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_to_dict(self):
        """Should convert to dictionary."""
        result = EvaluationResult(
            document_id="doc-123",
            source_path="/test.pdf",
        )
        d = result.to_dict()

        assert d["document_id"] == "doc-123"
        assert "metrics" in d
        assert "evaluated_at" in d


class TestBatchEvaluation:
    """Tests for batch evaluation."""

    def test_aggregate_results(self):
        """Should aggregate multiple results."""
        results = [
            evaluate_indexing("good content", "good content"),
            evaluate_indexing("okay content", "okay content"),
            evaluate_indexing("test", ""),  # Poor
        ]

        batch = evaluate_batch(results)

        assert batch.total == 3
        assert batch.evaluated == 3
        assert batch.high_quality >= 1
        assert batch.low_quality >= 1

    def test_empty_batch(self):
        """Should handle empty batch."""
        batch = evaluate_batch([])
        assert batch.total == 0
        assert batch.average_score == 0.0


class TestFormatEvaluationReport:
    """Tests for report formatting."""

    def test_includes_grade(self):
        """Report should include grade."""
        result = evaluate_indexing("test content", "test content")
        report = format_evaluation_report(result)

        assert "Grade:" in report
        assert result.metrics.grade in report

    def test_includes_metrics(self):
        """Report should include all metrics."""
        result = evaluate_indexing("test", "test")
        report = format_evaluation_report(result)

        assert "Completeness:" in report
        assert "Accuracy:" in report
        assert "Structure:" in report
        assert "Metadata:" in report

    def test_includes_issues(self):
        """Report should include issues."""
        result = evaluate_indexing("long text with content", "x")
        report = format_evaluation_report(result)

        assert "Issues:" in report
