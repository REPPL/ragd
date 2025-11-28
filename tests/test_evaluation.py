"""Tests for evaluation module."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.evaluation.metrics import (
    EvaluationMetrics,
    MetricType,
    compute_context_precision,
    compute_context_recall,
    compute_relevance_score,
    compute_reciprocal_rank,
    compute_ndcg,
)
from ragd.evaluation.evaluator import (
    Evaluator,
    EvaluationConfig,
    EvaluationResult,
    EvaluationReport,
    evaluate_query,
)
from ragd.evaluation.storage import (
    EvaluationStorage,
    save_evaluation_result,
    load_evaluation_history,
)


class TestMetricType:
    """Tests for MetricType enum."""

    def test_metric_values(self):
        """Test metric type values."""
        assert MetricType.CONTEXT_PRECISION.value == "context_precision"
        assert MetricType.CONTEXT_RECALL.value == "context_recall"
        assert MetricType.RELEVANCE_SCORE.value == "relevance_score"
        assert MetricType.FAITHFULNESS.value == "faithfulness"
        assert MetricType.ANSWER_RELEVANCY.value == "answer_relevancy"


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics dataclass."""

    def test_default_metrics(self):
        """Test default metric values."""
        metrics = EvaluationMetrics()
        assert metrics.context_precision is None
        assert metrics.context_recall is None
        assert metrics.relevance_score is None
        assert metrics.faithfulness is None
        assert metrics.answer_relevancy is None

    def test_overall_score_single_metric(self):
        """Test overall score with single metric."""
        metrics = EvaluationMetrics(context_precision=0.8)
        # With only one metric, it should be the average
        assert metrics.overall_score == 0.8

    def test_overall_score_multiple_metrics(self):
        """Test overall score with multiple metrics."""
        metrics = EvaluationMetrics(
            context_precision=0.8,
            relevance_score=0.6,
        )
        # Normalised weighted average
        assert 0.6 < metrics.overall_score < 0.8

    def test_overall_score_empty(self):
        """Test overall score with no metrics."""
        metrics = EvaluationMetrics()
        assert metrics.overall_score == 0.0

    def test_to_dict(self):
        """Test serialisation to dict."""
        metrics = EvaluationMetrics(
            context_precision=0.85,
            relevance_score=0.75,
        )
        data = metrics.to_dict()
        assert data["context_precision"] == 0.85
        assert data["relevance_score"] == 0.75
        assert "overall_score" in data

    def test_from_dict(self):
        """Test deserialisation from dict."""
        data = {
            "context_precision": 0.9,
            "context_recall": 0.8,
            "relevance_score": 0.85,
        }
        metrics = EvaluationMetrics.from_dict(data)
        assert metrics.context_precision == 0.9
        assert metrics.context_recall == 0.8
        assert metrics.relevance_score == 0.85


class TestContextPrecision:
    """Tests for context precision metric."""

    def test_all_relevant(self):
        """Test precision when all results are relevant."""
        scores = [0.9, 0.8, 0.7, 0.6]
        precision = compute_context_precision(scores, relevance_threshold=0.5)
        assert precision == 1.0

    def test_half_relevant(self):
        """Test precision when half results are relevant."""
        scores = [0.9, 0.8, 0.3, 0.2]
        precision = compute_context_precision(scores, relevance_threshold=0.5)
        assert precision == 0.5

    def test_none_relevant(self):
        """Test precision when no results are relevant."""
        scores = [0.3, 0.2, 0.1]
        precision = compute_context_precision(scores, relevance_threshold=0.5)
        assert precision == 0.0

    def test_empty_results(self):
        """Test precision with empty results."""
        precision = compute_context_precision([])
        assert precision == 0.0

    def test_custom_threshold(self):
        """Test precision with custom threshold."""
        scores = [0.9, 0.8, 0.7]
        precision = compute_context_precision(scores, relevance_threshold=0.75)
        assert precision == pytest.approx(2/3)


class TestContextRecall:
    """Tests for context recall metric."""

    def test_full_recall(self):
        """Test recall when all expected docs retrieved."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2"]
        recall = compute_context_recall(retrieved, expected)
        assert recall == 1.0

    def test_partial_recall(self):
        """Test recall when some expected docs retrieved."""
        retrieved = ["doc1", "doc3"]
        expected = ["doc1", "doc2"]
        recall = compute_context_recall(retrieved, expected)
        assert recall == 0.5

    def test_no_recall(self):
        """Test recall when no expected docs retrieved."""
        retrieved = ["doc3", "doc4"]
        expected = ["doc1", "doc2"]
        recall = compute_context_recall(retrieved, expected)
        assert recall == 0.0

    def test_no_expected(self):
        """Test recall with no expected docs."""
        recall = compute_context_recall(["doc1"], [])
        assert recall == 1.0

    def test_empty_retrieved(self):
        """Test recall with empty retrieved."""
        recall = compute_context_recall([], ["doc1"])
        assert recall == 0.0


class TestRelevanceScore:
    """Tests for weighted relevance score."""

    def test_single_score(self):
        """Test relevance with single result."""
        score = compute_relevance_score([0.9])
        assert score == 0.9

    def test_decay_effect(self):
        """Test that position decay affects score."""
        # Same scores but later positions should contribute less
        scores = [0.5, 0.9]  # High score in second position
        score = compute_relevance_score(scores, decay_factor=0.5)
        # First position: 0.5 * 1.0 = 0.5
        # Second position: 0.9 * 0.5 = 0.45
        # Total weight: 1.0 + 0.5 = 1.5
        # Score: 0.95 / 1.5 = 0.633...
        assert score < 0.7

    def test_empty_results(self):
        """Test relevance with empty results."""
        score = compute_relevance_score([])
        assert score == 0.0

    def test_custom_decay(self):
        """Test relevance with custom decay factor."""
        scores = [0.8, 0.6]
        score_high_decay = compute_relevance_score(scores, decay_factor=0.5)
        score_low_decay = compute_relevance_score(scores, decay_factor=0.9)
        # Higher decay means later results matter more
        assert score_low_decay < score_high_decay


class TestReciprocalRank:
    """Tests for reciprocal rank metric."""

    def test_first_position(self):
        """Test MRR when relevant doc is first."""
        rr = compute_reciprocal_rank(["doc1", "doc2"], "doc1")
        assert rr == 1.0

    def test_second_position(self):
        """Test MRR when relevant doc is second."""
        rr = compute_reciprocal_rank(["doc1", "doc2"], "doc2")
        assert rr == 0.5

    def test_not_found(self):
        """Test MRR when relevant doc not found."""
        rr = compute_reciprocal_rank(["doc1", "doc2"], "doc3")
        assert rr == 0.0


class TestNDCG:
    """Tests for NDCG metric."""

    def test_perfect_ranking(self):
        """Test NDCG with perfect ranking."""
        scores = [1.0, 0.8, 0.6, 0.4]
        ndcg = compute_ndcg(scores)
        assert ndcg == pytest.approx(1.0)

    def test_reverse_ranking(self):
        """Test NDCG with reversed ranking."""
        scores = [0.4, 0.6, 0.8, 1.0]
        ndcg = compute_ndcg(scores)
        assert ndcg < 1.0

    def test_empty_scores(self):
        """Test NDCG with empty scores."""
        ndcg = compute_ndcg([])
        assert ndcg == 0.0

    def test_k_truncation(self):
        """Test NDCG with k truncation."""
        scores = [1.0, 0.8, 0.6, 0.4]
        ndcg_k2 = compute_ndcg(scores, k=2)
        assert ndcg_k2 == pytest.approx(1.0)


class TestEvaluationConfig:
    """Tests for EvaluationConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = EvaluationConfig()
        assert MetricType.CONTEXT_PRECISION in config.metrics
        assert MetricType.RELEVANCE_SCORE in config.metrics
        assert config.relevance_threshold == 0.5
        assert config.search_limit == 5
        assert config.include_llm_metrics is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = EvaluationConfig(
            metrics=[MetricType.CONTEXT_RECALL],
            relevance_threshold=0.7,
            search_limit=10,
            include_llm_metrics=True,
        )
        assert config.relevance_threshold == 0.7
        assert config.search_limit == 10


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_create_result(self):
        """Test creating evaluation result."""
        metrics = EvaluationMetrics(context_precision=0.8)
        result = EvaluationResult(
            query="test query",
            metrics=metrics,
            retrieved_chunks=5,
            evaluation_time_ms=100.5,
        )
        assert result.query == "test query"
        assert result.metrics.context_precision == 0.8
        assert result.retrieved_chunks == 5

    def test_to_dict(self):
        """Test serialisation."""
        metrics = EvaluationMetrics(context_precision=0.8)
        result = EvaluationResult(
            query="test",
            metrics=metrics,
            retrieved_chunks=3,
        )
        data = result.to_dict()
        assert data["query"] == "test"
        assert "metrics" in data
        assert "timestamp" in data

    def test_from_dict(self):
        """Test deserialisation."""
        data = {
            "query": "test query",
            "metrics": {"context_precision": 0.9},
            "retrieved_chunks": 5,
            "evaluation_time_ms": 50.0,
            "timestamp": datetime.now().isoformat(),
            "config": {},
        }
        result = EvaluationResult.from_dict(data)
        assert result.query == "test query"
        assert result.metrics.context_precision == 0.9


class TestEvaluationReport:
    """Tests for EvaluationReport."""

    def test_empty_report(self):
        """Test empty report."""
        report = EvaluationReport()
        report.compute_summary()
        assert report.summary == {}

    def test_compute_summary(self):
        """Test summary computation."""
        metrics1 = EvaluationMetrics(context_precision=0.8, relevance_score=0.7)
        metrics2 = EvaluationMetrics(context_precision=0.6, relevance_score=0.9)

        report = EvaluationReport(results=[
            EvaluationResult(query="q1", metrics=metrics1, retrieved_chunks=5),
            EvaluationResult(query="q2", metrics=metrics2, retrieved_chunks=5),
        ])
        report.compute_summary()

        assert report.summary["avg_context_precision"] == pytest.approx(0.7)
        assert report.summary["avg_relevance_score"] == pytest.approx(0.8)
        assert report.summary["total_queries"] == 2


class TestEvaluator:
    """Tests for Evaluator class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock ragd config."""
        config = MagicMock()
        return config

    def test_evaluate_no_results(self, mock_config):
        """Test evaluation with no search results."""
        with patch("ragd.evaluation.evaluator.HybridSearcher") as MockSearcher:
            MockSearcher.return_value.search.return_value = []

            evaluator = Evaluator(config=mock_config)
            result = evaluator.evaluate("test query")

            assert result.query == "test query"
            assert result.retrieved_chunks == 0
            assert result.metrics.context_precision == 0.0
            evaluator.close()

    def test_evaluate_with_results(self, mock_config):
        """Test evaluation with search results."""
        with patch("ragd.evaluation.evaluator.HybridSearcher") as MockSearcher:
            # Mock search results
            mock_result = MagicMock()
            mock_result.combined_score = 0.8
            mock_result.document_id = "doc1"
            MockSearcher.return_value.search.return_value = [mock_result]

            evaluator = Evaluator(config=mock_config)
            result = evaluator.evaluate("test query")

            assert result.query == "test query"
            assert result.retrieved_chunks == 1
            assert result.metrics.context_precision == 1.0  # 1 relevant of 1
            evaluator.close()


class TestEvaluationStorage:
    """Tests for EvaluationStorage."""

    def test_save_and_load_result(self):
        """Test saving and loading a result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EvaluationStorage(tmpdir)

            metrics = EvaluationMetrics(context_precision=0.85)
            result = EvaluationResult(
                query="test query",
                metrics=metrics,
                retrieved_chunks=5,
            )

            filepath = storage.save_result(result)
            assert filepath.exists()

            loaded = storage.load_result(filepath)
            assert loaded.query == "test query"
            assert loaded.metrics.context_precision == 0.85

    def test_list_results(self):
        """Test listing results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EvaluationStorage(tmpdir)

            # Save two results - microsecond precision ensures uniqueness
            for i in range(2):
                metrics = EvaluationMetrics(context_precision=0.5 + i * 0.1)
                result = EvaluationResult(
                    query=f"query {i}",
                    metrics=metrics,
                    retrieved_chunks=5,
                )
                storage.save_result(result)

            results = storage.list_results()
            assert len(results) == 2

    def test_list_results_with_limit(self):
        """Test listing results with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EvaluationStorage(tmpdir)

            for i in range(5):
                metrics = EvaluationMetrics()
                result = EvaluationResult(
                    query=f"query {i}",
                    metrics=metrics,
                    retrieved_chunks=5,
                )
                storage.save_result(result)

            results = storage.list_results(limit=3)
            assert len(results) == 3


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_evaluate_query(self):
        """Test evaluate_query function."""
        with patch("ragd.evaluation.evaluator.Evaluator") as MockEvaluator:
            mock_instance = MagicMock()
            mock_instance.evaluate.return_value = EvaluationResult(
                query="test",
                metrics=EvaluationMetrics(context_precision=0.9),
                retrieved_chunks=5,
            )
            MockEvaluator.return_value = mock_instance

            result = evaluate_query("test query")
            assert result.query == "test"
            mock_instance.close.assert_called_once()

    def test_save_evaluation_result(self):
        """Test save_evaluation_result function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = EvaluationMetrics(context_precision=0.7)
            result = EvaluationResult(
                query="test",
                metrics=metrics,
                retrieved_chunks=3,
            )

            filepath = save_evaluation_result(result, storage_dir=tmpdir)
            assert filepath.exists()
