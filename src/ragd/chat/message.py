"""Chat message types for ragd.

Defines the core data structures for chat conversations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ragd.citation import Citation


class ChatRole(str, Enum):
    """Role of a message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """A single message in a conversation.

    Attributes:
        role: Who sent the message
        content: Message content
        timestamp: When the message was created
        citations: Source citations (for assistant messages)
        metadata: Additional message metadata
    """

    role: ChatRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    citations: list[Citation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation.

        Returns:
            Dictionary representation
        """
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "citations": [
                {
                    "document_id": c.document_id,
                    "filename": c.filename,
                    "page_number": c.page_number,
                    "chunk_index": c.chunk_index,
                    "relevance_score": c.relevance_score,
                    "content_preview": c.content_preview,
                }
                for c in self.citations
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ChatMessage instance
        """
        citations = []
        for c in data.get("citations", []):
            citations.append(
                Citation(
                    document_id=c.get("document_id", ""),
                    filename=c.get("filename", ""),
                    page_number=c.get("page_number"),
                    chunk_index=c.get("chunk_index"),
                    relevance_score=c.get("relevance_score"),
                    content_preview=c.get("content_preview"),
                )
            )

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            role=ChatRole(data["role"]),
            content=data["content"],
            timestamp=timestamp,
            citations=citations,
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """Format for display."""
        return f"[{self.role.value}]: {self.content[:100]}..."


@dataclass
class CitedAnswer:
    """An answer with source citations.

    Attributes:
        answer: The generated answer text
        citations: Sources used to generate the answer
        model: The model used for generation
        tokens_used: Number of tokens used
        confidence: Confidence score (if available)
    """

    answer: str
    citations: list[Citation] = field(default_factory=list)
    model: str | None = None
    tokens_used: int | None = None
    confidence: float | None = None

    @property
    def has_citations(self) -> bool:
        """Check if answer has citations."""
        return len(self.citations) > 0

    def format_with_citations(self, style: str = "inline") -> str:
        """Format answer with inline citations.

        Args:
            style: Citation style (inline, numbered, footnote)

        Returns:
            Formatted answer with citations
        """
        if not self.citations:
            return self.answer

        if style == "numbered":
            citation_text = "\n\nSources:\n"
            for i, c in enumerate(self.citations, 1):
                loc = f", p. {c.page_number}" if c.page_number else ""
                citation_text += f"[{i}] {c.filename}{loc}\n"
            return self.answer + citation_text

        elif style == "footnote":
            # Add superscript numbers at end of answer
            numbers = "".join(f"[{i+1}]" for i in range(len(self.citations)))
            citation_text = f"\n\n{'─' * 40}\n"
            for i, c in enumerate(self.citations, 1):
                loc = f", p. {c.page_number}" if c.page_number else ""
                citation_text += f"{i}. {c.filename}{loc}\n"
            return f"{self.answer} {numbers}{citation_text}"

        else:  # inline
            sources = ", ".join(
                f"{c.filename}" + (f":p{c.page_number}" if c.page_number else "")
                for c in self.citations
            )
            return f"{self.answer}\n\n[Sources: {sources}]"
