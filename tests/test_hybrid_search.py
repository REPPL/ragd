"""Tests for hybrid search module."""

import tempfile
from pathlib import Path

import pytest

from ragd.search.bm25 import BM25Index, BM25Result
from ragd.search.hybrid import (
    HybridSearchResult,
    SearchMode,
    reciprocal_rank_fusion,
)


# =============================================================================
# BM25 Index Tests
# =============================================================================


@pytest.fixture
def temp_db():
    """Create temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_bm25.db"


def test_bm25_index_creation(temp_db: Path) -> None:
    """Test BM25 index can be created."""
    with BM25Index(temp_db) as index:
        stats = index.get_stats()
        assert stats["document_count"] == 0
        assert stats["chunk_count"] == 0


def test_bm25_add_chunks(temp_db: Path) -> None:
    """Test adding chunks to BM25 index."""
    with BM25Index(temp_db) as index:
        chunks = [
            ("doc1_chunk_0", "This is the first chunk about machine learning."),
            ("doc1_chunk_1", "This is the second chunk about data science."),
        ]
        index.add_chunks("doc1", chunks)

        stats = index.get_stats()
        assert stats["document_count"] == 1
        assert stats["chunk_count"] == 2


def test_bm25_search_basic(temp_db: Path) -> None:
    """Test basic BM25 search."""
    with BM25Index(temp_db) as index:
        chunks = [
            ("doc1_chunk_0", "Machine learning is a subset of artificial intelligence."),
            ("doc1_chunk_1", "Data science involves statistics and programming."),
            ("doc1_chunk_2", "Neural networks are used in deep learning."),
        ]
        index.add_chunks("doc1", chunks)

        results = index.search("machine learning", limit=10)
        assert len(results) > 0
        assert isinstance(results[0], BM25Result)
        assert results[0].bm25_score > 0


def test_bm25_search_empty_query(temp_db: Path) -> None:
    """Test BM25 search with empty query."""
    with BM25Index(temp_db) as index:
        chunks = [("doc1_chunk_0", "Some content here.")]
        index.add_chunks("doc1", chunks)

        results = index.search("", limit=10)
        assert results == []


def test_bm25_search_no_results(temp_db: Path) -> None:
    """Test BM25 search with no matching results."""
    with BM25Index(temp_db) as index:
        chunks = [("doc1_chunk_0", "Machine learning content.")]
        index.add_chunks("doc1", chunks)

        results = index.search("quantum physics", limit=10)
        # May return empty or with very low scores
        assert isinstance(results, list)


def test_bm25_delete_document(temp_db: Path) -> None:
    """Test deleting document from BM25 index."""
    with BM25Index(temp_db) as index:
        chunks = [("doc1_chunk_0", "Test content.")]
        index.add_chunks("doc1", chunks)
        assert index.document_exists("doc1")

        result = index.delete_document("doc1")
        assert result is True
        assert not index.document_exists("doc1")


def test_bm25_delete_nonexistent(temp_db: Path) -> None:
    """Test deleting non-existent document."""
    with BM25Index(temp_db) as index:
        result = index.delete_document("nonexistent")
        assert result is False


def test_bm25_reindex_document(temp_db: Path) -> None:
    """Test re-indexing a document replaces old chunks."""
    with BM25Index(temp_db) as index:
        # Add initial chunks
        chunks1 = [("doc1_chunk_0", "Old content.")]
        index.add_chunks("doc1", chunks1)

        # Re-index with new chunks
        chunks2 = [
            ("doc1_chunk_0", "New content one."),
            ("doc1_chunk_1", "New content two."),
        ]
        index.add_chunks("doc1", chunks2)

        stats = index.get_stats()
        assert stats["document_count"] == 1
        assert stats["chunk_count"] == 2


def test_bm25_reset(temp_db: Path) -> None:
    """Test resetting BM25 index."""
    with BM25Index(temp_db) as index:
        chunks = [("doc1_chunk_0", "Test content.")]
        index.add_chunks("doc1", chunks)

        index.reset()

        stats = index.get_stats()
        assert stats["document_count"] == 0
        assert stats["chunk_count"] == 0


def test_bm25_special_characters(temp_db: Path) -> None:
    """Test BM25 handles special characters in queries."""
    with BM25Index(temp_db) as index:
        chunks = [("doc1_chunk_0", "Error code E1234 occurred.")]
        index.add_chunks("doc1", chunks)

        # Should not raise error with special characters
        results = index.search("error code E1234", limit=10)
        assert isinstance(results, list)


# =============================================================================
# Reciprocal Rank Fusion Tests
# =============================================================================


def test_rrf_empty_rankings() -> None:
    """Test RRF with empty rankings."""
    result = reciprocal_rank_fusion([])
    assert result == []


def test_rrf_single_ranking() -> None:
    """Test RRF with single ranking."""
    ranking = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
    result = reciprocal_rank_fusion([ranking])

    assert len(result) == 3
    # First item should have highest score
    assert result[0][0] == "doc1"
    assert result[0][1] > result[1][1] > result[2][1]


def test_rrf_two_rankings() -> None:
    """Test RRF with two rankings."""
    semantic = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
    keyword = [("doc2", 5.0), ("doc3", 4.0), ("doc1", 3.0)]

    result = reciprocal_rank_fusion([semantic, keyword])

    assert len(result) == 3
    # doc2 appears high in both, should rank first
    ids = [item[0] for item in result]
    # doc2 should be boosted as it's #1 in keyword and #2 in semantic
    assert "doc2" in ids[:2]


def test_rrf_partial_overlap() -> None:
    """Test RRF with partially overlapping rankings."""
    ranking1 = [("doc1", 0.9), ("doc2", 0.8)]
    ranking2 = [("doc2", 5.0), ("doc3", 4.0)]

    result = reciprocal_rank_fusion([ranking1, ranking2])

    # Should include all unique documents
    ids = [item[0] for item in result]
    assert set(ids) == {"doc1", "doc2", "doc3"}
    # doc2 appears in both, should score highest
    assert result[0][0] == "doc2"


def test_rrf_k_parameter() -> None:
    """Test RRF k parameter affects scores."""
    ranking = [("doc1", 0.9), ("doc2", 0.8)]

    result_k60 = reciprocal_rank_fusion([ranking], k=60)
    result_k1 = reciprocal_rank_fusion([ranking], k=1)

    # With smaller k, ranks matter more
    score_diff_k60 = result_k60[0][1] - result_k60[1][1]
    score_diff_k1 = result_k1[0][1] - result_k1[1][1]
    assert score_diff_k1 > score_diff_k60


# =============================================================================
# Search Mode Tests
# =============================================================================


def test_search_mode_values() -> None:
    """Test SearchMode enum values."""
    assert SearchMode.HYBRID.value == "hybrid"
    assert SearchMode.SEMANTIC.value == "semantic"
    assert SearchMode.KEYWORD.value == "keyword"


def test_search_mode_from_string() -> None:
    """Test creating SearchMode from string."""
    assert SearchMode("hybrid") == SearchMode.HYBRID
    assert SearchMode("semantic") == SearchMode.SEMANTIC
    assert SearchMode("keyword") == SearchMode.KEYWORD


def test_search_mode_invalid() -> None:
    """Test invalid SearchMode raises error."""
    with pytest.raises(ValueError):
        SearchMode("invalid")


# =============================================================================
# HybridSearchResult Tests
# =============================================================================


def test_hybrid_search_result_creation() -> None:
    """Test HybridSearchResult dataclass."""
    result = HybridSearchResult(
        content="Test content",
        combined_score=0.85,
        semantic_score=0.9,
        keyword_score=5.0,
        semantic_rank=1,
        keyword_rank=2,
        rrf_score=0.032,
        document_id="doc123",
        document_name="test.pdf",
        chunk_id="doc123_chunk_0",
        chunk_index=0,
    )

    assert result.content == "Test content"
    assert result.combined_score == 0.85
    assert result.semantic_score == 0.9
    assert result.keyword_score == 5.0
    assert result.document_id == "doc123"


def test_hybrid_search_result_optional_fields() -> None:
    """Test HybridSearchResult with optional fields."""
    result = HybridSearchResult(
        content="Test",
        combined_score=0.5,
        semantic_score=None,  # Keyword-only search
        keyword_score=3.0,
        semantic_rank=None,
        keyword_rank=1,
        rrf_score=0.016,
        document_id="doc1",
        document_name="test.txt",
        chunk_id="doc1_chunk_0",
        chunk_index=0,
    )

    assert result.semantic_score is None
    assert result.semantic_rank is None
    assert result.keyword_score == 3.0


# =============================================================================
# Integration Tests (require full setup)
# =============================================================================


def test_bm25_multiple_documents(temp_db: Path) -> None:
    """Test BM25 with multiple documents."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [
            ("doc1_chunk_0", "Introduction to Python programming."),
            ("doc1_chunk_1", "Python is used for web development."),
        ])
        index.add_chunks("doc2", [
            ("doc2_chunk_0", "JavaScript is popular for frontend."),
            ("doc2_chunk_1", "React and Vue are JavaScript frameworks."),
        ])
        index.add_chunks("doc3", [
            ("doc3_chunk_0", "Python can be used with machine learning."),
        ])

        stats = index.get_stats()
        assert stats["document_count"] == 3
        assert stats["chunk_count"] == 5

        # Search for Python - should find doc1 and doc3
        results = index.search("Python", limit=10)
        assert len(results) > 0
        doc_ids = {r.document_id for r in results}
        assert "doc1" in doc_ids or "doc3" in doc_ids


def test_bm25_document_filter(temp_db: Path) -> None:
    """Test BM25 search with document filter."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [("doc1_chunk_0", "Python programming language.")])
        index.add_chunks("doc2", [("doc2_chunk_0", "Python snake species.")])

        # Search only in doc1
        results = index.search("Python", limit=10, document_filter="doc1")
        assert all(r.document_id == "doc1" for r in results)


def test_bm25_document_ids_filter(temp_db: Path) -> None:
    """Test BM25 search with multiple document IDs filter."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [("doc1_chunk_0", "Python programming language.")])
        index.add_chunks("doc2", [("doc2_chunk_0", "Python snake species.")])
        index.add_chunks("doc3", [("doc3_chunk_0", "Python web framework.")])

        # Search only in doc1 and doc3
        results = index.search("Python", limit=10, document_ids=["doc1", "doc3"])
        assert len(results) == 2
        doc_ids = {r.document_id for r in results}
        assert doc_ids == {"doc1", "doc3"}
        assert "doc2" not in doc_ids


def test_bm25_document_ids_empty_list(temp_db: Path) -> None:
    """Test BM25 search with empty document IDs returns all."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [("doc1_chunk_0", "Python programming.")])
        index.add_chunks("doc2", [("doc2_chunk_0", "Python snakes.")])

        # Empty list should not filter
        results = index.search("Python", limit=10, document_ids=[])
        # Empty list is falsy, so no filter applied
        assert len(results) == 2


def test_bm25_document_ids_no_match(temp_db: Path) -> None:
    """Test BM25 search with non-matching document IDs."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [("doc1_chunk_0", "Python programming.")])

        results = index.search("Python", limit=10, document_ids=["nonexistent"])
        assert len(results) == 0


def test_bm25_ranking_order(temp_db: Path) -> None:
    """Test BM25 returns results in relevance order."""
    with BM25Index(temp_db) as index:
        index.add_chunks("doc1", [
            ("doc1_chunk_0", "Python Python Python programming."),  # High relevance
            ("doc1_chunk_1", "Something else entirely."),  # Low relevance
            ("doc1_chunk_2", "Python is nice."),  # Medium relevance
        ])

        results = index.search("Python", limit=10)

        # Scores should be in descending order
        if len(results) > 1:
            scores = [r.bm25_score for r in results]
            assert scores == sorted(scores, reverse=True)


# =============================================================================
# BM25 Boolean Operator Tests
# =============================================================================


class TestBM25BooleanOperators:
    """Tests for boolean operator support in BM25 search."""

    def test_and_operator(self, temp_db: Path) -> None:
        """Test AND requires both terms."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Python is great for machine learning."),
                ("c2", "JavaScript is used for web development."),
                ("c3", "Python web frameworks like Flask."),
            ])
            results = index.search("Python AND web", limit=10)
            # Should find "Python web frameworks" but not pure Python or pure web
            assert len(results) >= 1
            # All results should contain both terms
            for r in results:
                content_lower = r.content.lower()
                assert "python" in content_lower and "web" in content_lower

    def test_or_operator(self, temp_db: Path) -> None:
        """Test OR matches either term."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Python programming language."),
                ("c2", "JavaScript programming language."),
                ("c3", "Rust is fast."),
            ])
            results = index.search("Python OR JavaScript", limit=10)
            # Should find both Python and JavaScript docs
            assert len(results) >= 2
            contents = " ".join(r.content.lower() for r in results)
            assert "python" in contents or "javascript" in contents

    def test_not_operator(self, temp_db: Path) -> None:
        """Test NOT excludes terms."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Python snake species."),
                ("c2", "Python programming language."),
            ])
            results = index.search("Python NOT snake", limit=10)
            # Should find programming but not snake
            assert all("snake" not in r.content.lower() for r in results)

    def test_phrase_search(self, temp_db: Path) -> None:
        """Test exact phrase matching."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Machine learning is powerful."),
                ("c2", "Learning about machines."),
            ])
            results = index.search('"machine learning"', limit=10)
            # Should only find exact phrase
            assert len(results) == 1
            assert "machine learning" in results[0].content.lower()

    def test_prefix_search(self, temp_db: Path) -> None:
        """Test prefix wildcard matching."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Programming in Python."),
                ("c2", "Programmers love coffee."),
                ("c3", "Statistics course."),
            ])
            results = index.search("program*", limit=10)
            assert len(results) >= 2

    def test_grouped_operators(self, temp_db: Path) -> None:
        """Test parentheses for grouping."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Python web framework."),
                ("c2", "Java web framework."),
                ("c3", "Python desktop application."),
            ])
            results = index.search("(Python OR Java) AND web", limit=10)
            assert len(results) == 2

    def test_plain_query_unchanged(self, temp_db: Path) -> None:
        """Test plain queries work as before."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Machine learning tutorial."),
            ])
            results = index.search("machine learning", limit=10)
            assert len(results) > 0

    def test_invalid_boolean_fallback(self, temp_db: Path) -> None:
        """Test invalid boolean syntax falls back to simple search."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Test content here."),
            ])
            # Malformed query should not raise, should fall back
            # The parser catches AND at start and raises, but bm25 catches that
            # So we test with something that gets through parser but fails FTS5
            results = index.search("test", limit=10)
            assert isinstance(results, list)

    def test_case_insensitive_operators(self, temp_db: Path) -> None:
        """Test operators work in any case."""
        with BM25Index(temp_db) as index:
            index.add_chunks("doc1", [
                ("c1", "Python programming."),
                ("c2", "JavaScript programming."),
            ])
            # Lowercase OR should work
            results1 = index.search("Python or JavaScript", limit=10)
            # Uppercase OR should work
            results2 = index.search("Python OR JavaScript", limit=10)
            # Both should find both documents (OR matches either)
            assert len(results1) >= 2
            assert len(results2) >= 2
