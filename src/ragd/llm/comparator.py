"""Model comparison for ragd (F-057).

Provides comparison of outputs from multiple LLM models,
with optional judge evaluation and ensemble modes.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ragd.llm.ollama import OllamaClient, OllamaError

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    """Response from a single model."""

    model: str
    response: str
    time_ms: float
    tokens: int
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "response": self.response,
            "time_ms": self.time_ms,
            "tokens": self.tokens,
            "error": self.error,
        }


@dataclass
class JudgeScore:
    """Score from judge evaluation."""

    accuracy: int  # 1-5
    completeness: int  # 1-5
    clarity: int  # 1-5
    citations: int  # 1-5

    @property
    def total(self) -> int:
        """Total score out of 20."""
        return self.accuracy + self.completeness + self.clarity + self.citations

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "clarity": self.clarity,
            "citations": self.citations,
            "total": self.total,
        }


@dataclass
class JudgeEvaluation:
    """Evaluation from judge model."""

    winner: str  # "A", "B", or "tie"
    scores: dict[str, JudgeScore]  # model -> scores
    reasoning: str
    judge_model: str
    time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "winner": self.winner,
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "reasoning": self.reasoning,
            "judge_model": self.judge_model,
            "time_ms": self.time_ms,
        }


@dataclass
class ComparisonResult:
    """Result of model comparison."""

    query: str
    context: str
    responses: list[ModelResponse]
    evaluation: JudgeEvaluation | None = None
    ensemble_winner: str | None = None
    ensemble_votes: list[str] = field(default_factory=list)
    ensemble_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "context": self.context[:200] + "..." if len(self.context) > 200 else self.context,
            "responses": [r.to_dict() for r in self.responses],
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "ensemble_winner": self.ensemble_winner,
            "ensemble_votes": self.ensemble_votes,
            "ensemble_confidence": self.ensemble_confidence,
        }


# Judge prompt template
JUDGE_PROMPT = """You are evaluating responses from different language models.

Question: {question}

Context provided:
{context}

---

Response A ({model_a}):
{response_a}

---

Response B ({model_b}):
{response_b}

---

Evaluate which response better answers the question based on:
1. Accuracy - Does it correctly use information from the context?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it well-structured and easy to understand?
4. Citations - Does it reference source material?

You MUST respond in this exact JSON format:
{{
    "winner": "A" or "B" or "tie",
    "scores": {{
        "A": {{"accuracy": 1-5, "completeness": 1-5, "clarity": 1-5, "citations": 1-5}},
        "B": {{"accuracy": 1-5, "completeness": 1-5, "clarity": 1-5, "citations": 1-5}}
    }},
    "reasoning": "Brief explanation of the decision"
}}
"""


class ModelComparator:
    """Compare outputs from multiple LLM models.

    Supports:
    - Side-by-side comparison
    - Judge evaluation
    - Ensemble voting

    Example:
        >>> comparator = ModelComparator()
        >>> result = comparator.compare(
        ...     query="What is RAG?",
        ...     models=["llama3.2:3b", "qwen2.5:3b"],
        ...     context="RAG is..."
        ... )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 120,
    ) -> None:
        """Initialise comparator.

        Args:
            base_url: Ollama API base URL
            timeout_seconds: Request timeout
        """
        self.base_url = base_url
        self.timeout = timeout_seconds

    def compare(
        self,
        query: str,
        models: list[str],
        context: str = "",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ComparisonResult:
        """Compare responses from multiple models.

        Args:
            query: User query
            models: List of model names to compare
            context: Optional context to include
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response

        Returns:
            ComparisonResult with all responses
        """
        responses: list[ModelResponse] = []

        for model in models:
            response = self._query_model(
                model=model,
                query=query,
                context=context,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            responses.append(response)

        return ComparisonResult(
            query=query,
            context=context,
            responses=responses,
        )

    def compare_with_judge(
        self,
        query: str,
        models: list[str],
        judge_model: str,
        context: str = "",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ComparisonResult:
        """Compare models with judge evaluation.

        Args:
            query: User query
            models: List of model names to compare (max 2)
            judge_model: Model to use as judge
            context: Optional context
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response

        Returns:
            ComparisonResult with evaluation
        """
        if len(models) < 2:
            raise ValueError("Need at least 2 models for comparison")
        if len(models) > 2:
            logger.warning("Judge mode only compares first 2 models")
            models = models[:2]

        # Get responses
        result = self.compare(
            query=query,
            models=models,
            context=context,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Get judge evaluation
        evaluation = self._get_judgment(
            judge_model=judge_model,
            query=query,
            context=context,
            response_a=result.responses[0],
            response_b=result.responses[1],
        )

        result.evaluation = evaluation
        return result

    def compare_ensemble(
        self,
        query: str,
        models: list[str],
        context: str = "",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ComparisonResult:
        """Compare models using ensemble voting.

        Each model votes on the best response from other models.

        Args:
            query: User query
            models: List of model names (min 3 recommended)
            context: Optional context
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response

        Returns:
            ComparisonResult with ensemble winner
        """
        if len(models) < 2:
            raise ValueError("Need at least 2 models for ensemble")

        # Get responses
        result = self.compare(
            query=query,
            models=models,
            context=context,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Have each model vote on responses
        votes = []
        for voter_model in models:
            # Skip models that errored
            for i, resp_a in enumerate(result.responses):
                for j, resp_b in enumerate(result.responses):
                    if i < j and not resp_a.error and not resp_b.error:
                        vote = self._get_vote(
                            voter_model=voter_model,
                            query=query,
                            context=context,
                            response_a=resp_a,
                            response_b=resp_b,
                        )
                        if vote == "A":
                            votes.append(resp_a.model)
                        elif vote == "B":
                            votes.append(resp_b.model)

        # Count votes
        if votes:
            vote_counts = {}
            for v in votes:
                vote_counts[v] = vote_counts.get(v, 0) + 1

            winner = max(vote_counts, key=lambda k: vote_counts[k])
            confidence = vote_counts[winner] / len(votes)

            result.ensemble_winner = winner
            result.ensemble_votes = votes
            result.ensemble_confidence = confidence

        return result

    def _query_model(
        self,
        model: str,
        query: str,
        context: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int | None,
    ) -> ModelResponse:
        """Query a single model.

        Args:
            model: Model name
            query: User query
            context: Context to include
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Max tokens

        Returns:
            ModelResponse with response or error
        """
        client = OllamaClient(
            base_url=self.base_url,
            model=model,
            timeout_seconds=self.timeout,
        )

        # Build prompt with context
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {query}"
        else:
            prompt = query

        start = time.perf_counter()
        try:
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            time_ms = (time.perf_counter() - start) * 1000

            return ModelResponse(
                model=model,
                response=response.content,
                time_ms=time_ms,
                tokens=response.tokens_used or 0,
            )

        except OllamaError as e:
            time_ms = (time.perf_counter() - start) * 1000
            return ModelResponse(
                model=model,
                response="",
                time_ms=time_ms,
                tokens=0,
                error=str(e),
            )

    def _get_judgment(
        self,
        judge_model: str,
        query: str,
        context: str,
        response_a: ModelResponse,
        response_b: ModelResponse,
    ) -> JudgeEvaluation:
        """Get judge evaluation.

        Args:
            judge_model: Model to use as judge
            query: Original query
            context: Original context
            response_a: First response
            response_b: Second response

        Returns:
            JudgeEvaluation with scores and reasoning
        """
        client = OllamaClient(
            base_url=self.base_url,
            model=judge_model,
            timeout_seconds=self.timeout,
        )

        prompt = JUDGE_PROMPT.format(
            question=query,
            context=context or "(No context provided)",
            model_a=response_a.model,
            response_a=response_a.response or "(Error - no response)",
            model_b=response_b.model,
            response_b=response_b.response or "(Error - no response)",
        )

        start = time.perf_counter()
        try:
            response = client.generate(
                prompt=prompt,
                temperature=0.0,  # Deterministic for judging
                max_tokens=500,
            )
            time_ms = (time.perf_counter() - start) * 1000

            # Parse JSON from response
            evaluation = self._parse_judge_response(
                response.content,
                response_a.model,
                response_b.model,
            )
            evaluation.judge_model = judge_model
            evaluation.time_ms = time_ms
            return evaluation

        except Exception as e:
            logger.error("Judge evaluation failed: %s", e)
            time_ms = (time.perf_counter() - start) * 1000
            return JudgeEvaluation(
                winner="tie",
                scores={
                    response_a.model: JudgeScore(3, 3, 3, 3),
                    response_b.model: JudgeScore(3, 3, 3, 3),
                },
                reasoning=f"Evaluation failed: {e}",
                judge_model=judge_model,
                time_ms=time_ms,
            )

    def _parse_judge_response(
        self,
        content: str,
        model_a: str,
        model_b: str,
    ) -> JudgeEvaluation:
        """Parse judge response JSON.

        Args:
            content: Raw response content
            model_a: First model name
            model_b: Second model name

        Returns:
            Parsed JudgeEvaluation
        """
        # Try to find JSON in response
        try:
            # Find JSON object in response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)

                winner = data.get("winner", "tie")
                scores_data = data.get("scores", {})
                reasoning = data.get("reasoning", "")

                scores = {}
                for label, model in [("A", model_a), ("B", model_b)]:
                    model_scores = scores_data.get(label, {})
                    scores[model] = JudgeScore(
                        accuracy=model_scores.get("accuracy", 3),
                        completeness=model_scores.get("completeness", 3),
                        clarity=model_scores.get("clarity", 3),
                        citations=model_scores.get("citations", 3),
                    )

                return JudgeEvaluation(
                    winner=winner,
                    scores=scores,
                    reasoning=reasoning,
                    judge_model="",  # Set by caller
                )

        except json.JSONDecodeError:
            pass

        # Default if parsing fails
        return JudgeEvaluation(
            winner="tie",
            scores={
                model_a: JudgeScore(3, 3, 3, 3),
                model_b: JudgeScore(3, 3, 3, 3),
            },
            reasoning="Could not parse judge response",
            judge_model="",
        )

    def _get_vote(
        self,
        voter_model: str,
        query: str,
        context: str,
        response_a: ModelResponse,
        response_b: ModelResponse,
    ) -> str:
        """Get a single vote from a model.

        Args:
            voter_model: Model voting
            query: Original query
            context: Original context
            response_a: First response
            response_b: Second response

        Returns:
            "A", "B", or "tie"
        """
        evaluation = self._get_judgment(
            judge_model=voter_model,
            query=query,
            context=context,
            response_a=response_a,
            response_b=response_b,
        )
        return evaluation.winner


def get_available_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Get list of available Ollama models.

    Args:
        base_url: Ollama API URL

    Returns:
        List of model names
    """
    client = OllamaClient(base_url=base_url)
    try:
        return client.list_models()
    except OllamaError:
        return []
