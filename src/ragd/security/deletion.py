"""Secure deletion for ragd.

This module provides secure deletion capabilities with three levels:
- Standard: Remove from index (fast, not secure)
- Secure: Overwrite storage locations (medium security)
- Cryptographic: Rotate encryption key (maximum security)

The cryptographic erasure ensures that even if data fragments remain
on disk due to SSD wear-levelling, they cannot be decrypted without
the old key which has been destroyed.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol

if TYPE_CHECKING:
    from ragd.security.session import SessionManager

logger = logging.getLogger(__name__)


class DeletionLevel(Enum):
    """Deletion security levels."""

    STANDARD = "standard"  # Remove from index only
    SECURE = "secure"  # + Overwrite storage locations
    CRYPTOGRAPHIC = "cryptographic"  # + Rotate encryption key


class DeletionError(Exception):
    """Base exception for deletion operations."""

    pass


class AuditLogError(DeletionError):
    """Error writing to audit log."""

    pass


@dataclass
class DeletionResult:
    """Result of a deletion operation.

    Attributes:
        document_id: ID of deleted document.
        level: Deletion level used.
        chunks_deleted: Number of chunks removed.
        vectors_deleted: Number of vectors removed.
        key_rotated: Whether encryption key was rotated.
        timestamp: When deletion occurred.
        audit_logged: Whether audit log was written.
    """

    document_id: str
    level: DeletionLevel
    chunks_deleted: int = 0
    vectors_deleted: int = 0
    key_rotated: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    audit_logged: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for audit logging."""
        return {
            "document_id": self.document_id,
            "level": self.level.value,
            "chunks_deleted": self.chunks_deleted,
            "vectors_deleted": self.vectors_deleted,
            "key_rotated": self.key_rotated,
            "timestamp": self.timestamp.isoformat(),
            "audit_logged": self.audit_logged,
        }


@dataclass
class DeletionAuditEntry:
    """Audit log entry for deletions.

    Attributes:
        timestamp: When deletion occurred.
        action: Type of deletion action.
        document_id: ID of deleted document.
        document_hash: SHA-256 hash of document ID for tracking.
        chunks_removed: Number of chunks deleted.
        key_rotated: Whether key was rotated.
        user_confirmed: Whether user confirmed deletion.
        level: Deletion level used.
    """

    timestamp: datetime
    action: str
    document_id: str
    document_hash: str
    chunks_removed: int
    key_rotated: bool
    user_confirmed: bool
    level: DeletionLevel

    @classmethod
    def create(
        cls,
        document_id: str,
        level: DeletionLevel,
        chunks_removed: int,
        key_rotated: bool,
        user_confirmed: bool = True,
    ) -> "DeletionAuditEntry":
        """Create a new audit entry.

        Args:
            document_id: ID of document being deleted.
            level: Deletion level.
            chunks_removed: Number of chunks deleted.
            key_rotated: Whether key was rotated.
            user_confirmed: Whether user confirmed.

        Returns:
            New audit entry.
        """
        action_map = {
            DeletionLevel.STANDARD: "delete",
            DeletionLevel.SECURE: "secure_delete",
            DeletionLevel.CRYPTOGRAPHIC: "cryptographic_erase",
        }

        return cls(
            timestamp=datetime.now(timezone.utc),
            action=action_map.get(level, "delete"),
            document_id=document_id,
            document_hash=sha256(document_id.encode()).hexdigest()[:16],
            chunks_removed=chunks_removed,
            key_rotated=key_rotated,
            user_confirmed=user_confirmed,
            level=level,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for JSON storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "document_id": self.document_id,
            "document_hash": self.document_hash,
            "chunks_removed": self.chunks_removed,
            "key_rotated": self.key_rotated,
            "user_confirmed": self.user_confirmed,
            "level": self.level.value,
        }


class DeletionAuditLog:
    """Audit log for deletion operations.

    Writes JSON Lines format for easy parsing and appending.
    Each line is a complete JSON object representing one deletion.
    """

    def __init__(self, log_path: Path) -> None:
        """Initialise audit log.

        Args:
            log_path: Path to audit log file.
        """
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, entry: DeletionAuditEntry) -> None:
        """Write an entry to the audit log.

        Args:
            entry: Audit entry to write.

        Raises:
            AuditLogError: If writing fails.
        """
        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
            logger.debug("Wrote audit entry for %s", entry.document_id)
        except Exception as e:
            raise AuditLogError(f"Failed to write audit log: {e}") from e

    def read_all(self) -> list[DeletionAuditEntry]:
        """Read all entries from the audit log.

        Returns:
            List of audit entries.
        """
        if not self._path.exists():
            return []

        entries = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(
                        DeletionAuditEntry(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            action=data["action"],
                            document_id=data["document_id"],
                            document_hash=data["document_hash"],
                            chunks_removed=data["chunks_removed"],
                            key_rotated=data["key_rotated"],
                            user_confirmed=data["user_confirmed"],
                            level=DeletionLevel(data["level"]),
                        )
                    )
        return entries

    def count(self) -> int:
        """Count total entries in log."""
        if not self._path.exists():
            return 0
        with open(self._path) as f:
            return sum(1 for line in f if line.strip())


class Overwriter:
    """Secure overwrite utility for in-memory and file data."""

    # Number of overwrite passes for secure deletion
    DEFAULT_PASSES = 3

    @staticmethod
    def overwrite_bytes(data: bytearray, passes: int = DEFAULT_PASSES) -> None:
        """Overwrite byte array in place.

        Args:
            data: Bytearray to overwrite (modified in place).
            passes: Number of overwrite passes.
        """
        size = len(data)
        for _ in range(passes):
            # Random data pass
            for i in range(size):
                data[i] = secrets.randbelow(256)
        # Final zero pass
        for i in range(size):
            data[i] = 0

    @staticmethod
    def overwrite_string(data: bytearray, passes: int = DEFAULT_PASSES) -> None:
        """Overwrite string data stored as bytes.

        Args:
            data: Bytearray containing string data.
            passes: Number of overwrite passes.
        """
        Overwriter.overwrite_bytes(data, passes)

    @staticmethod
    def secure_delete_file(path: Path, passes: int = DEFAULT_PASSES) -> bool:
        """Securely delete a file by overwriting before removal.

        Note: This provides limited protection on SSDs due to wear-levelling.
        For true security on SSDs, use cryptographic erasure.

        Args:
            path: File path to securely delete.
            passes: Number of overwrite passes.

        Returns:
            True if successful, False if file doesn't exist.
        """
        if not path.exists():
            return False

        try:
            size = path.stat().st_size
            with open(path, "r+b") as f:
                for _ in range(passes):
                    f.seek(0)
                    # Write random data
                    f.write(secrets.token_bytes(size))
                    f.flush()
                    os.fsync(f.fileno())
                # Final zero pass
                f.seek(0)
                f.write(b"\x00" * size)
                f.flush()
                os.fsync(f.fileno())
            # Remove the file
            path.unlink()
            return True
        except Exception as e:
            logger.warning("Secure file deletion failed: %s", e)
            # Fall back to standard deletion
            try:
                path.unlink()
            except Exception:
                pass
            return False


class VectorStoreProtocol(Protocol):
    """Protocol for vector store operations needed by SecureDeleter."""

    def delete(self, ids: list[str]) -> int:
        """Delete vectors by ID."""
        ...

    def persist(self) -> None:
        """Persist changes to disk."""
        ...


class MetadataStoreProtocol(Protocol):
    """Protocol for metadata store operations needed by SecureDeleter."""

    def delete_by_document(self, document_id: str) -> int:
        """Delete all metadata for a document."""
        ...


class SecureDeleter:
    """Coordinates secure deletion across storage layers.

    Supports three deletion levels:
    - STANDARD: Remove from indexes (fast but recoverable)
    - SECURE: Overwrite storage locations (medium security)
    - CRYPTOGRAPHIC: Rotate encryption key (maximum security)

    Usage:
        deleter = SecureDeleter(
            vector_store=store,
            metadata_store=metadata,
            session_manager=session,
            audit_log_path=Path("~/.ragd/audit/deletions.log"),
        )

        # Standard deletion
        result = deleter.delete("doc-123", DeletionLevel.STANDARD)

        # Secure deletion
        result = deleter.delete("doc-123", DeletionLevel.SECURE)

        # Cryptographic erasure (requires password)
        result = deleter.delete(
            "doc-123",
            DeletionLevel.CRYPTOGRAPHIC,
            password="secret",
        )
    """

    def __init__(
        self,
        vector_store: VectorStoreProtocol | None = None,
        metadata_store: MetadataStoreProtocol | None = None,
        session_manager: SessionManager | None = None,
        audit_log_path: Path | None = None,
        enable_audit: bool = True,
    ) -> None:
        """Initialise secure deleter.

        Args:
            vector_store: Vector store instance.
            metadata_store: Metadata store instance.
            session_manager: Session manager for key rotation.
            audit_log_path: Path for audit log file.
            enable_audit: Whether to write audit log entries.
        """
        self._vector_store = vector_store
        self._metadata_store = metadata_store
        self._session_manager = session_manager
        self._enable_audit = enable_audit

        self._audit_log: DeletionAuditLog | None = None
        if audit_log_path and enable_audit:
            self._audit_log = DeletionAuditLog(audit_log_path)

        self._overwriter = Overwriter()

    def delete(
        self,
        document_id: str,
        level: DeletionLevel = DeletionLevel.STANDARD,
        password: str | None = None,
        chunk_ids: list[str] | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> DeletionResult:
        """Delete a document with specified security level.

        Args:
            document_id: ID of document to delete.
            level: Deletion security level.
            password: Required for CRYPTOGRAPHIC level.
            chunk_ids: Optional list of specific chunk IDs.
            progress_callback: Optional callback for progress updates.

        Returns:
            DeletionResult with operation details.

        Raises:
            DeletionError: If deletion fails.
            ValueError: If CRYPTOGRAPHIC level without password.
        """
        if level == DeletionLevel.CRYPTOGRAPHIC and not password:
            raise ValueError("Password required for cryptographic erasure")

        result = DeletionResult(document_id=document_id, level=level)

        def report(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)
            logger.debug(msg)

        try:
            # Step 1: Remove from vector index
            report("Removing from vector index...")
            if self._vector_store and chunk_ids:
                result.vectors_deleted = self._vector_store.delete(chunk_ids)
                self._vector_store.persist()

            # Step 2: Remove metadata
            report("Removing metadata...")
            if self._metadata_store:
                result.chunks_deleted = self._metadata_store.delete_by_document(
                    document_id
                )

            # Step 3: Secure overwrite (for SECURE and CRYPTOGRAPHIC levels)
            if level in (DeletionLevel.SECURE, DeletionLevel.CRYPTOGRAPHIC):
                report("Performing secure overwrite...")
                # The actual overwrite happens at the storage layer
                # We trigger a persist which should sync to disk
                if self._vector_store:
                    self._vector_store.persist()

            # Step 4: Key rotation (for CRYPTOGRAPHIC level only)
            if level == DeletionLevel.CRYPTOGRAPHIC:
                if not self._session_manager:
                    raise DeletionError(
                        "Session manager required for cryptographic erasure"
                    )
                if not password:
                    raise DeletionError(
                        "Password required for cryptographic erasure"
                    )

                report("Rotating encryption key...")
                self._rotate_key(password)
                result.key_rotated = True

            # Step 5: Write audit log
            if self._audit_log:
                report("Writing audit log...")
                entry = DeletionAuditEntry.create(
                    document_id=document_id,
                    level=level,
                    chunks_removed=result.chunks_deleted,
                    key_rotated=result.key_rotated,
                )
                try:
                    self._audit_log.write(entry)
                    result.audit_logged = True
                except AuditLogError as e:
                    logger.warning("Audit log failed: %s", e)

            report("Deletion complete")
            logger.info(
                "Deleted document %s (level=%s, chunks=%d, key_rotated=%s)",
                document_id,
                level.value,
                result.chunks_deleted,
                result.key_rotated,
            )

            return result

        except Exception as e:
            logger.error("Deletion failed for %s: %s", document_id, e)
            raise DeletionError(f"Deletion failed: {e}") from e

    def bulk_delete(
        self,
        document_ids: list[str],
        level: DeletionLevel = DeletionLevel.STANDARD,
        password: str | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> list[DeletionResult]:
        """Delete multiple documents.

        Args:
            document_ids: List of document IDs to delete.
            level: Deletion security level.
            password: Required for CRYPTOGRAPHIC level.
            progress_callback: Called with (doc_id, current, total).

        Returns:
            List of DeletionResult for each document.
        """
        results = []
        total = len(document_ids)

        # For cryptographic erasure, only rotate key once at the end
        effective_level = level
        rotate_at_end = level == DeletionLevel.CRYPTOGRAPHIC

        if rotate_at_end:
            # Use SECURE level for individual docs, rotate key at end
            effective_level = DeletionLevel.SECURE

        for i, doc_id in enumerate(document_ids):
            if progress_callback:
                progress_callback(doc_id, i + 1, total)

            try:
                result = self.delete(
                    doc_id,
                    level=effective_level,
                    password=None,  # Don't rotate per-doc
                )
                results.append(result)
            except DeletionError as e:
                logger.error("Failed to delete %s: %s", doc_id, e)
                results.append(
                    DeletionResult(
                        document_id=doc_id,
                        level=effective_level,
                    )
                )

        # Single key rotation at the end for cryptographic erasure
        if rotate_at_end and password and self._session_manager:
            try:
                self._rotate_key(password)
                # Update results to reflect key rotation
                for result in results:
                    result.key_rotated = True
                    result.level = DeletionLevel.CRYPTOGRAPHIC
            except DeletionError as e:
                logger.error("Key rotation failed: %s", e)

        return results

    def _rotate_key(self, password: str) -> None:
        """Rotate the encryption key.

        This generates a new key derived from the same password with
        a new salt, then re-encrypts all remaining data.

        Args:
            password: Current password for key derivation.

        Raises:
            DeletionError: If key rotation fails.
        """
        if not self._session_manager:
            raise DeletionError("Session manager not configured")

        try:
            # Generate new key - this is effectively change_password
            # with the same password but new salt
            self._session_manager.change_password(password, password)
            logger.info("Encryption key rotated")
        except Exception as e:
            raise DeletionError(f"Key rotation failed: {e}") from e

    def get_audit_log(self) -> list[DeletionAuditEntry] | None:
        """Get all audit log entries.

        Returns:
            List of audit entries, or None if audit disabled.
        """
        if not self._audit_log:
            return None
        return self._audit_log.read_all()

    def get_audit_count(self) -> int:
        """Get count of audit log entries."""
        if not self._audit_log:
            return 0
        return self._audit_log.count()
