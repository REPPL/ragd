"""Context window management for ragd chat.

Handles assembling retrieved content into context for LLM prompts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ragd.citation import Citation
from ragd.search.hybrid import HybridSearchResult

logger = logging.getLogger(__name__)

# Default minimum relevance score to include in context (v0.7.6)
DEFAULT_MIN_RELEVANCE = 0.3


@dataclass
class RetrievedContext:
    """A piece of retrieved context with metadata.

    Attributes:
        content: The text content
        source: Source document name
        score: Relevance score
        page_number: Page number (if applicable)
        chunk_index: Chunk index
        document_id: Document identifier
        metadata: Additional metadata
    """

    content: str
    source: str
    score: float
    page_number: int | None = None
    chunk_index: int | None = None
    document_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_search_result(cls, result: HybridSearchResult) -> RetrievedContext:
        """Create from a search result.

        Args:
            result: HybridSearchResult instance

        Returns:
            RetrievedContext instance
        """
        page_number = None
        if result.location:
            page_number = result.location.page_number
        if page_number is None:
            page_number = result.metadata.get("page_number")

        return cls(
            content=result.content,
            source=result.document_name or result.metadata.get("filename", "Unknown"),
            score=result.combined_score,
            page_number=page_number,
            chunk_index=result.chunk_index,
            document_id=result.document_id,
            metadata=result.metadata,
        )

    def to_citation(self) -> Citation:
        """Convert to Citation object.

        Returns:
            Citation instance
        """
        return Citation(
            document_id=self.document_id,
            filename=self.source,
            page_number=self.page_number,
            chunk_index=self.chunk_index,
            relevance_score=self.score,
            content_preview=self.content[:200] if self.content else None,
            extra=self.metadata,
        )


class ContextWindow:
    """Manages context assembly for LLM prompts.

    Handles token counting (approximate) and context truncation
    to fit within LLM context windows.
    """

    # Approximate tokens per character (conservative estimate)
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        max_tokens: int = 4096,
        reserved_tokens: int = 1024,
    ) -> None:
        """Initialise context window.

        Args:
            max_tokens: Maximum context tokens
            reserved_tokens: Tokens reserved for response
        """
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens
        self._contexts: list[RetrievedContext] = []

    @property
    def available_tokens(self) -> int:
        """Get available tokens for context."""
        return self.max_tokens - self.reserved_tokens

    @property
    def available_chars(self) -> int:
        """Get available characters for context."""
        return self.available_tokens * self.CHARS_PER_TOKEN

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Approximate token count
        """
        return len(text) // self.CHARS_PER_TOKEN

    def add_context(self, context: RetrievedContext) -> bool:
        """Add context if it fits within window.

        Args:
            context: Context to add

        Returns:
            True if added, False if no room
        """
        current_chars = sum(len(c.content) for c in self._contexts)
        if current_chars + len(context.content) > self.available_chars:
            return False
        self._contexts.append(context)
        return True

    def add_search_results(
        self,
        results: list[HybridSearchResult],
        max_results: int | None = None,
        min_relevance: float = DEFAULT_MIN_RELEVANCE,
    ) -> int:
        """Add search results as context with relevance filtering.

        Args:
            results: Search results to add
            max_results: Maximum results to add
            min_relevance: Minimum relevance score to include (v0.7.6)

        Returns:
            Number of results added
        """
        added = 0
        filtered = 0

        for result in results:
            if max_results is not None and added >= max_results:
                break

            # Relevance validation (v0.7.6): skip low-scoring results
            if result.combined_score < min_relevance:
                filtered += 1
                continue

            context = RetrievedContext.from_search_result(result)
            if self.add_context(context):
                added += 1
            else:
                break  # No more room

        if filtered > 0:
            logger.debug(
                "Filtered %d results below min_relevance threshold %.2f",
                filtered,
                min_relevance,
            )

        return added

    def format_context(self, include_scores: bool = False) -> str:
        """Format all context for prompt.

        Args:
            include_scores: Include relevance scores

        Returns:
            Formatted context string
        """
        if not self._contexts:
            return "[No relevant context found]"

        parts = []
        for i, ctx in enumerate(self._contexts, 1):
            header = f"[Source {i}: {ctx.source}"
            if ctx.page_number:
                header += f", p. {ctx.page_number}"
            if include_scores:
                header += f", score: {ctx.score:.2f}"
            header += "]"

            parts.append(f"{header}\n{ctx.content}")

        return "\n\n".join(parts)

    def get_citations(self) -> list[Citation]:
        """Get citations for all context.

        Returns:
            List of Citation objects
        """
        return [ctx.to_citation() for ctx in self._contexts]

    def clear(self) -> None:
        """Clear all context."""
        self._contexts.clear()

    def __len__(self) -> int:
        """Get number of context items."""
        return len(self._contexts)

    def __iter__(self):
        """Iterate over context items."""
        return iter(self._contexts)


def build_context_from_results(
    results: list[HybridSearchResult],
    max_tokens: int = 4096,
    reserved_tokens: int = 1024,
    max_results: int | None = None,
) -> tuple[str, list[Citation]]:
    """Build context string from search results.

    Convenience function for simple context assembly.

    Args:
        results: Search results
        max_tokens: Maximum context tokens
        reserved_tokens: Tokens reserved for response
        max_results: Maximum results to include

    Returns:
        Tuple of (formatted_context, citations)
    """
    window = ContextWindow(max_tokens=max_tokens, reserved_tokens=reserved_tokens)
    window.add_search_results(results, max_results=max_results)
    return window.format_context(), window.get_citations()
