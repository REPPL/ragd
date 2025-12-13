"""Contextual retrieval - generates context for chunks using LLM.

Implements the contextual retrieval technique from Anthropic research:
https://www.anthropic.com/news/contextual-retrieval

v1.0.5: Configuration exposure - prompts and parameters now configurable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ragd.llm.client import LLMClient
from ragd.prompts import get_prompt
from ragd.prompts.defaults import CONTEXT_GENERATION_PROMPT as DEFAULT_CONTEXT

if TYPE_CHECKING:
    from ragd.config import RagdConfig


@dataclass
class ContextualChunk:
    """A chunk with generated context."""

    content: str  # Original chunk text
    context: str  # Generated context
    combined: str  # Context + Content (for embedding)
    index: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextGenerator:
    """Generates contextual descriptions for chunks using an LLM.

    This improves retrieval by adding document-level context to each
    chunk before embedding, addressing the "lost context" problem.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_template: str | None = None,
        max_context_length: int = 200,
        config: RagdConfig | None = None,
    ) -> None:
        """Initialise context generator.

        Args:
            llm_client: LLM client for generation
            prompt_template: Custom prompt template (uses default if None)
            max_context_length: Maximum characters for context
            config: Optional ragd config for parameters and prompts
        """
        self.llm = llm_client
        self._config = config

        # Use config values if available
        if config:
            params = config.metadata_params
            self.max_context_length = params.max_context_length
            ctx_params = params.context_generation
            self._context_temperature = ctx_params.temperature or 0.0
            self._context_max_tokens = ctx_params.max_tokens or 100

            # Load prompt from config
            self.prompt_template = get_prompt(
                config.metadata_prompts.context_generation,
                DEFAULT_CONTEXT,
                category="metadata",
                name="context_generation",
            )
        else:
            # Legacy defaults
            self.prompt_template = prompt_template or DEFAULT_CONTEXT
            self.max_context_length = max_context_length
            self._context_temperature = 0.0
            self._context_max_tokens = 100

    def generate_context(
        self,
        chunk_content: str,
        title: str = "Unknown",
        file_type: str = "document",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Generate context for a single chunk.

        Args:
            chunk_content: The chunk text
            title: Document title/filename
            file_type: Type of document
            metadata: Additional metadata

        Returns:
            Generated context string, or empty string on failure
        """
        prompt = self.prompt_template.format(
            title=title,
            file_type=file_type,
            chunk_content=chunk_content[:2000],  # Limit chunk size in prompt
        )

        try:
            response = self.llm.generate(
                prompt=prompt,
                temperature=self._context_temperature,
                max_tokens=self._context_max_tokens,
            )

            if response.success:
                context = response.content.strip()
                # Truncate if too long
                if len(context) > self.max_context_length:
                    context = context[: self.max_context_length - 3] + "..."
                return context

            return ""

        except Exception:
            # Graceful fallback - return empty context
            return ""

    def generate_contextual_chunks(
        self,
        chunks: list[tuple[int, str]],
        title: str = "Unknown",
        file_type: str = "document",
        metadata: dict[str, Any] | None = None,
    ) -> list[ContextualChunk]:
        """Generate context for multiple chunks.

        Args:
            chunks: List of (index, content) tuples
            title: Document title/filename
            file_type: Type of document
            metadata: Additional metadata

        Returns:
            List of ContextualChunk objects
        """
        results = []

        for index, content in chunks:
            context = self.generate_context(
                chunk_content=content,
                title=title,
                file_type=file_type,
                metadata=metadata,
            )

            # Combine context and content for embedding
            if context:
                combined = f"{context}\n\n{content}"
            else:
                combined = content

            results.append(
                ContextualChunk(
                    content=content,
                    context=context,
                    combined=combined,
                    index=index,
                    metadata=metadata or {},
                )
            )

        return results

    def generate_batch(
        self,
        chunks: list[tuple[int, str]],
        title: str = "Unknown",
        file_type: str = "document",
    ) -> list[ContextualChunk]:
        """Generate context for chunks in batch (if supported by LLM).

        Falls back to sequential processing if batch not supported.

        Args:
            chunks: List of (index, content) tuples
            title: Document title
            file_type: Document type

        Returns:
            List of ContextualChunk objects
        """
        # Build prompts for all chunks
        prompts = [
            self.prompt_template.format(
                title=title,
                file_type=file_type,
                chunk_content=content[:2000],
            )
            for _, content in chunks
        ]

        # Try batch generation
        try:
            responses = self.llm.generate_batch(
                prompts=prompts,
                temperature=self._context_temperature,
                max_tokens=self._context_max_tokens,
            )
        except Exception:
            # Fall back to sequential
            return self.generate_contextual_chunks(chunks, title, file_type)

        # Build contextual chunks from responses
        results = []
        for (index, content), response in zip(chunks, responses):
            context = ""
            if response.success:
                context = response.content.strip()
                if len(context) > self.max_context_length:
                    context = context[: self.max_context_length - 3] + "..."

            combined = f"{context}\n\n{content}" if context else content

            results.append(
                ContextualChunk(
                    content=content,
                    context=context,
                    combined=combined,
                    index=index,
                    metadata={},
                )
            )

        return results


def create_context_generator(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2:3b",
    prompt_template: str | None = None,
    config: RagdConfig | None = None,
) -> ContextGenerator | None:
    """Create a context generator with Ollama.

    Returns None if Ollama is not available.

    Args:
        base_url: Ollama API URL
        model: Model to use
        prompt_template: Custom prompt template
        config: Optional ragd config for parameters and prompts

    Returns:
        ContextGenerator or None if unavailable
    """
    from ragd.llm.ollama import OllamaClient, check_ollama_available

    available, _ = check_ollama_available(base_url, model)
    if not available:
        return None

    client = OllamaClient(base_url=base_url, model=model)
    return ContextGenerator(
        llm_client=client,
        prompt_template=prompt_template,
        config=config,
    )
