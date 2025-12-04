"""Tests for index statistics (F-109)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ragd.ui.cli.statistics import (
    IndexStatistics,
    get_index_statistics,
    format_statistics_json,
    format_statistics_plain,
)


class TestIndexStatistics:
    """Tests for IndexStatistics dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        stats = IndexStatistics()

        assert stats.total_documents == 0
        assert stats.total_chunks == 0
        assert stats.documents_by_type == {}
        assert stats.total_size_bytes == 0

    def test_total_size_mb(self) -> None:
        """Test MB conversion."""
        stats = IndexStatistics(total_size_bytes=10 * 1024 * 1024)
        assert stats.total_size_mb == 10.0

    def test_index_size_mb(self) -> None:
        """Test index size MB conversion."""
        stats = IndexStatistics(index_size_bytes=5 * 1024 * 1024)
        assert stats.index_size_mb == 5.0

    def test_average_chunks_per_doc(self) -> None:
        """Test chunks per doc calculation."""
        stats = IndexStatistics(total_documents=10, total_chunks=50)
        assert stats.average_chunks_per_doc == 5.0

    def test_average_chunks_per_doc_zero_docs(self) -> None:
        """Test chunks per doc with zero documents."""
        stats = IndexStatistics(total_documents=0, total_chunks=0)
        assert stats.average_chunks_per_doc == 0.0


class TestGetIndexStatistics:
    """Tests for get_index_statistics function."""

    def test_empty_directory(self) -> None:
        """Test with empty data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = get_index_statistics(Path(tmpdir))

            assert stats.total_documents == 0
            assert stats.total_chunks == 0

    def test_with_database(self) -> None:
        """Test with actual database."""
        import sqlite3

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            db_path = data_dir / "ragd.db"

            # Create test database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE documents (
                    id INTEGER PRIMARY KEY,
                    path TEXT,
                    indexed_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER
                )
            """)

            # Insert test data
            cursor.execute(
                "INSERT INTO documents (path, indexed_at) VALUES (?, ?)",
                ("test.pdf", "2024-01-01T00:00:00"),
            )
            cursor.execute(
                "INSERT INTO documents (path, indexed_at) VALUES (?, ?)",
                ("test.txt", "2024-01-02T00:00:00"),
            )
            cursor.execute("INSERT INTO chunks (document_id) VALUES (1)")
            cursor.execute("INSERT INTO chunks (document_id) VALUES (1)")
            cursor.execute("INSERT INTO chunks (document_id) VALUES (2)")

            conn.commit()
            conn.close()

            stats = get_index_statistics(data_dir)

            assert stats.total_documents == 2
            assert stats.total_chunks == 3
            assert stats.index_size_bytes > 0


class TestFormatStatisticsJson:
    """Tests for JSON formatting."""

    def test_format_json(self) -> None:
        """Test JSON formatting."""
        stats = IndexStatistics(
            total_documents=100,
            total_chunks=500,
            documents_by_type={"pdf": 50, "txt": 50},
            index_size_bytes=1024 * 1024,
        )

        result = format_statistics_json(stats)

        assert result["documents"]["total"] == 100
        assert result["chunks"]["total"] == 500
        assert result["documents"]["by_type"]["pdf"] == 50
        assert result["storage"]["index_size_mb"] == 1.0

    def test_json_serialisable(self) -> None:
        """Test result is JSON serialisable."""
        stats = IndexStatistics(
            total_documents=10,
            documents_by_type={"pdf": 5},
        )

        result = format_statistics_json(stats)
        json_str = json.dumps(result)

        assert "documents" in json_str


class TestFormatStatisticsPlain:
    """Tests for plain text formatting."""

    def test_format_plain(self) -> None:
        """Test plain text formatting."""
        stats = IndexStatistics(
            total_documents=100,
            total_chunks=500,
            documents_by_type={"pdf": 60, "txt": 40},
            index_size_bytes=2 * 1024 * 1024,
            last_indexed_at="2024-01-01T12:00:00",
        )

        result = format_statistics_plain(stats)

        assert "Documents: 100" in result
        assert "Chunks: 500" in result
        assert "2.00 MB" in result
        assert "PDF: 60" in result
        assert "TXT: 40" in result
        assert "2024-01-01" in result

    def test_format_plain_empty(self) -> None:
        """Test plain text with empty stats."""
        stats = IndexStatistics()

        result = format_statistics_plain(stats)

        assert "Documents: 0" in result
        assert "Chunks: 0" in result
