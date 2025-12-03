"""Ollama LLM client implementation.

Provides local LLM inference via Ollama. Ollama must be installed
and running separately: https://ollama.ai
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from ragd.llm.client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """A chunk of streamed response."""

    content: str
    done: bool = False
    model: str | None = None
    tokens_used: int | None = None
    finish_reason: str | None = None


class OllamaError(Exception):
    """Error from Ollama service."""

    pass


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""

    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    timeout_seconds: int = 60


class OllamaClient(LLMClient):
    """Ollama LLM client for local inference.

    Requires Ollama to be installed and running:
    - Install: https://ollama.ai
    - Run: ollama serve
    - Pull model: ollama pull llama3.2:3b
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout_seconds: int = 60,
    ) -> None:
        """Initialise Ollama client.

        Args:
            base_url: Ollama API base URL
            model: Default model to use
            timeout_seconds: Request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds

        # Security: Warn if using non-localhost URL without HTTPS
        self._check_url_security(self.base_url)

    def _check_url_security(self, url: str) -> None:
        """Check URL security and warn if potentially insecure.

        Security: Non-localhost HTTP connections are vulnerable to MITM attacks.
        """
        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        is_https = parsed.scheme == "https"

        if not is_localhost and not is_https:
            logger.warning(
                "Ollama URL %s uses HTTP over network. "
                "Consider using HTTPS for security.",
                url,
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate response using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens (maps to num_predict)

        Returns:
            LLMResponse with generated content

        Raises:
            OllamaError: If request fails
        """
        url = f"{self.base_url}/api/generate"

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = self._request("POST", url, payload)
        except OllamaError:
            raise
        except Exception as e:
            raise OllamaError(f"Failed to generate: {e}") from e

        return LLMResponse(
            content=response.get("response", ""),
            model=response.get("model", self.model),
            tokens_used=response.get("eval_count"),
            finish_reason=response.get("done_reason", "stop"),
            metadata={
                "total_duration": response.get("total_duration"),
                "load_duration": response.get("load_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
            },
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> Iterator[StreamChunk]:
        """Generate streaming response using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens (maps to num_predict)

        Yields:
            StreamChunk objects with content fragments

        Raises:
            OllamaError: If request fails
        """
        url = f"{self.base_url}/api/generate"

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        headers = {"Content-Type": "application/json"}
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                for line in response:
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            chunk = StreamChunk(
                                content=data.get("response", ""),
                                done=data.get("done", False),
                                model=data.get("model"),
                                tokens_used=data.get("eval_count"),
                                finish_reason=data.get("done_reason"),
                            )
                            yield chunk
                            if chunk.done:
                                break
                        except json.JSONDecodeError:
                            continue

        except urllib.error.URLError as e:
            if "Connection refused" in str(e):
                raise OllamaError(
                    "Cannot connect to Ollama. Is it running? "
                    "Start with: ollama serve"
                ) from e
            raise OllamaError(f"Network error: {e}") from e

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            raise OllamaError(f"HTTP {e.code}: {error_body}") from e

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available.

        Returns:
            True if Ollama is reachable and has the model
        """
        try:
            models = self.list_models()
            # Check if current model (or base name) is available
            model_base = self.model.split(":")[0]
            return any(
                m == self.model or m.startswith(model_base)
                for m in models
            )
        except OllamaError:
            return False

    def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names

        Raises:
            OllamaError: If request fails
        """
        url = f"{self.base_url}/api/tags"

        try:
            response = self._request("GET", url)
        except OllamaError:
            raise
        except Exception as e:
            raise OllamaError(f"Failed to list models: {e}") from e

        models = response.get("models", [])
        return [m.get("name", "") for m in models]

    def pull_model(self, model: str | None = None) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model: Model to pull (uses default if not specified)

        Returns:
            True if successful

        Raises:
            OllamaError: If pull fails
        """
        url = f"{self.base_url}/api/pull"
        model_name = model or self.model

        payload = {
            "name": model_name,
            "stream": False,
        }

        try:
            self._request("POST", url, payload, timeout=600)
            return True
        except OllamaError:
            raise
        except Exception as e:
            raise OllamaError(f"Failed to pull model: {e}") from e

    def _request(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Ollama API.

        Args:
            method: HTTP method
            url: Full URL
            data: JSON payload
            timeout: Override timeout

        Returns:
            JSON response as dict

        Raises:
            OllamaError: If request fails
        """
        headers = {"Content-Type": "application/json"}
        req_timeout = timeout or self.timeout

        if data:
            body = json.dumps(data).encode("utf-8")
            request = urllib.request.Request(
                url, data=body, headers=headers, method=method
            )
        else:
            request = urllib.request.Request(url, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=req_timeout) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data) if response_data else {}

        except urllib.error.URLError as e:
            if "Connection refused" in str(e):
                raise OllamaError(
                    "Cannot connect to Ollama. Is it running? "
                    "Start with: ollama serve"
                ) from e
            raise OllamaError(f"Network error: {e}") from e

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            raise OllamaError(f"HTTP {e.code}: {error_body}") from e

        except json.JSONDecodeError as e:
            raise OllamaError(f"Invalid JSON response: {e}") from e


def check_ollama_available(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.2:3b",
) -> tuple[bool, str]:
    """Check if Ollama is available with the specified model.

    Args:
        base_url: Ollama API URL
        model: Model to check for

    Returns:
        Tuple of (available: bool, message: str)
    """
    client = OllamaClient(base_url=base_url, model=model)

    try:
        models = client.list_models()

        if not models:
            return False, "Ollama is running but no models installed"

        model_base = model.split(":")[0]
        if any(m == model or m.startswith(model_base) for m in models):
            return True, f"Model '{model}' is available"
        else:
            available = ", ".join(models[:5])
            return False, f"Model '{model}' not found. Available: {available}"

    except OllamaError as e:
        if "Connection refused" in str(e):
            return False, "Ollama is not running. Start with: ollama serve"
        return False, str(e)
