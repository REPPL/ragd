"""RAG prompt templates for ragd.

Provides prompt templates for different RAG tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragd.config import ChatPromptsConfig


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

    def with_citation_instruction(self, instruction: str) -> "PromptTemplate":
        """Create a copy with custom citation instruction in system prompt.

        Args:
            instruction: Citation instruction to inject

        Returns:
            New PromptTemplate with modified system prompt
        """
        # Replace generic citation mentions with custom instruction
        modified_system = self.system_prompt
        # Look for existing citation text and replace
        citation_markers = [
            "cite sources",
            "Cite sources",
            "cite your sources",
            "Cite your sources",
        ]
        for marker in citation_markers:
            if marker in modified_system:
                modified_system = modified_system.replace(marker, instruction)
                break
        else:
            # No marker found, append instruction
            modified_system = f"{modified_system} {instruction}"

        return PromptTemplate(
            name=self.name,
            system_prompt=modified_system,
            user_template=self.user_template,
            description=self.description,
        )


# Default RAG prompt templates
RAG_ANSWER_TEMPLATE = PromptTemplate(
    name="rag_answer",
    system_prompt=(
        "You are a helpful assistant that answers questions based ONLY on the provided context. "
        "CRITICAL CITATION RULES:\n"
        "1. The context uses numbered markers [1], [2], etc. These identify documents in the knowledge base.\n"
        "2. Cite sources using ONLY these markers: [1] for single, [1;2] for multiple sources.\n"
        "3. NEVER mention author names or years from the source text. Write 'A review shows...' NOT "
        "'The review by Smith et al. (2021) shows...'. The [1] marker is the ONLY attribution needed.\n"
        "4. NEVER create a 'References' or 'Bibliography' section.\n"
        "5. NEVER invent or fabricate citations.\n"
        "\n"
        "OTHER RULES:\n"
        "6. ONLY use information explicitly stated in the provided context.\n"
        "7. If the context does not contain relevant information, say: "
        "'I don't have information about that in my indexed documents.'\n"
        "8. Place citations immediately after claims: 'Data sovereignty is contested [1].'\n"
        "Be concise and accurate."
    ),
    user_template="""Answer the following question based ONLY on the provided context.

IMPORTANT:
- Cite using ONLY the [1], [2], etc. markers shown below (use [1;2] for multiple)
- DO NOT mention author names or publication years - use [1] markers instead
- DO NOT create a References/Bibliography section

Context:
{context}

Question: {question}

Answer using [1] or [1;2] citations:""",
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
        "CRITICAL CITATION RULES:\n"
        "1. The context uses numbered markers [1], [2], etc. These identify documents in the knowledge base.\n"
        "2. Cite sources using ONLY these markers: [1] for single, [1;2] for multiple sources.\n"
        "3. NEVER mention author names or years from the source text. Write 'A review shows...' NOT "
        "'The review by Smith et al. (2021) shows...'. The [1] marker is the ONLY attribution needed.\n"
        "4. NEVER create a 'References' or 'Bibliography' section.\n"
        "5. NEVER invent or fabricate citations.\n"
        "\n"
        "OTHER RULES:\n"
        "6. ONLY use information from the provided context to answer questions.\n"
        "7. If the context does not contain relevant information, say: "
        "'I don't have information about that in my indexed documents.'\n"
        "8. Place citations after claims: 'The study found X [1].'\n"
        "Maintain conversation continuity where relevant."
    ),
    user_template="""Previous conversation:
{history}

Retrieved context:
{context}

User: {question}

IMPORTANT:
- Cite using ONLY [1], [2], etc. markers (use [1;2] for multiple)
- DO NOT mention author names or publication years - use [1] markers instead
- DO NOT create a References/Bibliography section
- If no relevant context, say "I don't have information about that in my indexed documents."

Answer:""",
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


def get_prompt_template(
    name: str,
    citation_instruction: str | None = None,
    config: "ChatPromptsConfig | None" = None,
) -> PromptTemplate:
    """Get a prompt template by name.

    Templates can be customised via:
    1. Config overrides (config.overrides[name].system/user)
    2. Citation instruction (config.citation_instruction or parameter)

    Args:
        name: Template name (e.g., 'answer', 'summarise', 'chat')
        citation_instruction: Optional custom citation instruction (deprecated, use config)
        config: ChatPromptsConfig with overrides and citation instruction

    Returns:
        PromptTemplate instance

    Raises:
        KeyError: If template not found
    """
    if name not in _TEMPLATES:
        available = ", ".join(sorted(set(_TEMPLATES.keys())))
        raise KeyError(f"Unknown template '{name}'. Available: {available}")

    template = _TEMPLATES[name]

    # Apply config overrides if provided
    if config:
        # Check for template-specific overrides
        if name in config.overrides:
            override = config.overrides[name]
            if override.system or override.user:
                template = PromptTemplate(
                    name=template.name,
                    system_prompt=override.system or template.system_prompt,
                    user_template=override.user or template.user_template,
                    description=template.description,
                )

        # Apply citation instruction from config
        template = template.with_citation_instruction(config.citation_instruction)

    # Legacy: Apply citation instruction parameter if no config provided
    elif citation_instruction:
        template = template.with_citation_instruction(citation_instruction)

    return template


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
