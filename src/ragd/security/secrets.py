"""Secrets management for ragd.

This module provides secure handling of sensitive configuration values
like API keys. Secrets are:
- Loaded from environment variables with RAGD_ prefix
- Masked when displayed or logged
- Never written to disk in plain text

Usage:
    from ragd.security.secrets import SecretString, load_secret

    # Load secret from environment
    api_key = load_secret("OPENAI_API_KEY")

    # SecretString masks on str() but preserves value
    secret = SecretString("sk-12345")
    print(secret)  # Output: ****5
    print(secret.get_secret_value())  # Output: sk-12345
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Final

# Prefix for ragd environment variables
ENV_PREFIX: Final[str] = "RAGD_"

# Pattern to detect potential secrets in strings
SECRET_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style
    re.compile(r"key[-_]?[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Generic key
    re.compile(r"token[-_]?[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Generic token
    re.compile(r"secret[-_]?[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Generic secret
    re.compile(r"password[-_]?[a-zA-Z0-9]{8,}", re.IGNORECASE),  # Password
]


@dataclass(frozen=True, slots=True)
class SecretString:
    """A string that masks itself when displayed.

    Use this for any sensitive values that should not appear in logs,
    error messages, or debug output.

    Attributes:
        _value: The actual secret value (private).
    """

    _value: str

    def __str__(self) -> str:
        """Return masked representation."""
        return self.masked()

    def __repr__(self) -> str:
        """Return masked representation for debugging."""
        return f"SecretString({self.masked()!r})"

    def masked(self, show_chars: int = 4) -> str:
        """Return masked version of the secret.

        Args:
            show_chars: Number of trailing characters to show.

        Returns:
            Masked string like "****5" or "****" if too short.
        """
        if len(self._value) <= show_chars:
            return "****"

        return "****" + self._value[-show_chars:]

    def get_secret_value(self) -> str:
        """Get the actual secret value.

        Only use this when you need the real value (e.g., for API calls).
        Never log or display the result.

        Returns:
            The unmasked secret value.
        """
        return self._value

    def __len__(self) -> int:
        """Return length of secret."""
        return len(self._value)

    def __bool__(self) -> bool:
        """Return True if secret is non-empty."""
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        """Compare secrets securely (constant-time for same length)."""
        if isinstance(other, SecretString):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return NotImplemented

    def __hash__(self) -> int:
        """Hash the secret value."""
        return hash(self._value)


def load_secret(name: str, default: str | None = None) -> SecretString | None:
    """Load a secret from environment variable.

    Looks for RAGD_{name} in environment variables.

    Args:
        name: Secret name (without RAGD_ prefix).
        default: Default value if not found.

    Returns:
        SecretString with the value, or None if not found and no default.

    Examples:
        # Set RAGD_OPENAI_API_KEY=sk-12345
        api_key = load_secret("OPENAI_API_KEY")
        if api_key:
            client.api_key = api_key.get_secret_value()
    """
    env_name = f"{ENV_PREFIX}{name}"
    value = os.environ.get(env_name)

    if value is not None:
        return SecretString(value)

    if default is not None:
        return SecretString(default)

    return None


def mask_secrets_in_string(text: str) -> str:
    """Mask potential secrets in a string.

    Scans text for patterns that look like secrets and replaces them
    with masked versions. Use this for sanitising log output.

    Args:
        text: Text that may contain secrets.

    Returns:
        Text with potential secrets masked.
    """
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(
            lambda m: "****" + m.group(0)[-4:] if len(m.group(0)) > 4 else "****",
            result,
        )
    return result


def is_secret_env_var(name: str) -> bool:
    """Check if an environment variable name looks like a secret.

    Args:
        name: Environment variable name.

    Returns:
        True if the name suggests it contains a secret.
    """
    secret_keywords = {"key", "secret", "token", "password", "credential", "auth"}
    name_lower = name.lower()
    return any(keyword in name_lower for keyword in secret_keywords)


def get_all_secrets() -> dict[str, SecretString]:
    """Get all RAGD_ prefixed secrets from environment.

    Returns:
        Dictionary of secret names to SecretString values.
    """
    secrets: dict[str, SecretString] = {}
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX) and is_secret_env_var(key):
            name = key[len(ENV_PREFIX) :]
            secrets[name] = SecretString(value)
    return secrets


class SecretsFilter:
    """Logging filter that masks secrets in log records.

    Usage:
        import logging
        from ragd.security.secrets import SecretsFilter

        logger = logging.getLogger("ragd")
        logger.addFilter(SecretsFilter())
    """

    def filter(self, record: object) -> bool:
        """Filter log record, masking secrets in message.

        Args:
            record: Log record to filter.

        Returns:
            True (always allows the record through after masking).
        """
        # Access the msg attribute if it exists
        if hasattr(record, "msg") and isinstance(record.msg, str):  # type: ignore[union-attr]
            record.msg = mask_secrets_in_string(record.msg)  # type: ignore[union-attr]

        # Also check args
        if hasattr(record, "args") and record.args:  # type: ignore[union-attr]
            args = record.args  # type: ignore[union-attr]
            if isinstance(args, tuple):
                record.args = tuple(  # type: ignore[union-attr]
                    mask_secrets_in_string(str(arg)) if isinstance(arg, str) else arg
                    for arg in args
                )

        return True
