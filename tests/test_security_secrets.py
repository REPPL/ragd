"""Tests for secrets management module (F-083)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from ragd.security.secrets import (
    ENV_PREFIX,
    SecretString,
    SecretsFilter,
    get_all_secrets,
    is_secret_env_var,
    load_secret,
    mask_secrets_in_string,
)


class TestSecretString:
    """Tests for SecretString class."""

    def test_str_returns_masked(self) -> None:
        """Test that str() returns masked value."""
        secret = SecretString("sk-12345678901234567890")
        assert str(secret) == "****7890"

    def test_repr_returns_masked(self) -> None:
        """Test that repr() returns masked value."""
        secret = SecretString("sk-12345678901234567890")
        assert "****7890" in repr(secret)
        assert "SecretString" in repr(secret)

    def test_get_secret_value(self) -> None:
        """Test that get_secret_value() returns actual value."""
        original = "sk-12345678901234567890"
        secret = SecretString(original)
        assert secret.get_secret_value() == original

    def test_masked_short_value(self) -> None:
        """Test masking of short values."""
        secret = SecretString("abc")
        assert secret.masked() == "****"

    def test_masked_custom_chars(self) -> None:
        """Test masking with custom trailing char count."""
        secret = SecretString("sk-12345678901234567890")
        assert secret.masked(show_chars=6) == "****567890"

    def test_len(self) -> None:
        """Test length of secret."""
        secret = SecretString("12345")
        assert len(secret) == 5

    def test_bool_true(self) -> None:
        """Test that non-empty secrets are truthy."""
        secret = SecretString("value")
        assert bool(secret) is True

    def test_bool_false(self) -> None:
        """Test that empty secrets are falsy."""
        secret = SecretString("")
        assert bool(secret) is False

    def test_equality_with_secret(self) -> None:
        """Test equality comparison between secrets."""
        secret1 = SecretString("same")
        secret2 = SecretString("same")
        secret3 = SecretString("different")

        assert secret1 == secret2
        assert secret1 != secret3

    def test_equality_with_string(self) -> None:
        """Test equality comparison with strings."""
        secret = SecretString("value")
        assert secret == "value"
        assert secret != "other"

    def test_hash(self) -> None:
        """Test that secrets are hashable."""
        secret1 = SecretString("value")
        secret2 = SecretString("value")

        # Same value should have same hash
        assert hash(secret1) == hash(secret2)

        # Can be used in sets/dicts
        secret_set = {secret1}
        assert secret2 in secret_set


class TestLoadSecret:
    """Tests for load_secret function."""

    def test_load_from_environment(self) -> None:
        """Test loading secret from environment variable."""
        with patch.dict(os.environ, {"RAGD_TEST_API_KEY": "secret123"}):
            result = load_secret("TEST_API_KEY")
            assert result is not None
            assert result.get_secret_value() == "secret123"

    def test_missing_secret_returns_none(self) -> None:
        """Test that missing secrets return None."""
        # Ensure the env var doesn't exist
        env_name = f"{ENV_PREFIX}NONEXISTENT_KEY"
        with patch.dict(os.environ, {}, clear=False):
            if env_name in os.environ:
                del os.environ[env_name]
            result = load_secret("NONEXISTENT_KEY")
            assert result is None

    def test_default_value(self) -> None:
        """Test that default value is used when env var missing."""
        env_name = f"{ENV_PREFIX}MISSING_KEY"
        with patch.dict(os.environ, {}, clear=False):
            if env_name in os.environ:
                del os.environ[env_name]
            result = load_secret("MISSING_KEY", default="fallback")
            assert result is not None
            assert result.get_secret_value() == "fallback"


class TestMaskSecretsInString:
    """Tests for mask_secrets_in_string function."""

    def test_masks_openai_style_keys(self) -> None:
        """Test masking of OpenAI-style API keys."""
        text = "API key is sk-1234567890abcdefghijklmnop"
        result = mask_secrets_in_string(text)
        assert "sk-1234567890" not in result
        assert "****" in result

    def test_masks_generic_keys(self) -> None:
        """Test masking of generic key patterns."""
        text = "Found key-abcdef1234567890abcdef in config"
        result = mask_secrets_in_string(text)
        assert "abcdef1234567890" not in result

    def test_preserves_normal_text(self) -> None:
        """Test that normal text is preserved."""
        text = "This is normal text without secrets"
        result = mask_secrets_in_string(text)
        assert result == text

    def test_masks_multiple_secrets(self) -> None:
        """Test masking of multiple secrets in one string."""
        text = "Key1: sk-aaaaaaaaaaaaaaaaaaaaaa Key2: token-bbbbbbbbbbbbbbbbbbbb"
        result = mask_secrets_in_string(text)
        assert "aaaaaaaaaaaaaaaa" not in result
        assert "bbbbbbbbbbbbbbbb" not in result
        assert result.count("****") >= 2


class TestIsSecretEnvVar:
    """Tests for is_secret_env_var function."""

    def test_detects_key_names(self) -> None:
        """Test detection of key-related names."""
        assert is_secret_env_var("RAGD_API_KEY") is True
        assert is_secret_env_var("OPENAI_API_KEY") is True
        assert is_secret_env_var("SECRET_TOKEN") is True

    def test_detects_password_names(self) -> None:
        """Test detection of password-related names."""
        assert is_secret_env_var("DB_PASSWORD") is True
        assert is_secret_env_var("USER_PASSWORD") is True

    def test_detects_token_names(self) -> None:
        """Test detection of token-related names."""
        assert is_secret_env_var("AUTH_TOKEN") is True
        assert is_secret_env_var("ACCESS_TOKEN") is True

    def test_rejects_non_secret_names(self) -> None:
        """Test that non-secret names are rejected."""
        assert is_secret_env_var("RAGD_LOG_LEVEL") is False
        assert is_secret_env_var("HOME") is False
        assert is_secret_env_var("PATH") is False


class TestGetAllSecrets:
    """Tests for get_all_secrets function."""

    def test_returns_ragd_secrets(self) -> None:
        """Test that RAGD_ prefixed secrets are returned."""
        with patch.dict(
            os.environ,
            {
                "RAGD_API_KEY": "secret1",
                "RAGD_SECRET_TOKEN": "secret2",
                "RAGD_LOG_LEVEL": "DEBUG",  # Not a secret
                "OTHER_API_KEY": "notragd",  # Not RAGD_ prefix
            },
        ):
            secrets = get_all_secrets()

            # Should include secret-looking RAGD_ vars
            assert "API_KEY" in secrets
            assert "SECRET_TOKEN" in secrets

            # Should not include non-secret RAGD_ vars
            assert "LOG_LEVEL" not in secrets

            # Values should be SecretString
            assert isinstance(secrets["API_KEY"], SecretString)
            assert secrets["API_KEY"].get_secret_value() == "secret1"


class TestSecretsFilter:
    """Tests for SecretsFilter class."""

    def test_masks_secrets_in_log_message(self) -> None:
        """Test that secrets are masked in log messages."""
        filter = SecretsFilter()

        class MockRecord:
            msg: str = "API key: sk-1234567890abcdefghijklmnop"
            args: tuple[object, ...] | None = None

        record = MockRecord()
        result = filter.filter(record)

        assert result is True  # Always allows record through
        assert "sk-1234567890" not in record.msg
        assert "****" in record.msg

    def test_masks_secrets_in_args(self) -> None:
        """Test that secrets are masked in log args."""
        filter = SecretsFilter()

        class MockRecord:
            msg: str = "Key: %s"
            args: tuple[object, ...] = ("sk-1234567890abcdefghijklmnop",)

        record = MockRecord()
        filter.filter(record)

        assert "sk-1234567890" not in str(record.args)

    def test_preserves_non_string_args(self) -> None:
        """Test that non-string args are preserved."""
        filter = SecretsFilter()

        class MockRecord:
            msg: str = "Count: %d"
            args: tuple[object, ...] = (42,)

        record = MockRecord()
        filter.filter(record)

        assert record.args == (42,)
