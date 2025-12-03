"""Query decomposition for complex multi-part queries.

F-066: Query Decomposition

Breaks complex queries into sub-queries, retrieves for each, and aggregates
results. Supports rule-based and LLM-based decomposition strategies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class DecompositionStrategy(Enum):
    """Strategy for query decomposition."""

    NONE = "none"  # No decomposition
    RULE_BASED = "rule"  # Rule-based splitting
    LLM = "llm"  # LLM-based decomposition


class AggregationMethod(Enum):
    """Method for aggregating results from sub-queries."""

    MAX = "max"  # Take max score per document
    SUM = "sum"  # Sum scores
    WEIGHTED = "weighted"  # Weighted by sub-query relevance


@dataclass
class SubQuery:
    """A decomposed sub-query with metadata.

    Attributes:
        text: The sub-query text
        index: Position in decomposition order
        source: Original query this came from
        focus: The conceptual focus of this sub-query
    """

    text: str
    index: int
    source: str
    focus: str = ""


@dataclass
class DecomposedResult:
    """A search result with sub-query provenance.

    Attributes:
        result: The original search result
        sub_queries: Which sub-queries found this result
        scores: Scores from each sub-query
        aggregated_score: Final combined score
    """

    result: Any
    sub_queries: list[SubQuery] = field(default_factory=list)
    scores: dict[int, float] = field(default_factory=dict)  # sub_query.index -> score
    aggregated_score: float = 0.0


@dataclass
class DecomposerConfig:
    """Configuration for query decomposition.

    Attributes:
        strategy: Decomposition strategy
        min_sub_queries: Minimum sub-queries to generate
        max_sub_queries: Maximum sub-queries to generate
        aggregation: Result aggregation method
        llm_model: Model for LLM-based decomposition
        deduplicate: Whether to de-duplicate results
    """

    strategy: DecompositionStrategy = DecompositionStrategy.RULE_BASED
    min_sub_queries: int = 1
    max_sub_queries: int = 5
    aggregation: AggregationMethod = AggregationMethod.MAX
    llm_model: str | None = None
    deduplicate: bool = True


class QueryDecomposer:
    """Decomposes complex queries into simpler sub-queries."""

    # Conjunctions that indicate multiple aspects
    CONJUNCTIONS = [
        r"\band\b",
        r"\balso\b",
        r"\bas well as\b",
        r"\bin addition to\b",
        r"\btogether with\b",
    ]

    # Comparison patterns
    COMPARISONS = [
        r"\bvs\.?\b",
        r"\bversus\b",
        r"\bcompare\b",
        r"\bcompared to\b",
        r"\bdifference between\b",
        r"\bor\b",  # when used in comparison context
    ]

    # Multi-aspect patterns
    MULTI_ASPECT = [
        r"\bfor\s+(\w+)\s+and\s+(\w+)\b",  # "for security and performance"
        r"\b(?:in terms of|regarding)\s+(.+?)\s+and\s+(.+?)(?:\s|$)",
    ]

    def __init__(self, config: DecomposerConfig | None = None) -> None:
        """Initialise decomposer with configuration.

        Args:
            config: Decomposer configuration
        """
        self.config = config or DecomposerConfig()
        self._llm = None

    def decompose(self, query: str) -> list[SubQuery]:
        """Decompose a query into sub-queries.

        Args:
            query: The original query

        Returns:
            List of SubQuery objects
        """
        if self.config.strategy == DecompositionStrategy.NONE:
            return [SubQuery(text=query, index=0, source=query, focus="original")]

        if self.config.strategy == DecompositionStrategy.LLM:
            sub_queries = self._llm_decompose(query)
            if sub_queries:
                return sub_queries
            # Fall back to rule-based
            logger.debug("LLM decomposition unavailable, falling back to rules")

        return self._rule_based_decompose(query)

    def _rule_based_decompose(self, query: str) -> list[SubQuery]:
        """Decompose query using rule-based patterns.

        Args:
            query: The original query

        Returns:
            List of SubQuery objects
        """
        sub_queries = []
        query_lower = query.lower()

        # Check for comparison patterns
        for pattern in self.COMPARISONS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                sub_queries.extend(self._decompose_comparison(query))
                break

        # Check for multi-aspect patterns
        if not sub_queries:
            for pattern in self.MULTI_ASPECT:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    sub_queries.extend(self._decompose_aspects(query, match))
                    break

        # Check for conjunction-based decomposition
        if not sub_queries:
            for pattern in self.CONJUNCTIONS:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    sub_queries.extend(self._decompose_conjunction(query))
                    break

        # If no decomposition happened, return original
        if not sub_queries:
            return [SubQuery(text=query, index=0, source=query, focus="original")]

        # Limit and deduplicate
        seen = set()
        unique = []
        for sq in sub_queries:
            text_norm = sq.text.lower().strip()
            if text_norm not in seen and text_norm:
                seen.add(text_norm)
                unique.append(sq)

        # Apply limits
        return unique[: self.config.max_sub_queries]

    def _decompose_comparison(self, query: str) -> list[SubQuery]:
        """Decompose comparison queries like 'X vs Y'.

        Args:
            query: Query containing comparison

        Returns:
            Sub-queries for each compared item
        """
        sub_queries = []

        # Find comparison terms
        vs_pattern = r"(.+?)\s+(?:vs\.?|versus|compared to)\s+(.+?)(?:\s+for\s+|\s+in\s+|\s*$)"
        match = re.search(vs_pattern, query, re.IGNORECASE)

        if match:
            term_a = match.group(1).strip()
            term_b = match.group(2).strip()

            # Extract context (what they're being compared for)
            context_match = re.search(
                r"(?:for|in terms of|regarding)\s+(.+)",
                query,
                re.IGNORECASE,
            )
            context = context_match.group(1) if context_match else ""

            # Create sub-queries for each term
            if context:
                sub_queries.append(
                    SubQuery(
                        text=f"{term_a} {context}",
                        index=0,
                        source=query,
                        focus=term_a,
                    )
                )
                sub_queries.append(
                    SubQuery(
                        text=f"{term_b} {context}",
                        index=1,
                        source=query,
                        focus=term_b,
                    )
                )
            else:
                sub_queries.append(
                    SubQuery(text=term_a, index=0, source=query, focus=term_a)
                )
                sub_queries.append(
                    SubQuery(text=term_b, index=1, source=query, focus=term_b)
                )

        return sub_queries

    def _decompose_aspects(
        self,
        query: str,
        match: re.Match,
    ) -> list[SubQuery]:
        """Decompose multi-aspect queries.

        Args:
            query: The original query
            match: Regex match with aspect groups

        Returns:
            Sub-queries for each aspect
        """
        sub_queries = []

        # Extract the base topic (before 'for X and Y')
        base_pattern = r"^(.+?)\s+(?:for|in terms of|regarding)"
        base_match = re.search(base_pattern, query, re.IGNORECASE)
        base = base_match.group(1) if base_match else ""

        # Get aspects from match groups
        aspects = [g for g in match.groups() if g]

        for i, aspect in enumerate(aspects):
            aspect = aspect.strip()
            if base:
                sub_queries.append(
                    SubQuery(
                        text=f"{base} {aspect}",
                        index=i,
                        source=query,
                        focus=aspect,
                    )
                )
            else:
                sub_queries.append(
                    SubQuery(text=aspect, index=i, source=query, focus=aspect)
                )

        return sub_queries

    def _decompose_conjunction(self, query: str) -> list[SubQuery]:
        """Decompose conjunction-based queries.

        Args:
            query: Query with conjunctions

        Returns:
            Sub-queries for each part
        """
        sub_queries = []

        # Split on conjunctions
        parts = re.split(
            r"\s+(?:and|also|as well as)\s+",
            query,
            flags=re.IGNORECASE,
        )

        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 3:  # Avoid tiny fragments
                sub_queries.append(
                    SubQuery(text=part, index=i, source=query, focus=part)
                )

        return sub_queries

    def _llm_decompose(self, query: str) -> list[SubQuery] | None:
        """Decompose query using LLM.

        Args:
            query: The original query

        Returns:
            List of SubQuery objects or None if unavailable
        """
        if self._llm is None:
            try:
                from ragd.llm import get_llm

                self._llm = get_llm(model=self.config.llm_model)
            except ImportError:
                logger.debug("LLM not available for decomposition")
                return None
            except Exception as e:
                logger.debug("Failed to initialise LLM: %s", e)
                return None

        prompt = f"""Break down this search query into simpler sub-queries.
Return each sub-query on a new line.
Only return the sub-queries, no explanations.
If the query is already simple, return just the original query.

Query: {query}

Sub-queries:"""

        try:
            response = self._llm.generate(prompt, max_tokens=200)
            lines = [
                line.strip()
                for line in response.strip().split("\n")
                if line.strip() and not line.startswith("-")
            ]

            if not lines:
                return None

            sub_queries = []
            for i, line in enumerate(lines[: self.config.max_sub_queries]):
                # Clean up common prefixes
                line = re.sub(r"^\d+[\.\)]\s*", "", line)
                line = re.sub(r"^[-*]\s*", "", line)
                line = line.strip('"\'')

                if line:
                    sub_queries.append(
                        SubQuery(text=line, index=i, source=query, focus=line)
                    )

            return sub_queries if sub_queries else None

        except Exception as e:
            logger.debug("LLM decomposition failed: %s", e)
            return None


class ResultAggregator:
    """Aggregates results from multiple sub-queries."""

    def __init__(self, config: DecomposerConfig | None = None) -> None:
        """Initialise aggregator.

        Args:
            config: Decomposer configuration
        """
        self.config = config or DecomposerConfig()

    def aggregate(
        self,
        sub_queries: list[SubQuery],
        results_per_query: dict[int, list[Any]],
        get_id: Callable[[Any], str] | None = None,
        get_score: Callable[[Any], float] | None = None,
    ) -> list[DecomposedResult]:
        """Aggregate results from multiple sub-queries.

        Args:
            sub_queries: List of sub-queries used
            results_per_query: Map of sub_query.index -> results
            get_id: Function to get unique ID from result (for dedup)
            get_score: Function to get score from result

        Returns:
            Aggregated DecomposedResult objects
        """
        # Default extractors
        if get_id is None:
            get_id = self._default_get_id
        if get_score is None:
            get_score = self._default_get_score

        # Build map of id -> DecomposedResult
        result_map: dict[str, DecomposedResult] = {}

        for sub_query in sub_queries:
            results = results_per_query.get(sub_query.index, [])
            for result in results:
                result_id = get_id(result)
                score = get_score(result)

                if result_id not in result_map:
                    result_map[result_id] = DecomposedResult(result=result)

                dr = result_map[result_id]
                dr.sub_queries.append(sub_query)
                dr.scores[sub_query.index] = score

        # Calculate aggregated scores
        for dr in result_map.values():
            dr.aggregated_score = self._aggregate_scores(
                list(dr.scores.values())
            )

        # Sort by aggregated score
        sorted_results = sorted(
            result_map.values(),
            key=lambda x: x.aggregated_score,
            reverse=True,
        )

        return sorted_results

    def _aggregate_scores(self, scores: list[float]) -> float:
        """Aggregate multiple scores into one.

        Args:
            scores: List of scores

        Returns:
            Aggregated score
        """
        if not scores:
            return 0.0

        if self.config.aggregation == AggregationMethod.MAX:
            return max(scores)
        elif self.config.aggregation == AggregationMethod.SUM:
            return sum(scores)
        elif self.config.aggregation == AggregationMethod.WEIGHTED:
            # Weight by position (earlier sub-queries weighted higher)
            weighted = sum(
                score * (1.0 / (i + 1))
                for i, score in enumerate(scores)
            )
            return weighted / len(scores)
        else:
            return max(scores)

    def _default_get_id(self, result: Any) -> str:
        """Default ID extractor."""
        if hasattr(result, "chunk_id"):
            return result.chunk_id
        if hasattr(result, "id"):
            return result.id
        if isinstance(result, dict):
            return result.get("chunk_id") or result.get("id") or str(id(result))
        return str(id(result))

    def _default_get_score(self, result: Any) -> float:
        """Default score extractor."""
        if hasattr(result, "combined_score"):
            return result.combined_score
        if hasattr(result, "rrf_score"):
            return result.rrf_score
        if hasattr(result, "score"):
            return result.score
        if isinstance(result, dict):
            return (
                result.get("combined_score")
                or result.get("score")
                or 0.0
            )
        return 0.0


# Module-level convenience functions

_default_decomposer: QueryDecomposer | None = None


def get_decomposer(config: DecomposerConfig | None = None) -> QueryDecomposer:
    """Get or create a decomposer instance.

    Args:
        config: Optional configuration

    Returns:
        QueryDecomposer instance
    """
    global _default_decomposer

    if config is not None:
        return QueryDecomposer(config)

    if _default_decomposer is None:
        _default_decomposer = QueryDecomposer()

    return _default_decomposer


def decompose_query(
    query: str,
    strategy: DecompositionStrategy = DecompositionStrategy.RULE_BASED,
) -> list[SubQuery]:
    """Convenience function to decompose a query.

    Args:
        query: The query to decompose
        strategy: Decomposition strategy

    Returns:
        List of SubQuery objects
    """
    config = DecomposerConfig(strategy=strategy)
    decomposer = QueryDecomposer(config)
    return decomposer.decompose(query)
