"""Chat session management for ragd.

Provides the main ChatSession class for conversational RAG.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ragd.chat.context import ContextWindow, build_context_from_results
from ragd.chat.history import ChatHistory, get_history_path, save_history
from ragd.chat.message import ChatMessage, ChatRole, CitedAnswer
from ragd.chat.prompts import PromptTemplate, get_prompt_template
from ragd.citation import Citation
from ragd.config import RagdConfig, load_config
from ragd.llm import LLMResponse, OllamaClient, OllamaError, StreamChunk
from ragd.search.hybrid import HybridSearcher, HybridSearchResult, SearchMode

# Response when no relevant context is found
NO_CONTEXT_RESPONSE = (
    "I don't have information about that in my indexed documents.\n\n"
    "Suggestions:\n"
    "- Try rephrasing your question with different keywords\n"
    "- Run 'ragd search \"your query\"' to check if relevant content exists\n"
    "- Run 'ragd stats' to see what topics are indexed"
)


@dataclass
class ChatConfig:
    """Configuration for chat sessions.

    Attributes:
        model: LLM model to use
        temperature: Sampling temperature
        max_tokens: Maximum response tokens
        context_window: Max context tokens
        history_turns: Previous turns to include in prompt
        search_limit: Maximum search results
        auto_save: Auto-save history after each response
    """

    model: str = "llama3.2:3b"
    temperature: float = 0.7
    max_tokens: int = 1024
    context_window: int = 4096
    history_turns: int = 5
    search_limit: int = 5
    auto_save: bool = True


class ChatSession:
    """A chat session with RAG-powered responses.

    Manages conversation state, retrieval, and LLM generation.
    """

    def __init__(
        self,
        config: RagdConfig | None = None,
        chat_config: ChatConfig | None = None,
        session_id: str | None = None,
    ) -> None:
        """Initialise chat session.

        Args:
            config: ragd configuration
            chat_config: Chat-specific configuration
            session_id: Unique session identifier
        """
        self.config = config or load_config()
        self.chat_config = chat_config or ChatConfig()
        self.session_id = session_id or str(uuid.uuid4())[:8]

        # Initialise components
        self._llm = OllamaClient(
            base_url=self.config.llm.base_url,
            model=self.chat_config.model,
            timeout_seconds=120,
        )
        self._searcher = HybridSearcher(config=self.config)
        self._history = ChatHistory(
            session_id=self.session_id,
            created_at=datetime.now(),
        )

    @property
    def history(self) -> ChatHistory:
        """Get conversation history."""
        return self._history

    def is_llm_available(self) -> bool:
        """Check if LLM is available.

        Returns:
            True if LLM is reachable
        """
        return self._llm.is_available()

    def ask(
        self,
        question: str,
        template: str | PromptTemplate = "answer",
        stream: bool = False,
    ) -> CitedAnswer | Iterator[str]:
        """Ask a question with RAG.

        Args:
            question: User question
            template: Prompt template name or instance
            stream: Stream response tokens

        Returns:
            CitedAnswer or iterator of response chunks if streaming
        """
        # Add user message to history
        self._history.add_user_message(question)

        # Retrieve relevant context
        results = self._retrieve(question)
        context, citations = build_context_from_results(
            results,
            max_tokens=self.chat_config.context_window,
            max_results=self.chat_config.search_limit,
        )

        # Get prompt template with citation instruction from config
        if isinstance(template, str):
            citation_instruction = self.config.chat.prompts.citation_instruction
            template = get_prompt_template(template, citation_instruction)

        # Format prompt
        history_text = self._history.format_for_prompt(
            n=self.chat_config.history_turns - 1  # Exclude current message
        )
        system_prompt, user_prompt = template.format(
            context=context,
            question=question,
            history=history_text,
        )

        if stream:
            return self._stream_response(
                system_prompt, user_prompt, citations
            )
        else:
            return self._generate_response(
                system_prompt, user_prompt, citations
            )

    def _retrieve(self, query: str) -> list[HybridSearchResult]:
        """Retrieve relevant context for a query.

        Args:
            query: Search query

        Returns:
            List of search results
        """
        return self._searcher.search(
            query=query,
            limit=self.chat_config.search_limit * 2,  # Fetch extra for filtering
            mode=SearchMode.HYBRID,
        )

    def _generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        citations: list[Citation],
    ) -> CitedAnswer:
        """Generate a non-streaming response.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt with context
            citations: Source citations

        Returns:
            CitedAnswer with response and citations
        """
        # Empty-context guard: return helpful message if no relevant context
        if not citations:
            answer = CitedAnswer(
                answer=NO_CONTEXT_RESPONSE,
                citations=[],
            )
            self._history.add_assistant_message(NO_CONTEXT_RESPONSE, citations=[])
            if self.chat_config.auto_save:
                self._save_history()
            return answer

        try:
            response = self._llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=self.chat_config.temperature,
                max_tokens=self.chat_config.max_tokens,
            )

            answer = CitedAnswer(
                answer=response.content,
                citations=citations,
                model=response.model,
                tokens_used=response.tokens_used,
            )

            # Add to history
            self._history.add_assistant_message(
                response.content,
                citations=citations,
            )

            # Auto-save if enabled
            if self.chat_config.auto_save:
                self._save_history()

            return answer

        except OllamaError as e:
            # Return error as answer
            error_answer = CitedAnswer(
                answer=f"Error generating response: {e}",
                citations=[],
            )
            return error_answer

    def _stream_response(
        self,
        system_prompt: str,
        user_prompt: str,
        citations: list[Citation],
    ) -> Iterator[str]:
        """Generate a streaming response.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt with context
            citations: Source citations

        Yields:
            Response chunks as strings
        """
        # Empty-context guard: return helpful message if no relevant context
        if not citations:
            self._history.add_assistant_message(NO_CONTEXT_RESPONSE, citations=[])
            if self.chat_config.auto_save:
                self._save_history()
            yield NO_CONTEXT_RESPONSE
            return

        full_response = ""

        try:
            for chunk in self._llm.generate_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=self.chat_config.temperature,
                max_tokens=self.chat_config.max_tokens,
            ):
                full_response += chunk.content
                yield chunk.content

                if chunk.done:
                    break

            # Add complete response to history
            self._history.add_assistant_message(
                full_response,
                citations=citations,
            )

            # Auto-save if enabled
            if self.chat_config.auto_save:
                self._save_history()

        except OllamaError as e:
            yield f"\nError: {e}"

    def chat(
        self,
        message: str,
        stream: bool = False,
    ) -> CitedAnswer | Iterator[str]:
        """Continue conversation with context from history.

        Args:
            message: User message
            stream: Stream response tokens

        Returns:
            CitedAnswer or iterator of response chunks
        """
        return self.ask(message, template="chat", stream=stream)

    def summarise(
        self,
        topic: str,
        stream: bool = False,
    ) -> CitedAnswer | Iterator[str]:
        """Summarise information about a topic.

        Args:
            topic: Topic to summarise
            stream: Stream response tokens

        Returns:
            CitedAnswer or iterator of response chunks
        """
        return self.ask(topic, template="summarise", stream=stream)

    def _save_history(self) -> None:
        """Save history to file."""
        path = get_history_path(self.session_id)
        save_history(self._history, path)

    def close(self) -> None:
        """Close session and save history."""
        if self.chat_config.auto_save:
            self._save_history()
        self._searcher.close()


def ask_question(
    question: str,
    config: RagdConfig | None = None,
    model: str = "llama3.2:3b",
    temperature: float = 0.7,
    max_results: int = 5,
    stream: bool = False,
) -> CitedAnswer | Iterator[str]:
    """Ask a single question (convenience function).

    Args:
        question: Question to ask
        config: ragd configuration
        model: LLM model to use
        temperature: Sampling temperature
        max_results: Maximum search results
        stream: Stream response

    Returns:
        CitedAnswer or iterator of response chunks
    """
    chat_config = ChatConfig(
        model=model,
        temperature=temperature,
        search_limit=max_results,
        auto_save=False,
    )

    session = ChatSession(config=config, chat_config=chat_config)
    try:
        return session.ask(question, stream=stream)
    finally:
        session.close()


def check_chat_available(config: RagdConfig | None = None) -> tuple[bool, str]:
    """Check if chat functionality is available.

    Args:
        config: ragd configuration

    Returns:
        Tuple of (available: bool, message: str)
    """
    config = config or load_config()

    try:
        client = OllamaClient(
            base_url=config.llm.base_url,
            model=config.llm.model,
        )

        if not client.is_available():
            models = client.list_models()
            if not models:
                return False, "Ollama running but no models installed"
            return False, f"Model '{config.llm.model}' not found. Available: {', '.join(models[:3])}"

        return True, f"Chat available with model '{config.llm.model}'"

    except OllamaError as e:
        if "Connection refused" in str(e):
            return False, "Ollama not running. Start with: ollama serve"
        return False, str(e)
