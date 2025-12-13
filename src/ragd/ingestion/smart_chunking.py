"""Smart chunking strategies (F-101).

Content-aware chunking that respects document structure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with metadata."""

    text: str
    start_pos: int
    end_pos: int
    chunk_type: str = "text"  # text, header, list, code


class StructuralChunker:
    """Chunk text respecting document structure.

    Preserves headers, lists, and code blocks.
    """

    def __init__(
        self,
        max_chunk_size: int = 512,
        min_chunk_size: int = 100,
        overlap: int = 50,
        respect_headers: bool = True,
        respect_lists: bool = True,
        respect_code: bool = True,
    ):
        """Initialise structural chunker.

        Args:
            max_chunk_size: Maximum tokens per chunk
            min_chunk_size: Minimum tokens per chunk
            overlap: Token overlap between chunks
            respect_headers: Keep headers with content
            respect_lists: Don't split lists
            respect_code: Don't split code blocks
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        self.respect_headers = respect_headers
        self.respect_lists = respect_lists
        self.respect_code = respect_code

        # Patterns
        self.header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        self.list_pattern = re.compile(r"^(\s*[-*+]\s+.+\n?)+", re.MULTILINE)
        self.code_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        self.paragraph_pattern = re.compile(r"\n\n+")

    def chunk(self, text: str) -> list[Chunk]:
        """Chunk text with structural awareness.

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        # Identify structural elements
        elements = self._identify_elements(text)

        # Group elements into chunks
        chunks = self._group_elements(elements)

        return chunks

    def _identify_elements(self, text: str) -> list[Chunk]:
        """Identify structural elements in text.

        Args:
            text: Text to analyse

        Returns:
            List of elements
        """
        elements: list[Chunk] = []
        pos = 0

        # Find all code blocks first (they take precedence)
        if self.respect_code:
            for match in self.code_pattern.finditer(text):
                # Add text before code block
                if match.start() > pos:
                    before_text = text[pos:match.start()].strip()
                    if before_text:
                        elements.extend(self._split_text(before_text, pos))

                # Add code block
                elements.append(Chunk(
                    text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    chunk_type="code",
                ))
                pos = match.end()

        # Handle remaining text
        if pos < len(text):
            remaining = text[pos:].strip()
            if remaining:
                elements.extend(self._split_text(remaining, pos))

        return elements

    def _split_text(self, text: str, start_offset: int) -> list[Chunk]:
        """Split text into paragraphs and structural elements.

        Args:
            text: Text to split
            start_offset: Starting position in original text

        Returns:
            List of chunks
        """
        elements: list[Chunk] = []
        paragraphs = self.paragraph_pattern.split(text)

        pos = start_offset
        current_header = None

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if header
            header_match = self.header_pattern.match(para)
            if header_match and self.respect_headers:
                current_header = para
                elements.append(Chunk(
                    text=para,
                    start_pos=pos,
                    end_pos=pos + len(para),
                    chunk_type="header",
                ))
            # Check if list
            elif self.list_pattern.match(para) and self.respect_lists:
                # Include header if present
                chunk_text = f"{current_header}\n\n{para}" if current_header else para
                elements.append(Chunk(
                    text=chunk_text,
                    start_pos=pos,
                    end_pos=pos + len(para),
                    chunk_type="list",
                ))
                current_header = None
            else:
                # Regular paragraph
                # Include header if present
                chunk_text = f"{current_header}\n\n{para}" if current_header else para
                elements.append(Chunk(
                    text=chunk_text,
                    start_pos=pos,
                    end_pos=pos + len(para),
                    chunk_type="text",
                ))
                current_header = None

            pos += len(para) + 2  # Account for paragraph separator

        return elements

    def _group_elements(self, elements: list[Chunk]) -> list[Chunk]:
        """Group small elements into larger chunks.

        Args:
            elements: List of elements

        Returns:
            List of grouped chunks
        """
        if not elements:
            return []

        chunks: list[Chunk] = []
        current_texts: list[str] = []
        current_start = elements[0].start_pos
        current_size = 0

        for elem in elements:
            elem_size = self._estimate_tokens(elem.text)

            # If element is too large, split it
            if elem_size > self.max_chunk_size:
                # Flush current
                if current_texts:
                    chunks.append(Chunk(
                        text="\n\n".join(current_texts),
                        start_pos=current_start,
                        end_pos=elem.start_pos,
                        chunk_type="text",
                    ))
                    current_texts = []
                    current_size = 0

                # Add large element as its own chunk (may need further splitting)
                chunks.append(elem)
                current_start = elem.end_pos
                continue

            # If adding would exceed max, flush current
            if current_size + elem_size > self.max_chunk_size and current_texts:
                chunks.append(Chunk(
                    text="\n\n".join(current_texts),
                    start_pos=current_start,
                    end_pos=elem.start_pos,
                    chunk_type="text",
                ))
                current_texts = []
                current_size = 0
                current_start = elem.start_pos

            current_texts.append(elem.text)
            current_size += elem_size

        # Flush remaining
        if current_texts:
            chunks.append(Chunk(
                text="\n\n".join(current_texts),
                start_pos=current_start,
                end_pos=elements[-1].end_pos if elements else current_start,
                chunk_type="text",
            ))

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses simple word count approximation.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 word ≈ 1.3 tokens
        words = len(text.split())
        return int(words * 1.3)


def structural_chunk(
    text: str,
    max_size: int = 512,
    overlap: int = 50,
    respect_structure: bool = True,
) -> list[str]:
    """Chunk text with structural awareness.

    Convenience function for structural chunking.

    Args:
        text: Text to chunk
        max_size: Maximum tokens per chunk
        overlap: Token overlap
        respect_structure: Whether to respect document structure

    Returns:
        List of chunk texts
    """
    chunker = StructuralChunker(
        max_chunk_size=max_size,
        overlap=overlap,
        respect_headers=respect_structure,
        respect_lists=respect_structure,
        respect_code=respect_structure,
    )

    chunks = chunker.chunk(text)
    return [c.text for c in chunks]
