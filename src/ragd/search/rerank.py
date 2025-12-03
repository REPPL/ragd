"""Cross-encoder reranking for improved search precision.

F-065: Cross-Encoder Reranking

Cross-encoders process query-document pairs together for deeper semantic
understanding. This improves precision at the cost of speed (O(n) inference).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, Sequence

if TYPE_CHECKING:
    from ragd.search.hybrid import HybridSearchResult

logger = logging.getLogger(__name__)


# Default cross-encoder models (from sentence-transformers)
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
FAST_RERANKER_MODEL = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
QUALITY_RERANKER_MODEL = "BAAI/bge-reranker-base"


class Reranker(Protocol):
    """Protocol for reranker implementations."""

    def rerank(
        self,
        query: str,
        results: Sequence[Any],
        top_k: int | None = None,
    ) -> list[Any]:
        """Rerank search results by relevance to query."""
        ...


@dataclass
class RerankerConfig:
    """Configuration for cross-encoder reranker.

    Attributes:
        model_name: Cross-encoder model name
        device: Device for inference (cuda, cpu, mps)
        batch_size: Batch size for inference
        top_k: Default number of results to return
        min_score: Minimum reranker score threshold
    """

    model_name: str = DEFAULT_RERANKER_MODEL
    device: str = "cpu"
    batch_size: int = 32
    top_k: int = 10
    min_score: float = 0.0


@dataclass
class RerankResult:
    """A reranked search result with additional scoring.

    Attributes:
        original: The original search result
        rerank_score: Score from the cross-encoder
        original_rank: Rank before reranking
        final_rank: Rank after reranking
    """

    original: Any
    rerank_score: float
    original_rank: int
    final_rank: int = 0


class CrossEncoderReranker:
    """Cross-encoder based reranker using sentence-transformers.

    Lazy-loads the model on first use to avoid startup cost.
    """

    def __init__(self, config: RerankerConfig | None = None) -> None:
        """Initialise reranker with configuration.

        Args:
            config: Reranker configuration
        """
        self.config = config or RerankerConfig()
        self._model = None
        self._model_loaded = False

    def _load_model(self) -> None:
        """Lazy-load the cross-encoder model."""
        if self._model_loaded:
            return

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(
                self.config.model_name,
                device=self.config.device,
            )
            self._model_loaded = True
            logger.info(
                "Loaded cross-encoder model: %s",
                self.config.model_name,
            )
        except ImportError:
            logger.warning(
                "sentence-transformers not available, reranking disabled"
            )
            self._model = None
            self._model_loaded = True
        except Exception as e:
            logger.warning(
                "Failed to load cross-encoder model: %s",
                e,
            )
            self._model = None
            self._model_loaded = True

    @property
    def available(self) -> bool:
        """Check if reranker is available."""
        self._load_model()
        return self._model is not None

    def rerank(
        self,
        query: str,
        results: Sequence[Any],
        top_k: int | None = None,
    ) -> list[Any]:
        """Rerank search results using cross-encoder.

        Args:
            query: The search query
            results: Search results to rerank (must have 'content' attribute)
            top_k: Number of results to return (default from config)

        Returns:
            Reranked results, limited to top_k
        """
        if not results:
            return []

        self._load_model()

        if self._model is None:
            logger.debug("Reranker unavailable, returning original order")
            return list(results[:top_k] if top_k else results)

        top_k = top_k or self.config.top_k

        # Build query-document pairs
        pairs = []
        for result in results:
            # Handle both objects with content attribute and dicts
            if hasattr(result, "content"):
                content = result.content
            elif isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)

            pairs.append((query, content))

        # Score with cross-encoder
        try:
            scores = self._model.predict(
                pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
            )
        except Exception as e:
            logger.warning("Reranking failed: %s", e)
            return list(results[:top_k] if top_k else results)

        # Create scored results
        scored = [
            RerankResult(
                original=result,
                rerank_score=float(score),
                original_rank=i + 1,
            )
            for i, (result, score) in enumerate(zip(results, scores))
        ]

        # Sort by rerank score descending
        scored.sort(key=lambda x: x.rerank_score, reverse=True)

        # Assign final ranks
        for i, item in enumerate(scored):
            item.final_rank = i + 1

        # Filter by min_score and limit
        filtered = [
            s.original
            for s in scored
            if s.rerank_score >= self.config.min_score
        ]

        return filtered[:top_k] if top_k else filtered

    def rerank_with_scores(
        self,
        query: str,
        results: Sequence[Any],
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """Rerank and return full RerankResult objects with scores.

        Args:
            query: The search query
            results: Search results to rerank
            top_k: Number of results to return

        Returns:
            List of RerankResult with scores and ranks
        """
        if not results:
            return []

        self._load_model()

        if self._model is None:
            # Return results with placeholder scores
            return [
                RerankResult(
                    original=r,
                    rerank_score=0.0,
                    original_rank=i + 1,
                    final_rank=i + 1,
                )
                for i, r in enumerate(results[:top_k] if top_k else results)
            ]

        top_k = top_k or self.config.top_k

        # Build query-document pairs
        pairs = []
        for result in results:
            if hasattr(result, "content"):
                content = result.content
            elif isinstance(result, dict):
                content = result.get("content", "")
            else:
                content = str(result)

            pairs.append((query, content))

        # Score with cross-encoder
        try:
            scores = self._model.predict(
                pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
            )
        except Exception as e:
            logger.warning("Reranking failed: %s", e)
            return [
                RerankResult(
                    original=r,
                    rerank_score=0.0,
                    original_rank=i + 1,
                    final_rank=i + 1,
                )
                for i, r in enumerate(results[:top_k] if top_k else results)
            ]

        # Create scored results
        scored = [
            RerankResult(
                original=result,
                rerank_score=float(score),
                original_rank=i + 1,
            )
            for i, (result, score) in enumerate(zip(results, scores))
        ]

        # Sort by rerank score descending
        scored.sort(key=lambda x: x.rerank_score, reverse=True)

        # Assign final ranks and filter
        filtered = []
        for i, item in enumerate(scored):
            item.final_rank = i + 1
            if item.rerank_score >= self.config.min_score:
                filtered.append(item)

        return filtered[:top_k] if top_k else filtered


# Module-level reranker instance for convenience
_default_reranker: CrossEncoderReranker | None = None


def get_reranker(config: RerankerConfig | None = None) -> CrossEncoderReranker:
    """Get or create a reranker instance.

    Args:
        config: Optional configuration (uses defaults if not provided)

    Returns:
        CrossEncoderReranker instance
    """
    global _default_reranker

    if config is not None:
        # Custom config, create new instance
        return CrossEncoderReranker(config)

    if _default_reranker is None:
        _default_reranker = CrossEncoderReranker()

    return _default_reranker


def rerank(
    query: str,
    results: Sequence[Any],
    top_k: int = 10,
    config: RerankerConfig | None = None,
) -> list[Any]:
    """Convenience function for reranking search results.

    Args:
        query: The search query
        results: Search results to rerank
        top_k: Number of results to return
        config: Optional reranker configuration

    Returns:
        Reranked results
    """
    reranker = get_reranker(config)
    return reranker.rerank(query, results, top_k=top_k)
