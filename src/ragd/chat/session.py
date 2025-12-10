"""Chat session management for ragd.

Provides the main ChatSession class for conversational RAG.
"""

from __future__ import annotations

import logging
import uuid

logger = logging.getLogger(__name__)
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragd.citation import ValidationReport

from ragd.chat.context import (
    ContextWindow,
    build_context_from_results,
    calculate_token_budget,
)
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
        context_window: Max context tokens (None = auto-detect from model card)
        history_turns: Previous turns to include in prompt
        search_limit: Maximum search results
        auto_save: Auto-save history after each response
        min_relevance: Minimum relevance score for context chunks
        history_budget_ratio: Ratio of available tokens for history
        min_history_tokens: Minimum tokens for history
        min_context_tokens: Minimum tokens for context
        rewrite_history_turns: History turns for query rewriting
    """

    model: str = "llama3.2:3b"
    temperature: float = 0.7
    max_tokens: int = 1024
    context_window: int | None = None  # None = auto-detect from model card
    history_turns: int = 5
    search_limit: int = 5
    auto_save: bool = True
    min_relevance: float = 0.55  # Raised from 0.3 to reduce hallucination
    history_budget_ratio: float = 0.3
    min_history_tokens: int = 256
    min_context_tokens: int = 1024
    rewrite_history_turns: int = 4
    # Citation validation settings
    validate_citations: bool = True  # Enable citation validation by default
    validation_mode: str = "warn"  # warn | filter | strict


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

        # Auto-detect context window from model card if not explicitly set
        if self.chat_config.context_window is None:
            self.chat_config.context_window = self._resolve_context_window()

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

    def _resolve_context_window(self) -> int:
        """Resolve context window size from model card or fallback.

        Returns:
            Context window size in tokens
        """
        try:
            from ragd.models.cards import load_model_card

            card = load_model_card(self.chat_config.model)
            if card and card.context_length:
                return card.context_length
        except Exception:
            pass  # Fall back to default

        return 4096  # Default fallback

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

        # Calculate token budget based on actual history size
        preliminary_history = self._history.format_for_prompt(
            n=self.chat_config.history_turns - 1  # Exclude current message
        )
        budget = calculate_token_budget(
            context_window=self.chat_config.context_window,
            reserved_tokens=self.chat_config.max_tokens,
            history_ratio=self.chat_config.history_budget_ratio,
            actual_history_chars=len(preliminary_history),
            min_history=self.chat_config.min_history_tokens,
            min_context=self.chat_config.min_context_tokens,
        )

        # Rewrite follow-up queries to include conversation context
        enhanced_query = self._rewrite_query_with_context(question)

        # Retrieve relevant context with allocated budget
        results = self._retrieve(enhanced_query)
        context, citations = build_context_from_results(
            results,
            max_tokens=budget.context + self.chat_config.max_tokens,
            reserved_tokens=self.chat_config.max_tokens,
            max_results=self.chat_config.search_limit,
            min_relevance=self.chat_config.min_relevance,
        )

        # Get prompt template with config (overrides and citation instruction)
        if isinstance(template, str):
            template = get_prompt_template(template, config=self.config.chat.prompts)

        # Format history with token budget truncation
        history_text = self._history.format_for_prompt(
            n=self.chat_config.history_turns - 1,
            max_tokens=budget.history,
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

    def _rewrite_query_with_context(self, question: str) -> str:
        """Rewrite ambiguous follow-up queries using LLM.

        Uses conversation history to make the query self-contained.
        E.g., "tell me more" → "tell me more about data sovereignty"

        Also performs deterministic document reference resolution to match
        partial references like "the hummel paper" to exact filenames.

        Args:
            question: User's question

        Returns:
            Enhanced query with context, or original if no enhancement needed
        """
        # Indicators that suggest the query needs context from conversation
        FOLLOW_UP_INDICATORS = [
            "it", "this", "that", "these", "those",
            "the concept", "the topic", "the subject",
            "paper", "document", "article",  # Referenced sources
            "more about", "else about", "what else",
            "tell me more", "elaborate", "expand",
            "continue", "go on", "and",
        ]

        question_lower = question.lower()
        needs_rewrite = any(ind in question_lower for ind in FOLLOW_UP_INDICATORS)

        if not needs_rewrite:
            return question

        # Get recent history - need at least one previous exchange
        recent = self._history.get_recent(4)
        if not recent:
            return question

        # Format history for the rewrite prompt
        history_text = self._history.format_for_prompt(
            n=self.chat_config.rewrite_history_turns
        )
        if not history_text.strip():
            return question

        # Get cited documents from recent conversation for context
        cited_docs = self._history.get_cited_documents(
            n=self.chat_config.rewrite_history_turns
        )
        doc_context = "\n".join(f"- {f}" for f in cited_docs) if cited_docs else "None"

        # Resolve document references deterministically (e.g., "hummel paper" -> filename)
        resolved_refs = self._resolve_document_references(question)

        # Use the configured query rewrite prompt
        prompt = self.config.chat.prompts.query_rewrite.format(
            history=history_text,
            question=question,
            cited_documents=doc_context,
            resolved_references=resolved_refs,
        )

        try:
            response = self._llm.generate(
                prompt=prompt,
                temperature=0.3,  # Low temperature for deterministic rewriting
                max_tokens=100,
            )
            rewritten = response.content.strip()

            # Only use rewritten query if it's meaningfully different
            if rewritten and rewritten.lower() != question.lower():
                logger.debug("Query rewritten: '%s' → '%s'", question, rewritten)
                return rewritten
            return question

        except OllamaError:
            # Fall back to original on error
            return question

    def _resolve_document_references(self, question: str) -> str:
        """Resolve partial document references to exact filenames.

        Uses citation metadata (author_hint, year) from recent conversation
        to match references like "the hummel paper" to exact filenames.

        Args:
            question: User's question

        Returns:
            Formatted string of resolved references, or "None"
        """
        from ragd.chat.reference_resolver import resolve_document_references

        # Get full Citation objects (not just filenames) for metadata
        recent_citations = self._history.get_recent_citations(
            n=self.chat_config.rewrite_history_turns
        )

        if not recent_citations:
            return "None"

        resolutions = resolve_document_references(question, recent_citations)

        if not resolutions:
            return "None"

        # Format as: "hummel paper" -> hummel-et-al-2021-data-sovereignty.pdf
        return "\n".join(
            f'- "{r.original_text}" → {r.matched_filename}'
            for r in resolutions
            if r.original_text  # Skip token-match-only results
        ) or "None"

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

            # Validate citations if enabled
            validation_report = None
            if self.chat_config.validate_citations and citations:
                validation_report = self._validate_citations(
                    response.content, citations
                )

            answer = CitedAnswer(
                answer=response.content,
                citations=citations,
                model=response.model,
                tokens_used=response.tokens_used,
                validation_report=validation_report,
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

    def _validate_citations(
        self,
        response_text: str,
        citations: list[Citation],
    ) -> "ValidationReport":
        """Validate citations in a response.

        Uses keyword overlap to check if cited documents contain
        content supporting the claims made.

        Args:
            response_text: LLM-generated response
            citations: Source citations

        Returns:
            ValidationReport with results for each citation usage
        """
        from ragd.citation import (
            CitationValidator,
            ValidationMode,
            extract_citation_markers,
        )

        extracted = extract_citation_markers(response_text)
        validator = CitationValidator(
            mode=ValidationMode(self.chat_config.validation_mode),
            use_semantic=False,  # Keyword-only for performance
        )
        return validator.validate(response_text, citations, extracted)

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
