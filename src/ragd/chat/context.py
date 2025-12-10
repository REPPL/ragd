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
class TokenBudget:
    """Token allocation for a chat turn.

    Provides calculated allocations for history and context based on
    total available tokens and actual content sizes.

    Attributes:
        total: Total context window tokens
        reserved_for_response: Tokens reserved for LLM response
        history: Tokens allocated for conversation history
        context: Tokens allocated for retrieved context
    """

    total: int
    reserved_for_response: int
    history: int
    context: int

    @property
    def available(self) -> int:
        """Get total available tokens (total minus reserved)."""
        return self.total - self.reserved_for_response


def calculate_token_budget(
    context_window: int,
    reserved_tokens: int,
    history_ratio: float,
    actual_history_chars: int,
    min_history: int,
    min_context: int,
) -> TokenBudget:
    """Calculate optimal token allocation based on actual history size.

    Dynamically allocates tokens between history and context, respecting
    the configured ratio while adapting to actual content sizes.

    Args:
        context_window: Total context window size in tokens
        reserved_tokens: Tokens reserved for LLM response
        history_ratio: Target ratio of available tokens for history (0.0-1.0)
        actual_history_chars: Actual character count of history to include
        min_history: Minimum tokens to allocate for history
        min_context: Minimum tokens to allocate for context

    Returns:
        TokenBudget with calculated allocations
    """
    available = context_window - reserved_tokens

    # Estimate tokens from actual history (4 chars per token)
    history_tokens_needed = actual_history_chars // 4

    # Calculate max history based on ratio
    max_history_from_ratio = int(available * history_ratio)

    # History gets the minimum of what it needs and what the ratio allows
    # but at least min_history
    history_budget = min(history_tokens_needed, max_history_from_ratio)
    history_budget = max(history_budget, min_history)

    # Context gets the rest, but at least min_context
    context_budget = available - history_budget
    context_budget = max(context_budget, min_context)

    # If we've over-allocated, reduce history (context is more important)
    if history_budget + context_budget > available:
        history_budget = available - context_budget
        history_budget = max(history_budget, 0)

    return TokenBudget(
        total=context_window,
        reserved_for_response=reserved_tokens,
        history=history_budget,
        context=context_budget,
    )


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
        """Format all context for prompt with citation guidance.

        Consolidates chunks by document - each document gets ONE citation number
        with all its chunks combined into a single context block.

        Args:
            include_scores: Include relevance scores

        Returns:
            Formatted context string with citation guidance header
        """
        if not self._contexts:
            return "[No relevant context found]"

        # Citation guidance header
        header = (
            "=== KNOWLEDGE BASE SOURCES ===\n"
            "Cite using [1] or [1;2] for multiple. "
            "Ignore (Author, Year) citations within text.\n\n"
        )

        # Group chunks by document (document_id or source as fallback)
        from collections import OrderedDict

        doc_chunks: OrderedDict[str, list[RetrievedContext]] = OrderedDict()

        for ctx in self._contexts:
            doc_key = ctx.document_id or ctx.source
            if doc_key not in doc_chunks:
                doc_chunks[doc_key] = []
            doc_chunks[doc_key].append(ctx)

        # Format each document as a single context block
        parts = []
        for citation_num, (doc_key, chunks) in enumerate(doc_chunks.items(), 1):
            # Use first chunk for source name, collect all page numbers
            first_chunk = chunks[0]
            page_numbers = sorted(set(
                c.page_number for c in chunks if c.page_number is not None
            ))

            # Build source header
            source_header = f"[{citation_num}] {first_chunk.source}"
            if page_numbers:
                if len(page_numbers) == 1:
                    source_header += f", page {page_numbers[0]}"
                else:
                    source_header += f", pages {page_numbers[0]}-{page_numbers[-1]}"
            if include_scores:
                avg_score = sum(c.score for c in chunks) / len(chunks)
                source_header += f" (avg score: {avg_score:.2f})"

            # Combine all chunk content with separator
            combined_content = "\n\n[...]\n\n".join(c.content for c in chunks)
            parts.append(f"{source_header}\n{combined_content}")

        return header + "\n\n---\n\n".join(parts)

    def get_citations(self) -> list[Citation]:
        """Get citations for all context.

        Returns:
            List of Citation objects
        """
        return [ctx.to_citation() for ctx in self._contexts]

    def get_deduplicated_citations(self) -> list[Citation]:
        """Get unique citations, one per document.

        Deduplicates by document_id, keeping first occurrence.
        This prevents the same source appearing multiple times
        in the reference list.

        Returns:
            List of unique Citation objects
        """
        seen_docs: set[str] = set()
        unique: list[Citation] = []

        for ctx in self._contexts:
            doc_id = ctx.document_id
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique.append(ctx.to_citation())
            elif not doc_id:
                # No document_id, use source as fallback key
                if ctx.source not in seen_docs:
                    seen_docs.add(ctx.source)
                    unique.append(ctx.to_citation())

        return unique

    def clear(self) -> None:
        """Clear all context."""
        self._contexts.clear()

    def __len__(self) -> int:
        """Get number of context items."""
        return len(self._contexts)

    def __iter__(self):
        """Iterate over context items."""
        return iter(self._contexts)


def deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    """Deduplicate citations by document_id.

    Keeps first occurrence of each document.

    Args:
        citations: List of citations (may contain duplicates)

    Returns:
        List of unique citations
    """
    seen_docs: set[str] = set()
    unique: list[Citation] = []

    for cit in citations:
        key = cit.document_id or cit.filename
        if key and key not in seen_docs:
            seen_docs.add(key)
            unique.append(cit)
        elif not key:
            # Fallback: include if no identifier
            unique.append(cit)

    return unique


def build_context_from_results(
    results: list[HybridSearchResult],
    max_tokens: int = 4096,
    reserved_tokens: int = 1024,
    max_results: int | None = None,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> tuple[str, list[Citation]]:
    """Build context string from search results.

    Convenience function for simple context assembly.

    Args:
        results: Search results
        max_tokens: Maximum context tokens
        reserved_tokens: Tokens reserved for response
        max_results: Maximum results to include
        min_relevance: Minimum relevance score for context chunks

    Returns:
        Tuple of (formatted_context, citations)
    """
    window = ContextWindow(max_tokens=max_tokens, reserved_tokens=reserved_tokens)
    window.add_search_results(
        results,
        max_results=max_results,
        min_relevance=min_relevance,
    )
    return window.format_context(), window.get_citations()
