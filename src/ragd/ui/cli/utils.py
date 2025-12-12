"""Shared CLI utilities for ragd.

This module contains utility functions and classes used across CLI commands.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ragd.citation import Citation


def get_console(no_color: bool = False, max_width: int | None = None) -> Console:
    """Get console with colour and width settings.

    Args:
        no_color: Whether to disable colour
        max_width: Maximum output width (None = use terminal width)

    Returns:
        Console instance
    """
    # Check NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        no_color = True
    return Console(no_color=no_color, width=max_width, soft_wrap=True)


def format_citation_location(cit: "Citation") -> str:
    """Format citation location with page range support.

    Handles both single page numbers and aggregated page ranges
    from multi-chunk citations.

    Args:
        cit: Citation object (may have all_pages in extra metadata)

    Returns:
        Location string like ", p. 5" or ", pp. 1-5" or ""
    """
    # Check for aggregated pages from multi-chunk citations
    all_pages = cit.extra.get("all_pages", []) if cit.extra else []
    if all_pages and len(all_pages) > 1:
        return f", pp. {all_pages[0]}-{all_pages[-1]}"
    elif cit.page_number:
        return f", p. {cit.page_number}"
    return ""


class StreamingWordWrapper:
    """Buffers streaming output for word-boundary aware wrapping.

    When streaming LLM responses character-by-character, Rich's soft_wrap
    doesn't work because each chunk is printed immediately. This class
    buffers partial words and wraps at word boundaries.
    """

    def __init__(
        self,
        console: Console,
        max_width: int,
        prefix_width: int = 3,
    ) -> None:
        """Initialise streaming wrapper.

        Args:
            console: Rich console for output
            max_width: Maximum line width
            prefix_width: Width of line prefix (e.g., "A: " = 3)
        """
        self.console = console
        self.max_width = max_width
        self.prefix_width = prefix_width
        self.current_line_len = prefix_width
        self.word_buffer = ""

    def write(self, chunk: str) -> None:
        """Write chunk with word-aware wrapping.

        Args:
            chunk: Text chunk to write (may be partial word)
        """
        for char in chunk:
            if char in " \n\t":
                # Whitespace: flush word buffer first
                self._flush_word()
                if char == "\n":
                    self._newline()
                elif char == " ":
                    self._write_space()
                # Tabs treated as spaces
                elif char == "\t":
                    self._write_space()
            else:
                self.word_buffer += char

    def _flush_word(self) -> None:
        """Flush buffered word to output."""
        if not self.word_buffer:
            return

        word_len = len(self.word_buffer)

        # Check if word fits on current line
        if self.current_line_len + word_len > self.max_width:
            # Word doesn't fit - wrap to new line
            self._newline()

        # Handle words longer than max_width (rare edge case)
        if word_len > self.max_width:
            # Split long word across lines
            remaining = self.word_buffer
            while remaining:
                space_left = self.max_width - self.current_line_len
                if space_left <= 0:
                    self._newline()
                    space_left = self.max_width
                chunk = remaining[:space_left]
                self.console.print(chunk, end="", markup=False)
                self.current_line_len += len(chunk)
                remaining = remaining[space_left:]
        else:
            self.console.print(self.word_buffer, end="", markup=False)
            self.current_line_len += word_len

        self.word_buffer = ""

    def _write_space(self) -> None:
        """Write a space if room on line."""
        if self.current_line_len < self.max_width:
            self.console.print(" ", end="", markup=False)
            self.current_line_len += 1

    def _newline(self) -> None:
        """Output newline and reset line counter."""
        self.console.print()
        self.current_line_len = 0

    def flush(self) -> None:
        """Flush any remaining buffered content."""
        self._flush_word()


__all__ = [
    "get_console",
    "format_citation_location",
    "StreamingWordWrapper",
]
