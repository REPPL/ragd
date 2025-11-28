"""RAG prompt templates for ragd.

Provides prompt templates for different RAG tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PromptType(str, Enum):
    """Types of RAG prompts."""

    ANSWER = "answer"
    SUMMARISE = "summarise"
    COMPARE = "compare"
    CHAT = "chat"
    REFINE = "refine"


@dataclass
class PromptTemplate:
    """A prompt template with placeholders.

    Attributes:
        name: Template identifier
        system_prompt: System prompt for the LLM
        user_template: User message template with {placeholders}
        description: What this template is for
    """

    name: str
    system_prompt: str
    user_template: str
    description: str = ""

    def format(
        self,
        context: str = "",
        question: str = "",
        history: str = "",
        **kwargs: Any,
    ) -> tuple[str, str]:
        """Format the template with provided values.

        Args:
            context: Retrieved context chunks
            question: User question
            history: Conversation history
            **kwargs: Additional template variables

        Returns:
            Tuple of (system_prompt, user_message)
        """
        user_message = self.user_template.format(
            context=context,
            question=question,
            history=history,
            **kwargs,
        )
        return self.system_prompt, user_message


# Default RAG prompt templates
RAG_ANSWER_TEMPLATE = PromptTemplate(
    name="rag_answer",
    system_prompt=(
        "You are a helpful assistant that answers questions based on the provided context. "
        "Always cite your sources by referencing the document names. "
        "If the context doesn't contain enough information to answer, say so clearly. "
        "Be concise and accurate."
    ),
    user_template="""Answer the following question based ONLY on the provided context.

Context:
{context}

Question: {question}

Provide a clear, accurate answer with source citations.""",
    description="Answer a single question using retrieved context",
)


RAG_SUMMARISE_TEMPLATE = PromptTemplate(
    name="rag_summarise",
    system_prompt=(
        "You are a helpful assistant that summarises information from multiple sources. "
        "Synthesise the key points and cite all sources used. "
        "Be comprehensive yet concise."
    ),
    user_template="""Summarise the following content about: {question}

Content from multiple sources:
{context}

Provide a comprehensive summary with source citations.""",
    description="Summarise multiple sources on a topic",
)


RAG_COMPARE_TEMPLATE = PromptTemplate(
    name="rag_compare",
    system_prompt=(
        "You are a helpful assistant that compares and contrasts information from different sources. "
        "Highlight similarities, differences, and any contradictions. "
        "Cite specific sources for each point."
    ),
    user_template="""Compare the following information: {question}

Sources:
{context}

Analyse similarities, differences, and any contradictions. Cite sources for each point.""",
    description="Compare information across sources",
)


RAG_CHAT_TEMPLATE = PromptTemplate(
    name="rag_chat",
    system_prompt=(
        "You are a helpful assistant having a conversation about the user's documents. "
        "Use the provided context to answer questions accurately. "
        "If you need clarification or the context is insufficient, ask or say so. "
        "Maintain conversation continuity and cite sources."
    ),
    user_template="""Previous conversation:
{history}

Retrieved context:
{context}

User: {question}

Respond helpfully, citing sources when using information from the context.""",
    description="Multi-turn chat with context",
)


RAG_REFINE_TEMPLATE = PromptTemplate(
    name="rag_refine",
    system_prompt=(
        "You are improving a previous answer with additional context. "
        "Enhance the answer while maintaining accuracy and citations."
    ),
    user_template="""Previous answer:
{previous_answer}

Additional context:
{context}

Question: {question}

Provide an improved answer incorporating the additional context.""",
    description="Refine a previous answer with more context",
)


# Template registry
_TEMPLATES: dict[str, PromptTemplate] = {
    "answer": RAG_ANSWER_TEMPLATE,
    "rag_answer": RAG_ANSWER_TEMPLATE,
    "summarise": RAG_SUMMARISE_TEMPLATE,
    "rag_summarise": RAG_SUMMARISE_TEMPLATE,
    "compare": RAG_COMPARE_TEMPLATE,
    "rag_compare": RAG_COMPARE_TEMPLATE,
    "chat": RAG_CHAT_TEMPLATE,
    "rag_chat": RAG_CHAT_TEMPLATE,
    "refine": RAG_REFINE_TEMPLATE,
    "rag_refine": RAG_REFINE_TEMPLATE,
}


def get_prompt_template(name: str) -> PromptTemplate:
    """Get a prompt template by name.

    Args:
        name: Template name (e.g., 'answer', 'summarise', 'chat')

    Returns:
        PromptTemplate instance

    Raises:
        KeyError: If template not found
    """
    if name not in _TEMPLATES:
        available = ", ".join(sorted(set(_TEMPLATES.keys())))
        raise KeyError(f"Unknown template '{name}'. Available: {available}")
    return _TEMPLATES[name]


def register_template(template: PromptTemplate) -> None:
    """Register a custom prompt template.

    Args:
        template: Template to register
    """
    _TEMPLATES[template.name] = template


def list_templates() -> list[str]:
    """List available template names.

    Returns:
        List of unique template names
    """
    return sorted(set(_TEMPLATES.keys()))
