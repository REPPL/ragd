"""Evaluation metrics for ragd.

Implements retrieval and generation quality metrics inspired by RAGAS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricType(str, Enum):
    """Types of evaluation metrics."""

    # Retrieval metrics (no LLM required)
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    RELEVANCE_SCORE = "relevance_score"

    # Generation metrics (requires LLM)
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"


@dataclass
class EvaluationMetrics:
    """Collection of evaluation metrics.

    Attributes:
        context_precision: Precision of retrieved context (0-1)
        context_recall: Recall of relevant context (0-1, requires ground truth)
        relevance_score: Average relevance score of retrieved chunks (0-1)
        faithfulness: How grounded the answer is in context (0-1, requires LLM)
        answer_relevancy: How well answer addresses the question (0-1, requires LLM)
    """

    context_precision: float | None = None
    context_recall: float | None = None
    relevance_score: float | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        """Calculate overall score as weighted average of available metrics."""
        scores = []
        weights = []

        # Add retrieval metrics with weight 0.4
        if self.context_precision is not None:
            scores.append(self.context_precision)
            weights.append(0.3)

        if self.context_recall is not None:
            scores.append(self.context_recall)
            weights.append(0.2)

        if self.relevance_score is not None:
            scores.append(self.relevance_score)
            weights.append(0.2)

        # Add generation metrics with weight 0.6
        if self.faithfulness is not None:
            scores.append(self.faithfulness)
            weights.append(0.15)

        if self.answer_relevancy is not None:
            scores.append(self.answer_relevancy)
            weights.append(0.15)

        if not scores:
            return 0.0

        # Normalise weights
        total_weight = sum(weights)
        normalised_weights = [w / total_weight for w in weights]

        return sum(s * w for s, w in zip(scores, normalised_weights, strict=False))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "relevance_score": self.relevance_score,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "overall_score": self.overall_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationMetrics":
        """Create from dictionary."""
        return cls(
            context_precision=data.get("context_precision"),
            context_recall=data.get("context_recall"),
            relevance_score=data.get("relevance_score"),
            faithfulness=data.get("faithfulness"),
            answer_relevancy=data.get("answer_relevancy"),
            metadata=data.get("metadata", {}),
        )


def compute_context_precision(
    retrieved_scores: list[float],
    relevance_threshold: float = 0.5,
) -> float:
    """Compute context precision from retrieval scores.

    Measures the proportion of retrieved chunks that are relevant.

    Args:
        retrieved_scores: List of relevance scores for retrieved chunks
        relevance_threshold: Minimum score to consider a chunk relevant

    Returns:
        Precision score (0-1)
    """
    if not retrieved_scores:
        return 0.0

    relevant_count = sum(1 for score in retrieved_scores if score >= relevance_threshold)
    return relevant_count / len(retrieved_scores)


def compute_context_recall(
    retrieved_docs: list[str],
    expected_docs: list[str],
) -> float:
    """Compute context recall against expected documents.

    Measures the proportion of expected relevant documents that were retrieved.

    Args:
        retrieved_docs: List of retrieved document identifiers
        expected_docs: List of expected relevant document identifiers

    Returns:
        Recall score (0-1)
    """
    if not expected_docs:
        return 1.0  # No expected docs means nothing to recall

    if not retrieved_docs:
        return 0.0

    retrieved_set = set(retrieved_docs)
    expected_set = set(expected_docs)

    intersection = retrieved_set & expected_set
    return len(intersection) / len(expected_set)


def compute_relevance_score(
    retrieved_scores: list[float],
    decay_factor: float = 0.9,
) -> float:
    """Compute weighted relevance score with position decay.

    Higher ranked results contribute more to the overall score.

    Args:
        retrieved_scores: List of relevance scores (in rank order)
        decay_factor: Decay multiplier for each position (0-1)

    Returns:
        Weighted relevance score (0-1)
    """
    if not retrieved_scores:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0

    for i, score in enumerate(retrieved_scores):
        position_weight = decay_factor ** i
        weighted_sum += score * position_weight
        weight_total += position_weight

    return weighted_sum / weight_total if weight_total > 0 else 0.0


def compute_reciprocal_rank(
    retrieved_docs: list[str],
    relevant_doc: str,
) -> float:
    """Compute Mean Reciprocal Rank (MRR) for a single query.

    Args:
        retrieved_docs: List of retrieved document identifiers (in rank order)
        relevant_doc: The expected relevant document

    Returns:
        Reciprocal rank (1/position) or 0 if not found
    """
    try:
        position = retrieved_docs.index(relevant_doc) + 1  # 1-indexed
        return 1.0 / position
    except ValueError:
        return 0.0


def compute_ndcg(
    retrieved_scores: list[float],
    ideal_scores: list[float] | None = None,
    k: int | None = None,
) -> float:
    """Compute Normalised Discounted Cumulative Gain (NDCG).

    Measures ranking quality considering both relevance and position.

    Args:
        retrieved_scores: Relevance scores in retrieval order
        ideal_scores: Ideal relevance scores (sorted descending). If None, uses
                      sorted retrieved_scores as ideal.
        k: Number of top results to consider. If None, uses all.

    Returns:
        NDCG score (0-1)
    """
    import math

    if not retrieved_scores:
        return 0.0

    if k is not None:
        retrieved_scores = retrieved_scores[:k]

    if ideal_scores is None:
        ideal_scores = sorted(retrieved_scores, reverse=True)
    else:
        ideal_scores = sorted(ideal_scores, reverse=True)
        if k is not None:
            ideal_scores = ideal_scores[:k]

    def dcg(scores: list[float]) -> float:
        """Compute Discounted Cumulative Gain."""
        return sum(
            score / math.log2(i + 2)  # i+2 because log2(1) = 0
            for i, score in enumerate(scores)
        )

    actual_dcg = dcg(retrieved_scores)
    ideal_dcg = dcg(ideal_scores)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg
