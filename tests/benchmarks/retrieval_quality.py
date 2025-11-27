"""Retrieval quality benchmarks for ragd.

This module provides infrastructure for measuring retrieval quality metrics:
- Precision@K: Fraction of retrieved documents that are relevant
- Recall@K: Fraction of relevant documents that are retrieved
- MRR (Mean Reciprocal Rank): Average of reciprocal ranks of first relevant result
- nDCG (Normalised Discounted Cumulative Gain): Ranking quality metric

Usage:
    python -m pytest tests/benchmarks/retrieval_quality.py -v

    Or run specific benchmark:
    python tests/benchmarks/retrieval_quality.py
"""

from __future__ import annotations

import math
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


@dataclass
class QueryResult:
    """A single query result with relevance judgment."""

    doc_id: str
    score: float
    relevant: bool


@dataclass
class BenchmarkQuery:
    """A benchmark query with expected relevant documents."""

    query: str
    relevant_doc_ids: set[str]
    results: list[QueryResult] = field(default_factory=list)


@dataclass
class BenchmarkMetrics:
    """Computed benchmark metrics."""

    precision_at_k: dict[int, float] = field(default_factory=dict)
    recall_at_k: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    ndcg_at_k: dict[int, float] = field(default_factory=dict)
    avg_precision: float = 0.0

    def summary(self) -> str:
        """Return human-readable summary."""
        lines = [
            "Retrieval Quality Metrics",
            "=" * 30,
        ]

        if self.precision_at_k:
            lines.append("\nPrecision@K:")
            for k, p in sorted(self.precision_at_k.items()):
                lines.append(f"  P@{k}: {p:.4f}")

        if self.recall_at_k:
            lines.append("\nRecall@K:")
            for k, r in sorted(self.recall_at_k.items()):
                lines.append(f"  R@{k}: {r:.4f}")

        lines.append(f"\nMRR: {self.mrr:.4f}")
        lines.append(f"MAP: {self.avg_precision:.4f}")

        if self.ndcg_at_k:
            lines.append("\nnDCG@K:")
            for k, n in sorted(self.ndcg_at_k.items()):
                lines.append(f"  nDCG@{k}: {n:.4f}")

        return "\n".join(lines)


def precision_at_k(results: list[QueryResult], k: int) -> float:
    """Calculate Precision@K.

    Args:
        results: Ordered list of query results
        k: Number of top results to consider

    Returns:
        Precision value (0.0 to 1.0)
    """
    if k <= 0 or not results:
        return 0.0

    top_k = results[:k]
    relevant_count = sum(1 for r in top_k if r.relevant)
    return relevant_count / k


def recall_at_k(
    results: list[QueryResult],
    k: int,
    total_relevant: int,
) -> float:
    """Calculate Recall@K.

    Args:
        results: Ordered list of query results
        k: Number of top results to consider
        total_relevant: Total number of relevant documents

    Returns:
        Recall value (0.0 to 1.0)
    """
    if total_relevant <= 0 or not results:
        return 0.0

    top_k = results[:k]
    relevant_count = sum(1 for r in top_k if r.relevant)
    return relevant_count / total_relevant


def mean_reciprocal_rank(queries: list[BenchmarkQuery]) -> float:
    """Calculate Mean Reciprocal Rank across queries.

    Args:
        queries: List of benchmark queries with results

    Returns:
        MRR value (0.0 to 1.0)
    """
    if not queries:
        return 0.0

    rr_sum = 0.0
    for query in queries:
        for rank, result in enumerate(query.results, start=1):
            if result.relevant:
                rr_sum += 1.0 / rank
                break

    return rr_sum / len(queries)


def average_precision(results: list[QueryResult], total_relevant: int) -> float:
    """Calculate Average Precision for a single query.

    Args:
        results: Ordered list of query results
        total_relevant: Total number of relevant documents

    Returns:
        AP value (0.0 to 1.0)
    """
    if total_relevant <= 0 or not results:
        return 0.0

    ap_sum = 0.0
    relevant_count = 0

    for rank, result in enumerate(results, start=1):
        if result.relevant:
            relevant_count += 1
            ap_sum += relevant_count / rank

    return ap_sum / total_relevant


def dcg_at_k(results: list[QueryResult], k: int) -> float:
    """Calculate Discounted Cumulative Gain at K.

    Args:
        results: Ordered list of query results
        k: Number of top results to consider

    Returns:
        DCG value
    """
    if k <= 0 or not results:
        return 0.0

    dcg = 0.0
    for i, result in enumerate(results[:k]):
        relevance = 1.0 if result.relevant else 0.0
        dcg += relevance / math.log2(i + 2)  # +2 because log2(1) = 0

    return dcg


def ndcg_at_k(results: list[QueryResult], k: int, total_relevant: int) -> float:
    """Calculate Normalised Discounted Cumulative Gain at K.

    Args:
        results: Ordered list of query results
        k: Number of top results to consider
        total_relevant: Total number of relevant documents

    Returns:
        nDCG value (0.0 to 1.0)
    """
    if k <= 0 or not results or total_relevant <= 0:
        return 0.0

    # Calculate actual DCG
    dcg = dcg_at_k(results, k)

    # Calculate ideal DCG (all relevant documents at top)
    ideal_results = [QueryResult("ideal", 1.0, True)] * min(k, total_relevant)
    ideal_dcg = dcg_at_k(ideal_results, k)

    if ideal_dcg == 0:
        return 0.0

    return dcg / ideal_dcg


def compute_metrics(
    queries: list[BenchmarkQuery],
    k_values: list[int] | None = None,
) -> BenchmarkMetrics:
    """Compute all metrics for a set of benchmark queries.

    Args:
        queries: List of benchmark queries with results
        k_values: K values to compute metrics for (default: [1, 3, 5, 10])

    Returns:
        BenchmarkMetrics with all computed values
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    metrics = BenchmarkMetrics()

    if not queries:
        return metrics

    # Aggregate metrics across queries
    for k in k_values:
        p_sum = 0.0
        r_sum = 0.0
        ndcg_sum = 0.0

        for query in queries:
            total_relevant = len(query.relevant_doc_ids)
            p_sum += precision_at_k(query.results, k)
            r_sum += recall_at_k(query.results, k, total_relevant)
            ndcg_sum += ndcg_at_k(query.results, k, total_relevant)

        metrics.precision_at_k[k] = p_sum / len(queries)
        metrics.recall_at_k[k] = r_sum / len(queries)
        metrics.ndcg_at_k[k] = ndcg_sum / len(queries)

    # MRR
    metrics.mrr = mean_reciprocal_rank(queries)

    # MAP (Mean Average Precision)
    ap_sum = 0.0
    for query in queries:
        total_relevant = len(query.relevant_doc_ids)
        ap_sum += average_precision(query.results, total_relevant)
    metrics.avg_precision = ap_sum / len(queries)

    return metrics


# ============================================================================
# Test Cases
# ============================================================================


class TestMetricCalculations:
    """Tests for metric calculation functions."""

    def test_precision_at_k(self) -> None:
        """Test Precision@K calculation."""
        results = [
            QueryResult("1", 0.9, True),
            QueryResult("2", 0.8, True),
            QueryResult("3", 0.7, False),
            QueryResult("4", 0.6, True),
            QueryResult("5", 0.5, False),
        ]

        assert precision_at_k(results, 1) == 1.0  # 1/1
        assert precision_at_k(results, 2) == 1.0  # 2/2
        assert precision_at_k(results, 3) == pytest.approx(2 / 3)  # 2/3
        assert precision_at_k(results, 5) == pytest.approx(3 / 5)  # 3/5

    def test_recall_at_k(self) -> None:
        """Test Recall@K calculation."""
        results = [
            QueryResult("1", 0.9, True),
            QueryResult("2", 0.8, True),
            QueryResult("3", 0.7, False),
        ]

        # 4 total relevant documents
        assert recall_at_k(results, 1, 4) == 0.25  # 1/4
        assert recall_at_k(results, 2, 4) == 0.5  # 2/4
        assert recall_at_k(results, 3, 4) == 0.5  # 2/4 (only 2 relevant in results)

    def test_mrr(self) -> None:
        """Test Mean Reciprocal Rank calculation."""
        queries = [
            BenchmarkQuery(
                query="query 1",
                relevant_doc_ids={"1"},
                results=[
                    QueryResult("1", 0.9, True),  # rank 1
                    QueryResult("2", 0.8, False),
                ],
            ),
            BenchmarkQuery(
                query="query 2",
                relevant_doc_ids={"2"},
                results=[
                    QueryResult("1", 0.9, False),
                    QueryResult("2", 0.8, True),  # rank 2
                ],
            ),
        ]

        # MRR = (1/1 + 1/2) / 2 = 0.75
        assert mean_reciprocal_rank(queries) == pytest.approx(0.75)

    def test_average_precision(self) -> None:
        """Test Average Precision calculation."""
        results = [
            QueryResult("1", 0.9, True),  # P@1 = 1/1
            QueryResult("2", 0.8, False),
            QueryResult("3", 0.7, True),  # P@3 = 2/3
            QueryResult("4", 0.6, False),
            QueryResult("5", 0.5, True),  # P@5 = 3/5
        ]

        # AP = (1/1 + 2/3 + 3/5) / 3 = (1 + 0.667 + 0.6) / 3 = 0.756
        assert average_precision(results, 3) == pytest.approx((1 + 2 / 3 + 3 / 5) / 3)

    def test_ndcg_at_k(self) -> None:
        """Test nDCG@K calculation."""
        results = [
            QueryResult("1", 0.9, True),
            QueryResult("2", 0.8, False),
            QueryResult("3", 0.7, True),
        ]

        # DCG@3 = 1/log2(2) + 0/log2(3) + 1/log2(4) = 1 + 0 + 0.5 = 1.5
        # IDCG@3 = 1/log2(2) + 1/log2(3) = 1 + 0.63 = 1.63 (if 2 relevant)
        ndcg = ndcg_at_k(results, 3, 2)
        assert 0 <= ndcg <= 1

    def test_compute_metrics(self) -> None:
        """Test complete metrics computation."""
        queries = [
            BenchmarkQuery(
                query="test query",
                relevant_doc_ids={"1", "3"},
                results=[
                    QueryResult("1", 0.9, True),
                    QueryResult("2", 0.8, False),
                    QueryResult("3", 0.7, True),
                ],
            )
        ]

        metrics = compute_metrics(queries, k_values=[1, 3])

        assert metrics.precision_at_k[1] == 1.0
        assert metrics.precision_at_k[3] == pytest.approx(2 / 3)
        assert metrics.mrr == 1.0  # First result is relevant
        assert metrics.avg_precision > 0


class TestBenchmarkInfrastructure:
    """Tests for benchmark infrastructure."""

    def test_metrics_summary(self) -> None:
        """Test metrics summary generation."""
        metrics = BenchmarkMetrics(
            precision_at_k={1: 0.8, 5: 0.6},
            recall_at_k={1: 0.2, 5: 0.4},
            mrr=0.75,
            ndcg_at_k={1: 0.8, 5: 0.7},
            avg_precision=0.65,
        )

        summary = metrics.summary()

        assert "Precision@K" in summary
        assert "Recall@K" in summary
        assert "MRR: 0.7500" in summary
        assert "MAP: 0.6500" in summary
        assert "nDCG@K" in summary

    def test_empty_queries(self) -> None:
        """Test metrics with empty queries."""
        metrics = compute_metrics([])

        assert metrics.mrr == 0.0
        assert metrics.avg_precision == 0.0
        assert metrics.precision_at_k == {}


if __name__ == "__main__":
    # Run quick verification
    print("Running benchmark metric verification...")

    queries = [
        BenchmarkQuery(
            query="python programming",
            relevant_doc_ids={"doc-1", "doc-3", "doc-5"},
            results=[
                QueryResult("doc-1", 0.95, True),
                QueryResult("doc-2", 0.85, False),
                QueryResult("doc-3", 0.80, True),
                QueryResult("doc-4", 0.75, False),
                QueryResult("doc-5", 0.70, True),
            ],
        ),
        BenchmarkQuery(
            query="data science",
            relevant_doc_ids={"doc-6", "doc-8"},
            results=[
                QueryResult("doc-7", 0.90, False),
                QueryResult("doc-6", 0.85, True),
                QueryResult("doc-8", 0.80, True),
            ],
        ),
    ]

    metrics = compute_metrics(queries)
    print(metrics.summary())
