"""Tests for operation audit trail (F-112)."""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ragd.operations.audit import (
    AuditEntry,
    AuditLog,
    audit_operation,
    log_operation,
)


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_create_entry(self):
        """Should create an audit entry."""
        entry = AuditEntry.create(
            operation="index",
            target="/path/to/file.pdf",
            result="success",
            duration_ms=100,
            documents=5,
        )

        assert entry.operation == "index"
        assert entry.target == "/path/to/file.pdf"
        assert entry.result == "success"
        assert entry.duration_ms == 100
        assert entry.details["documents"] == 5
        assert entry.id is not None
        assert entry.timestamp is not None

    def test_entry_has_uuid(self):
        """Entry ID should be a valid UUID."""
        entry = AuditEntry.create(operation="test")
        assert len(entry.id) == 36  # UUID format
        assert "-" in entry.id

    def test_entry_has_timestamp(self):
        """Entry should have timestamp close to now."""
        before = datetime.now()
        entry = AuditEntry.create(operation="test")
        after = datetime.now()

        assert before <= entry.timestamp <= after

    def test_to_dict(self):
        """Should convert to dictionary."""
        entry = AuditEntry.create(
            operation="search",
            target="test query",
            result="success",
            duration_ms=50,
        )

        d = entry.to_dict()
        assert d["operation"] == "search"
        assert d["target"] == "test query"
        assert isinstance(d["timestamp"], str)  # ISO format

    def test_from_row(self):
        """Should create from database row."""
        row = (
            "abc-123",
            "2024-01-15T10:30:00",
            "index",
            "/path/file.pdf",
            "success",
            150,
            '{"documents": 3}',
        )

        entry = AuditEntry.from_row(row)
        assert entry.id == "abc-123"
        assert entry.operation == "index"
        assert entry.details["documents"] == 3


class TestAuditLog:
    """Tests for AuditLog class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_audit.db"
            yield db_path

    def test_create_audit_log(self, temp_db):
        """Should create audit log with tables."""
        log = AuditLog(db_path=temp_db)
        assert temp_db.exists()

    def test_add_entry(self, temp_db):
        """Should add an entry."""
        log = AuditLog(db_path=temp_db)
        entry = AuditEntry.create(
            operation="index",
            target="/test.pdf",
            result="success",
        )

        log.add(entry)
        assert log.count() == 1

    def test_list_entries(self, temp_db):
        """Should list entries."""
        log = AuditLog(db_path=temp_db)

        for i in range(5):
            entry = AuditEntry.create(
                operation="index",
                target=f"/file{i}.pdf",
                result="success",
            )
            log.add(entry)

        entries = log.list()
        assert len(entries) == 5

    def test_list_with_limit(self, temp_db):
        """Should respect limit."""
        log = AuditLog(db_path=temp_db)

        for i in range(10):
            entry = AuditEntry.create(operation="index", target=f"/file{i}.pdf")
            log.add(entry)

        entries = log.list(limit=5)
        assert len(entries) == 5

    def test_list_filter_by_operation(self, temp_db):
        """Should filter by operation type."""
        log = AuditLog(db_path=temp_db)

        log.add(AuditEntry.create(operation="index", target="/a.pdf"))
        log.add(AuditEntry.create(operation="search", target="query"))
        log.add(AuditEntry.create(operation="index", target="/b.pdf"))

        entries = log.list(operation="index")
        assert len(entries) == 2
        assert all(e.operation == "index" for e in entries)

    def test_list_filter_by_result(self, temp_db):
        """Should filter by result."""
        log = AuditLog(db_path=temp_db)

        log.add(AuditEntry.create(operation="index", result="success"))
        log.add(AuditEntry.create(operation="index", result="failed"))
        log.add(AuditEntry.create(operation="index", result="success"))

        entries = log.list(result="failed")
        assert len(entries) == 1

    def test_list_filter_by_time_range(self, temp_db):
        """Should filter by time range."""
        log = AuditLog(db_path=temp_db)

        # Add entries
        now = datetime.now()
        log.add(AuditEntry.create(operation="index"))

        entries = log.list(
            since=now - timedelta(minutes=1),
            until=now + timedelta(minutes=1),
        )
        assert len(entries) == 1

    def test_get_entry(self, temp_db):
        """Should get specific entry by ID."""
        log = AuditLog(db_path=temp_db)
        entry = AuditEntry.create(operation="index", target="/test.pdf")
        log.add(entry)

        retrieved = log.get(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id
        assert retrieved.target == "/test.pdf"

    def test_get_nonexistent(self, temp_db):
        """Should return None for nonexistent entry."""
        log = AuditLog(db_path=temp_db)
        assert log.get("nonexistent-id") is None

    def test_count(self, temp_db):
        """Should count entries."""
        log = AuditLog(db_path=temp_db)

        for i in range(7):
            log.add(AuditEntry.create(operation="index"))

        assert log.count() == 7

    def test_count_with_filters(self, temp_db):
        """Should count with filters."""
        log = AuditLog(db_path=temp_db)

        log.add(AuditEntry.create(operation="index", result="success"))
        log.add(AuditEntry.create(operation="index", result="failed"))
        log.add(AuditEntry.create(operation="search", result="success"))

        assert log.count(operation="index") == 2
        assert log.count(result="failed") == 1

    def test_clear_all(self, temp_db):
        """Should clear all entries."""
        log = AuditLog(db_path=temp_db)

        for i in range(5):
            log.add(AuditEntry.create(operation="index"))

        removed = log.clear()
        assert removed == 5
        assert log.count() == 0

    def test_clear_before_date(self, temp_db):
        """Should clear entries before date."""
        log = AuditLog(db_path=temp_db)

        # Add entry
        log.add(AuditEntry.create(operation="index"))

        # Clear entries before tomorrow (should remove the entry)
        removed = log.clear(before=datetime.now() + timedelta(days=1))
        assert removed == 1

    def test_rotate(self, temp_db):
        """Should rotate old entries."""
        log = AuditLog(db_path=temp_db)

        # Add more than max_entries
        for i in range(15):
            log.add(AuditEntry.create(operation="index"))

        # Rotate to max 10 entries
        removed = log.rotate(max_entries=10, max_age_days=365)
        assert removed == 5
        assert log.count() == 10


class TestAuditOperation:
    """Tests for audit_operation context manager."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_audit.db"
            # Reset global audit log
            import ragd.operations.audit as audit_module
            audit_module._audit_log = AuditLog(db_path=db_path)
            yield db_path
            audit_module._audit_log = None

    def test_audit_successful_operation(self, temp_db):
        """Should audit successful operation."""
        import ragd.operations.audit as audit_module

        with audit_operation("index", "/test.pdf") as ctx:
            ctx["documents"] = 5
            ctx["chunks"] = 100

        log = audit_module._audit_log
        entries = log.list()
        assert len(entries) == 1
        assert entries[0].operation == "index"
        assert entries[0].result == "success"
        assert entries[0].details["documents"] == 5

    def test_audit_failed_operation(self, temp_db):
        """Should audit failed operation."""
        import ragd.operations.audit as audit_module

        with pytest.raises(ValueError):
            with audit_operation("index", "/test.pdf") as ctx:
                raise ValueError("Test error")

        log = audit_module._audit_log
        entries = log.list()
        assert len(entries) == 1
        assert entries[0].result == "failed"
        assert "Test error" in entries[0].details.get("error", "")

    def test_audit_partial_success(self, temp_db):
        """Should detect partial success."""
        import ragd.operations.audit as audit_module

        with audit_operation("index", "/test") as ctx:
            ctx["succeeded"] = 5
            ctx["failed"] = 2

        log = audit_module._audit_log
        entries = log.list()
        assert entries[0].result == "partial"

    def test_audit_records_duration(self, temp_db):
        """Should record operation duration."""
        import ragd.operations.audit as audit_module

        with audit_operation("index", "/test.pdf") as ctx:
            time.sleep(0.05)  # 50ms

        log = audit_module._audit_log
        entries = log.list()
        assert entries[0].duration_ms >= 50


class TestLogOperation:
    """Tests for log_operation function."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_audit.db"
            import ragd.operations.audit as audit_module
            audit_module._audit_log = AuditLog(db_path=db_path)
            yield db_path
            audit_module._audit_log = None

    def test_log_operation_directly(self, temp_db):
        """Should log operation directly."""
        import ragd.operations.audit as audit_module

        entry = log_operation(
            operation="search",
            target="test query",
            result="success",
            duration_ms=25,
            results=10,
        )

        assert entry.operation == "search"
        assert entry.details["results"] == 10

        log = audit_module._audit_log
        assert log.count() == 1
