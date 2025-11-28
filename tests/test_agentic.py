"""Tests for agentic RAG (CRAG + Self-RAG)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ragd.chat.agentic import (
    AgenticConfig,
    AgenticRAG,
    AgenticResponse,
    RetrievalQuality,
    agentic_ask,
    RELEVANCE_EVAL_PROMPT,
    QUERY_REWRITE_PROMPT,
    FAITHFULNESS_EVAL_PROMPT,
)
from ragd.citation import Citation
from ragd.llm import LLMResponse


class TestRetrievalQuality:
    """Tests for RetrievalQuality enum."""

    def test_quality_values(self):
        """Test quality enum values."""
        assert RetrievalQuality.EXCELLENT.value == "excellent"
        assert RetrievalQuality.GOOD.value == "good"
        assert RetrievalQuality.POOR.value == "poor"
        assert RetrievalQuality.IRRELEVANT.value == "irrelevant"


class TestAgenticConfig:
    """Tests for AgenticConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AgenticConfig()
        assert config.crag_enabled is True
        assert config.self_rag_enabled is True
        assert config.relevance_threshold == 0.6
        assert config.faithfulness_threshold == 0.7
        assert config.max_rewrites == 2
        assert config.max_refinements == 1

    def test_custom_config(self):
        """Test custom configuration."""
        config = AgenticConfig(
            crag_enabled=False,
            self_rag_enabled=False,
            relevance_threshold=0.8,
            faithfulness_threshold=0.9,
            max_rewrites=5,
            max_refinements=3,
        )
        assert config.crag_enabled is False
        assert config.self_rag_enabled is False
        assert config.relevance_threshold == 0.8
        assert config.faithfulness_threshold == 0.9
        assert config.max_rewrites == 5
        assert config.max_refinements == 3


class TestAgenticResponse:
    """Tests for AgenticResponse."""

    def test_create_response(self):
        """Test creating agentic response."""
        response = AgenticResponse(
            answer="Test answer",
            confidence=0.85,
            retrieval_quality=RetrievalQuality.GOOD,
            rewrites_attempted=1,
            refinements_attempted=0,
            citations=[],
        )
        assert response.answer == "Test answer"
        assert response.confidence == 0.85
        assert response.retrieval_quality == RetrievalQuality.GOOD
        assert response.rewrites_attempted == 1
        assert response.refinements_attempted == 0

    def test_default_values(self):
        """Test default values for optional fields."""
        response = AgenticResponse(
            answer="Test",
            confidence=0.5,
            retrieval_quality=RetrievalQuality.POOR,
        )
        assert response.rewrites_attempted == 0
        assert response.refinements_attempted == 0
        assert response.citations == []
        assert response.metadata == {}

    def test_to_cited_answer(self):
        """Test conversion to CitedAnswer."""
        citation = Citation(
            document_id="doc1",
            filename="test.pdf",
            page_number=1,
            relevance_score=0.9,
        )
        response = AgenticResponse(
            answer="Test answer",
            confidence=0.85,
            retrieval_quality=RetrievalQuality.GOOD,
            citations=[citation],
        )
        cited = response.to_cited_answer()
        assert cited.answer == "Test answer"
        assert cited.confidence == 0.85
        assert len(cited.citations) == 1
        assert cited.citations[0].filename == "test.pdf"


class TestAgenticRAG:
    """Tests for AgenticRAG class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock ragd config."""
        config = MagicMock()
        config.llm.ollama_url = "http://localhost:11434"
        config.llm.model = "llama3.2:3b"
        return config

    @pytest.fixture
    def mock_rag(self, mock_config):
        """Create AgenticRAG with mocked dependencies."""
        with patch("ragd.chat.agentic.OllamaClient") as MockClient, \
             patch("ragd.chat.agentic.HybridSearcher") as MockSearcher:
            MockClient.return_value = MagicMock()
            MockSearcher.return_value = MagicMock()
            rag = AgenticRAG(config=mock_config)
            return rag

    def test_extract_score_valid(self, mock_rag):
        """Test extracting score from valid response."""
        assert mock_rag._extract_score("0.75") == 0.75
        assert mock_rag._extract_score("The score is 0.85") == 0.85
        assert mock_rag._extract_score("Score: 0.9") == 0.9

    def test_extract_score_clamping(self, mock_rag):
        """Test score clamping to 0-1 range."""
        assert mock_rag._extract_score("1.5") == 1.0
        assert mock_rag._extract_score("-0.5") == 0.5  # Invalid, defaults to 0.5
        assert mock_rag._extract_score("0.0") == 0.0

    def test_extract_score_invalid(self, mock_rag):
        """Test extracting score from invalid response."""
        assert mock_rag._extract_score("no number here") == 0.5
        assert mock_rag._extract_score("") == 0.5

    def test_calculate_confidence(self, mock_rag):
        """Test confidence calculation."""
        # 40% relevance, 60% faithfulness
        confidence = mock_rag._calculate_confidence(1.0, 1.0)
        assert confidence == 1.0

        confidence = mock_rag._calculate_confidence(0.5, 0.5)
        assert confidence == 0.5

        confidence = mock_rag._calculate_confidence(0.0, 1.0)
        assert confidence == 0.6  # 0 * 0.4 + 1 * 0.6

        confidence = mock_rag._calculate_confidence(1.0, 0.0)
        assert confidence == 0.4  # 1 * 0.4 + 0 * 0.6

    def test_quality_from_score_excellent(self, mock_rag):
        """Test excellent quality threshold."""
        assert mock_rag._quality_from_score(0.9) == RetrievalQuality.EXCELLENT
        assert mock_rag._quality_from_score(0.8) == RetrievalQuality.EXCELLENT

    def test_quality_from_score_good(self, mock_rag):
        """Test good quality threshold."""
        assert mock_rag._quality_from_score(0.79) == RetrievalQuality.GOOD
        assert mock_rag._quality_from_score(0.6) == RetrievalQuality.GOOD

    def test_quality_from_score_poor(self, mock_rag):
        """Test poor quality threshold."""
        assert mock_rag._quality_from_score(0.59) == RetrievalQuality.POOR
        assert mock_rag._quality_from_score(0.4) == RetrievalQuality.POOR

    def test_quality_from_score_irrelevant(self, mock_rag):
        """Test irrelevant quality threshold."""
        assert mock_rag._quality_from_score(0.39) == RetrievalQuality.IRRELEVANT
        assert mock_rag._quality_from_score(0.0) == RetrievalQuality.IRRELEVANT

    def test_no_results_response(self, mock_rag):
        """Test response when no results found."""
        response = mock_rag._no_results_response("test question")
        assert "couldn't find" in response.answer.lower()
        assert response.confidence == 0.0
        assert response.retrieval_quality == RetrievalQuality.IRRELEVANT
        assert response.citations == []

    def test_ask_no_results(self, mock_rag):
        """Test ask with no search results."""
        mock_rag._searcher.search.return_value = []

        response = mock_rag.ask("What is Python?")
        assert response.confidence == 0.0
        assert response.retrieval_quality == RetrievalQuality.IRRELEVANT

    def test_ask_with_results_no_agentic(self, mock_config):
        """Test ask with results but agentic disabled."""
        with patch("ragd.chat.agentic.OllamaClient") as MockClient, \
             patch("ragd.chat.agentic.HybridSearcher") as MockSearcher, \
             patch("ragd.chat.agentic.build_context_from_results") as mock_build:

            # Setup mocks
            mock_llm = MagicMock()
            mock_llm.generate.return_value = LLMResponse(
                content="Test answer",
                model="llama3.2:3b",
                tokens_used=100,
            )
            MockClient.return_value = mock_llm

            mock_search_result = MagicMock()
            mock_search_result.chunk_id = "chunk1"
            mock_search_result.content = "Test content"
            mock_search_result.score = 0.8
            MockSearcher.return_value.search.return_value = [mock_search_result]

            mock_build.return_value = ("Test context", [])

            # Create RAG with agentic disabled
            agentic_config = AgenticConfig(
                crag_enabled=False,
                self_rag_enabled=False,
            )
            rag = AgenticRAG(config=mock_config, agentic_config=agentic_config)

            response = rag.ask("What is Python?", agentic=False)

            assert response.answer == "Test answer"
            assert response.confidence == 1.0  # Default when no evaluation
            assert response.rewrites_attempted == 0
            assert response.refinements_attempted == 0

    def test_evaluate_relevance(self, mock_rag):
        """Test relevance evaluation."""
        mock_rag._llm.generate.return_value = LLMResponse(
            content="0.85",
            model="llama3.2:3b",
            tokens_used=10,
        )

        score = mock_rag._evaluate_relevance("test query", "test context")
        assert score == 0.85

    def test_evaluate_relevance_error(self, mock_rag):
        """Test relevance evaluation on error."""
        from ragd.llm import OllamaError
        mock_rag._llm.generate.side_effect = OllamaError("Connection error")

        score = mock_rag._evaluate_relevance("test query", "test context")
        assert score == 0.5  # Default on error

    def test_rewrite_query(self, mock_rag):
        """Test query rewriting."""
        mock_rag._llm.generate.return_value = LLMResponse(
            content="improved search query",
            model="llama3.2:3b",
            tokens_used=20,
        )

        rewritten = mock_rag._rewrite_query("original query", "irrelevant context")
        assert rewritten == "improved search query"

    def test_rewrite_query_error(self, mock_rag):
        """Test query rewriting on error."""
        from ragd.llm import OllamaError
        mock_rag._llm.generate.side_effect = OllamaError("Connection error")

        rewritten = mock_rag._rewrite_query("original query", "irrelevant context")
        assert rewritten is None

    def test_evaluate_faithfulness(self, mock_rag):
        """Test faithfulness evaluation."""
        mock_rag._llm.generate.return_value = LLMResponse(
            content="0.92",
            model="llama3.2:3b",
            tokens_used=10,
        )

        score = mock_rag._evaluate_faithfulness("test answer", "test context")
        assert score == 0.92

    def test_evaluate_faithfulness_error(self, mock_rag):
        """Test faithfulness evaluation on error."""
        from ragd.llm import OllamaError
        mock_rag._llm.generate.side_effect = OllamaError("Connection error")

        score = mock_rag._evaluate_faithfulness("test answer", "test context")
        assert score == 0.5  # Default on error

    def test_refine_response(self, mock_rag):
        """Test response refinement."""
        mock_rag._llm.generate.return_value = LLMResponse(
            content="Refined answer based only on sources",
            model="llama3.2:3b",
            tokens_used=50,
        )

        refined = mock_rag._refine_response(
            "original question",
            "original answer with hallucinations",
            "source context",
        )
        assert refined == "Refined answer based only on sources"

    def test_refine_response_error(self, mock_rag):
        """Test response refinement on error."""
        from ragd.llm import OllamaError
        mock_rag._llm.generate.side_effect = OllamaError("Connection error")

        refined = mock_rag._refine_response(
            "question",
            "original answer",
            "context",
        )
        assert refined == "original answer"  # Returns original on error

    def test_close(self, mock_rag):
        """Test closing resources."""
        mock_rag.close()
        mock_rag._searcher.close.assert_called_once()


class TestAgenticAskFunction:
    """Tests for agentic_ask convenience function."""

    def test_agentic_ask_basic(self):
        """Test basic agentic_ask call."""
        with patch("ragd.chat.agentic.AgenticRAG") as MockRAG:
            mock_instance = MagicMock()
            mock_instance.ask.return_value = AgenticResponse(
                answer="Test answer",
                confidence=0.9,
                retrieval_quality=RetrievalQuality.EXCELLENT,
            )
            MockRAG.return_value = mock_instance

            response = agentic_ask("What is Python?")

            assert response.answer == "Test answer"
            assert response.confidence == 0.9
            mock_instance.close.assert_called_once()

    def test_agentic_ask_with_params(self):
        """Test agentic_ask with custom parameters."""
        with patch("ragd.chat.agentic.AgenticRAG") as MockRAG:
            mock_instance = MagicMock()
            mock_instance.ask.return_value = AgenticResponse(
                answer="Test",
                confidence=0.5,
                retrieval_quality=RetrievalQuality.GOOD,
            )
            MockRAG.return_value = mock_instance

            response = agentic_ask(
                "Question",
                max_results=10,
                agentic=False,
            )

            mock_instance.ask.assert_called_once_with(
                "Question",
                max_results=10,
                agentic=False,
            )


class TestPrompts:
    """Tests for agentic prompts."""

    def test_relevance_prompt_placeholders(self):
        """Test relevance prompt has required placeholders."""
        assert "{query}" in RELEVANCE_EVAL_PROMPT
        assert "{context}" in RELEVANCE_EVAL_PROMPT

    def test_rewrite_prompt_placeholders(self):
        """Test rewrite prompt has required placeholders."""
        assert "{query}" in QUERY_REWRITE_PROMPT
        assert "{summary}" in QUERY_REWRITE_PROMPT

    def test_faithfulness_prompt_placeholders(self):
        """Test faithfulness prompt has required placeholders."""
        assert "{response}" in FAITHFULNESS_EVAL_PROMPT
        assert "{context}" in FAITHFULNESS_EVAL_PROMPT
