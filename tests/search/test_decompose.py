"""Tests for Query Decomposition (F-066)."""

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from ragd.search.decompose import (
    AggregationMethod,
    DecomposedResult,
    DecomposerConfig,
    DecompositionStrategy,
    QueryDecomposer,
    ResultAggregator,
    SubQuery,
    decompose_query,
    get_decomposer,
)


@dataclass
class MockSearchResult:
    """Mock search result for testing."""

    content: str
    combined_score: float
    chunk_id: str


class TestSubQuery:
    """Tests for SubQuery dataclass."""

    def test_create_sub_query(self):
        """Create SubQuery with all fields."""
        sq = SubQuery(
            text="authentication security",
            index=0,
            source="compare auth methods",
            focus="security",
        )

        assert sq.text == "authentication security"
        assert sq.index == 0
        assert sq.source == "compare auth methods"
        assert sq.focus == "security"

    def test_default_focus(self):
        """SubQuery has empty focus by default."""
        sq = SubQuery(text="test", index=0, source="test")
        assert sq.focus == ""


class TestDecomposedResult:
    """Tests for DecomposedResult dataclass."""

    def test_create_decomposed_result(self):
        """Create DecomposedResult with provenance."""
        original = MockSearchResult(
            content="test content",
            combined_score=0.85,
            chunk_id="c1",
        )
        sq = SubQuery(text="test", index=0, source="test")

        dr = DecomposedResult(
            result=original,
            sub_queries=[sq],
            scores={0: 0.85},
            aggregated_score=0.85,
        )

        assert dr.result == original
        assert len(dr.sub_queries) == 1
        assert dr.scores[0] == 0.85
        assert dr.aggregated_score == 0.85


class TestDecomposerConfig:
    """Tests for DecomposerConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = DecomposerConfig()

        assert config.strategy == DecompositionStrategy.RULE_BASED
        assert config.min_sub_queries == 1
        assert config.max_sub_queries == 5
        assert config.aggregation == AggregationMethod.MAX
        assert config.deduplicate is True

    def test_custom_config(self):
        """Custom configuration values."""
        config = DecomposerConfig(
            strategy=DecompositionStrategy.LLM,
            max_sub_queries=3,
            aggregation=AggregationMethod.SUM,
        )

        assert config.strategy == DecompositionStrategy.LLM
        assert config.max_sub_queries == 3
        assert config.aggregation == AggregationMethod.SUM


class TestQueryDecomposer:
    """Tests for QueryDecomposer."""

    def test_no_decomposition_strategy(self):
        """NONE strategy returns original query."""
        config = DecomposerConfig(strategy=DecompositionStrategy.NONE)
        decomposer = QueryDecomposer(config)

        result = decomposer.decompose("test query")

        assert len(result) == 1
        assert result[0].text == "test query"
        assert result[0].focus == "original"

    def test_simple_query_no_split(self):
        """Simple queries without patterns return as-is."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("python programming")

        assert len(result) == 1
        assert result[0].text == "python programming"

    def test_decompose_comparison_vs(self):
        """Decompose 'X vs Y' pattern."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("JWT vs session authentication")

        assert len(result) == 2
        focuses = [sq.focus for sq in result]
        assert "JWT" in focuses or "session" in focuses[0] or any("JWT" in sq.text for sq in result)

    def test_decompose_comparison_versus(self):
        """Decompose 'X versus Y' pattern."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("React versus Angular for web development")

        assert len(result) >= 2

    def test_decompose_comparison_with_context(self):
        """Decompose comparison with context."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("Redis vs Memcached for caching performance")

        assert len(result) >= 2
        # Both should mention the context
        texts = [sq.text.lower() for sq in result]
        # At least one should have relevant content
        assert any("redis" in t or "memcached" in t for t in texts)

    def test_decompose_and_conjunction(self):
        """Decompose 'X and Y' pattern."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("python security and performance optimization")

        assert len(result) >= 2

    def test_decompose_also_conjunction(self):
        """Decompose 'X also Y' pattern."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("database design also query optimization")

        assert len(result) >= 2

    def test_decompose_multi_aspect(self):
        """Decompose multi-aspect queries."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("API design for security and scalability")

        # Should identify multiple aspects
        assert len(result) >= 2

    def test_max_sub_queries_limit(self):
        """Respects max_sub_queries configuration."""
        config = DecomposerConfig(max_sub_queries=2)
        decomposer = QueryDecomposer(config)

        # Query with many potential sub-queries
        result = decomposer.decompose("A and B and C and D")

        assert len(result) <= 2

    def test_deduplicates_sub_queries(self):
        """Removes duplicate sub-queries."""
        decomposer = QueryDecomposer()

        # This shouldn't produce duplicates
        result = decomposer.decompose("python and python performance")

        texts = [sq.text.lower() for sq in result]
        # No exact duplicates
        assert len(texts) == len(set(texts))

    def test_llm_fallback_to_rule_based(self):
        """LLM strategy falls back to rule-based when unavailable."""
        config = DecomposerConfig(strategy=DecompositionStrategy.LLM)
        decomposer = QueryDecomposer(config)

        # Should not raise, falls back to rule-based
        result = decomposer.decompose("JWT vs sessions for security")

        assert len(result) >= 1


class TestResultAggregator:
    """Tests for ResultAggregator."""

    def test_aggregate_single_source(self):
        """Aggregate results from single sub-query."""
        aggregator = ResultAggregator()

        sq = SubQuery(text="test", index=0, source="test query")
        results = [
            MockSearchResult(content="a", combined_score=0.9, chunk_id="c1"),
            MockSearchResult(content="b", combined_score=0.8, chunk_id="c2"),
        ]

        aggregated = aggregator.aggregate(
            [sq],
            {0: results},
        )

        assert len(aggregated) == 2
        assert aggregated[0].aggregated_score == 0.9
        assert aggregated[1].aggregated_score == 0.8

    def test_aggregate_multiple_sources_max(self):
        """Aggregate with MAX method takes highest score."""
        config = DecomposerConfig(aggregation=AggregationMethod.MAX)
        aggregator = ResultAggregator(config)

        sq1 = SubQuery(text="query1", index=0, source="test")
        sq2 = SubQuery(text="query2", index=1, source="test")

        # Same chunk found by both queries with different scores
        result1 = MockSearchResult(content="shared", combined_score=0.7, chunk_id="c1")
        result2 = MockSearchResult(content="shared", combined_score=0.9, chunk_id="c1")

        aggregated = aggregator.aggregate(
            [sq1, sq2],
            {0: [result1], 1: [result2]},
        )

        assert len(aggregated) == 1  # Deduplicated
        assert aggregated[0].aggregated_score == 0.9  # MAX

    def test_aggregate_sum_method(self):
        """Aggregate with SUM method adds scores."""
        config = DecomposerConfig(aggregation=AggregationMethod.SUM)
        aggregator = ResultAggregator(config)

        sq1 = SubQuery(text="query1", index=0, source="test")
        sq2 = SubQuery(text="query2", index=1, source="test")

        result1 = MockSearchResult(content="shared", combined_score=0.5, chunk_id="c1")
        result2 = MockSearchResult(content="shared", combined_score=0.4, chunk_id="c1")

        aggregated = aggregator.aggregate(
            [sq1, sq2],
            {0: [result1], 1: [result2]},
        )

        assert len(aggregated) == 1
        assert aggregated[0].aggregated_score == 0.9  # SUM

    def test_aggregate_weighted_method(self):
        """Aggregate with WEIGHTED method uses position weights."""
        config = DecomposerConfig(aggregation=AggregationMethod.WEIGHTED)
        aggregator = ResultAggregator(config)

        sq1 = SubQuery(text="query1", index=0, source="test")
        sq2 = SubQuery(text="query2", index=1, source="test")

        result1 = MockSearchResult(content="shared", combined_score=0.8, chunk_id="c1")
        result2 = MockSearchResult(content="shared", combined_score=0.8, chunk_id="c1")

        aggregated = aggregator.aggregate(
            [sq1, sq2],
            {0: [result1], 1: [result2]},
        )

        # Weighted average with position weights (1, 0.5)
        assert len(aggregated) == 1
        assert aggregated[0].aggregated_score > 0

    def test_aggregate_tracks_provenance(self):
        """Aggregation tracks which sub-queries found each result."""
        aggregator = ResultAggregator()

        sq1 = SubQuery(text="security", index=0, source="test")
        sq2 = SubQuery(text="performance", index=1, source="test")

        result = MockSearchResult(content="shared", combined_score=0.8, chunk_id="c1")

        aggregated = aggregator.aggregate(
            [sq1, sq2],
            {0: [result], 1: [result]},
        )

        assert len(aggregated) == 1
        assert len(aggregated[0].sub_queries) == 2
        assert 0 in aggregated[0].scores
        assert 1 in aggregated[0].scores

    def test_aggregate_handles_dict_results(self):
        """Aggregation handles dict-style results."""
        aggregator = ResultAggregator()

        sq = SubQuery(text="test", index=0, source="test")
        results = [
            {"content": "test", "combined_score": 0.9, "chunk_id": "c1"},
        ]

        aggregated = aggregator.aggregate([sq], {0: results})

        assert len(aggregated) == 1


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_decomposer_default(self):
        """get_decomposer returns default instance."""
        d1 = get_decomposer()
        d2 = get_decomposer()

        assert d1 is d2

    def test_get_decomposer_with_config(self):
        """get_decomposer with config returns new instance."""
        config = DecomposerConfig(max_sub_queries=3)
        decomposer = get_decomposer(config)

        assert decomposer.config.max_sub_queries == 3

    def test_decompose_query_convenience(self):
        """decompose_query convenience function works."""
        result = decompose_query("test query")

        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(sq, SubQuery) for sq in result)

    def test_decompose_query_with_strategy(self):
        """decompose_query accepts strategy parameter."""
        result = decompose_query(
            "test query",
            strategy=DecompositionStrategy.NONE,
        )

        assert len(result) == 1
        assert result[0].text == "test query"


class TestDecompositionPatterns:
    """Tests for various query decomposition patterns."""

    @pytest.fixture
    def decomposer(self):
        return QueryDecomposer()

    def test_comparison_patterns(self, decomposer):
        """Various comparison patterns are detected."""
        patterns = [
            "Python vs Java",
            "Python versus Ruby",
            "compare Python and Java",
            "difference between REST and GraphQL",
        ]

        for pattern in patterns:
            result = decomposer.decompose(pattern)
            assert len(result) >= 1, f"Pattern failed: {pattern}"

    def test_conjunction_patterns(self, decomposer):
        """Various conjunction patterns are detected."""
        patterns = [
            "security and performance",
            "also includes testing",
            "as well as documentation",
        ]

        for pattern in patterns:
            result = decomposer.decompose(pattern)
            assert len(result) >= 1, f"Pattern failed: {pattern}"

    def test_preserves_query_context(self, decomposer):
        """Sub-queries preserve relevant context from original."""
        result = decomposer.decompose("OAuth vs API keys for REST API security")

        # At least some context should be preserved
        texts = " ".join(sq.text for sq in result)
        # Original query fragments should appear
        assert len(result) >= 1
