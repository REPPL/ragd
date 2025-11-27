"""Tests for LLM metadata enhancement module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ragd.llm.metadata import (
    DEFAULT_CLASSIFICATION_PROMPT,
    DEFAULT_SUMMARY_PROMPT,
    EnhancedMetadata,
    LLMMetadataEnhancer,
    create_metadata_enhancer,
)
from ragd.llm.ollama import LLMResponse, OllamaError


class TestEnhancedMetadata:
    """Tests for EnhancedMetadata dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        metadata = EnhancedMetadata()
        assert metadata.summary == ""
        assert metadata.classification == ""
        assert metadata.success is True
        assert metadata.error is None

    def test_with_values(self) -> None:
        """Test with values."""
        metadata = EnhancedMetadata(
            summary="A test summary.",
            classification="report",
            success=True,
        )
        assert metadata.summary == "A test summary."
        assert metadata.classification == "report"
        assert metadata.success is True

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        metadata = EnhancedMetadata(
            summary="Summary text",
            classification="article",
            success=False,
            error="Test error",
        )
        data = metadata.to_dict()
        assert data["summary"] == "Summary text"
        assert data["classification"] == "article"
        assert data["success"] is False
        assert data["error"] == "Test error"


class TestLLMMetadataEnhancer:
    """Tests for LLMMetadataEnhancer."""

    def test_init_with_defaults(self) -> None:
        """Test initialisation with defaults."""
        enhancer = LLMMetadataEnhancer()
        assert enhancer._base_url == "http://localhost:11434"
        assert enhancer._summary_model == "llama3.2:3b"
        assert enhancer._classification_model == "llama3.2:3b"
        assert enhancer._summary_max_tokens == 150

    def test_init_with_custom_values(self) -> None:
        """Test initialisation with custom values."""
        enhancer = LLMMetadataEnhancer(
            base_url="http://custom:11434",
            summary_model="mistral:7b",
            classification_model="llama2:13b",
            timeout_seconds=120,
            summary_max_tokens=200,
        )
        assert enhancer._base_url == "http://custom:11434"
        assert enhancer._summary_model == "mistral:7b"
        assert enhancer._classification_model == "llama2:13b"
        assert enhancer._timeout == 120
        assert enhancer._summary_max_tokens == 200

    def test_init_with_custom_prompts(self) -> None:
        """Test initialisation with custom prompts."""
        custom_summary = "Summarise: {text}"
        custom_class = "Classify: {text}"
        enhancer = LLMMetadataEnhancer(
            summary_prompt=custom_summary,
            classification_prompt=custom_class,
        )
        assert enhancer._summary_prompt == custom_summary
        assert enhancer._classification_prompt == custom_class

    def test_truncate_text_short(self) -> None:
        """Test truncation with short text."""
        enhancer = LLMMetadataEnhancer()
        short_text = "This is a short text."
        result = enhancer._truncate_text(short_text)
        assert result == short_text

    def test_truncate_text_long(self) -> None:
        """Test truncation with long text."""
        enhancer = LLMMetadataEnhancer()
        long_text = "A" * 10000
        result = enhancer._truncate_text(long_text)
        assert len(result) < len(long_text)
        assert "[Document truncated" in result

    def test_truncate_at_sentence_boundary(self) -> None:
        """Test truncation attempts sentence boundary."""
        enhancer = LLMMetadataEnhancer()
        # Create text with sentence ending near MAX_TEXT_LENGTH (8000)
        # Put a sentence at ~7500 chars (within 80% of 8000)
        # Then add enough text to exceed 8000 chars total
        text = ("A" * 7500) + ". " + ("B" * 1000)  # 7500 + 2 + 1000 = 8502 chars
        result = enhancer._truncate_text(text)
        # Should truncate at sentence boundary (at the period after 7500 A's)
        assert result.endswith(".\n\n[Document truncated for processing...]")

    @patch("ragd.llm.metadata.OllamaClient")
    def test_generate_summary_success(self, mock_client_class: MagicMock) -> None:
        """Test successful summary generation."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="This document discusses Python programming best practices.",
            model="llama3.2:3b",
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        summary = enhancer.generate_summary("Python is a programming language...")

        assert summary == "This document discusses Python programming best practices."
        mock_client.generate.assert_called_once()

    @patch("ragd.llm.metadata.OllamaClient")
    def test_generate_summary_empty_text(self, mock_client_class: MagicMock) -> None:
        """Test summary generation with empty text."""
        enhancer = LLMMetadataEnhancer()
        summary = enhancer.generate_summary("")
        assert summary == ""
        mock_client_class.return_value.generate.assert_not_called()

    @patch("ragd.llm.metadata.OllamaClient")
    def test_generate_summary_ollama_error(self, mock_client_class: MagicMock) -> None:
        """Test summary generation handles Ollama errors."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = OllamaError("Connection refused")
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        summary = enhancer.generate_summary("Some text")

        assert summary == ""

    @patch("ragd.llm.metadata.OllamaClient")
    def test_classify_document_success(self, mock_client_class: MagicMock) -> None:
        """Test successful document classification."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="report",
            model="llama3.2:3b",
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        classification = enhancer.classify_document("Q1 Financial Report...")

        assert classification == "report"

    @patch("ragd.llm.metadata.OllamaClient")
    def test_classify_document_normalises_output(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test classification normalises output."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="  REPORT  \n",
            model="llama3.2:3b",
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        classification = enhancer.classify_document("Some report text")

        assert classification == "report"

    @patch("ragd.llm.metadata.OllamaClient")
    def test_classify_document_unknown_defaults_to_other(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test unknown classification defaults to 'other'."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="unknown_category",
            model="llama3.2:3b",
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        classification = enhancer.classify_document("Random text")

        assert classification == "other"

    @patch("ragd.llm.metadata.OllamaClient")
    def test_classify_document_empty_text(self, mock_client_class: MagicMock) -> None:
        """Test classification with empty text."""
        enhancer = LLMMetadataEnhancer()
        classification = enhancer.classify_document("")
        assert classification == ""

    @patch("ragd.llm.metadata.OllamaClient")
    def test_enhance_full(self, mock_client_class: MagicMock) -> None:
        """Test full enhancement with both summary and classification."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            LLMResponse(content="Summary of the document.", model="llama3.2:3b"),
            LLMResponse(content="article", model="llama3.2:3b"),
        ]
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        result = enhancer.enhance("Some document text here")

        assert result.summary == "Summary of the document."
        assert result.classification == "article"
        assert result.success is True
        assert result.error is None

    @patch("ragd.llm.metadata.OllamaClient")
    def test_enhance_summary_only(self, mock_client_class: MagicMock) -> None:
        """Test enhancement with summary only."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="Summary only.", model="llama3.2:3b"
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        result = enhancer.enhance("Text", generate_summary=True, classify=False)

        assert result.summary == "Summary only."
        assert result.classification == ""
        assert mock_client.generate.call_count == 1

    @patch("ragd.llm.metadata.OllamaClient")
    def test_enhance_classify_only(self, mock_client_class: MagicMock) -> None:
        """Test enhancement with classification only."""
        mock_client = MagicMock()
        mock_client.generate.return_value = LLMResponse(
            content="documentation", model="llama3.2:3b"
        )
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        result = enhancer.enhance("Text", generate_summary=False, classify=True)

        assert result.summary == ""
        assert result.classification == "documentation"
        assert mock_client.generate.call_count == 1

    def test_enhance_empty_text(self) -> None:
        """Test enhancement with empty text."""
        enhancer = LLMMetadataEnhancer()
        result = enhancer.enhance("")

        assert result.success is False
        assert result.error == "Empty document text"

    @patch("ragd.llm.metadata.OllamaClient")
    def test_is_available_true(self, mock_client_class: MagicMock) -> None:
        """Test is_available returns True when Ollama is running."""
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        assert enhancer.is_available() is True

    @patch("ragd.llm.metadata.OllamaClient")
    def test_is_available_false(self, mock_client_class: MagicMock) -> None:
        """Test is_available returns False when Ollama is not running."""
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        assert enhancer.is_available() is False


class TestCreateMetadataEnhancer:
    """Tests for create_metadata_enhancer factory function."""

    @patch("ragd.llm.metadata.LLMMetadataEnhancer")
    def test_returns_enhancer_when_available(
        self, mock_enhancer_class: MagicMock
    ) -> None:
        """Test returns enhancer when Ollama is available."""
        mock_enhancer = MagicMock()
        mock_enhancer.is_available.return_value = True
        mock_enhancer_class.return_value = mock_enhancer

        result = create_metadata_enhancer()

        assert result is mock_enhancer
        mock_enhancer_class.assert_called_once()

    @patch("ragd.llm.metadata.LLMMetadataEnhancer")
    def test_returns_none_when_unavailable(
        self, mock_enhancer_class: MagicMock
    ) -> None:
        """Test returns None when Ollama is unavailable."""
        mock_enhancer = MagicMock()
        mock_enhancer.is_available.return_value = False
        mock_enhancer_class.return_value = mock_enhancer

        result = create_metadata_enhancer()

        assert result is None


class TestDefaultPrompts:
    """Tests for default prompts."""

    def test_summary_prompt_has_placeholder(self) -> None:
        """Test summary prompt has {text} placeholder."""
        assert "{text}" in DEFAULT_SUMMARY_PROMPT

    def test_classification_prompt_has_placeholder(self) -> None:
        """Test classification prompt has {text} placeholder."""
        assert "{text}" in DEFAULT_CLASSIFICATION_PROMPT

    def test_classification_prompt_lists_categories(self) -> None:
        """Test classification prompt lists all valid categories."""
        categories = [
            "report",
            "article",
            "documentation",
            "correspondence",
            "legal",
            "financial",
            "academic",
            "other",
        ]
        for category in categories:
            assert category in DEFAULT_CLASSIFICATION_PROMPT
