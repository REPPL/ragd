"""Evaluation metrics for ragd.

Implements retrieval and generation quality metrics inspired by RAGAS.

v1.0.5: Configuration exposure - prompts and parameters now configurable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from ragd.prompts import get_prompt
from ragd.prompts.defaults import (
    EVALUATION_FAITHFULNESS_PROMPT as DEFAULT_FAITHFULNESS,
    EVALUATION_RELEVANCY_PROMPT as DEFAULT_RELEVANCY,
)

if TYPE_CHECKING:
    from ragd.config import RagdConfig


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
    def from_dict(cls, data: dict[str, Any]) -> EvaluationMetrics:
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
    decay_factor: float | None = None,
    config: RagdConfig | None = None,
) -> float:
    """Compute weighted relevance score with position decay.

    Higher ranked results contribute more to the overall score.

    Args:
        retrieved_scores: List of relevance scores (in rank order)
        decay_factor: Decay multiplier for each position (0-1). If None, uses config.
        config: Optional ragd config for parameters

    Returns:
        Weighted relevance score (0-1)
    """
    # Resolve decay factor from config or default
    if decay_factor is None:
        if config is not None:
            decay_factor = config.search_tuning.position_decay_factor
        else:
            decay_factor = 0.9  # Default
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


# Note: Default prompts are now in ragd.prompts.defaults
# Custom prompts can be configured via config.yaml or prompt files


def compute_faithfulness(
    question: str,
    answer: str,
    context: str,
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2:3b",
    config: RagdConfig | None = None,
) -> float | None:
    """Compute faithfulness score using LLM.

    Measures how grounded the answer is in the provided context.
    No hallucinations = high faithfulness.

    Args:
        question: The user's question
        answer: The generated answer
        context: The retrieved context
        base_url: Ollama API base URL
        model: Model to use for evaluation
        config: Optional ragd config for prompts and parameters

    Returns:
        Faithfulness score (0-1), or None if LLM unavailable
    """
    # Load prompt from config or defaults
    if config is not None:
        prompt_template = get_prompt(
            config.evaluation_prompts.faithfulness,
            DEFAULT_FAITHFULNESS,
            category="evaluation",
            name="faithfulness",
        )
        truncation = config.processing.context_truncation_chars
    else:
        prompt_template = DEFAULT_FAITHFULNESS
        truncation = 2000

    return _call_llm_for_score(
        prompt=prompt_template.format(
            context=context[:truncation],
            question=question,
            answer=answer,
        ),
        base_url=base_url,
        model=model,
    )


def compute_answer_relevancy(
    question: str,
    answer: str,
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2:3b",
    config: RagdConfig | None = None,
) -> float | None:
    """Compute answer relevancy score using LLM.

    Measures how well the answer addresses the question.

    Args:
        question: The user's question
        answer: The generated answer
        base_url: Ollama API base URL
        model: Model to use for evaluation
        config: Optional ragd config for prompts

    Returns:
        Relevancy score (0-1), or None if LLM unavailable
    """
    # Load prompt from config or defaults
    if config is not None:
        prompt_template = get_prompt(
            config.evaluation_prompts.answer_relevancy,
            DEFAULT_RELEVANCY,
            category="evaluation",
            name="answer_relevancy",
        )
    else:
        prompt_template = DEFAULT_RELEVANCY

    return _call_llm_for_score(
        prompt=prompt_template.format(
            question=question,
            answer=answer,
        ),
        base_url=base_url,
        model=model,
    )


def _call_llm_for_score(
    prompt: str,
    base_url: str,
    model: str,
) -> float | None:
    """Call LLM and parse numeric score from response.

    Args:
        prompt: The evaluation prompt
        base_url: Ollama API base URL
        model: Model to use

    Returns:
        Parsed score (0-1), or None if failed
    """
    import json
    import urllib.request

    try:
        url = f"{base_url}/api/generate"
        data = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Deterministic for evaluation
                "num_predict": 10,  # Only need a short response
            },
        }).encode()

        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode())
            response_text = result.get("response", "").strip()

            # Parse the numeric response
            return _parse_score(response_text)

    except Exception:
        # Graceful degradation - return None if LLM unavailable
        return None


def _parse_score(response: str) -> float | None:
    """Parse a numeric score from LLM response.

    Args:
        response: The LLM response text

    Returns:
        Parsed score (0-1), or None if invalid
    """
    import re

    # Try to extract a decimal number
    match = re.search(r"(\d+\.?\d*)", response)
    if match:
        try:
            score = float(match.group(1))
            # Clamp to 0-1 range
            return max(0.0, min(1.0, score))
        except ValueError:
            return None
    return None
