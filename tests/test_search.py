"""Tests for search module."""

from ragd.search.searcher import SearchResult, SourceLocation


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_basic(self) -> None:
        """Test basic SearchResult creation."""
        result = SearchResult(
            content="Test content",
            score=0.95,
            document_id="doc_123",
            document_name="test.pdf",
            chunk_index=0,
        )
        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.document_id == "doc_123"
        assert result.document_name == "test.pdf"
        assert result.chunk_index == 0
        assert result.metadata == {}
        assert result.location is None

    def test_search_result_with_location(self) -> None:
        """Test SearchResult with location."""
        location = SourceLocation(
            page_number=1,
            char_start=100,
            char_end=200,
        )
        result = SearchResult(
            content="Test content",
            score=0.9,
            document_id="doc_123",
            document_name="test.pdf",
            chunk_index=5,
            location=location,
        )
        assert result.location is not None
        assert result.location.page_number == 1
        assert result.location.char_start == 100
        assert result.location.char_end == 200

    def test_search_result_with_metadata(self) -> None:
        """Test SearchResult with metadata."""
        result = SearchResult(
            content="Test content",
            score=0.85,
            document_id="doc_123",
            document_name="test.pdf",
            chunk_index=2,
            metadata={"source": "test.pdf", "pages": 10},
        )
        assert result.metadata["source"] == "test.pdf"
        assert result.metadata["pages"] == 10


class TestSourceLocation:
    """Tests for SourceLocation dataclass."""

    def test_source_location_defaults(self) -> None:
        """Test SourceLocation default values."""
        location = SourceLocation()
        assert location.page_number is None
        assert location.char_start is None
        assert location.char_end is None

    def test_source_location_with_values(self) -> None:
        """Test SourceLocation with values."""
        location = SourceLocation(
            page_number=5,
            char_start=1000,
            char_end=1500,
        )
        assert location.page_number == 5
        assert location.char_start == 1000
        assert location.char_end == 1500
