"""Tests for F-075: Backend Migration Tool.

Tests the migration module components.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ragd.storage.migration.format import (
    MigrationManifest,
    MigratedChunk,
    MigratedDocument,
    MigrationCheckpoint,
)
from ragd.storage.migration.engine import MigrationEngine, MigrationResult


class TestMigratedChunk:
    """Test MigratedChunk dataclass."""

    def test_chunk_creation(self) -> None:
        """MigratedChunk should be created correctly."""
        chunk = MigratedChunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            metadata={"page": 1},
        )

        assert chunk.chunk_id == "chunk_001"
        assert chunk.document_id == "doc_001"
        assert chunk.content == "Test content"
        assert len(chunk.embedding) == 3
        assert chunk.metadata["page"] == 1

    def test_chunk_to_dict(self) -> None:
        """MigratedChunk should convert to dict."""
        chunk = MigratedChunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            content="Test",
            embedding=[0.1],
        )

        data = chunk.to_dict()
        assert data["chunk_id"] == "chunk_001"
        assert data["embedding"] == [0.1]

    def test_chunk_from_dict(self) -> None:
        """MigratedChunk should be created from dict."""
        data = {
            "chunk_id": "chunk_001",
            "document_id": "doc_001",
            "content": "Test",
            "embedding": [0.1, 0.2],
            "metadata": {"key": "value"},
        }

        chunk = MigratedChunk.from_dict(data)
        assert chunk.chunk_id == "chunk_001"
        assert chunk.metadata["key"] == "value"

    def test_chunk_roundtrip(self) -> None:
        """MigratedChunk should roundtrip through dict."""
        original = MigratedChunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            metadata={"page": 1},
        )

        restored = MigratedChunk.from_dict(original.to_dict())
        assert restored.chunk_id == original.chunk_id
        assert restored.embedding == original.embedding
        assert restored.metadata == original.metadata


class TestMigratedDocument:
    """Test MigratedDocument dataclass."""

    def test_document_creation(self) -> None:
        """MigratedDocument should be created correctly."""
        doc = MigratedDocument(
            document_id="doc_001",
            path="/path/to/file.pdf",
            metadata={"title": "Test"},
        )

        assert doc.document_id == "doc_001"
        assert doc.path == "/path/to/file.pdf"
        assert doc.metadata["title"] == "Test"

    def test_document_to_dict(self) -> None:
        """MigratedDocument should convert to dict."""
        doc = MigratedDocument(
            document_id="doc_001",
            path="/path/to/file.pdf",
        )

        data = doc.to_dict()
        assert data["document_id"] == "doc_001"
        assert data["path"] == "/path/to/file.pdf"

    def test_document_from_dict(self) -> None:
        """MigratedDocument should be created from dict."""
        data = {
            "document_id": "doc_001",
            "path": "/path/to/file.pdf",
            "metadata": {"author": "Test"},
        }

        doc = MigratedDocument.from_dict(data)
        assert doc.document_id == "doc_001"
        assert doc.metadata["author"] == "Test"


class TestMigrationManifest:
    """Test MigrationManifest dataclass."""

    def test_manifest_creation(self) -> None:
        """MigrationManifest should be created correctly."""
        manifest = MigrationManifest(
            source_backend="chromadb",
            target_backend="faiss",
            total_documents=10,
            total_chunks=100,
        )

        assert manifest.source_backend == "chromadb"
        assert manifest.target_backend == "faiss"
        assert manifest.total_documents == 10
        assert manifest.total_chunks == 100

    def test_manifest_defaults(self) -> None:
        """MigrationManifest should have sensible defaults."""
        manifest = MigrationManifest()

        assert manifest.version == "1.0"
        assert manifest.embedding_dimension == 384
        assert manifest.export_timestamp != ""

    def test_manifest_to_dict(self) -> None:
        """MigrationManifest should convert to dict."""
        manifest = MigrationManifest(
            source_backend="chromadb",
            target_backend="faiss",
        )

        data = manifest.to_dict()
        assert data["source_backend"] == "chromadb"
        assert data["target_backend"] == "faiss"
        assert "version" in data

    def test_manifest_from_dict(self) -> None:
        """MigrationManifest should be created from dict."""
        data = {
            "version": "1.0",
            "source_backend": "chromadb",
            "target_backend": "faiss",
            "total_documents": 5,
            "total_chunks": 50,
        }

        manifest = MigrationManifest.from_dict(data)
        assert manifest.source_backend == "chromadb"
        assert manifest.total_documents == 5

    def test_manifest_save_load(self) -> None:
        """MigrationManifest should save and load from file."""
        manifest = MigrationManifest(
            source_backend="chromadb",
            target_backend="faiss",
            total_documents=10,
            total_chunks=100,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            manifest.save(path)

            assert path.exists()

            loaded = MigrationManifest.load(path)
            assert loaded.source_backend == "chromadb"
            assert loaded.total_documents == 10


class TestMigrationCheckpoint:
    """Test MigrationCheckpoint dataclass."""

    def test_checkpoint_creation(self) -> None:
        """MigrationCheckpoint should be created correctly."""
        manifest = MigrationManifest(
            total_chunks=100,
        )
        checkpoint = MigrationCheckpoint(
            manifest=manifest,
            chunks_migrated=50,
        )

        assert checkpoint.chunks_migrated == 50
        assert checkpoint.manifest.total_chunks == 100

    def test_checkpoint_progress_percent(self) -> None:
        """MigrationCheckpoint should calculate progress percentage."""
        manifest = MigrationManifest(total_chunks=100)
        checkpoint = MigrationCheckpoint(
            manifest=manifest,
            chunks_migrated=75,
        )

        assert checkpoint.progress_percent == 75.0

    def test_checkpoint_progress_empty(self) -> None:
        """MigrationCheckpoint should handle zero chunks."""
        manifest = MigrationManifest(total_chunks=0)
        checkpoint = MigrationCheckpoint(manifest=manifest)

        assert checkpoint.progress_percent == 100.0

    def test_checkpoint_is_complete(self) -> None:
        """MigrationCheckpoint should detect completion."""
        manifest = MigrationManifest(total_chunks=100)

        incomplete = MigrationCheckpoint(
            manifest=manifest,
            chunks_migrated=50,
        )
        assert not incomplete.is_complete

        complete = MigrationCheckpoint(
            manifest=manifest,
            chunks_migrated=100,
        )
        assert complete.is_complete

    def test_checkpoint_save_load(self) -> None:
        """MigrationCheckpoint should save and load from file."""
        manifest = MigrationManifest(
            source_backend="chromadb",
            total_chunks=100,
        )
        checkpoint = MigrationCheckpoint(
            manifest=manifest,
            chunks_migrated=50,
            last_chunk_id="chunk_050",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checkpoint.json"
            checkpoint.save(path)

            assert path.exists()

            loaded = MigrationCheckpoint.load(path)
            assert loaded.chunks_migrated == 50
            assert loaded.last_chunk_id == "chunk_050"
            assert loaded.manifest.source_backend == "chromadb"


class TestMigrationResult:
    """Test MigrationResult dataclass."""

    def test_result_creation(self) -> None:
        """MigrationResult should be created correctly."""
        result = MigrationResult(
            success=True,
            source_backend="chromadb",
            target_backend="faiss",
            chunks_migrated=100,
            documents_migrated=10,
            duration_seconds=5.5,
        )

        assert result.success is True
        assert result.chunks_migrated == 100
        assert result.duration_seconds == 5.5

    def test_result_with_errors(self) -> None:
        """MigrationResult should include errors."""
        result = MigrationResult(
            success=False,
            source_backend="chromadb",
            target_backend="faiss",
            errors=["Error 1", "Error 2"],
        )

        assert result.success is False
        assert len(result.errors) == 2

    def test_result_to_dict(self) -> None:
        """MigrationResult should convert to dict."""
        result = MigrationResult(
            success=True,
            source_backend="chromadb",
            target_backend="faiss",
        )

        data = result.to_dict()
        assert data["success"] is True
        assert data["source_backend"] == "chromadb"


class TestMigrationEngine:
    """Test MigrationEngine class."""

    def test_engine_creation(self) -> None:
        """MigrationEngine should be created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))
            assert engine.data_dir == Path(tmpdir)

    def test_engine_invalid_same_backend(self) -> None:
        """MigrationEngine should reject same source and target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))

            with pytest.raises(ValueError, match="must be different"):
                engine.migrate(
                    source_backend="chromadb",
                    target_backend="chromadb",
                )

    def test_engine_invalid_backend(self) -> None:
        """MigrationEngine should reject invalid backends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))

            with pytest.raises(ValueError, match="Invalid source backend"):
                engine.migrate(
                    source_backend="invalid",
                    target_backend="faiss",
                )

            with pytest.raises(ValueError, match="Invalid target backend"):
                engine.migrate(
                    source_backend="chromadb",
                    target_backend="invalid",
                )

    def test_engine_has_checkpoint(self) -> None:
        """MigrationEngine should detect checkpoint presence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))

            assert not engine.has_checkpoint()

            # Create checkpoint
            manifest = MigrationManifest()
            checkpoint = MigrationCheckpoint(manifest=manifest)
            checkpoint.save(engine.checkpoint_path)

            assert engine.has_checkpoint()

    def test_engine_get_checkpoint_info(self) -> None:
        """MigrationEngine should return checkpoint info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))

            assert engine.get_checkpoint_info() is None

            # Create checkpoint
            manifest = MigrationManifest(source_backend="chromadb")
            checkpoint = MigrationCheckpoint(manifest=manifest, chunks_migrated=50)
            checkpoint.save(engine.checkpoint_path)

            info = engine.get_checkpoint_info()
            assert info is not None
            assert info.chunks_migrated == 50
            assert info.manifest.source_backend == "chromadb"

    def test_engine_resume_no_checkpoint(self) -> None:
        """MigrationEngine.resume should fail without checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MigrationEngine(data_dir=Path(tmpdir))

            with pytest.raises(FileNotFoundError, match="No migration checkpoint"):
                engine.resume()


class TestMigrationEngineEmptySource:
    """Test MigrationEngine with empty source."""

    def test_migrate_empty_source(self) -> None:
        """MigrationEngine should handle empty source gracefully."""
        # Check if FAISS is available
        try:
            import faiss  # noqa: F401
        except ImportError:
            pytest.skip("FAISS not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "chromadb").mkdir(parents=True)
            (data_dir / "faiss").mkdir(parents=True)

            engine = MigrationEngine(data_dir=data_dir)

            result = engine.migrate(
                source_backend="chromadb",
                target_backend="faiss",
            )

            # Empty source should succeed with 0 chunks
            assert result.success is True
            assert result.chunks_migrated == 0
