"""Base LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM."""

    content: str
    model: str
    tokens_used: int | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return bool(self.content)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 for deterministic)
            max_tokens: Maximum tokens in response

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available.

        Returns:
            True if service is reachable and model is available
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of model names
        """
        pass

    def generate_batch(
        self,
        prompts: list[str],
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> list[LLMResponse]:
        """Generate responses for multiple prompts.

        Default implementation is sequential. Override for parallel processing.

        Args:
            prompts: List of prompts
            system_prompt: Optional system prompt (same for all)
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response

        Returns:
            List of LLMResponse objects
        """
        return [
            self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            for prompt in prompts
        ]
