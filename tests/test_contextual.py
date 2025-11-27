"""Tests for contextual retrieval (F-010).

Tests the LLM client interface, Ollama client, and context generator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ragd.llm.client import LLMClient, LLMResponse
from ragd.llm.context import (
    ContextGenerator,
    ContextualChunk,
    DEFAULT_CONTEXT_PROMPT,
    create_context_generator,
)
from ragd.llm.ollama import OllamaClient, OllamaError, check_ollama_available


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_response_creation(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Generated text",
            model="test-model",
            tokens_used=50,
        )
        assert response.content == "Generated text"
        assert response.model == "test-model"
        assert response.tokens_used == 50
        assert response.success is True

    def test_response_empty_content(self):
        """Test response with empty content indicates failure."""
        response = LLMResponse(
            content="",
            model="test-model",
        )
        assert response.success is False

    def test_response_defaults(self):
        """Test response default values."""
        response = LLMResponse(content="text", model="model")
        assert response.tokens_used is None
        assert response.finish_reason is None
        assert response.metadata == {}


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self, responses: list[LLMResponse] | None = None):
        self.responses = responses or []
        self.call_count = 0
        self.prompts = []

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return LLMResponse(content="Default response", model="mock")

    def is_available(self) -> bool:
        return True

    def list_models(self) -> list[str]:
        return ["mock-model"]


class TestContextGenerator:
    """Tests for ContextGenerator."""

    def test_generate_context(self):
        """Test generating context for a single chunk."""
        mock_client = MockLLMClient([
            LLMResponse(content="This section discusses Python programming.", model="test")
        ])
        generator = ContextGenerator(llm_client=mock_client)

        context = generator.generate_context(
            chunk_content="Python is a high-level programming language.",
            title="programming.md",
            file_type="md",
        )

        assert context == "This section discusses Python programming."
        assert len(mock_client.prompts) == 1
        assert "Python is a high-level" in mock_client.prompts[0]

    def test_generate_context_truncation(self):
        """Test that long contexts are truncated."""
        long_response = "A" * 300  # Exceeds default 200 char limit
        mock_client = MockLLMClient([
            LLMResponse(content=long_response, model="test")
        ])
        generator = ContextGenerator(llm_client=mock_client, max_context_length=200)

        context = generator.generate_context(
            chunk_content="Test content",
            title="test.txt",
            file_type="txt",
        )

        assert len(context) <= 200
        assert context.endswith("...")

    def test_generate_context_failure(self):
        """Test graceful handling of LLM failure (empty response)."""
        mock_client = MockLLMClient([
            LLMResponse(content="", model="test")  # Empty content indicates failure
        ])
        generator = ContextGenerator(llm_client=mock_client)

        context = generator.generate_context(
            chunk_content="Test content",
            title="test.txt",
            file_type="txt",
        )

        assert context == ""

    def test_generate_contextual_chunks(self):
        """Test generating context for multiple chunks."""
        mock_client = MockLLMClient([
            LLMResponse(content="Context for chunk 1", model="test"),
            LLMResponse(content="Context for chunk 2", model="test"),
        ])
        generator = ContextGenerator(llm_client=mock_client)

        chunks = [
            (0, "First chunk content"),
            (1, "Second chunk content"),
        ]

        results = generator.generate_contextual_chunks(
            chunks=chunks,
            title="document.pdf",
            file_type="pdf",
        )

        assert len(results) == 2
        assert isinstance(results[0], ContextualChunk)
        assert results[0].content == "First chunk content"
        assert results[0].context == "Context for chunk 1"
        assert "Context for chunk 1" in results[0].combined
        assert results[0].index == 0

    def test_contextual_chunk_combined_format(self):
        """Test that combined text has correct format."""
        mock_client = MockLLMClient([
            LLMResponse(content="Document context", model="test"),
        ])
        generator = ContextGenerator(llm_client=mock_client)

        results = generator.generate_contextual_chunks(
            chunks=[(0, "Chunk content")],
            title="doc.txt",
            file_type="txt",
        )

        # Combined should be context + newlines + content
        assert results[0].combined == "Document context\n\nChunk content"

    def test_contextual_chunk_no_context(self):
        """Test chunk with empty context uses original content."""
        mock_client = MockLLMClient([
            LLMResponse(content="", model="test"),  # Empty response
        ])
        generator = ContextGenerator(llm_client=mock_client)

        results = generator.generate_contextual_chunks(
            chunks=[(0, "Chunk content")],
            title="doc.txt",
            file_type="txt",
        )

        # Combined should just be the original content
        assert results[0].combined == "Chunk content"
        assert results[0].context == ""

    def test_custom_prompt_template(self):
        """Test using a custom prompt template."""
        custom_template = "Summarise: {chunk_content}"
        mock_client = MockLLMClient([
            LLMResponse(content="Summary", model="test"),
        ])
        generator = ContextGenerator(
            llm_client=mock_client,
            prompt_template=custom_template,
        )

        generator.generate_context(
            chunk_content="Test content",
            title="test.txt",
            file_type="txt",
        )

        assert mock_client.prompts[0] == "Summarise: Test content"

    def test_generate_batch(self):
        """Test batch context generation."""
        mock_client = MockLLMClient([
            LLMResponse(content="Context 1", model="test"),
            LLMResponse(content="Context 2", model="test"),
        ])
        generator = ContextGenerator(llm_client=mock_client)

        chunks = [
            (0, "Chunk 1"),
            (1, "Chunk 2"),
        ]

        results = generator.generate_batch(
            chunks=chunks,
            title="doc.txt",
            file_type="txt",
        )

        assert len(results) == 2
        assert results[0].context == "Context 1"
        assert results[1].context == "Context 2"


class TestOllamaClient:
    """Tests for OllamaClient."""

    def test_client_initialisation(self):
        """Test client initialisation with defaults."""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "llama3.2:3b"
        assert client.timeout == 60

    def test_client_custom_config(self):
        """Test client with custom configuration."""
        client = OllamaClient(
            base_url="http://custom:8080",
            model="llama2:7b",
            timeout_seconds=120,
        )
        assert client.base_url == "http://custom:8080"
        assert client.model == "llama2:7b"
        assert client.timeout == 120

    def test_generate_builds_correct_payload(self):
        """Test that generate builds correct API payload."""
        client = OllamaClient()

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "response": "Generated text",
                "model": "llama3.2:3b",
                "eval_count": 50,
            }

            response = client.generate(
                prompt="Test prompt",
                system_prompt="System message",
                temperature=0.5,
                max_tokens=100,
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            payload = call_args[0][2]  # Third positional arg is data

            assert payload["prompt"] == "Test prompt"
            assert payload["system"] == "System message"
            assert payload["options"]["temperature"] == 0.5
            assert payload["options"]["num_predict"] == 100
            assert payload["stream"] is False

    def test_generate_response_parsing(self):
        """Test response parsing from Ollama API."""
        client = OllamaClient()

        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "response": "Generated text",
                "model": "llama3.2:3b",
                "eval_count": 50,
                "done_reason": "stop",
                "total_duration": 1000000,
            }

            response = client.generate(prompt="Test")

            assert response.content == "Generated text"
            assert response.model == "llama3.2:3b"
            assert response.tokens_used == 50
            assert response.finish_reason == "stop"
            assert response.success is True

    @patch('ragd.llm.ollama.urllib.request.urlopen')
    def test_connection_refused_error(self, mock_urlopen):
        """Test handling of connection refused error."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        client = OllamaClient()

        with pytest.raises(OllamaError) as exc_info:
            client.generate(prompt="Test")

        assert "Cannot connect to Ollama" in str(exc_info.value)

    def test_is_available_with_model(self):
        """Test is_available when model exists."""
        client = OllamaClient(model="llama3.2:3b")

        with patch.object(client, 'list_models') as mock_list:
            mock_list.return_value = ["llama3.2:3b", "mistral:7b"]
            assert client.is_available() is True

    def test_is_available_model_not_found(self):
        """Test is_available when model doesn't exist."""
        client = OllamaClient(model="nonexistent:model")

        with patch.object(client, 'list_models') as mock_list:
            mock_list.return_value = ["llama3.2:3b", "mistral:7b"]
            assert client.is_available() is False

    def test_is_available_connection_failed(self):
        """Test is_available when connection fails."""
        client = OllamaClient()

        with patch.object(client, 'list_models') as mock_list:
            mock_list.side_effect = OllamaError("Connection refused")
            assert client.is_available() is False


class TestCheckOllamaAvailable:
    """Tests for check_ollama_available function."""

    def test_available_with_model(self):
        """Test when Ollama is available with requested model."""
        with patch('ragd.llm.ollama.OllamaClient') as MockClient:
            instance = MockClient.return_value
            instance.list_models.return_value = ["llama3.2:3b", "mistral:7b"]

            available, message = check_ollama_available(model="llama3.2:3b")

            assert available is True
            assert "available" in message.lower()

    def test_model_not_found(self):
        """Test when model is not installed."""
        with patch('ragd.llm.ollama.OllamaClient') as MockClient:
            instance = MockClient.return_value
            instance.list_models.return_value = ["mistral:7b"]

            available, message = check_ollama_available(model="llama3.2:3b")

            assert available is False
            assert "not found" in message.lower()

    def test_no_models_installed(self):
        """Test when no models are installed."""
        with patch('ragd.llm.ollama.OllamaClient') as MockClient:
            instance = MockClient.return_value
            instance.list_models.return_value = []

            available, message = check_ollama_available()

            assert available is False
            assert "no models" in message.lower()

    def test_connection_refused(self):
        """Test when Ollama is not running."""
        with patch('ragd.llm.ollama.OllamaClient') as MockClient:
            instance = MockClient.return_value
            instance.list_models.side_effect = OllamaError("Connection refused")

            available, message = check_ollama_available()

            assert available is False
            assert "not running" in message.lower()


class TestCreateContextGenerator:
    """Tests for create_context_generator factory function."""

    def test_returns_none_when_ollama_unavailable(self):
        """Test returns None when Ollama is not available."""
        with patch('ragd.llm.ollama.check_ollama_available') as mock_check:
            mock_check.return_value = (False, "Not running")

            generator = create_context_generator()

            assert generator is None

    def test_creates_generator_when_available(self):
        """Test creates generator when Ollama is available."""
        with patch('ragd.llm.ollama.check_ollama_available') as mock_check:
            with patch('ragd.llm.ollama.OllamaClient') as MockClient:
                mock_check.return_value = (True, "Available")

                generator = create_context_generator(
                    base_url="http://localhost:11434",
                    model="llama3.2:3b",
                )

                assert generator is not None
                assert isinstance(generator, ContextGenerator)


class TestContextualChunk:
    """Tests for ContextualChunk dataclass."""

    def test_chunk_creation(self):
        """Test creating a contextual chunk."""
        chunk = ContextualChunk(
            content="Original content",
            context="Generated context",
            combined="Generated context\n\nOriginal content",
            index=0,
        )
        assert chunk.content == "Original content"
        assert chunk.context == "Generated context"
        assert chunk.combined == "Generated context\n\nOriginal content"
        assert chunk.index == 0
        assert chunk.metadata == {}

    def test_chunk_with_metadata(self):
        """Test chunk with metadata."""
        chunk = ContextualChunk(
            content="Content",
            context="Context",
            combined="Context\n\nContent",
            index=1,
            metadata={"source": "test.pdf", "page": 5},
        )
        assert chunk.metadata["source"] == "test.pdf"
        assert chunk.metadata["page"] == 5


class TestDefaultContextPrompt:
    """Tests for the default context prompt template."""

    def test_prompt_has_required_placeholders(self):
        """Test that default prompt has all required placeholders."""
        assert "{title}" in DEFAULT_CONTEXT_PROMPT
        assert "{file_type}" in DEFAULT_CONTEXT_PROMPT
        assert "{chunk_content}" in DEFAULT_CONTEXT_PROMPT

    def test_prompt_can_be_formatted(self):
        """Test that prompt can be formatted without errors."""
        formatted = DEFAULT_CONTEXT_PROMPT.format(
            title="test.pdf",
            file_type="pdf",
            chunk_content="Sample content here",
        )
        assert "test.pdf" in formatted
        assert "pdf" in formatted
        assert "Sample content" in formatted
