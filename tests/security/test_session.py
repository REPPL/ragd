"""Tests for ragd.security.session module."""

import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ragd.security.session import (
    AuthenticationError,
    LockoutError,
    SessionConfig,
    SessionError,
    SessionLockError,
    SessionManager,
    SessionMetadata,
    SessionState,
)


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fast_config() -> SessionConfig:
    """Fast config for testing (short timeouts)."""
    return SessionConfig(
        auto_lock_minutes=0,  # Disabled for most tests
        failed_attempts_lockout=3,
        lockout_minutes=1,
    )


class TestSessionState:
    """Tests for SessionState enum."""

    def test_states_exist(self) -> None:
        """All expected states exist."""
        assert SessionState.LOCKED.value == "locked"
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.IDLE.value == "idle"


class TestSessionMetadata:
    """Tests for SessionMetadata dataclass."""

    def test_to_dict_and_from_dict(self) -> None:
        """Roundtrip through dict serialisation."""
        metadata = SessionMetadata(
            salt=b"test_salt_16_byt",
            verification_hash=b"test_hash_32_bytes_xxxxxxxxxx",
            failed_attempts=2,
            lockout_until=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        data = metadata.to_dict()
        restored = SessionMetadata.from_dict(data)

        assert restored.salt == metadata.salt
        assert restored.verification_hash == metadata.verification_hash
        assert restored.failed_attempts == metadata.failed_attempts
        assert restored.lockout_until == metadata.lockout_until

    def test_to_dict_with_no_lockout(self) -> None:
        """To dict handles None lockout."""
        metadata = SessionMetadata(
            salt=b"test_salt_16_byt",
            verification_hash=b"test_hash_32_bytes_xxxxxxxxxx",
        )

        data = metadata.to_dict()
        assert data["lockout_until"] is None

        restored = SessionMetadata.from_dict(data)
        assert restored.lockout_until is None


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_initial_state_locked(self, temp_dir: Path, fast_config: SessionConfig) -> None:
        """Manager starts in locked state."""
        manager = SessionManager(temp_dir, fast_config)
        assert manager.is_locked
        assert manager.state == SessionState.LOCKED
        assert not manager.is_active

    def test_not_initialised_initially(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Manager is not initialised until setup."""
        manager = SessionManager(temp_dir, fast_config)
        assert not manager.is_initialised

    def test_initialise(self, temp_dir: Path, fast_config: SessionConfig) -> None:
        """Can initialise with password."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        assert manager.is_initialised
        assert manager.is_active
        assert not manager.is_locked

    def test_initialise_twice_fails(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot initialise twice."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        with pytest.raises(SessionError, match="already initialised"):
            manager.initialise("another_password")

    def test_initialise_empty_password_fails(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot initialise with empty password."""
        manager = SessionManager(temp_dir, fast_config)

        with pytest.raises(ValueError, match="empty"):
            manager.initialise("")

    def test_get_key_when_active(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Can get key when session is active."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        key = manager.get_key()
        assert isinstance(key, bytes)
        assert len(key) == 32  # Default key length

    def test_get_key_when_locked_fails(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot get key when locked."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        with pytest.raises(SessionLockError, match="locked"):
            manager.get_key()

    def test_lock(self, temp_dir: Path, fast_config: SessionConfig) -> None:
        """Can lock session."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        assert manager.is_locked
        assert not manager.is_active

    def test_unlock(self, temp_dir: Path, fast_config: SessionConfig) -> None:
        """Can unlock with correct password."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()
        manager.unlock("test_password")

        assert manager.is_active
        assert not manager.is_locked

    def test_unlock_wrong_password(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Wrong password fails."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        with pytest.raises(AuthenticationError, match="Incorrect"):
            manager.unlock("wrong_password")

    def test_unlock_not_initialised_fails(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot unlock if not initialised."""
        manager = SessionManager(temp_dir, fast_config)

        with pytest.raises(SessionError, match="not initialised"):
            manager.unlock("any_password")


class TestFailedAttempts:
    """Tests for failed attempt tracking."""

    def test_failed_attempts_increment(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Failed attempts are tracked."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        for _ in range(2):
            with pytest.raises(AuthenticationError):
                manager.unlock("wrong_password")

        status = manager.get_status()
        assert status["failed_attempts"] == 2

    def test_lockout_after_max_attempts(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Lockout after max failed attempts."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        # Fail 3 times (config limit)
        for _ in range(3):
            with pytest.raises(AuthenticationError):
                manager.unlock("wrong_password")

        # Next attempt should be lockout
        with pytest.raises(LockoutError):
            manager.unlock("wrong_password")

    def test_successful_unlock_clears_failures(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Successful unlock clears failed attempts."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        # Fail twice
        for _ in range(2):
            with pytest.raises(AuthenticationError):
                manager.unlock("wrong_password")

        # Succeed
        manager.unlock("test_password")

        status = manager.get_status()
        assert status["failed_attempts"] == 0


class TestPasswordChange:
    """Tests for password change functionality."""

    def test_change_password(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Can change password."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("old_password")
        manager.change_password("old_password", "new_password")
        manager.lock()

        # Old password should fail
        with pytest.raises(AuthenticationError):
            manager.unlock("old_password")

        # New password should work
        manager.unlock("new_password")
        assert manager.is_active

    def test_change_password_wrong_current(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot change with wrong current password."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        with pytest.raises(AuthenticationError, match="Incorrect"):
            manager.change_password("wrong_password", "new_password")

    def test_change_password_empty_new(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Cannot change to empty password."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        with pytest.raises(ValueError, match="empty"):
            manager.change_password("test_password", "")


class TestAutoLock:
    """Tests for auto-lock functionality."""

    def test_auto_lock_timeout(self, temp_dir: Path) -> None:
        """Session auto-locks after timeout."""
        config = SessionConfig(auto_lock_minutes=0.02)  # ~1.2 seconds
        manager = SessionManager(temp_dir, config)
        manager.initialise("test_password")

        assert manager.is_active

        # Wait for timeout
        time.sleep(1.5)

        assert manager.is_locked

    def test_time_remaining(self, temp_dir: Path) -> None:
        """Time remaining is tracked."""
        config = SessionConfig(auto_lock_minutes=5)
        manager = SessionManager(temp_dir, config)
        manager.initialise("test_password")

        remaining = manager.time_remaining()
        assert remaining is not None
        assert remaining.total_seconds() > 290  # Should be close to 5 min
        assert remaining.total_seconds() <= 300

    def test_time_remaining_when_locked(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Time remaining is None when locked."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        assert manager.time_remaining() is None


class TestPersistence:
    """Tests for session persistence across instances."""

    def test_metadata_persists(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Session metadata persists to disk."""
        # Create and initialise
        manager1 = SessionManager(temp_dir, fast_config)
        manager1.initialise("test_password")
        manager1.lock()

        # Create new manager pointing to same directory
        manager2 = SessionManager(temp_dir, fast_config)

        assert manager2.is_initialised
        assert manager2.is_locked

        # Should be able to unlock
        manager2.unlock("test_password")
        assert manager2.is_active

    def test_failed_attempts_persist(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Failed attempts persist across instances."""
        manager1 = SessionManager(temp_dir, fast_config)
        manager1.initialise("test_password")
        manager1.lock()

        # Fail twice
        for _ in range(2):
            with pytest.raises(AuthenticationError):
                manager1.unlock("wrong_password")

        # New instance should see failed attempts
        manager2 = SessionManager(temp_dir, fast_config)
        status = manager2.get_status()
        assert status["failed_attempts"] == 2


class TestReset:
    """Tests for reset functionality."""

    def test_reset_requires_confirmation(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Reset requires explicit confirmation."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        with pytest.raises(SessionError, match="confirmation"):
            manager.reset()

    def test_reset_clears_everything(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Reset clears all encryption data."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.reset(confirm=True)

        assert not manager.is_initialised
        assert manager.is_locked

    def test_can_reinitialise_after_reset(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Can initialise again after reset."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("old_password")
        manager.reset(confirm=True)
        manager.initialise("new_password")

        assert manager.is_initialised
        assert manager.is_active


class TestGetStatus:
    """Tests for status reporting."""

    def test_status_when_locked(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Status reflects locked state."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")
        manager.lock()

        status = manager.get_status()
        assert status["state"] == "locked"
        assert status["is_locked"] is True
        assert status["is_initialised"] is True

    def test_status_when_active(
        self, temp_dir: Path, fast_config: SessionConfig
    ) -> None:
        """Status reflects active state."""
        manager = SessionManager(temp_dir, fast_config)
        manager.initialise("test_password")

        status = manager.get_status()
        assert status["state"] == "active"
        assert status["is_locked"] is False
        assert status["unlock_time"] is not None
