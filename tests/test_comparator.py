"""Tests for F-057: Model Comparison Mode.

Tests the model comparator and comparison formatter.
"""

from __future__ import annotations

import json
import pytest

from ragd.llm.comparator import (
    ModelResponse,
    JudgeScore,
    JudgeEvaluation,
    ComparisonResult,
    ModelComparator,
    JUDGE_PROMPT,
)


class TestModelResponse:
    """Test ModelResponse dataclass."""

    def test_response_creation(self) -> None:
        """ModelResponse should be created correctly."""
        response = ModelResponse(
            model="llama3.2:3b",
            response="This is a test response.",
            time_ms=150.5,
            tokens=42,
        )

        assert response.model == "llama3.2:3b"
        assert response.response == "This is a test response."
        assert response.time_ms == 150.5
        assert response.tokens == 42
        assert response.error is None

    def test_response_with_error(self) -> None:
        """ModelResponse should handle errors."""
        response = ModelResponse(
            model="broken-model",
            response="",
            time_ms=50.0,
            tokens=0,
            error="Model not found",
        )

        assert response.error == "Model not found"
        assert response.response == ""

    def test_response_to_dict(self) -> None:
        """ModelResponse should convert to dict."""
        response = ModelResponse(
            model="test-model",
            response="Response text",
            time_ms=100.0,
            tokens=25,
        )

        data = response.to_dict()
        assert data["model"] == "test-model"
        assert data["response"] == "Response text"
        assert data["time_ms"] == 100.0
        assert data["tokens"] == 25
        assert data["error"] is None


class TestJudgeScore:
    """Test JudgeScore dataclass."""

    def test_score_creation(self) -> None:
        """JudgeScore should be created correctly."""
        score = JudgeScore(
            accuracy=4,
            completeness=3,
            clarity=5,
            citations=2,
        )

        assert score.accuracy == 4
        assert score.completeness == 3
        assert score.clarity == 5
        assert score.citations == 2

    def test_score_total(self) -> None:
        """JudgeScore.total should sum all scores."""
        score = JudgeScore(
            accuracy=4,
            completeness=3,
            clarity=5,
            citations=2,
        )

        assert score.total == 14  # 4 + 3 + 5 + 2

    def test_score_to_dict(self) -> None:
        """JudgeScore should convert to dict."""
        score = JudgeScore(
            accuracy=4,
            completeness=3,
            clarity=5,
            citations=2,
        )

        data = score.to_dict()
        assert data["accuracy"] == 4
        assert data["completeness"] == 3
        assert data["clarity"] == 5
        assert data["citations"] == 2
        assert data["total"] == 14


class TestJudgeEvaluation:
    """Test JudgeEvaluation dataclass."""

    def test_evaluation_creation(self) -> None:
        """JudgeEvaluation should be created correctly."""
        score_a = JudgeScore(4, 4, 4, 4)
        score_b = JudgeScore(3, 3, 3, 3)

        evaluation = JudgeEvaluation(
            winner="A",
            scores={"model_a": score_a, "model_b": score_b},
            reasoning="Model A gave a more complete answer.",
            judge_model="llama3.1:8b",
            time_ms=500.0,
        )

        assert evaluation.winner == "A"
        assert evaluation.scores["model_a"].total == 16
        assert evaluation.scores["model_b"].total == 12
        assert evaluation.reasoning == "Model A gave a more complete answer."
        assert evaluation.judge_model == "llama3.1:8b"

    def test_evaluation_to_dict(self) -> None:
        """JudgeEvaluation should convert to dict."""
        score = JudgeScore(4, 4, 4, 4)

        evaluation = JudgeEvaluation(
            winner="tie",
            scores={"model": score},
            reasoning="Equal quality.",
            judge_model="test-judge",
        )

        data = evaluation.to_dict()
        assert data["winner"] == "tie"
        assert "model" in data["scores"]
        assert data["reasoning"] == "Equal quality."


class TestComparisonResult:
    """Test ComparisonResult dataclass."""

    def test_result_creation(self) -> None:
        """ComparisonResult should be created correctly."""
        response1 = ModelResponse("model1", "Response 1", 100.0, 20)
        response2 = ModelResponse("model2", "Response 2", 150.0, 25)

        result = ComparisonResult(
            query="Test query",
            context="Test context",
            responses=[response1, response2],
        )

        assert result.query == "Test query"
        assert result.context == "Test context"
        assert len(result.responses) == 2
        assert result.evaluation is None
        assert result.ensemble_winner is None

    def test_result_with_evaluation(self) -> None:
        """ComparisonResult should include evaluation."""
        response1 = ModelResponse("model1", "Response 1", 100.0, 20)
        response2 = ModelResponse("model2", "Response 2", 150.0, 25)

        score1 = JudgeScore(4, 4, 4, 4)
        score2 = JudgeScore(3, 3, 3, 3)
        evaluation = JudgeEvaluation(
            winner="A",
            scores={"model1": score1, "model2": score2},
            reasoning="Model 1 is better.",
            judge_model="judge",
        )

        result = ComparisonResult(
            query="Query",
            context="Context",
            responses=[response1, response2],
            evaluation=evaluation,
        )

        assert result.evaluation is not None
        assert result.evaluation.winner == "A"

    def test_result_with_ensemble(self) -> None:
        """ComparisonResult should include ensemble data."""
        response1 = ModelResponse("model1", "Response 1", 100.0, 20)
        response2 = ModelResponse("model2", "Response 2", 150.0, 25)

        result = ComparisonResult(
            query="Query",
            context="Context",
            responses=[response1, response2],
            ensemble_winner="model1",
            ensemble_votes=["model1", "model1", "model2"],
            ensemble_confidence=0.67,
        )

        assert result.ensemble_winner == "model1"
        assert len(result.ensemble_votes) == 3
        assert result.ensemble_confidence == 0.67

    def test_result_to_dict(self) -> None:
        """ComparisonResult should convert to dict."""
        response = ModelResponse("model", "Response", 100.0, 20)

        result = ComparisonResult(
            query="Query",
            context="This is a long context" * 50,  # > 200 chars
            responses=[response],
        )

        data = result.to_dict()
        assert data["query"] == "Query"
        assert data["context"].endswith("...")  # Truncated
        assert len(data["responses"]) == 1


class TestJudgePrompt:
    """Test the JUDGE_PROMPT template."""

    def test_prompt_has_placeholders(self) -> None:
        """JUDGE_PROMPT should have all required placeholders."""
        assert "{question}" in JUDGE_PROMPT
        assert "{context}" in JUDGE_PROMPT
        assert "{model_a}" in JUDGE_PROMPT
        assert "{response_a}" in JUDGE_PROMPT
        assert "{model_b}" in JUDGE_PROMPT
        assert "{response_b}" in JUDGE_PROMPT

    def test_prompt_includes_json_format(self) -> None:
        """JUDGE_PROMPT should specify JSON output format."""
        assert '"winner"' in JUDGE_PROMPT
        assert '"scores"' in JUDGE_PROMPT
        assert '"reasoning"' in JUDGE_PROMPT

    def test_prompt_formatting(self) -> None:
        """JUDGE_PROMPT should format correctly."""
        formatted = JUDGE_PROMPT.format(
            question="What is AI?",
            context="Artificial Intelligence is...",
            model_a="model1",
            response_a="AI is machine learning.",
            model_b="model2",
            response_b="AI is a broad field.",
        )

        assert "What is AI?" in formatted
        assert "model1" in formatted
        assert "model2" in formatted
        assert "AI is machine learning." in formatted


class TestModelComparator:
    """Test ModelComparator class."""

    def test_comparator_creation(self) -> None:
        """ModelComparator should be created correctly."""
        comparator = ModelComparator(
            base_url="http://localhost:11434",
            timeout_seconds=60,
        )

        assert comparator.base_url == "http://localhost:11434"
        assert comparator.timeout == 60

    def test_comparator_default_url(self) -> None:
        """ModelComparator should use default Ollama URL."""
        comparator = ModelComparator()

        assert comparator.base_url == "http://localhost:11434"

    def test_compare_needs_models(self) -> None:
        """compare() should accept a list of models."""
        comparator = ModelComparator()

        # We can't easily test the actual comparison without Ollama,
        # but we can verify the method signature
        import inspect
        sig = inspect.signature(comparator.compare)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "models" in params
        assert "context" in params

    def test_compare_with_judge_min_models(self) -> None:
        """compare_with_judge() should require at least 2 models."""
        comparator = ModelComparator()

        with pytest.raises(ValueError, match="at least 2 models"):
            comparator.compare_with_judge(
                query="Test",
                models=["only-one"],
                judge_model="judge",
            )

    def test_compare_ensemble_min_models(self) -> None:
        """compare_ensemble() should require at least 2 models."""
        comparator = ModelComparator()

        with pytest.raises(ValueError, match="at least 2 models"):
            comparator.compare_ensemble(
                query="Test",
                models=["only-one"],
            )


class TestModelComparatorJudgeParsing:
    """Test judge response parsing logic."""

    def test_parse_valid_json(self) -> None:
        """_parse_judge_response should parse valid JSON."""
        comparator = ModelComparator()

        json_content = """{
            "winner": "A",
            "scores": {
                "A": {"accuracy": 4, "completeness": 4, "clarity": 5, "citations": 3},
                "B": {"accuracy": 3, "completeness": 3, "clarity": 4, "citations": 2}
            },
            "reasoning": "Model A provided a more detailed explanation."
        }"""

        result = comparator._parse_judge_response(
            json_content, "model_a", "model_b"
        )

        assert result.winner == "A"
        assert result.scores["model_a"].accuracy == 4
        assert result.scores["model_b"].accuracy == 3
        assert "detailed" in result.reasoning

    def test_parse_json_with_surrounding_text(self) -> None:
        """_parse_judge_response should extract JSON from text."""
        comparator = ModelComparator()

        content = """Here's my analysis:

        {
            "winner": "B",
            "scores": {
                "A": {"accuracy": 3, "completeness": 3, "clarity": 3, "citations": 3},
                "B": {"accuracy": 4, "completeness": 4, "clarity": 4, "citations": 4}
            },
            "reasoning": "B is better."
        }

        That's my evaluation."""

        result = comparator._parse_judge_response(
            content, "model_a", "model_b"
        )

        assert result.winner == "B"
        assert result.scores["model_b"].total == 16

    def test_parse_invalid_json(self) -> None:
        """_parse_judge_response should handle invalid JSON gracefully."""
        comparator = ModelComparator()

        content = "This is not valid JSON at all."

        result = comparator._parse_judge_response(
            content, "model_a", "model_b"
        )

        # Should return default tie with neutral scores
        assert result.winner == "tie"
        assert result.scores["model_a"].accuracy == 3
        assert result.scores["model_b"].accuracy == 3

    def test_parse_partial_json(self) -> None:
        """_parse_judge_response should handle partial JSON."""
        comparator = ModelComparator()

        content = '{"winner": "A"'  # Incomplete JSON

        result = comparator._parse_judge_response(
            content, "model_a", "model_b"
        )

        # Should return default
        assert result.winner == "tie"


class TestComparisonFormatter:
    """Test comparison output formatting."""

    def test_format_stars(self) -> None:
        """_format_stars should create star ratings."""
        from ragd.ui.formatters.comparison import _format_stars

        assert _format_stars(1) == "★☆☆☆☆"
        assert _format_stars(3) == "★★★☆☆"
        assert _format_stars(5) == "★★★★★"

    def test_print_comparison_accepts_result(self) -> None:
        """print_comparison should accept ComparisonResult."""
        from ragd.ui.formatters.comparison import print_comparison
        import io
        from contextlib import redirect_stdout

        response = ModelResponse("model", "Response", 100.0, 20)
        result = ComparisonResult(
            query="Test query",
            context="Test context",
            responses=[response],
        )

        # Should not raise an error
        # (Actual output goes to console which we can't easily capture)
        try:
            print_comparison(result, no_color=True)
        except Exception as e:
            pytest.fail(f"print_comparison raised an exception: {e}")
