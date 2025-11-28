"""Chat module for ragd.

Provides conversational RAG with LLM integration, context assembly,
and citation tracking.
"""

from ragd.chat.agentic import (
    AgenticConfig,
    AgenticRAG,
    AgenticResponse,
    RetrievalQuality,
    agentic_ask,
)
from ragd.chat.context import ContextWindow, RetrievedContext
from ragd.chat.history import ChatHistory, save_history, load_history
from ragd.chat.message import ChatMessage, ChatRole, CitedAnswer
from ragd.chat.prompts import PromptTemplate, get_prompt_template
from ragd.chat.session import ChatSession, ChatConfig, ask_question, check_chat_available

__all__ = [
    # Core types
    "ChatMessage",
    "ChatRole",
    "CitedAnswer",
    # Config
    "ChatConfig",
    # Context management
    "ContextWindow",
    "RetrievedContext",
    # Prompts
    "PromptTemplate",
    "get_prompt_template",
    # History
    "ChatHistory",
    "save_history",
    "load_history",
    # Session
    "ChatSession",
    "ask_question",
    "check_chat_available",
    # Agentic RAG
    "AgenticConfig",
    "AgenticRAG",
    "AgenticResponse",
    "RetrievalQuality",
    "agentic_ask",
]
