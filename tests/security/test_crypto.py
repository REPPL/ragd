"""Tests for ragd.security.crypto module."""

import pytest

from ragd.security.crypto import (
    CryptoConfig,
    derive_key,
    derive_key_with_verification,
    generate_salt,
    verify_key,
)


class TestGenerateSalt:
    """Tests for generate_salt function."""

    def test_default_length(self) -> None:
        """Salt has default length of 16 bytes."""
        salt = generate_salt()
        assert len(salt) == 16

    def test_custom_length(self) -> None:
        """Salt can have custom length."""
        salt = generate_salt(32)
        assert len(salt) == 32

    def test_uniqueness(self) -> None:
        """Each salt generation produces unique value."""
        salts = [generate_salt() for _ in range(100)]
        assert len(set(salts)) == 100

    def test_is_bytes(self) -> None:
        """Salt is returned as bytes."""
        salt = generate_salt()
        assert isinstance(salt, bytes)


class TestCryptoConfig:
    """Tests for CryptoConfig dataclass."""

    def test_default_values(self) -> None:
        """Config has expected default values."""
        config = CryptoConfig()
        assert config.memory_kb == 65536  # 64 MB
        assert config.iterations == 3
        assert config.parallelism == 4
        assert config.key_length == 32

    def test_custom_values(self) -> None:
        """Config accepts custom values."""
        config = CryptoConfig(
            memory_kb=32768,
            iterations=5,
            parallelism=2,
            key_length=64,
        )
        assert config.memory_kb == 32768
        assert config.iterations == 5
        assert config.parallelism == 2
        assert config.key_length == 64

    def test_validate_memory_minimum(self) -> None:
        """Validation rejects memory below minimum."""
        config = CryptoConfig(memory_kb=1024)
        with pytest.raises(ValueError, match="at least 8192 KB"):
            config.validate()

    def test_validate_iterations_minimum(self) -> None:
        """Validation rejects zero iterations."""
        config = CryptoConfig(iterations=0)
        with pytest.raises(ValueError, match="at least 1"):
            config.validate()

    def test_validate_parallelism_minimum(self) -> None:
        """Validation rejects zero parallelism."""
        config = CryptoConfig(parallelism=0)
        with pytest.raises(ValueError, match="at least 1"):
            config.validate()

    def test_validate_key_length_minimum(self) -> None:
        """Validation rejects short keys."""
        config = CryptoConfig(key_length=8)
        with pytest.raises(ValueError, match="at least 16 bytes"):
            config.validate()

    def test_validate_valid_config(self) -> None:
        """Validation accepts valid config."""
        config = CryptoConfig()
        config.validate()  # Should not raise


class TestDeriveKey:
    """Tests for derive_key function."""

    @pytest.fixture
    def salt(self) -> bytes:
        """Provide a consistent salt for testing."""
        return b"test_salt_16byt"  # 16 bytes

    @pytest.fixture
    def fast_config(self) -> CryptoConfig:
        """Provide fast config for testing."""
        return CryptoConfig(
            memory_kb=8192,  # 8 MB (minimum)
            iterations=1,
            parallelism=1,
            key_length=32,
        )

    def test_empty_password_rejected(self, salt: bytes) -> None:
        """Empty password raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            derive_key("", salt)

    def test_short_salt_rejected(self, fast_config: CryptoConfig) -> None:
        """Salt shorter than 8 bytes raises ValueError."""
        with pytest.raises(ValueError, match="at least 8 bytes"):
            derive_key("password", b"short", fast_config)

    def test_key_length(self, salt: bytes, fast_config: CryptoConfig) -> None:
        """Derived key has correct length."""
        key = derive_key("password", salt, fast_config)
        assert len(key) == 32

    def test_deterministic(self, salt: bytes, fast_config: CryptoConfig) -> None:
        """Same password and salt produce same key."""
        key1 = derive_key("password", salt, fast_config)
        key2 = derive_key("password", salt, fast_config)
        assert key1 == key2

    def test_different_passwords(self, salt: bytes, fast_config: CryptoConfig) -> None:
        """Different passwords produce different keys."""
        key1 = derive_key("password1", salt, fast_config)
        key2 = derive_key("password2", salt, fast_config)
        assert key1 != key2

    def test_different_salts(self, fast_config: CryptoConfig) -> None:
        """Different salts produce different keys."""
        key1 = derive_key("password", b"salt_one_16_byt", fast_config)
        key2 = derive_key("password", b"salt_two_16_byt", fast_config)
        assert key1 != key2

    def test_custom_key_length(self, salt: bytes) -> None:
        """Custom key length is respected."""
        config = CryptoConfig(
            memory_kb=8192,
            iterations=1,
            parallelism=1,
            key_length=64,
        )
        key = derive_key("password", salt, config)
        assert len(key) == 64


class TestVerifyKey:
    """Tests for verify_key function."""

    @pytest.fixture
    def salt(self) -> bytes:
        """Provide a consistent salt."""
        return b"test_salt_16byt"

    @pytest.fixture
    def fast_config(self) -> CryptoConfig:
        """Provide fast config for testing."""
        return CryptoConfig(
            memory_kb=8192,
            iterations=1,
            parallelism=1,
        )

    def test_correct_password_verifies(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Correct password verifies successfully."""
        key = derive_key("password", salt, fast_config)
        assert verify_key("password", salt, key, fast_config)

    def test_wrong_password_fails(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Wrong password fails verification."""
        key = derive_key("password", salt, fast_config)
        assert not verify_key("wrong_password", salt, key, fast_config)

    def test_wrong_salt_fails(self, salt: bytes, fast_config: CryptoConfig) -> None:
        """Wrong salt fails verification."""
        key = derive_key("password", salt, fast_config)
        wrong_salt = b"wrong_salt_16byt"
        assert not verify_key("password", wrong_salt, key, fast_config)

    def test_empty_password_returns_false(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Empty password returns False instead of raising."""
        key = derive_key("password", salt, fast_config)
        assert not verify_key("", salt, key, fast_config)


class TestDeriveKeyWithVerification:
    """Tests for derive_key_with_verification function."""

    @pytest.fixture
    def salt(self) -> bytes:
        """Provide a consistent salt."""
        return b"test_salt_16byt"

    @pytest.fixture
    def fast_config(self) -> CryptoConfig:
        """Provide fast config for testing."""
        return CryptoConfig(
            memory_kb=8192,
            iterations=1,
            parallelism=1,
        )

    def test_returns_tuple(self, salt: bytes, fast_config: CryptoConfig) -> None:
        """Returns tuple of key and verification hash."""
        result = derive_key_with_verification("password", salt, fast_config)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_key_is_correct_length(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Key has correct length."""
        key, _ = derive_key_with_verification("password", salt, fast_config)
        assert len(key) == 32

    def test_verification_hash_length(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Verification hash is SHA-256 (32 bytes)."""
        _, verification = derive_key_with_verification("password", salt, fast_config)
        assert len(verification) == 32

    def test_same_password_same_results(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Same password produces same key and verification."""
        result1 = derive_key_with_verification("password", salt, fast_config)
        result2 = derive_key_with_verification("password", salt, fast_config)
        assert result1 == result2

    def test_different_passwords_different_results(
        self, salt: bytes, fast_config: CryptoConfig
    ) -> None:
        """Different passwords produce different results."""
        key1, ver1 = derive_key_with_verification("password1", salt, fast_config)
        key2, ver2 = derive_key_with_verification("password2", salt, fast_config)
        assert key1 != key2
        assert ver1 != ver2
