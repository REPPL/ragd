"""Tests for text chunking module."""

from ragd.ingestion.chunker import (
    Chunk,
    SentenceChunker,
    FixedChunker,
    RecursiveChunker,
    chunk_text,
    count_tokens,
    CHUNKERS,
)


def test_count_tokens() -> None:
    """Test token counting."""
    count = count_tokens("Hello world")
    assert count > 0
    assert count < 10


def test_chunk_dataclass() -> None:
    """Test Chunk dataclass."""
    chunk = Chunk(
        content="Test content",
        index=0,
        start_char=0,
        end_char=12,
        token_count=2,
    )
    assert chunk.content == "Test content"
    assert chunk.index == 0
    assert chunk.token_count == 2


def test_sentence_chunker_basic() -> None:
    """Test basic sentence chunking."""
    chunker = SentenceChunker(chunk_size=50, overlap=10)
    text = "This is sentence one. This is sentence two. This is sentence three."
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1
    assert all(c.content for c in chunks)


def test_sentence_chunker_metadata() -> None:
    """Test sentence chunker preserves metadata."""
    chunker = SentenceChunker(chunk_size=100, overlap=10)
    text = "This is a test sentence."
    metadata = {"source": "test.txt"}
    chunks = chunker.chunk(text, metadata)
    assert len(chunks) == 1
    assert chunks[0].metadata.get("source") == "test.txt"


def test_sentence_chunker_empty() -> None:
    """Test sentence chunker with empty text."""
    chunker = SentenceChunker()
    chunks = chunker.chunk("")
    assert chunks == []


def test_fixed_chunker_basic() -> None:
    """Test basic fixed chunking."""
    chunker = FixedChunker(chunk_size=10, overlap=2)
    text = "This is a longer piece of text that should be split into multiple chunks."
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1
    assert all(c.content for c in chunks)


def test_fixed_chunker_empty() -> None:
    """Test fixed chunker with empty text."""
    chunker = FixedChunker()
    chunks = chunker.chunk("")
    assert chunks == []


def test_recursive_chunker_basic() -> None:
    """Test basic recursive chunking."""
    chunker = RecursiveChunker(chunk_size=50, overlap=10, min_chunk_size=5)
    text = "# Header\n\nParagraph one with some content.\n\nParagraph two with more content."
    chunks = chunker.chunk(text)
    assert len(chunks) >= 1
    assert all(c.content for c in chunks)


def test_recursive_chunker_empty() -> None:
    """Test recursive chunker with empty text."""
    chunker = RecursiveChunker()
    chunks = chunker.chunk("")
    assert chunks == []


def test_chunk_text_function() -> None:
    """Test chunk_text convenience function."""
    text = "This is a test. This is another test."
    chunks = chunk_text(text, strategy="sentence", chunk_size=100)
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_text_strategies() -> None:
    """Test all chunking strategies."""
    # Use reasonable parameters for all strategies
    text = "This is test content. " * 50  # ~250 tokens
    for strategy in ["sentence", "fixed", "recursive"]:
        chunks = chunk_text(
            text,
            strategy=strategy,  # type: ignore
            chunk_size=100,
            min_chunk_size=20,
        )
        assert len(chunks) >= 1


def test_chunkers_registry() -> None:
    """Test chunkers are registered."""
    assert "sentence" in CHUNKERS
    assert "fixed" in CHUNKERS
    assert "recursive" in CHUNKERS


def test_chunk_indices() -> None:
    """Test chunk indices are sequential."""
    chunker = SentenceChunker(chunk_size=20, overlap=5)
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    chunks = chunker.chunk(text)
    if len(chunks) > 1:
        indices = [c.index for c in chunks]
        assert indices == list(range(len(chunks)))
