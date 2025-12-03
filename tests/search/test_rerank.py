"""Tests for Cross-Encoder Reranking (F-065)."""

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from ragd.search.rerank import (
    CrossEncoderReranker,
    RerankerConfig,
    RerankResult,
    get_reranker,
    rerank,
    DEFAULT_RERANKER_MODEL,
)


@dataclass
class MockSearchResult:
    """Mock search result for testing."""

    content: str
    score: float
    chunk_id: str


class TestRerankerConfig:
    """Tests for RerankerConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = RerankerConfig()

        assert config.model_name == DEFAULT_RERANKER_MODEL
        assert config.device == "cpu"
        assert config.batch_size == 32
        assert config.top_k == 10
        assert config.min_score == 0.0

    def test_custom_config(self):
        """Custom configuration values."""
        config = RerankerConfig(
            model_name="custom-model",
            device="cuda",
            batch_size=16,
            top_k=5,
            min_score=0.5,
        )

        assert config.model_name == "custom-model"
        assert config.device == "cuda"
        assert config.batch_size == 16
        assert config.top_k == 5
        assert config.min_score == 0.5


class TestRerankResult:
    """Tests for RerankResult."""

    def test_create_result(self):
        """Create RerankResult with original and scores."""
        original = MockSearchResult(content="test", score=0.8, chunk_id="c1")
        result = RerankResult(
            original=original,
            rerank_score=0.95,
            original_rank=3,
            final_rank=1,
        )

        assert result.original == original
        assert result.rerank_score == 0.95
        assert result.original_rank == 3
        assert result.final_rank == 1


class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker."""

    def test_rerank_empty_results(self):
        """Reranking empty results returns empty list."""
        reranker = CrossEncoderReranker()
        results = reranker.rerank("query", [])

        assert results == []

    def test_rerank_without_model_returns_original(self):
        """Without model, returns original order."""
        reranker = CrossEncoderReranker()
        # Force model unavailable
        reranker._model = None
        reranker._model_loaded = True

        results = [
            MockSearchResult(content="first", score=0.9, chunk_id="c1"),
            MockSearchResult(content="second", score=0.8, chunk_id="c2"),
        ]

        reranked = reranker.rerank("query", results, top_k=10)

        assert len(reranked) == 2
        assert reranked[0].content == "first"
        assert reranked[1].content == "second"

    def test_rerank_respects_top_k(self):
        """Reranking respects top_k limit."""
        reranker = CrossEncoderReranker()
        reranker._model = None
        reranker._model_loaded = True

        results = [
            MockSearchResult(content=f"result-{i}", score=0.9 - i * 0.1, chunk_id=f"c{i}")
            for i in range(10)
        ]

        reranked = reranker.rerank("query", results, top_k=3)

        assert len(reranked) == 3

    def test_rerank_with_mock_model(self):
        """Reranking with mocked cross-encoder."""
        with patch.dict("sys.modules", {"sentence_transformers": MagicMock()}):
            mock_model = MagicMock()
            mock_model.predict.return_value = [0.5, 0.9, 0.3]  # Scores for 3 results

            reranker = CrossEncoderReranker()
            reranker._model = mock_model
            reranker._model_loaded = True

            results = [
                MockSearchResult(content="low relevance", score=0.9, chunk_id="c1"),
                MockSearchResult(content="high relevance", score=0.5, chunk_id="c2"),
                MockSearchResult(content="medium relevance", score=0.7, chunk_id="c3"),
            ]

            reranked = reranker.rerank("query", results, top_k=10)

            # Should be sorted by rerank score (0.9, 0.5, 0.3)
            assert len(reranked) == 3
            assert reranked[0].content == "high relevance"  # score 0.9
            assert reranked[1].content == "low relevance"   # score 0.5
            assert reranked[2].content == "medium relevance"  # score 0.3

    def test_rerank_with_min_score(self):
        """Reranking filters by min_score."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.8, 0.3, 0.6]

        config = RerankerConfig(min_score=0.5)
        reranker = CrossEncoderReranker(config)
        reranker._model = mock_model
        reranker._model_loaded = True

        results = [
            MockSearchResult(content="a", score=0.9, chunk_id="c1"),
            MockSearchResult(content="b", score=0.8, chunk_id="c2"),
            MockSearchResult(content="c", score=0.7, chunk_id="c3"),
        ]

        reranked = reranker.rerank("query", results)

        # Only scores >= 0.5 should be included
        assert len(reranked) == 2
        assert reranked[0].content == "a"  # score 0.8
        assert reranked[1].content == "c"  # score 0.6

    def test_rerank_with_scores(self):
        """rerank_with_scores returns RerankResult objects."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.7, 0.9]

        reranker = CrossEncoderReranker()
        reranker._model = mock_model
        reranker._model_loaded = True

        results = [
            MockSearchResult(content="first", score=0.9, chunk_id="c1"),
            MockSearchResult(content="second", score=0.8, chunk_id="c2"),
        ]

        reranked = reranker.rerank_with_scores("query", results)

        assert len(reranked) == 2
        assert all(isinstance(r, RerankResult) for r in reranked)

        # Sorted by score descending
        assert reranked[0].rerank_score == 0.9
        assert reranked[0].final_rank == 1
        assert reranked[1].rerank_score == 0.7
        assert reranked[1].final_rank == 2

    def test_available_property_without_model(self):
        """available property returns False when model unavailable."""
        reranker = CrossEncoderReranker()
        reranker._model = None
        reranker._model_loaded = True

        assert reranker.available is False

    def test_available_property_with_model(self):
        """available property returns True when model loaded."""
        reranker = CrossEncoderReranker()
        reranker._model = MagicMock()
        reranker._model_loaded = True

        assert reranker.available is True

    def test_rerank_handles_dict_results(self):
        """Reranking handles dict-style results."""
        reranker = CrossEncoderReranker()
        reranker._model = None
        reranker._model_loaded = True

        results = [
            {"content": "first doc", "score": 0.9},
            {"content": "second doc", "score": 0.8},
        ]

        reranked = reranker.rerank("query", results)

        assert len(reranked) == 2


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_reranker_default(self):
        """get_reranker returns default instance."""
        reranker1 = get_reranker()
        reranker2 = get_reranker()

        # Same instance (cached)
        assert reranker1 is reranker2

    def test_get_reranker_with_config(self):
        """get_reranker with config returns new instance."""
        config = RerankerConfig(model_name="custom")
        reranker = get_reranker(config)

        assert reranker.config.model_name == "custom"

    def test_rerank_convenience_function(self):
        """rerank convenience function works."""
        results = [
            MockSearchResult(content="test", score=0.9, chunk_id="c1"),
        ]

        # Should not raise
        reranked = rerank("query", results, top_k=5)

        assert isinstance(reranked, list)
