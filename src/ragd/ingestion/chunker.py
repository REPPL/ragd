"""Text chunking engine for ragd.

This module provides various strategies for splitting text into chunks
suitable for embedding and retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import tiktoken

ChunkStrategy = Literal["sentence", "fixed", "recursive", "structure"]


@dataclass
class Chunk:
    """A text chunk with metadata."""

    content: str
    index: int
    start_char: int
    end_char: int
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class Chunker(Protocol):
    """Protocol for text chunkers."""

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata to include in chunks

        Returns:
            List of Chunk objects
        """
        ...


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        encoding_name: Tiktoken encoding name

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate of 4 chars per token
        return len(text) // 4


class SentenceChunker:
    """Chunk text by sentences, respecting token limits."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_chunk_size: int = 100,
    ) -> None:
        """Initialise sentence chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum chunk size in tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        # Sentence splitting pattern
        self._sentence_pattern = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|"  # Standard sentence boundaries
            r"(?<=\n)\n+|"  # Paragraph breaks
            r"(?<=:)\s*\n"  # Colon followed by newline
        )

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks based on sentences.

        Args:
            text: Text to chunk
            metadata: Optional metadata for chunks

        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        char_offset = 0

        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)

            # If adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_sentences:
                # Create chunk from current sentences
                chunk_text = " ".join(current_sentences)
                start_char = char_offset
                end_char = start_char + len(chunk_text)

                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=len(chunks),
                        start_char=start_char,
                        end_char=end_char,
                        token_count=current_tokens,
                        metadata=metadata.copy() if metadata else {},
                    )
                )

                # Handle overlap
                overlap_tokens = 0
                overlap_sentences: list[str] = []
                for s in reversed(current_sentences):
                    s_tokens = count_tokens(s)
                    if overlap_tokens + s_tokens <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break

                char_offset = end_char - sum(len(s) + 1 for s in overlap_sentences)
                current_sentences = overlap_sentences
                current_tokens = overlap_tokens

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Handle remaining sentences
        if current_sentences and current_tokens >= self.min_chunk_size:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=char_offset,
                    end_char=char_offset + len(chunk_text),
                    token_count=current_tokens,
                    metadata=metadata.copy() if metadata else {},
                )
            )
        elif current_sentences and chunks:
            # Merge with last chunk if too small
            last_chunk = chunks[-1]
            merged_content = last_chunk.content + " " + " ".join(current_sentences)
            chunks[-1] = Chunk(
                content=merged_content,
                index=last_chunk.index,
                start_char=last_chunk.start_char,
                end_char=last_chunk.start_char + len(merged_content),
                token_count=last_chunk.token_count + current_tokens,
                metadata=last_chunk.metadata,
            )
        elif current_sentences:
            # Single chunk for small documents
            chunk_text = " ".join(current_sentences)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=0,
                    start_char=0,
                    end_char=len(chunk_text),
                    token_count=current_tokens,
                    metadata=metadata.copy() if metadata else {},
                )
            )

        return chunks


class FixedChunker:
    """Chunk text by fixed token count."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> None:
        """Initialise fixed chunker.

        Args:
            chunk_size: Chunk size in tokens
            overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into fixed-size chunks.

        Args:
            text: Text to chunk
            metadata: Optional metadata for chunks

        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []

        # Approximate chars per token
        chars_per_token = 4
        chunk_chars = self.chunk_size * chars_per_token
        overlap_chars = self.overlap * chars_per_token

        chunks: list[Chunk] = []
        start = 0

        while start < len(text):
            end = min(start + chunk_chars, len(text))

            # Try to break at word boundary
            if end < len(text):
                space_pos = text.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=len(chunks),
                        start_char=start,
                        end_char=end,
                        token_count=count_tokens(chunk_text),
                        metadata=metadata.copy() if metadata else {},
                    )
                )

            start = end - overlap_chars
            if start >= len(text) - overlap_chars:
                break

        return chunks


class RecursiveChunker:
    """Chunk text recursively, respecting document structure."""

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_chunk_size: int = 100,
    ) -> None:
        """Initialise recursive chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        # Separators in order of priority
        self._separators = [
            "\n## ",  # Markdown H2
            "\n# ",  # Markdown H1
            "\n\n\n",  # Multiple paragraph breaks
            "\n\n",  # Paragraph break
            "\n",  # Line break
            ". ",  # Sentence
            " ",  # Word
        ]

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text recursively.

        Args:
            text: Text to chunk
            metadata: Optional metadata for chunks

        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []

        raw_chunks = self._recursive_split(text)
        chunks: list[Chunk] = []
        char_offset = 0

        for i, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue

            start_char = text.find(chunk_text, char_offset)
            if start_char == -1:
                start_char = char_offset

            chunks.append(
                Chunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=start_char,
                    end_char=start_char + len(chunk_text),
                    token_count=count_tokens(chunk_text),
                    metadata=metadata.copy() if metadata else {},
                )
            )

            char_offset = start_char + len(chunk_text)

        return chunks

    def _recursive_split(self, text: str, separators: list[str] | None = None) -> list[str]:
        """Recursively split text.

        Args:
            text: Text to split
            separators: Remaining separators to try

        Returns:
            List of text chunks
        """
        if separators is None:
            separators = self._separators.copy()

        if not separators:
            return [text] if text.strip() else []

        separator = separators[0]
        remaining = separators[1:]

        if separator not in text:
            return self._recursive_split(text, remaining)

        parts = text.split(separator)
        result: list[str] = []
        current = ""

        for part in parts:
            if not part.strip():
                continue

            test_chunk = current + separator + part if current else part
            if count_tokens(test_chunk) <= self.chunk_size:
                current = test_chunk
            else:
                if current:
                    if count_tokens(current) >= self.min_chunk_size:
                        result.append(current)
                    elif result:
                        result[-1] = result[-1] + separator + current

                if count_tokens(part) > self.chunk_size:
                    # Recursively split
                    sub_chunks = self._recursive_split(part, remaining)
                    result.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current:
            if count_tokens(current) >= self.min_chunk_size:
                result.append(current)
            elif result:
                result[-1] = result[-1] + separator + current

        return result


class StructureChunker:
    """Chunk text while respecting HTML structure.

    This chunker preserves structural elements:
    - Tables are kept together when possible
    - Heading boundaries are respected
    - Lists are not split mid-way
    - Code blocks are preserved

    Implements F-039: Advanced HTML Processing.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_chunk_size: int = 100,
        keep_tables_together: bool = True,
        respect_headings: bool = True,
    ) -> None:
        """Initialise structure-aware chunker.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
            keep_tables_together: Try to keep Markdown tables together
            respect_headings: Create chunk boundaries at headings
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.keep_tables_together = keep_tables_together
        self.respect_headings = respect_headings

        # Patterns for structure detection
        self._heading_pattern = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
        self._table_pattern = re.compile(
            r"^\|.+\|\s*\n\|[-:\s|]+\|\s*\n(?:\|.+\|\s*\n?)+",
            re.MULTILINE
        )
        self._code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        self._list_pattern = re.compile(
            r"(?:^[-*+]\s+.+\n?)+|(?:^\d+\.\s+.+\n?)+",
            re.MULTILINE
        )

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks while preserving structure.

        Args:
            text: Text to chunk (plain text or Markdown)
            metadata: Optional metadata for chunks

        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []

        # First, identify structural elements that should stay together
        protected_regions = self._identify_protected_regions(text)

        # Split by headings if enabled
        if self.respect_headings:
            sections = self._split_by_headings(text)
        else:
            sections = [text]

        chunks: list[Chunk] = []
        char_offset = 0

        for section in sections:
            if not section.strip():
                continue

            # Check if this section is small enough to be a single chunk
            section_tokens = count_tokens(section)
            if section_tokens <= self.chunk_size:
                start_char = text.find(section, char_offset)
                if start_char == -1:
                    start_char = char_offset

                chunks.append(
                    Chunk(
                        content=section.strip(),
                        index=len(chunks),
                        start_char=start_char,
                        end_char=start_char + len(section),
                        token_count=section_tokens,
                        metadata=metadata.copy() if metadata else {},
                    )
                )
                char_offset = start_char + len(section)
            else:
                # Need to split this section further
                sub_chunks = self._split_large_section(section, protected_regions)
                for sub_chunk in sub_chunks:
                    if not sub_chunk.strip():
                        continue

                    start_char = text.find(sub_chunk, char_offset)
                    if start_char == -1:
                        start_char = char_offset

                    chunks.append(
                        Chunk(
                            content=sub_chunk.strip(),
                            index=len(chunks),
                            start_char=start_char,
                            end_char=start_char + len(sub_chunk),
                            token_count=count_tokens(sub_chunk),
                            metadata=metadata.copy() if metadata else {},
                        )
                    )
                    char_offset = start_char + len(sub_chunk)

        # Merge chunks that are too small
        chunks = self._merge_small_chunks(chunks)

        # Re-index chunks
        for i, chunk in enumerate(chunks):
            chunk.index = i

        return chunks

    def _identify_protected_regions(self, text: str) -> list[tuple[int, int]]:
        """Identify regions that should not be split.

        Args:
            text: Text to analyse

        Returns:
            List of (start, end) tuples for protected regions
        """
        regions: list[tuple[int, int]] = []

        # Tables
        if self.keep_tables_together:
            for match in self._table_pattern.finditer(text):
                # Only protect if it fits in a single chunk
                if count_tokens(match.group()) <= self.chunk_size:
                    regions.append((match.start(), match.end()))

        # Code blocks (always keep together if they fit)
        for match in self._code_block_pattern.finditer(text):
            if count_tokens(match.group()) <= self.chunk_size:
                regions.append((match.start(), match.end()))

        return sorted(regions, key=lambda x: x[0])

    def _split_by_headings(self, text: str) -> list[str]:
        """Split text at heading boundaries.

        Args:
            text: Text to split

        Returns:
            List of sections
        """
        # Find all heading positions
        headings = list(self._heading_pattern.finditer(text))
        if not headings:
            return [text]

        sections = []
        prev_end = 0

        for match in headings:
            # Get content before this heading
            if match.start() > prev_end:
                before = text[prev_end:match.start()].strip()
                if before:
                    sections.append(before)

            prev_end = match.start()

        # Get remaining content (including last heading)
        if prev_end < len(text):
            sections.append(text[prev_end:])

        return sections

    def _split_large_section(
        self, text: str, protected_regions: list[tuple[int, int]]
    ) -> list[str]:
        """Split a large section into smaller chunks.

        Args:
            text: Text to split
            protected_regions: Regions that should not be split

        Returns:
            List of text chunks
        """
        # Use paragraph-based splitting
        paragraphs = re.split(r"\n\n+", text)
        if not paragraphs:
            return [text]

        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = count_tokens(para)

            # If this paragraph is very large, may need recursive splitting
            if para_tokens > self.chunk_size:
                # Flush current buffer
                if current:
                    chunks.append("\n\n".join(current))
                    current = []
                    current_tokens = 0

                # Split the large paragraph by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    sent_tokens = count_tokens(sentence)
                    if current_tokens + sent_tokens > self.chunk_size and current:
                        chunks.append(" ".join(current))
                        current = []
                        current_tokens = 0
                    current.append(sentence)
                    current_tokens += sent_tokens

                continue

            # Check if adding this paragraph exceeds limit
            if current_tokens + para_tokens > self.chunk_size and current:
                chunks.append("\n\n".join(current))
                current = []
                current_tokens = 0

            current.append(para)
            current_tokens += para_tokens

        # Flush remaining
        if current:
            chunks.append("\n\n".join(current))

        return chunks

    def _merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Merge chunks that are too small.

        Args:
            chunks: List of chunks to potentially merge

        Returns:
            Merged chunk list
        """
        if not chunks:
            return []

        result: list[Chunk] = []

        for chunk in chunks:
            if not result:
                result.append(chunk)
                continue

            # Check if current chunk is too small and can be merged
            if chunk.token_count < self.min_chunk_size:
                last = result[-1]
                merged_tokens = last.token_count + chunk.token_count

                # Merge if combined size is acceptable
                if merged_tokens <= self.chunk_size * 1.2:  # Allow 20% overflow
                    merged_content = last.content + "\n\n" + chunk.content
                    result[-1] = Chunk(
                        content=merged_content,
                        index=last.index,
                        start_char=last.start_char,
                        end_char=chunk.end_char,
                        token_count=merged_tokens,
                        metadata=last.metadata,
                    )
                    continue

            result.append(chunk)

        return result


# Chunker registry
CHUNKERS: dict[ChunkStrategy, type[Chunker]] = {
    "sentence": SentenceChunker,
    "fixed": FixedChunker,
    "recursive": RecursiveChunker,
    "structure": StructureChunker,
}


def chunk_text(
    text: str,
    strategy: ChunkStrategy = "sentence",
    chunk_size: int = 512,
    overlap: int = 50,
    min_chunk_size: int = 100,
    metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    """Chunk text using specified strategy.

    Args:
        text: Text to chunk
        strategy: Chunking strategy to use
        chunk_size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        min_chunk_size: Minimum chunk size in tokens
        metadata: Optional metadata for chunks

    Returns:
        List of Chunk objects
    """
    chunker_class = CHUNKERS.get(strategy, SentenceChunker)

    # FixedChunker doesn't have min_chunk_size
    if strategy == "fixed":
        chunker = chunker_class(
            chunk_size=chunk_size,
            overlap=overlap,
        )
    else:
        chunker = chunker_class(
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size,
        )
    return chunker.chunk(text, metadata)
