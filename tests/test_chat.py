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
from ragd.chat.session import ChatSession, ChatConfig
from ragd.llm import LLMResponse, OllamaError


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


class TestQueryRewritingWithContext:
    """Tests for query rewriting with conversation context."""

    @pytest.fixture
    def mock_session(self):
        """Create a ChatSession with mocked dependencies."""
        with patch("ragd.chat.session.OllamaClient") as MockClient, \
             patch("ragd.chat.session.HybridSearcher") as MockSearcher:

            mock_llm = MagicMock()
            MockClient.return_value = mock_llm
            MockSearcher.return_value = MagicMock()

            # Mock config with query_rewrite prompt
            mock_config = MagicMock()
            mock_config.chat.prompts.query_rewrite = (
                "Rewrite this follow-up question to be self-contained.\n\n"
                "Conversation:\n{history}\n\n"
                "Follow-up question: {question}\n\n"
                "Rewritten question:"
            )
            mock_config.llm.base_url = "http://localhost:11434"

            session = ChatSession(config=mock_config, chat_config=ChatConfig())
            session._llm = mock_llm

            yield session

    def test_follow_up_triggers_rewrite(self, mock_session):
        """Test that follow-up questions trigger query rewriting."""
        # Setup: Add prior conversation about data sovereignty
        mock_session._history.add_user_message("Tell me about data sovereignty")
        mock_session._history.add_assistant_message(
            "Data sovereignty refers to control over data..."
        )

        # Mock LLM to return rewritten query
        mock_session._llm.generate.return_value = LLMResponse(
            content="tell me more about data sovereignty",
            model="test",
            tokens_used=10,
        )

        # Follow-up question should be rewritten
        result = mock_session._rewrite_query_with_context(
            "what else can you tell me about the concept?"
        )

        assert "data sovereignty" in result.lower()
        mock_session._llm.generate.assert_called_once()

    def test_history_includes_original_topic(self, mock_session):
        """Test that rewrite prompt includes the original topic question.

        This is the key behavioural test: regardless of the specific
        history window size, the topic from the original question must
        be captured in the rewrite prompt.
        """
        # Setup: Conversation with topic in first message
        mock_session._history.add_user_message("Tell me about data sovereignty")
        mock_session._history.add_assistant_message("Data sovereignty is...")
        mock_session._history.add_user_message("what else?")

        # Capture the prompt sent to LLM
        captured_prompt = None

        def capture_call(**kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs.get("prompt", "")
            return LLMResponse(content="rewritten query", model="test", tokens_used=5)

        mock_session._llm.generate.side_effect = capture_call

        mock_session._rewrite_query_with_context("what else?")

        # The history in the prompt should contain "data sovereignty"
        assert captured_prompt is not None
        assert "data sovereignty" in captured_prompt.lower()

    def test_insufficient_history_window_loses_original_question(self):
        """Test that a small history window loses the original user question.

        This test verifies the bug scenario: with rewrite_history_turns=2,
        the original user question is lost (only assistant response + follow-up
        are captured). The assistant's response may or may not contain the topic.
        """
        with patch("ragd.chat.session.OllamaClient") as MockClient, \
             patch("ragd.chat.session.HybridSearcher") as MockSearcher:

            mock_llm = MagicMock()
            MockClient.return_value = mock_llm
            MockSearcher.return_value = MagicMock()

            mock_config = MagicMock()
            mock_config.chat.prompts.query_rewrite = (
                "Conversation:\n{history}\n\nQuestion: {question}\nRewritten:"
            )
            mock_config.llm.base_url = "http://localhost:11434"

            # Configure with SMALL history window (the bug)
            chat_config = ChatConfig(rewrite_history_turns=2)
            session = ChatSession(config=mock_config, chat_config=chat_config)
            session._llm = mock_llm

            # Build conversation where the specific topic phrase is ONLY
            # in the first user message (assistant gives generic response)
            session._history.add_user_message("Tell me about quantum computing")
            session._history.add_assistant_message("It's a fascinating field...")
            session._history.add_user_message("what else?")

            captured_prompt = None

            def capture_call(**kwargs):
                nonlocal captured_prompt
                captured_prompt = kwargs.get("prompt", "")
                return LLMResponse(content="rewritten", model="test", tokens_used=5)

            session._llm.generate.side_effect = capture_call
            session._rewrite_query_with_context("what else?")

            # With n=2, we only get last 2 messages - original question is LOST
            assert captured_prompt is not None
            # The original user question should NOT be in the prompt
            assert "quantum computing" not in captured_prompt.lower()

    def test_adequate_history_window_captures_original_question(self):
        """Test that adequate history window captures the original user question.

        This test verifies the fix: with rewrite_history_turns=4 (default),
        the original user question is captured.
        """
        with patch("ragd.chat.session.OllamaClient") as MockClient, \
             patch("ragd.chat.session.HybridSearcher") as MockSearcher:

            mock_llm = MagicMock()
            MockClient.return_value = mock_llm
            MockSearcher.return_value = MagicMock()

            mock_config = MagicMock()
            mock_config.chat.prompts.query_rewrite = (
                "Conversation:\n{history}\n\nQuestion: {question}\nRewritten:"
            )
            mock_config.llm.base_url = "http://localhost:11434"

            # Configure with ADEQUATE history window (the fix)
            chat_config = ChatConfig(rewrite_history_turns=4)
            session = ChatSession(config=mock_config, chat_config=chat_config)
            session._llm = mock_llm

            # Build conversation where the specific topic phrase is ONLY
            # in the first user message (assistant gives generic response)
            session._history.add_user_message("Tell me about quantum computing")
            session._history.add_assistant_message("It's a fascinating field...")
            session._history.add_user_message("what else?")

            captured_prompt = None

            def capture_call(**kwargs):
                nonlocal captured_prompt
                captured_prompt = kwargs.get("prompt", "")
                return LLMResponse(content="rewritten", model="test", tokens_used=5)

            session._llm.generate.side_effect = capture_call
            session._rewrite_query_with_context("what else?")

            # With n=4, we capture all messages including the original question
            assert captured_prompt is not None
            assert "quantum computing" in captured_prompt.lower()

    def test_standalone_question_not_rewritten(self, mock_session):
        """Test that standalone questions are not rewritten."""
        result = mock_session._rewrite_query_with_context(
            "What is machine learning?"
        )

        # Should return original - no LLM call needed
        assert result == "What is machine learning?"
        mock_session._llm.generate.assert_not_called()

    def test_rewrite_with_various_follow_up_indicators(self, mock_session):
        """Test various follow-up patterns trigger rewriting."""
        mock_session._history.add_user_message("Tell me about RAG")
        mock_session._history.add_assistant_message("RAG stands for...")

        mock_session._llm.generate.return_value = LLMResponse(
            content="rewritten", model="test", tokens_used=5,
        )

        follow_ups = [
            "tell me more",
            "what else about it?",
            "elaborate on this",
            "continue",
            "and the challenges?",
            "the concept seems interesting",
        ]

        for question in follow_ups:
            mock_session._llm.reset_mock()
            mock_session._rewrite_query_with_context(question)
            assert mock_session._llm.generate.called, \
                f"'{question}' should trigger rewrite"

    def test_rewrite_error_returns_original(self, mock_session):
        """Test that LLM errors fall back to original question."""
        mock_session._history.add_user_message("Tell me about X")
        mock_session._history.add_assistant_message("X is...")

        mock_session._llm.generate.side_effect = OllamaError("Connection failed")

        result = mock_session._rewrite_query_with_context("tell me more")

        # Should return original question on error
        assert result == "tell me more"

    def test_empty_history_returns_original(self, mock_session):
        """Test that empty history returns original question."""
        # No prior conversation
        result = mock_session._rewrite_query_with_context("tell me more")

        # Should return original - no context to rewrite from
        assert result == "tell me more"
        mock_session._llm.generate.assert_not_called()

    def test_rewrite_identical_returns_original(self, mock_session):
        """Test that identical rewrites return original."""
        mock_session._history.add_user_message("Tell me about X")
        mock_session._history.add_assistant_message("X is...")

        # LLM returns same question (no meaningful rewrite)
        mock_session._llm.generate.return_value = LLMResponse(
            content="tell me more",  # Same as input
            model="test",
            tokens_used=5,
        )

        result = mock_session._rewrite_query_with_context("tell me more")

        # Should return original when LLM doesn't improve it
        assert result == "tell me more"


class TestStreamingWordWrapper:
    """Tests for StreamingWordWrapper."""

    def test_basic_wrapping(self):
        """Test basic word wrapping at max width."""
        from io import StringIO
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        # Mock console that captures output
        output = []

        mock_console = MagicMock()
        mock_console.print = lambda *args, **kwargs: output.append(
            (args[0] if args else "", kwargs.get("end", "\n"))
        )

        wrapper = StreamingWordWrapper(mock_console, max_width=20, prefix_width=0)

        # Write text that should wrap
        wrapper.write("Hello world this is a test")
        wrapper.flush()

        # Reconstruct output
        result = ""
        for text, end in output:
            result += text + end

        # Should have wrapped at word boundaries
        lines = result.strip().split("\n")
        for line in lines:
            assert len(line.strip()) <= 20, f"Line too long: '{line}'"

    def test_word_not_broken(self):
        """Test that words are not broken mid-word."""
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        output = []

        mock_console = MagicMock()
        mock_console.print = lambda *args, **kwargs: output.append(
            (args[0] if args else "", kwargs.get("end", "\n"))
        )

        wrapper = StreamingWordWrapper(mock_console, max_width=15, prefix_width=0)

        # Word "sovereignty" is 11 chars, should not be broken at width 15
        wrapper.write("data sovereignty")
        wrapper.flush()

        # Check that "sovereignty" appears intact
        result = "".join(text for text, _ in output)
        assert "sovereignty" in result

    def test_respects_prefix_width(self):
        """Test that prefix width is accounted for."""
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        output = []
        mock_console = MagicMock()
        mock_console.print = lambda *args, **kwargs: output.append(
            (args[0] if args else "", kwargs.get("end", "\n"))
        )

        # With prefix_width=3 (for "A: ") and max_width=20, effective first line is 17 chars
        wrapper = StreamingWordWrapper(mock_console, max_width=20, prefix_width=3)

        wrapper.write("Hello world test")
        wrapper.flush()

        # First line should account for prefix
        # The wrapper doesn't output the prefix, but accounts for its width

    def test_newlines_preserved(self):
        """Test that explicit newlines are preserved."""
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        output = []
        newline_count = 0

        def mock_print(*args, **kwargs):
            nonlocal newline_count
            if kwargs.get("end", "\n") == "\n" and not args:
                newline_count += 1
            elif args:
                output.append(args[0])

        mock_console = MagicMock()
        mock_console.print = mock_print

        wrapper = StreamingWordWrapper(mock_console, max_width=80, prefix_width=0)

        wrapper.write("Line one\nLine two")
        wrapper.flush()

        # Should have at least one explicit newline
        assert newline_count >= 1

    def test_streaming_chunks(self):
        """Test that streaming partial chunks works correctly."""
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        output = []

        mock_console = MagicMock()
        mock_console.print = lambda *args, **kwargs: output.append(
            args[0] if args else ""
        )

        wrapper = StreamingWordWrapper(mock_console, max_width=50, prefix_width=0)

        # Simulate streaming chunks (like from LLM)
        chunks = ["Hel", "lo ", "wor", "ld ", "this ", "is a ", "test"]
        for chunk in chunks:
            wrapper.write(chunk)
        wrapper.flush()

        result = "".join(output)
        assert "Hello" in result
        assert "world" in result

    def test_very_long_word(self):
        """Test handling of words longer than max_width."""
        from unittest.mock import MagicMock
        from ragd.ui.cli.commands import StreamingWordWrapper

        output = []
        mock_console = MagicMock()
        mock_console.print = lambda *args, **kwargs: output.append(
            (args[0] if args else "", kwargs.get("end", "\n"))
        )

        # Very narrow width
        wrapper = StreamingWordWrapper(mock_console, max_width=10, prefix_width=0)

        # Word longer than max_width
        wrapper.write("supercalifragilisticexpialidocious")
        wrapper.flush()

        # Word should be split (this is the edge case handling)
        result = "".join(text for text, _ in output)
        assert "super" in result.lower()


class TestCitationOrdering:
    """Tests for citation ordering consistency."""

    def test_format_context_and_citations_same_order(self):
        """Test that format_context and get_deduplicated_citations use same order."""
        window = ContextWindow()

        # Add contexts from different documents in specific order
        ctx1 = RetrievedContext(
            content="Content from doc A",
            source="doc_a.pdf",
            score=0.9,
            document_id="doc_a",
        )
        ctx2 = RetrievedContext(
            content="Content from doc B",
            source="doc_b.pdf",
            score=0.8,
            document_id="doc_b",
        )
        ctx3 = RetrievedContext(
            content="More from doc A",
            source="doc_a.pdf",
            score=0.7,
            document_id="doc_a",
        )

        window.add_context(ctx1)
        window.add_context(ctx2)
        window.add_context(ctx3)

        # Get formatted context and citations
        formatted = window.format_context()
        citations = window.get_deduplicated_citations()

        # Check that [1] in formatted context corresponds to first citation
        assert "[1] doc_a.pdf" in formatted
        assert "[2] doc_b.pdf" in formatted
        assert citations[0].filename == "doc_a.pdf"
        assert citations[1].filename == "doc_b.pdf"

    def test_deduplication_preserves_insertion_order(self):
        """Test that deduplication preserves the order documents were first seen."""
        from ragd.chat.context import deduplicate_citations

        citations = [
            Citation(document_id="doc_b", filename="b.pdf"),
            Citation(document_id="doc_a", filename="a.pdf"),
            Citation(document_id="doc_b", filename="b.pdf"),  # Duplicate
            Citation(document_id="doc_c", filename="c.pdf"),
            Citation(document_id="doc_a", filename="a.pdf"),  # Duplicate
        ]

        unique = deduplicate_citations(citations)

        # Should be in order of first occurrence: b, a, c
        assert len(unique) == 3
        assert unique[0].document_id == "doc_b"
        assert unique[1].document_id == "doc_a"
        assert unique[2].document_id == "doc_c"

    def test_group_by_document_ordering(self):
        """Test that _group_by_document maintains insertion order."""
        window = ContextWindow()

        # Add in order: C, A, B
        window.add_context(RetrievedContext(
            content="C content", source="c.pdf", score=0.9, document_id="doc_c"
        ))
        window.add_context(RetrievedContext(
            content="A content", source="a.pdf", score=0.8, document_id="doc_a"
        ))
        window.add_context(RetrievedContext(
            content="B content", source="b.pdf", score=0.7, document_id="doc_b"
        ))

        groups = window._group_by_document()
        keys = list(groups.keys())

        # Should maintain insertion order: C, A, B
        assert keys == ["doc_c", "doc_a", "doc_b"]

    def test_multiple_chunks_same_document(self):
        """Test that multiple chunks from same doc get single citation."""
        window = ContextWindow()

        # Add multiple chunks from same document
        for i in range(3):
            window.add_context(RetrievedContext(
                content=f"Chunk {i}",
                source="same.pdf",
                score=0.9 - i * 0.1,
                document_id="same_doc",
                chunk_index=i,
            ))

        citations = window.get_deduplicated_citations()

        # Should only have one citation
        assert len(citations) == 1
        assert citations[0].filename == "same.pdf"
