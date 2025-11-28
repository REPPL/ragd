"""Evaluation engine for ragd.

Orchestrates evaluation of RAG queries with configurable metrics.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ragd.config import RagdConfig, load_config
from ragd.evaluation.metrics import (
    EvaluationMetrics,
    MetricType,
    compute_context_precision,
    compute_context_recall,
    compute_relevance_score,
)
from ragd.search.hybrid import HybridSearcher, SearchMode


@dataclass
class EvaluationConfig:
    """Configuration for evaluation.

    Attributes:
        metrics: List of metrics to compute
        relevance_threshold: Threshold for considering a chunk relevant
        search_limit: Number of chunks to retrieve for evaluation
        include_llm_metrics: Whether to compute LLM-based metrics
    """

    metrics: list[MetricType] = field(
        default_factory=lambda: [
            MetricType.CONTEXT_PRECISION,
            MetricType.RELEVANCE_SCORE,
        ]
    )
    relevance_threshold: float = 0.5
    search_limit: int = 5
    include_llm_metrics: bool = False


@dataclass
class EvaluationResult:
    """Result of evaluating a single query.

    Attributes:
        query: The evaluated query
        metrics: Computed metrics
        retrieved_chunks: Number of chunks retrieved
        answer: Generated answer (if any)
        evaluation_time_ms: Time taken for evaluation
        timestamp: When evaluation was performed
        config: Evaluation configuration used
    """

    query: str
    metrics: EvaluationMetrics
    retrieved_chunks: int
    answer: str | None = None
    expected_answer: str | None = None
    expected_docs: list[str] | None = None
    evaluation_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "query": self.query,
            "metrics": self.metrics.to_dict(),
            "retrieved_chunks": self.retrieved_chunks,
            "answer": self.answer,
            "expected_answer": self.expected_answer,
            "expected_docs": self.expected_docs,
            "evaluation_time_ms": self.evaluation_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationResult":
        """Create from dictionary."""
        return cls(
            query=data["query"],
            metrics=EvaluationMetrics.from_dict(data["metrics"]),
            retrieved_chunks=data["retrieved_chunks"],
            answer=data.get("answer"),
            expected_answer=data.get("expected_answer"),
            expected_docs=data.get("expected_docs"),
            evaluation_time_ms=data.get("evaluation_time_ms", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            config=data.get("config", {}),
        )


@dataclass
class EvaluationReport:
    """Report containing multiple evaluation results.

    Attributes:
        results: List of individual evaluation results
        summary: Aggregated metrics across all results
        comparison: Comparison with previous evaluation (if available)
    """

    results: list[EvaluationResult] = field(default_factory=list)
    summary: dict[str, float] = field(default_factory=dict)
    comparison: dict[str, float] | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def compute_summary(self) -> None:
        """Compute summary statistics from results."""
        if not self.results:
            self.summary = {}
            return

        # Aggregate metrics
        precision_scores = []
        recall_scores = []
        relevance_scores = []
        overall_scores = []

        for result in self.results:
            if result.metrics.context_precision is not None:
                precision_scores.append(result.metrics.context_precision)
            if result.metrics.context_recall is not None:
                recall_scores.append(result.metrics.context_recall)
            if result.metrics.relevance_score is not None:
                relevance_scores.append(result.metrics.relevance_score)
            overall_scores.append(result.metrics.overall_score)

        def safe_avg(scores: list[float]) -> float | None:
            return sum(scores) / len(scores) if scores else None

        self.summary = {
            "avg_context_precision": safe_avg(precision_scores),
            "avg_context_recall": safe_avg(recall_scores),
            "avg_relevance_score": safe_avg(relevance_scores),
            "avg_overall_score": safe_avg(overall_scores),
            "total_queries": len(self.results),
            "avg_evaluation_time_ms": safe_avg(
                [r.evaluation_time_ms for r in self.results]
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "comparison": self.comparison,
            "timestamp": self.timestamp.isoformat(),
        }


class Evaluator:
    """Evaluator for RAG queries."""

    def __init__(
        self,
        config: RagdConfig | None = None,
        eval_config: EvaluationConfig | None = None,
    ) -> None:
        """Initialise evaluator.

        Args:
            config: ragd configuration
            eval_config: Evaluation configuration
        """
        self.config = config or load_config()
        self.eval_config = eval_config or EvaluationConfig()
        self._searcher = HybridSearcher(config=self.config)

    def evaluate(
        self,
        query: str,
        expected_answer: str | None = None,
        expected_docs: list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate a single query.

        Args:
            query: Query to evaluate
            expected_answer: Expected answer for recall computation
            expected_docs: Expected relevant document IDs for recall

        Returns:
            EvaluationResult with computed metrics
        """
        start_time = time.time()

        # Retrieve results
        results = self._searcher.search(
            query=query,
            limit=self.eval_config.search_limit,
            mode=SearchMode.HYBRID,
        )

        # Extract scores and document IDs
        scores = [r.combined_score for r in results]
        doc_ids = [r.document_id for r in results]

        # Compute metrics
        metrics = EvaluationMetrics()

        if MetricType.CONTEXT_PRECISION in self.eval_config.metrics:
            metrics.context_precision = compute_context_precision(
                scores, self.eval_config.relevance_threshold
            )

        if MetricType.CONTEXT_RECALL in self.eval_config.metrics and expected_docs:
            metrics.context_recall = compute_context_recall(doc_ids, expected_docs)

        if MetricType.RELEVANCE_SCORE in self.eval_config.metrics:
            metrics.relevance_score = compute_relevance_score(scores)

        # LLM-based metrics (Phase 2)
        if self.eval_config.include_llm_metrics:
            # TODO: Implement faithfulness and answer_relevancy
            pass

        evaluation_time = (time.time() - start_time) * 1000

        return EvaluationResult(
            query=query,
            metrics=metrics,
            retrieved_chunks=len(results),
            expected_answer=expected_answer,
            expected_docs=expected_docs,
            evaluation_time_ms=evaluation_time,
            config={
                "search_limit": self.eval_config.search_limit,
                "relevance_threshold": self.eval_config.relevance_threshold,
                "metrics": [m.value for m in self.eval_config.metrics],
            },
        )

    def evaluate_batch(
        self,
        queries: list[dict[str, Any]],
    ) -> EvaluationReport:
        """Evaluate a batch of queries.

        Args:
            queries: List of query dictionaries with keys:
                     - query (required)
                     - expected_answer (optional)
                     - expected_docs (optional)

        Returns:
            EvaluationReport with all results and summary
        """
        report = EvaluationReport()

        for query_data in queries:
            query = query_data["query"]
            expected_answer = query_data.get("expected_answer")
            expected_docs = query_data.get("expected_docs")

            result = self.evaluate(
                query=query,
                expected_answer=expected_answer,
                expected_docs=expected_docs,
            )
            report.results.append(result)

        report.compute_summary()
        return report

    def close(self) -> None:
        """Close resources."""
        self._searcher.close()


def evaluate_query(
    query: str,
    config: RagdConfig | None = None,
    expected_answer: str | None = None,
    expected_docs: list[str] | None = None,
) -> EvaluationResult:
    """Convenience function to evaluate a single query.

    Args:
        query: Query to evaluate
        config: ragd configuration
        expected_answer: Expected answer for comparison
        expected_docs: Expected relevant document IDs

    Returns:
        EvaluationResult with computed metrics
    """
    evaluator = Evaluator(config=config)
    try:
        return evaluator.evaluate(
            query=query,
            expected_answer=expected_answer,
            expected_docs=expected_docs,
        )
    finally:
        evaluator.close()
