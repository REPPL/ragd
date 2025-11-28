"""Chat history persistence for ragd.

Handles saving and loading conversation history.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ragd.chat.message import ChatMessage, ChatRole


@dataclass
class ChatHistory:
    """Conversation history container.

    Attributes:
        messages: List of messages in chronological order
        session_id: Unique session identifier
        created_at: When the session started
        metadata: Additional session metadata
    """

    messages: list[ChatMessage] = field(default_factory=list)
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(
        self,
        role: ChatRole,
        content: str,
        **kwargs: Any,
    ) -> ChatMessage:
        """Add a message to history.

        Args:
            role: Message role
            content: Message content
            **kwargs: Additional message attributes

        Returns:
            The created message
        """
        message = ChatMessage(role=role, content=content, **kwargs)
        self.messages.append(message)
        return message

    def add_user_message(self, content: str) -> ChatMessage:
        """Add a user message.

        Args:
            content: Message content

        Returns:
            The created message
        """
        return self.add_message(ChatRole.USER, content)

    def add_assistant_message(
        self,
        content: str,
        citations: list | None = None,
    ) -> ChatMessage:
        """Add an assistant message.

        Args:
            content: Message content
            citations: Source citations

        Returns:
            The created message
        """
        return self.add_message(
            ChatRole.ASSISTANT,
            content,
            citations=citations or [],
        )

    def get_recent(self, n: int = 5) -> list[ChatMessage]:
        """Get the n most recent messages.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of recent messages
        """
        return self.messages[-n:] if n > 0 else []

    def format_for_prompt(
        self,
        n: int = 5,
        include_system: bool = False,
    ) -> str:
        """Format recent history for inclusion in prompt.

        Args:
            n: Number of recent messages to include
            include_system: Include system messages

        Returns:
            Formatted history string
        """
        messages = self.get_recent(n)
        if not include_system:
            messages = [m for m in messages if m.role != ChatRole.SYSTEM]

        if not messages:
            return ""

        parts = []
        for msg in messages:
            role = msg.role.value.capitalize()
            parts.append(f"{role}: {msg.content}")

        return "\n".join(parts)

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatHistory:
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ChatHistory instance
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        messages = [
            ChatMessage.from_dict(m) for m in data.get("messages", [])
        ]

        return cls(
            session_id=data.get("session_id", ""),
            created_at=created_at,
            messages=messages,
            metadata=data.get("metadata", {}),
        )

    def __len__(self) -> int:
        """Get number of messages."""
        return len(self.messages)

    def __iter__(self):
        """Iterate over messages."""
        return iter(self.messages)


def save_history(
    history: ChatHistory,
    path: Path | str,
) -> None:
    """Save chat history to file.

    Args:
        history: Chat history to save
        path: File path to save to
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(history.to_dict(), f, indent=2, ensure_ascii=False)


def load_history(path: Path | str) -> ChatHistory:
    """Load chat history from file.

    Args:
        path: File path to load from

    Returns:
        ChatHistory instance

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is invalid JSON
    """
    path = Path(path)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return ChatHistory.from_dict(data)


def get_history_path(session_id: str | None = None) -> Path:
    """Get the default history file path.

    Args:
        session_id: Optional session ID for specific history

    Returns:
        Path to history file
    """
    history_dir = Path.home() / ".ragd" / "chat_history"
    history_dir.mkdir(parents=True, exist_ok=True)

    if session_id:
        return history_dir / f"{session_id}.json"
    return history_dir / "latest.json"


def list_history_sessions() -> list[dict[str, Any]]:
    """List available chat history sessions.

    Returns:
        List of session metadata dicts
    """
    history_dir = Path.home() / ".ragd" / "chat_history"
    if not history_dir.exists():
        return []

    sessions = []
    for path in history_dir.glob("*.json"):
        try:
            history = load_history(path)
            sessions.append({
                "session_id": history.session_id or path.stem,
                "created_at": history.created_at,
                "message_count": len(history),
                "path": str(path),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return sorted(sessions, key=lambda x: x["created_at"], reverse=True)
