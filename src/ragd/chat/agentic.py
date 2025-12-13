"""Agentic RAG for ragd.

Implements CRAG (Corrective RAG) and Self-RAG patterns for improved
retrieval and generation quality.

v1.0.5: Configuration exposure - prompts and parameters now configurable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ragd.chat.context import build_context_from_results
from ragd.chat.message import CitedAnswer
from ragd.chat.prompts import get_prompt_template
from ragd.citation import Citation
from ragd.config import RagdConfig, load_config
from ragd.llm import OllamaClient, OllamaError
from ragd.prompts import get_prompt
from ragd.prompts.defaults import (
    FAITHFULNESS_EVAL_PROMPT as DEFAULT_FAITHFULNESS_EVAL,
    QUERY_REWRITE_PROMPT as DEFAULT_QUERY_REWRITE,
    REFINE_RESPONSE_PROMPT as DEFAULT_REFINE_RESPONSE,
    RELEVANCE_EVAL_PROMPT as DEFAULT_RELEVANCE_EVAL,
)
from ragd.search.hybrid import HybridSearcher, HybridSearchResult, SearchMode


class RetrievalQuality(str, Enum):
    """Quality assessment of retrieval."""

    EXCELLENT = "excellent"  # > 0.8
    GOOD = "good"  # 0.6 - 0.8
    POOR = "poor"  # 0.4 - 0.6
    IRRELEVANT = "irrelevant"  # < 0.4


@dataclass
class AgenticConfig:
    """Configuration for agentic RAG.

    Attributes:
        crag_enabled: Enable Corrective RAG (query rewriting)
        self_rag_enabled: Enable Self-RAG (response assessment)
        relevance_threshold: Minimum relevance score for CRAG evaluation
        faithfulness_threshold: Minimum faithfulness score
        max_rewrites: Maximum query rewrite attempts
        max_refinements: Maximum response refinement attempts
        context_window: Max context tokens (None = auto-detect)
        min_relevance: Minimum relevance for context chunks
    """

    crag_enabled: bool = True
    self_rag_enabled: bool = True
    relevance_threshold: float = 0.6
    faithfulness_threshold: float = 0.7
    max_rewrites: int = 2
    max_refinements: int = 1
    context_window: int | None = None  # None = auto-detect from model card
    min_relevance: float = 0.3  # For context chunk filtering


@dataclass
class AgenticResponse:
    """Response from agentic RAG.

    Attributes:
        answer: Generated answer text
        confidence: Overall confidence score (0-1)
        retrieval_quality: Quality assessment of retrieval
        rewrites_attempted: Number of query rewrites attempted
        refinements_attempted: Number of response refinements
        citations: Source citations
        metadata: Additional metadata
    """

    answer: str
    confidence: float
    retrieval_quality: RetrievalQuality
    rewrites_attempted: int = 0
    refinements_attempted: int = 0
    citations: list[Citation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_cited_answer(self) -> CitedAnswer:
        """Convert to CitedAnswer format."""
        return CitedAnswer(
            answer=self.answer,
            citations=self.citations,
            confidence=self.confidence,
        )


# Note: Default prompts are now in ragd.prompts.defaults
# Custom prompts can be configured via config.yaml or prompt files


class AgenticRAG:
    """Agentic RAG with CRAG and Self-RAG capabilities."""

    def __init__(
        self,
        config: RagdConfig | None = None,
        agentic_config: AgenticConfig | None = None,
    ) -> None:
        """Initialise agentic RAG.

        Args:
            config: ragd configuration
            agentic_config: Agentic-specific configuration
        """
        self.config = config or load_config()
        self.agentic = agentic_config or AgenticConfig()

        # Auto-detect context window from model card if not set
        if self.agentic.context_window is None:
            self.agentic.context_window = self._resolve_context_window()

        self._llm = OllamaClient(
            base_url=self.config.llm.base_url,
            model=self.config.llm.model,
            timeout_seconds=120,
        )
        self._searcher = HybridSearcher(config=self.config)

    def _resolve_context_window(self) -> int:
        """Resolve context window size from model card, Ollama, or fallback.

        Priority:
        1. Model card context_length
        2. Ollama API (/api/show)
        3. Default fallback (4096)

        Returns:
            Context window size in tokens
        """
        # Try model card first
        try:
            from ragd.models.cards import load_model_card

            card = load_model_card(self.config.llm.model)
            if card and card.context_length:
                return card.context_length
        except Exception:
            pass

        # Fallback: query Ollama directly
        try:
            ctx_length = self._llm.get_context_length()
            if ctx_length:
                return ctx_length
        except Exception:
            pass

        return 4096  # Default fallback

    def ask(
        self,
        question: str,
        max_results: int = 5,
        agentic: bool | None = None,
    ) -> AgenticResponse:
        """Ask a question with agentic RAG.

        Args:
            question: User question
            max_results: Maximum search results
            agentic: Override agentic mode (None = use config)

        Returns:
            AgenticResponse with answer and metadata
        """
        use_agentic = agentic if agentic is not None else (
            self.agentic.crag_enabled or self.agentic.self_rag_enabled
        )

        # Initial retrieval
        results = self._retrieve(question, max_results)

        if not results:
            return self._no_results_response(question)

        context, citations = build_context_from_results(
            results,
            max_tokens=self.agentic.context_window,
            max_results=max_results,
            min_relevance=self.agentic.min_relevance,
        )

        # CRAG: Evaluate and potentially rewrite query
        rewrites = 0
        relevance_score = 1.0  # Default if not using CRAG

        # Use config thresholds (from config.yaml) or AgenticConfig defaults
        relevance_threshold = self.config.agentic_params.relevance_threshold
        faithfulness_threshold = self.config.agentic_params.faithfulness_threshold

        if use_agentic and self.agentic.crag_enabled:
            relevance_score = self._evaluate_relevance(question, context)

            # Rewrite if relevance is poor
            while (
                relevance_score < relevance_threshold
                and rewrites < self.agentic.max_rewrites
            ):
                rewrites += 1
                rewritten = self._rewrite_query(question, context)

                if rewritten and rewritten != question:
                    results = self._retrieve(rewritten, max_results)
                    if results:
                        context, citations = build_context_from_results(
                            results,
                            max_tokens=self.agentic.context_window,
                            max_results=max_results,
                            min_relevance=self.agentic.min_relevance,
                        )
                        relevance_score = self._evaluate_relevance(rewritten, context)
                else:
                    break  # No new query, stop

        # Generate response
        answer = self._generate(question, context)

        # Self-RAG: Evaluate faithfulness
        refinements = 0
        faithfulness_score = 1.0

        if use_agentic and self.agentic.self_rag_enabled:
            faithfulness_score = self._evaluate_faithfulness(answer, context)

            # Refine if faithfulness is poor
            if (
                faithfulness_score < faithfulness_threshold
                and refinements < self.agentic.max_refinements
            ):
                refinements += 1
                answer = self._refine_response(question, answer, context)
                faithfulness_score = self._evaluate_faithfulness(answer, context)

        # Calculate overall confidence
        confidence = self._calculate_confidence(relevance_score, faithfulness_score)

        return AgenticResponse(
            answer=answer,
            confidence=confidence,
            retrieval_quality=self._quality_from_score(relevance_score),
            rewrites_attempted=rewrites,
            refinements_attempted=refinements,
            citations=citations,
            metadata={
                "relevance_score": relevance_score,
                "faithfulness_score": faithfulness_score,
                "agentic_enabled": use_agentic,
            },
        )

    def _retrieve(
        self,
        query: str,
        limit: int,
    ) -> list[HybridSearchResult]:
        """Retrieve relevant context.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Search results
        """
        try:
            return self._searcher.search(
                query=query,
                limit=limit,
                mode=SearchMode.HYBRID,
            )
        except Exception:
            return []

    def _evaluate_relevance(self, query: str, context: str) -> float:
        """Evaluate relevance of retrieved context.

        Args:
            query: Original query
            context: Retrieved context

        Returns:
            Relevance score (0-1)
        """
        try:
            # Load prompt from config or defaults
            prompt_template = get_prompt(
                self.config.agentic_prompts.relevance_eval,
                DEFAULT_RELEVANCE_EVAL,
                category="agentic",
                name="relevance_eval",
            )
            truncation = self.config.processing.context_truncation_chars
            prompt = prompt_template.format(
                query=query,
                context=context[:truncation],
            )
            params = self.config.agentic_params.relevance_eval
            response = self._llm.generate(
                prompt=prompt,
                temperature=params.temperature or 0.0,
                max_tokens=params.max_tokens or 10,
            )
            return self._extract_score(response.content)
        except OllamaError:
            return 0.5  # Default on error

    def _rewrite_query(self, query: str, context: str) -> str | None:
        """Rewrite query for better retrieval.

        Args:
            query: Original query
            context: Poor retrieval context

        Returns:
            Rewritten query or None
        """
        try:
            # Load prompt from config or defaults
            prompt_template = get_prompt(
                self.config.agentic_prompts.query_rewrite,
                DEFAULT_QUERY_REWRITE,
                category="agentic",
                name="query_rewrite",
            )
            # Summarise context for rewrite prompt
            summary = context[:500] + "..." if len(context) > 500 else context

            prompt = prompt_template.format(
                query=query,
                summary=summary,
            )
            params = self.config.agentic_params.query_rewrite
            response = self._llm.generate(
                prompt=prompt,
                temperature=params.temperature or 0.3,
                max_tokens=params.max_tokens or 100,
            )
            rewritten = response.content.strip()
            return rewritten if rewritten else None
        except OllamaError:
            return None

    def _generate(self, question: str, context: str) -> str:
        """Generate response from context.

        Args:
            question: User question
            context: Retrieved context

        Returns:
            Generated answer
        """
        template = get_prompt_template("answer")
        system_prompt, user_prompt = template.format(
            context=context,
            question=question,
        )

        try:
            params = self.config.agentic_params.answer_generation
            response = self._llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=params.temperature or 0.7,
                max_tokens=params.max_tokens or 1024,
            )
            return response.content
        except OllamaError as e:
            return f"Error generating response: {e}"

    def _evaluate_faithfulness(self, answer: str, context: str) -> float:
        """Evaluate faithfulness of response to context.

        Args:
            answer: Generated answer
            context: Source context

        Returns:
            Faithfulness score (0-1)
        """
        try:
            # Load prompt from config or defaults
            prompt_template = get_prompt(
                self.config.agentic_prompts.faithfulness_eval,
                DEFAULT_FAITHFULNESS_EVAL,
                category="agentic",
                name="faithfulness_eval",
            )
            truncation = self.config.processing.context_truncation_chars
            prompt = prompt_template.format(
                response=answer,
                context=context[:truncation],
            )
            params = self.config.agentic_params.faithfulness_eval
            response = self._llm.generate(
                prompt=prompt,
                temperature=params.temperature or 0.0,
                max_tokens=params.max_tokens or 10,
            )
            return self._extract_score(response.content)
        except OllamaError:
            return 0.5

    def _refine_response(
        self,
        question: str,
        answer: str,
        context: str,
    ) -> str:
        """Refine response for better faithfulness.

        Args:
            question: Original question
            answer: Initial answer
            context: Source context

        Returns:
            Refined answer
        """
        # Load prompt from config or defaults
        prompt_template = get_prompt(
            self.config.agentic_prompts.refine_response,
            DEFAULT_REFINE_RESPONSE,
            category="agentic",
            name="refine_response",
        )
        truncation = self.config.processing.context_truncation_chars
        refine_prompt = prompt_template.format(
            answer=answer,
            context=context[:truncation],
            question=question,
        )

        try:
            params = self.config.agentic_params.refine_response
            response = self._llm.generate(
                prompt=refine_prompt,
                temperature=params.temperature or 0.3,
                max_tokens=params.max_tokens or 1024,
            )
            return response.content
        except OllamaError:
            return answer  # Return original on error

    def _extract_score(self, text: str) -> float:
        """Extract numeric score from LLM response.

        Args:
            text: LLM response text

        Returns:
            Score (0-1), defaults to 0.5
        """
        # Find decimal number in response
        match = re.search(r"(\d+\.?\d*)", text.strip())
        if match:
            try:
                score = float(match.group(1))
                # Clamp to 0-1 range
                return max(0.0, min(1.0, score))
            except ValueError:
                pass
        return 0.5

    def _calculate_confidence(
        self,
        relevance: float,
        faithfulness: float,
    ) -> float:
        """Calculate overall confidence score.

        Args:
            relevance: Retrieval relevance score
            faithfulness: Response faithfulness score

        Returns:
            Combined confidence (0-1)
        """
        # Weighted average favouring faithfulness
        rel_weight = self.config.agentic_params.confidence_relevance_weight
        faith_weight = self.config.agentic_params.confidence_faithfulness_weight
        return rel_weight * relevance + faith_weight * faithfulness

    def _quality_from_score(self, score: float) -> RetrievalQuality:
        """Convert numeric score to quality enum.

        Args:
            score: Relevance score

        Returns:
            RetrievalQuality enum value
        """
        thresholds = self.config.agentic_params
        if score >= thresholds.excellent_threshold:
            return RetrievalQuality.EXCELLENT
        elif score >= thresholds.good_threshold:
            return RetrievalQuality.GOOD
        elif score >= thresholds.poor_threshold:
            return RetrievalQuality.POOR
        else:
            return RetrievalQuality.IRRELEVANT

    def _no_results_response(self, question: str) -> AgenticResponse:
        """Generate response when no results found.

        Args:
            question: Original question

        Returns:
            Response indicating no results
        """
        return AgenticResponse(
            answer=(
                "I couldn't find any relevant information in your knowledge base "
                f"for: '{question}'. Try indexing more documents or rephrasing your question."
            ),
            confidence=0.0,
            retrieval_quality=RetrievalQuality.IRRELEVANT,
            rewrites_attempted=0,
            refinements_attempted=0,
            citations=[],
        )

    def close(self) -> None:
        """Close resources."""
        self._searcher.close()


def agentic_ask(
    question: str,
    config: RagdConfig | None = None,
    max_results: int = 5,
    agentic: bool = True,
) -> AgenticResponse:
    """Ask a question with agentic RAG (convenience function).

    Args:
        question: Question to ask
        config: ragd configuration
        max_results: Maximum search results
        agentic: Enable agentic mode

    Returns:
        AgenticResponse with answer and metadata
    """
    rag = AgenticRAG(config=config)
    try:
        return rag.ask(question, max_results=max_results, agentic=agentic)
    finally:
        rag.close()
