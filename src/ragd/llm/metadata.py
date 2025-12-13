"""LLM-enhanced metadata extraction for ragd documents.

Provides document summarisation and classification using local LLMs via Ollama.
This is an optional enhancement that requires Ollama to be running.

v1.0.5: Configuration exposure - prompts and parameters now configurable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ragd.llm.ollama import OllamaClient, OllamaError
from ragd.prompts import get_prompt
from ragd.prompts.defaults import (
    CLASSIFICATION_PROMPT as DEFAULT_CLASSIFICATION,
    SUMMARY_PROMPT as DEFAULT_SUMMARY,
)

if TYPE_CHECKING:
    from ragd.config import RagdConfig

logger = logging.getLogger(__name__)


@dataclass
class EnhancedMetadata:
    """Metadata extracted using LLM enhancement."""

    summary: str = ""
    classification: str = ""
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": self.summary,
            "classification": self.classification,
            "success": self.success,
            "error": self.error,
        }


class LLMMetadataEnhancer:
    """Enhances document metadata using LLM inference.

    Provides optional AI-powered metadata extraction including:
    - Document summarisation (2-3 sentence summary)
    - Document type classification

    Requires Ollama to be running locally. If Ollama is unavailable,
    operations gracefully return empty results.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        summary_model: str = "llama3.2:3b",
        classification_model: str = "llama3.2:3b",
        timeout_seconds: int = 60,
        summary_max_tokens: int = 150,
        summary_prompt: str = "",
        classification_prompt: str = "",
        config: RagdConfig | None = None,
    ) -> None:
        """Initialise LLM metadata enhancer.

        Args:
            base_url: Ollama API base URL
            summary_model: Model for generating summaries
            classification_model: Model for document classification
            timeout_seconds: Request timeout
            summary_max_tokens: Maximum tokens for summary
            summary_prompt: Custom summary prompt (uses default if empty)
            classification_prompt: Custom classification prompt (uses default if empty)
            config: Optional ragd config for parameters and prompts
        """
        self._base_url = base_url
        self._summary_model = summary_model
        self._classification_model = classification_model
        self._timeout = timeout_seconds
        self._config = config

        # Use config values if available, else constructor args, else defaults
        if config:
            params = config.metadata_params
            self._max_text_length = params.max_text_length
            # Use OperationParams for summary and classification
            summary_params = params.summary
            classification_params = params.classification
            self._summary_max_tokens = summary_params.max_tokens or 150
            self._classification_max_tokens = classification_params.max_tokens or 20
            self._summary_temperature = summary_params.temperature or 0.3
            self._classification_temperature = classification_params.temperature or 0.0
            self._valid_categories = set(params.classification_categories)

            # Load prompts from config
            self._summary_prompt = get_prompt(
                config.metadata_prompts.summary,
                DEFAULT_SUMMARY,
                category="metadata",
                name="summary",
            )
            self._classification_prompt = get_prompt(
                config.metadata_prompts.classification,
                DEFAULT_CLASSIFICATION,
                category="metadata",
                name="classification",
            )
        else:
            # Legacy defaults
            self._max_text_length = 8000
            self._summary_max_tokens = summary_max_tokens
            self._classification_max_tokens = 20
            self._summary_temperature = 0.3
            self._classification_temperature = 0.0
            self._valid_categories = {
                "report", "article", "documentation", "correspondence",
                "legal", "financial", "academic", "other",
            }
            self._summary_prompt = summary_prompt or DEFAULT_SUMMARY
            self._classification_prompt = classification_prompt or DEFAULT_CLASSIFICATION

        # Lazy initialise clients
        self._summary_client: OllamaClient | None = None
        self._classification_client: OllamaClient | None = None

    def _get_summary_client(self) -> OllamaClient:
        """Get or create summary client."""
        if self._summary_client is None:
            self._summary_client = OllamaClient(
                base_url=self._base_url,
                model=self._summary_model,
                timeout_seconds=self._timeout,
            )
        return self._summary_client

    def _get_classification_client(self) -> OllamaClient:
        """Get or create classification client."""
        if self._classification_client is None:
            self._classification_client = OllamaClient(
                base_url=self._base_url,
                model=self._classification_model,
                timeout_seconds=self._timeout,
            )
        return self._classification_client

    def is_available(self) -> bool:
        """Check if LLM enhancement is available.

        Returns:
            True if Ollama is running and models are available
        """
        try:
            client = self._get_summary_client()
            return client.is_available()
        except OllamaError:
            return False

    def _truncate_text(self, text: str) -> str:
        """Truncate text to maximum length for LLM processing.

        Args:
            text: Full document text

        Returns:
            Truncated text with indicator if shortened
        """
        if len(text) <= self._max_text_length:
            return text

        # Truncate and add indicator
        truncated = text[: self._max_text_length]
        # Try to break at sentence boundary
        last_period = truncated.rfind(".")
        if last_period > self._max_text_length * 0.8:
            truncated = truncated[: last_period + 1]

        return truncated + "\n\n[Document truncated for processing...]"

    def generate_summary(self, text: str) -> str:
        """Generate a summary of the document.

        Args:
            text: Document text to summarise

        Returns:
            Summary string (empty if generation fails)
        """
        if not text.strip():
            return ""

        try:
            client = self._get_summary_client()
            truncated = self._truncate_text(text)

            prompt = self._summary_prompt.format(text=truncated)

            response = client.generate(
                prompt=prompt,
                temperature=self._summary_temperature,
                max_tokens=self._summary_max_tokens,
            )

            summary = response.content.strip()
            logger.debug("Generated summary: %s...", summary[:100] if summary else "")
            return summary

        except OllamaError as e:
            logger.warning("Failed to generate summary: %s", e)
            return ""

    def classify_document(self, text: str) -> str:
        """Classify the document into a category.

        Args:
            text: Document text to classify

        Returns:
            Category string (empty if classification fails)
        """
        if not text.strip():
            return ""

        try:
            client = self._get_classification_client()
            truncated = self._truncate_text(text)

            prompt = self._classification_prompt.format(text=truncated)

            response = client.generate(
                prompt=prompt,
                temperature=self._classification_temperature,
                max_tokens=self._classification_max_tokens,
            )

            # Extract just the classification word
            classification = response.content.strip().lower()
            # Remove any explanation text
            classification = classification.split()[0] if classification else ""

            # Validate against known categories (from config or defaults)
            if classification not in self._valid_categories:
                classification = "other"

            logger.debug("Document classified as: %s", classification)
            return classification

        except OllamaError as e:
            logger.warning("Failed to classify document: %s", e)
            return ""

    def enhance(
        self,
        text: str,
        generate_summary: bool = True,
        classify: bool = True,
    ) -> EnhancedMetadata:
        """Enhance metadata for a document.

        Args:
            text: Document text
            generate_summary: Whether to generate a summary
            classify: Whether to classify the document

        Returns:
            EnhancedMetadata with results
        """
        result = EnhancedMetadata()

        if not text.strip():
            result.success = False
            result.error = "Empty document text"
            return result

        errors = []

        try:
            if generate_summary:
                result.summary = self.generate_summary(text)
                if not result.summary:
                    errors.append("Summary generation failed")

            if classify:
                result.classification = self.classify_document(text)
                if not result.classification:
                    errors.append("Classification failed")

            if errors:
                result.success = False
                result.error = "; ".join(errors)

        except Exception as e:
            logger.exception("Unexpected error during metadata enhancement")
            result.success = False
            result.error = str(e)

        return result


def create_metadata_enhancer(
    base_url: str = "http://localhost:11434",
    summary_model: str = "llama3.2:3b",
    classification_model: str = "llama3.2:3b",
    config: RagdConfig | None = None,
) -> LLMMetadataEnhancer | None:
    """Create an LLM metadata enhancer if available.

    Args:
        base_url: Ollama API base URL
        summary_model: Model for summaries
        classification_model: Model for classification
        config: Optional ragd config for parameters and prompts

    Returns:
        LLMMetadataEnhancer if Ollama is available, None otherwise
    """
    enhancer = LLMMetadataEnhancer(
        base_url=base_url,
        summary_model=summary_model,
        classification_model=classification_model,
        config=config,
    )

    if enhancer.is_available():
        return enhancer

    logger.info("LLM metadata enhancement unavailable (Ollama not running)")
    return None
