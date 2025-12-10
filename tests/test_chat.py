"""Tests for the chat module."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.chat.context import ContextWindow, RetrievedContext, build_context_from_results
from ragd.chat.history import ChatHistory, save_history, load_history
from ragd.chat.message import ChatMessage, ChatRole, CitedAnswer
from ragd.chat.prompts import (
    PromptTemplate,
    get_prompt_template,
    list_templates,
    register_template,
)
from ragd.citation import Citation


class TestChatMessage:
    """Tests for ChatMessage dataclass."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = ChatMessage(role=ChatRole.USER, content="Hello")
        assert msg.role == ChatRole.USER
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
        assert msg.citations == []

    def test_create_assistant_message_with_citations(self):
        """Test creating an assistant message with citations."""
        citation = Citation(
            document_id="doc1",
            filename="test.pdf",
            page_number=5,
        )
        msg = ChatMessage(
            role=ChatRole.ASSISTANT,
            content="Here is the answer.",
            citations=[citation],
        )
        assert msg.role == ChatRole.ASSISTANT
        assert len(msg.citations) == 1
        assert msg.citations[0].filename == "test.pdf"

    def test_to_dict(self):
        """Test serialising message to dict."""
        msg = ChatMessage(
            role=ChatRole.USER,
            content="Test message",
        )
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Test message"
        assert "timestamp" in data

    def test_from_dict(self):
        """Test deserialising message from dict."""
        data = {
            "role": "assistant",
            "content": "Response",
            "timestamp": "2024-01-01T12:00:00",
            "citations": [
                {"document_id": "doc1", "filename": "test.pdf"}
            ],
            "metadata": {},
        }
        msg = ChatMessage.from_dict(data)
        assert msg.role == ChatRole.ASSISTANT
        assert msg.content == "Response"

    def test_str_representation(self):
        """Test string representation."""
        msg = ChatMessage(role=ChatRole.USER, content="Hello world")
        assert "[user]" in str(msg).lower()


class TestCitedAnswer:
    """Tests for CitedAnswer dataclass."""

    def test_create_cited_answer(self):
        """Test creating a cited answer."""
        citation = Citation(
            document_id="doc1",
            filename="test.pdf",
            page_number=10,
        )
        answer = CitedAnswer(
            answer="The answer is 42.",
            citations=[citation],
            model="llama3.2:3b",
            tokens_used=50,
        )
        assert answer.answer == "The answer is 42."
        assert len(answer.citations) == 1
        assert answer.has_citations is True

    def test_format_with_citations_numbered(self):
        """Test formatting with numbered citations."""
        citation = Citation(
            document_id="doc1",
            filename="test.pdf",
            page_number=5,
        )
        answer = CitedAnswer(
            answer="The answer is here.",
            citations=[citation],
        )
        formatted = answer.format_with_citations(style="numbered")
        assert "Sources:" in formatted
        assert "[1]" in formatted
        assert "test.pdf" in formatted

    def test_format_with_citations_inline(self):
        """Test formatting with inline citations."""
        citation = Citation(
            document_id="doc1",
            filename="test.pdf",
        )
        answer = CitedAnswer(
            answer="The answer is here.",
            citations=[citation],
        )
        formatted = answer.format_with_citations(style="inline")
        assert "[Sources:" in formatted

    def test_answer_without_citations(self):
        """Test answer without citations."""
        answer = CitedAnswer(answer="Just an answer.")
        assert answer.has_citations is False
        formatted = answer.format_with_citations()
        assert formatted == "Just an answer."


class TestPromptTemplate:
    """Tests for PromptTemplate."""

    def test_get_answer_template(self):
        """Test getting the answer template."""
        template = get_prompt_template("answer")
        assert template.name == "rag_answer"
        assert "context" in template.user_template
        assert "question" in template.user_template

    def test_get_chat_template(self):
        """Test getting the chat template."""
        template = get_prompt_template("chat")
        assert template.name == "rag_chat"
        assert "history" in template.user_template

    def test_format_template(self):
        """Test formatting a template."""
        template = get_prompt_template("answer")
        system, user = template.format(
            context="Some context here.",
            question="What is the answer?",
        )
        assert "Some context here." in user
        assert "What is the answer?" in user
        assert len(system) > 0

    def test_list_templates(self):
        """Test listing available templates."""
        templates = list_templates()
        assert "answer" in templates
        assert "chat" in templates
        assert "summarise" in templates

    def test_get_unknown_template(self):
        """Test getting an unknown template raises error."""
        with pytest.raises(KeyError):
            get_prompt_template("nonexistent")

    def test_register_custom_template(self):
        """Test registering a custom template."""
        custom = PromptTemplate(
            name="custom_test",
            system_prompt="Test system",
            user_template="Test {question}",
        )
        register_template(custom)
        retrieved = get_prompt_template("custom_test")
        assert retrieved.name == "custom_test"


class TestContextWindow:
    """Tests for ContextWindow."""

    def test_create_context_window(self):
        """Test creating a context window."""
        window = ContextWindow(max_tokens=4096, reserved_tokens=1024)
        assert window.available_tokens == 3072

    def test_estimate_tokens(self):
        """Test token estimation."""
        window = ContextWindow()
        # Approx 4 chars per token
        tokens = window.estimate_tokens("Hello world!")
        assert tokens == 3  # 12 chars / 4

    def test_add_context(self):
        """Test adding context."""
        window = ContextWindow(max_tokens=1000, reserved_tokens=0)
        ctx = RetrievedContext(
            content="Test content",
            source="test.pdf",
            score=0.9,
        )
        assert window.add_context(ctx) is True
        assert len(window) == 1

    def test_add_context_overflow(self):
        """Test adding context when window is full."""
        window = ContextWindow(max_tokens=10, reserved_tokens=0)
        ctx = RetrievedContext(
            content="A" * 1000,  # Very long content
            source="test.pdf",
            score=0.9,
        )
        assert window.add_context(ctx) is False
        assert len(window) == 0

    def test_format_context(self):
        """Test formatting context with numbered citations."""
        window = ContextWindow()
        ctx = RetrievedContext(
            content="Test content here",
            source="test.pdf",
            score=0.9,
            page_number=5,
        )
        window.add_context(ctx)
        formatted = window.format_context()
        assert "[1] test.pdf" in formatted
        assert "page 5" in formatted
        assert "Test content here" in formatted

    def test_format_empty_context(self):
        """Test formatting empty context."""
        window = ContextWindow()
        formatted = window.format_context()
        assert "No relevant context found" in formatted

    def test_get_citations(self):
        """Test getting citations from context."""
        window = ContextWindow()
        ctx = RetrievedContext(
            content="Test",
            source="test.pdf",
            score=0.9,
            document_id="doc1",
        )
        window.add_context(ctx)
        citations = window.get_citations()
        assert len(citations) == 1
        assert citations[0].filename == "test.pdf"

    def test_clear(self):
        """Test clearing context."""
        window = ContextWindow()
        ctx = RetrievedContext(content="Test", source="test.pdf", score=0.9)
        window.add_context(ctx)
        assert len(window) == 1
        window.clear()
        assert len(window) == 0


class TestRetrievedContext:
    """Tests for RetrievedContext."""

    def test_create_retrieved_context(self):
        """Test creating retrieved context."""
        ctx = RetrievedContext(
            content="Content here",
            source="test.pdf",
            score=0.85,
            page_number=10,
            chunk_index=5,
        )
        assert ctx.content == "Content here"
        assert ctx.source == "test.pdf"
        assert ctx.score == 0.85

    def test_to_citation(self):
        """Test converting to citation."""
        ctx = RetrievedContext(
            content="Content",
            source="test.pdf",
            score=0.9,
            page_number=3,
            document_id="doc123",
        )
        citation = ctx.to_citation()
        assert citation.filename == "test.pdf"
        assert citation.page_number == 3
        assert citation.document_id == "doc123"


class TestChatHistory:
    """Tests for ChatHistory."""

    def test_create_history(self):
        """Test creating chat history."""
        history = ChatHistory(session_id="test-session")
        assert history.session_id == "test-session"
        assert len(history) == 0

    def test_add_messages(self):
        """Test adding messages."""
        history = ChatHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there!")
        assert len(history) == 2
        assert history.messages[0].role == ChatRole.USER
        assert history.messages[1].role == ChatRole.ASSISTANT

    def test_get_recent(self):
        """Test getting recent messages."""
        history = ChatHistory()
        for i in range(10):
            history.add_user_message(f"Message {i}")

        recent = history.get_recent(3)
        assert len(recent) == 3
        assert "Message 7" in recent[0].content

    def test_format_for_prompt(self):
        """Test formatting for prompt."""
        history = ChatHistory()
        history.add_user_message("What is RAG?")
        history.add_assistant_message("RAG is Retrieval-Augmented Generation.")

        formatted = history.format_for_prompt(n=2)
        assert "User:" in formatted
        assert "Assistant:" in formatted
        assert "RAG" in formatted

    def test_clear(self):
        """Test clearing history."""
        history = ChatHistory()
        history.add_user_message("Test")
        assert len(history) == 1
        history.clear()
        assert len(history) == 0

    def test_to_dict(self):
        """Test serialising to dict."""
        history = ChatHistory(session_id="sess123")
        history.add_user_message("Hello")

        data = history.to_dict()
        assert data["session_id"] == "sess123"
        assert len(data["messages"]) == 1

    def test_from_dict(self):
        """Test deserialising from dict."""
        data = {
            "session_id": "sess456",
            "created_at": "2024-01-01T12:00:00",
            "messages": [
                {"role": "user", "content": "Hello", "citations": [], "metadata": {}}
            ],
            "metadata": {},
        }
        history = ChatHistory.from_dict(data)
        assert history.session_id == "sess456"
        assert len(history) == 1


class TestHistoryPersistence:
    """Tests for history save/load."""

    def test_save_and_load_history(self, tmp_path):
        """Test saving and loading history."""
        history = ChatHistory(session_id="test")
        history.add_user_message("Hello")
        history.add_assistant_message("Hi!")

        path = tmp_path / "history.json"
        save_history(history, path)

        loaded = load_history(path)
        assert loaded.session_id == "test"
        assert len(loaded) == 2

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading nonexistent file."""
        path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_history(path)


class TestBuildContext:
    """Tests for build_context_from_results helper."""

    def test_build_context_empty(self):
        """Test building context from empty results."""
        context, citations = build_context_from_results([])
        assert "No relevant context" in context
        assert len(citations) == 0


class TestChatRole:
    """Tests for ChatRole enum."""

    def test_chat_roles(self):
        """Test chat role values."""
        assert ChatRole.USER.value == "user"
        assert ChatRole.ASSISTANT.value == "assistant"
        assert ChatRole.SYSTEM.value == "system"
