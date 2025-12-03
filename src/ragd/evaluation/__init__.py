"""Evaluation module for ragd.

Provides metrics for measuring RAG system quality including:
- Context Precision: Are retrieved docs relevant to the query?
- Context Recall: Were all relevant docs retrieved?
- Faithfulness: Is response grounded in retrieved context?
- Answer Relevancy: Does answer address the question?
"""

from ragd.evaluation.metrics import (
    EvaluationMetrics,
    MetricType,
    compute_context_precision,
    compute_context_recall,
    compute_relevance_score,
    compute_faithfulness,
    compute_answer_relevancy,
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
    load_evaluation_history,
    save_evaluation_result,
)

__all__ = [
    # Metrics
    "EvaluationMetrics",
    "MetricType",
    "compute_context_precision",
    "compute_context_recall",
    "compute_relevance_score",
    "compute_faithfulness",
    "compute_answer_relevancy",
    # Evaluator
    "Evaluator",
    "EvaluationConfig",
    "EvaluationResult",
    "EvaluationReport",
    "evaluate_query",
    # Storage
    "EvaluationStorage",
    "load_evaluation_history",
    "save_evaluation_result",
]
