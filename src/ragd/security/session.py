"""Session management for ragd.

This module provides secure session management with:
- State machine: LOCKED → ACTIVE → IDLE → LOCKED
- Automatic lock after configurable timeout
- Failed attempt tracking and lockout
- Key lifecycle management

The session manager ensures encryption keys are only in memory
when actively needed and are cleared on timeout or explicit lock.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ragd.security.crypto import (
    CryptoConfig,
    derive_key,
    derive_key_with_verification,
    generate_salt,
)
from ragd.security.keystore import KeyStore, VerificationStore

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state machine states."""

    LOCKED = "locked"  # No keys in memory, authentication required
    ACTIVE = "active"  # Keys in memory, timer running
    IDLE = "idle"  # Keys in memory, timeout imminent (warning state)


class SessionError(Exception):
    """Base exception for session operations."""

    pass


class SessionLockError(SessionError):
    """Exception raised when session is locked."""

    pass


class AuthenticationError(SessionError):
    """Exception raised on authentication failure."""

    pass


class LockoutError(SessionError):
    """Exception raised when account is locked out."""

    def __init__(self, message: str, lockout_until: datetime) -> None:
        super().__init__(message)
        self.lockout_until = lockout_until


@dataclass
class SessionConfig:
    """Configuration for session management.

    Attributes:
        auto_lock_minutes: Minutes until auto-lock (0 = disabled).
        failed_attempts_lockout: Number of failures before lockout.
        lockout_minutes: Duration of lockout period.
        activity_resets_timer: Whether activity resets the timeout.
        idle_warning_seconds: Seconds before lock to enter IDLE state.
    """

    auto_lock_minutes: int = 5
    failed_attempts_lockout: int = 5
    lockout_minutes: int = 15
    activity_resets_timer: bool = True
    idle_warning_seconds: int = 30


@dataclass
class SessionMetadata:
    """Persistent session metadata stored on disk.

    Attributes:
        salt: Salt for key derivation.
        verification_hash: Hash for password verification.
        failed_attempts: Current failed attempt count.
        lockout_until: Time when lockout expires (if any).
        created_at: When encryption was first set up.
    """

    salt: bytes
    verification_hash: bytes
    failed_attempts: int = 0
    lockout_until: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary."""
        return {
            "salt": self.salt.hex(),
            "verification_hash": self.verification_hash.hex(),
            "failed_attempts": self.failed_attempts,
            "lockout_until": (
                self.lockout_until.isoformat() if self.lockout_until else None
            ),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetadata":
        """Create from dictionary."""
        return cls(
            salt=bytes.fromhex(data["salt"]),
            verification_hash=bytes.fromhex(data["verification_hash"]),
            failed_attempts=data.get("failed_attempts", 0),
            lockout_until=(
                datetime.fromisoformat(data["lockout_until"])
                if data.get("lockout_until")
                else None
            ),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class SessionManager:
    """Manages encrypted database session lifecycle.

    Provides authentication, key management, and automatic timeout
    functionality for ragd's encrypted database.

    Usage:
        manager = SessionManager(security_path, config)

        # First-time setup
        manager.initialise("password")

        # Subsequent sessions
        manager.unlock("password")

        # Use encryption key
        key = manager.get_key()

        # Manual lock
        manager.lock()

    Thread Safety:
        This class is thread-safe. All state modifications are protected
        by a lock, and the timeout timer runs in a background thread.
    """

    def __init__(
        self,
        security_path: Path,
        config: SessionConfig | None = None,
        crypto_config: CryptoConfig | None = None,
    ) -> None:
        """Initialise session manager.

        Args:
            security_path: Path to store security metadata.
            config: Session configuration.
            crypto_config: Cryptographic configuration.
        """
        self._security_path = security_path
        self._config = config or SessionConfig()
        self._crypto_config = crypto_config or CryptoConfig()

        self._keystore = KeyStore()
        self._metadata: SessionMetadata | None = None
        self._state = SessionState.LOCKED
        self._lock = threading.RLock()

        # Timeout management
        self._timer: threading.Timer | None = None
        self._last_activity: datetime | None = None
        self._unlock_time: datetime | None = None

        # Load existing metadata if present
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load session metadata from disk."""
        metadata_file = self._security_path / "session.json"
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    data = json.load(f)
                self._metadata = SessionMetadata.from_dict(data)
                logger.debug("Loaded session metadata from %s", metadata_file)
            except Exception as e:
                logger.warning("Failed to load session metadata: %s", e)

    def _save_metadata(self) -> None:
        """Save session metadata to disk."""
        if self._metadata is None:
            return

        self._security_path.mkdir(parents=True, exist_ok=True)
        metadata_file = self._security_path / "session.json"

        with open(metadata_file, "w") as f:
            json.dump(self._metadata.to_dict(), f, indent=2)

        logger.debug("Saved session metadata to %s", metadata_file)

    @property
    def state(self) -> SessionState:
        """Get current session state."""
        with self._lock:
            return self._state

    @property
    def is_locked(self) -> bool:
        """Check if session is locked."""
        return self.state == SessionState.LOCKED

    @property
    def is_active(self) -> bool:
        """Check if session is active (unlocked)."""
        return self.state in (SessionState.ACTIVE, SessionState.IDLE)

    @property
    def is_initialised(self) -> bool:
        """Check if encryption has been set up."""
        return self._metadata is not None

    def time_remaining(self) -> timedelta | None:
        """Get time until auto-lock.

        Returns:
            Time remaining, or None if auto-lock disabled or locked.
        """
        with self._lock:
            if self._state == SessionState.LOCKED:
                return None
            if self._config.auto_lock_minutes == 0:
                return None
            if self._last_activity is None:
                return None

            timeout = timedelta(minutes=self._config.auto_lock_minutes)
            elapsed = datetime.now(timezone.utc) - self._last_activity
            remaining = timeout - elapsed

            return max(remaining, timedelta(0))

    def initialise(self, password: str) -> None:
        """Initialise encryption with a password.

        Creates salt, derives key, and stores verification hash.
        This should only be called once during initial setup.

        Args:
            password: User-chosen password.

        Raises:
            SessionError: If already initialised.
            ValueError: If password is empty.
        """
        with self._lock:
            if self._metadata is not None:
                raise SessionError("Encryption already initialised")

            if not password:
                raise ValueError("Password cannot be empty")

            # Generate salt
            salt = generate_salt()

            # Derive key and verification hash
            key, verification = derive_key_with_verification(
                password, salt, self._crypto_config
            )

            # Store metadata
            self._metadata = SessionMetadata(
                salt=salt,
                verification_hash=verification,
            )
            self._save_metadata()

            # Store key and activate session
            self._keystore.store_key(key)
            self._activate_session()

            logger.info("Encryption initialised")

    def unlock(self, password: str) -> None:
        """Unlock the session with a password.

        Args:
            password: User password.

        Raises:
            SessionError: If not initialised.
            LockoutError: If account is locked out.
            AuthenticationError: If password is wrong.
        """
        with self._lock:
            if self._metadata is None:
                raise SessionError("Encryption not initialised")

            # Check lockout
            self._check_lockout()

            # Derive key
            key = derive_key(password, self._metadata.salt, self._crypto_config)

            # Verify
            verification_store = VerificationStore(
                self._metadata.salt, self._metadata.verification_hash
            )

            if not verification_store.verify(key):
                self._handle_failed_attempt()
                raise AuthenticationError("Incorrect password")

            # Clear failed attempts on success
            self._metadata.failed_attempts = 0
            self._metadata.lockout_until = None
            self._save_metadata()

            # Store key and activate
            self._keystore.store_key(key)
            self._activate_session()

            logger.info("Session unlocked")

    def _check_lockout(self) -> None:
        """Check if account is locked out.

        Raises:
            LockoutError: If lockout is active.
        """
        if self._metadata is None:
            return

        if self._metadata.lockout_until is not None:
            now = datetime.now(timezone.utc)
            if now < self._metadata.lockout_until:
                remaining = self._metadata.lockout_until - now
                raise LockoutError(
                    f"Account locked for {int(remaining.total_seconds() / 60)} more minutes",
                    self._metadata.lockout_until,
                )
            else:
                # Lockout expired
                self._metadata.lockout_until = None
                self._metadata.failed_attempts = 0
                self._save_metadata()

    def _handle_failed_attempt(self) -> None:
        """Handle a failed authentication attempt."""
        if self._metadata is None:
            return

        self._metadata.failed_attempts += 1

        if self._metadata.failed_attempts >= self._config.failed_attempts_lockout:
            self._metadata.lockout_until = datetime.now(timezone.utc) + timedelta(
                minutes=self._config.lockout_minutes
            )
            logger.warning(
                "Account locked for %d minutes after %d failed attempts",
                self._config.lockout_minutes,
                self._metadata.failed_attempts,
            )

        self._save_metadata()

    def _activate_session(self) -> None:
        """Activate the session and start timeout timer."""
        self._state = SessionState.ACTIVE
        self._last_activity = datetime.now(timezone.utc)
        self._unlock_time = datetime.now(timezone.utc)
        self._start_timer()

    def _start_timer(self) -> None:
        """Start the auto-lock timeout timer."""
        self._cancel_timer()

        if self._config.auto_lock_minutes == 0:
            return

        timeout_seconds = self._config.auto_lock_minutes * 60
        self._timer = threading.Timer(timeout_seconds, self._on_timeout)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self) -> None:
        """Cancel the current timer if running."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _on_timeout(self) -> None:
        """Handle timeout - lock the session."""
        with self._lock:
            if self._state != SessionState.LOCKED:
                logger.info("Session auto-locked due to timeout")
                self._do_lock()

    def lock(self) -> None:
        """Lock the session immediately.

        Clears all keys from memory.
        """
        with self._lock:
            self._do_lock()
            logger.info("Session locked")

    def _do_lock(self) -> None:
        """Internal lock implementation."""
        self._cancel_timer()
        self._keystore.clear()
        self._state = SessionState.LOCKED
        self._last_activity = None
        self._unlock_time = None

    def get_key(self) -> bytes:
        """Get the encryption key.

        Args:
            None

        Returns:
            Encryption key bytes.

        Raises:
            SessionLockError: If session is locked.
        """
        with self._lock:
            if self._state == SessionState.LOCKED:
                raise SessionLockError("Session is locked. Run 'ragd unlock' first.")

            # Reset timer on activity
            if self._config.activity_resets_timer:
                self._last_activity = datetime.now(timezone.utc)
                self._start_timer()

            return self._keystore.get_key()

    def touch(self) -> None:
        """Record activity to reset the timeout timer.

        Call this on any database operation to prevent timeout.
        """
        with self._lock:
            if self._state != SessionState.LOCKED:
                self._last_activity = datetime.now(timezone.utc)
                if self._config.activity_resets_timer:
                    self._start_timer()

    def extend(self, minutes: int | None = None) -> None:
        """Extend the session by resetting the timer.

        Args:
            minutes: Additional minutes (defaults to config value).
        """
        with self._lock:
            if self._state == SessionState.LOCKED:
                raise SessionLockError("Cannot extend locked session")

            self._last_activity = datetime.now(timezone.utc)
            self._start_timer()
            logger.info("Session extended")

    def change_password(self, old_password: str, new_password: str) -> None:
        """Change the encryption password.

        Re-encrypts the key with the new password.

        Args:
            old_password: Current password.
            new_password: New password.

        Raises:
            SessionError: If not initialised.
            AuthenticationError: If old password is wrong.
            ValueError: If new password is empty.
        """
        with self._lock:
            if self._metadata is None:
                raise SessionError("Encryption not initialised")

            if not new_password:
                raise ValueError("New password cannot be empty")

            # Verify old password
            key = derive_key(old_password, self._metadata.salt, self._crypto_config)
            verification_store = VerificationStore(
                self._metadata.salt, self._metadata.verification_hash
            )

            if not verification_store.verify(key):
                raise AuthenticationError("Incorrect current password")

            # Generate new salt and derive new key
            new_salt = generate_salt()
            new_key, new_verification = derive_key_with_verification(
                new_password, new_salt, self._crypto_config
            )

            # Update metadata
            self._metadata.salt = new_salt
            self._metadata.verification_hash = new_verification
            self._save_metadata()

            # Update in-memory key if session is active
            if self._state != SessionState.LOCKED:
                self._keystore.store_key(new_key)

            logger.info("Password changed successfully")

    def get_status(self) -> dict[str, Any]:
        """Get current session status.

        Returns:
            Dictionary with session status information.
        """
        with self._lock:
            remaining = self.time_remaining()
            return {
                "state": self._state.value,
                "is_initialised": self.is_initialised,
                "is_locked": self.is_locked,
                "time_remaining_seconds": (
                    int(remaining.total_seconds()) if remaining else None
                ),
                "unlock_time": (
                    self._unlock_time.isoformat() if self._unlock_time else None
                ),
                "failed_attempts": (
                    self._metadata.failed_attempts if self._metadata else 0
                ),
                "is_locked_out": (
                    self._metadata.lockout_until is not None
                    and datetime.now(timezone.utc) < self._metadata.lockout_until
                    if self._metadata
                    else False
                ),
            }

    def reset(self, confirm: bool = False) -> None:
        """Reset all encryption data.

        WARNING: This deletes all encryption keys and metadata.
        Any encrypted data will become permanently inaccessible.

        Args:
            confirm: Must be True to proceed.

        Raises:
            SessionError: If confirm is not True.
        """
        if not confirm:
            raise SessionError(
                "Reset requires explicit confirmation. "
                "WARNING: All encrypted data will be lost!"
            )

        with self._lock:
            self._do_lock()

            # Remove metadata file
            metadata_file = self._security_path / "session.json"
            if metadata_file.exists():
                metadata_file.unlink()

            self._metadata = None
            logger.warning("Encryption reset - all keys deleted")

    def __del__(self) -> None:
        """Cleanup on destruction."""
        self._cancel_timer()
        self._keystore.clear()
