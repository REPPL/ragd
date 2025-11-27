"""Tests for archive export/import module."""

from __future__ import annotations

import json
import tarfile
from datetime import datetime
from pathlib import Path

import pytest

from ragd.archive import (
    ARCHIVE_VERSION,
    COMPATIBLE_VERSIONS,
    ArchiveFilters,
    ArchiveManifest,
    ArchiveStatistics,
    ArchiveValidationError,
    ArchivedChunk,
    ArchivedDocument,
    ChecksumMismatchError,
    ConflictInfo,
    ConflictResolution,
    EmbeddingInfo,
    ExportEngine,
    ExportOptions,
    ExportResult,
    ImportEngine,
    ImportOptions,
    ImportResult,
    IncompatibleVersionError,
    ValidationResult,
    is_version_compatible,
)
from ragd.storage import ChromaStore, DocumentRecord


class TestArchiveFormat:
    """Tests for archive format dataclasses."""

    def test_archive_version_constant(self) -> None:
        """Test archive version is defined."""
        assert ARCHIVE_VERSION == "1.0"
        assert "1.0" in COMPATIBLE_VERSIONS

    def test_is_version_compatible(self) -> None:
        """Test version compatibility checking."""
        assert is_version_compatible("1.0") is True
        assert is_version_compatible("2.0") is False
        assert is_version_compatible("0.9") is False

    def test_embedding_info(self) -> None:
        """Test EmbeddingInfo dataclass."""
        info = EmbeddingInfo(
            included=True,
            model="voyage-3",
            dimensions=1024,
        )
        assert info.included is True
        assert info.model == "voyage-3"
        assert info.dimensions == 1024
        assert info.format == "parquet"

    def test_archive_statistics(self) -> None:
        """Test ArchiveStatistics dataclass."""
        stats = ArchiveStatistics(
            document_count=10,
            chunk_count=100,
            total_size_bytes=1024000,
        )
        assert stats.document_count == 10
        assert stats.chunk_count == 100
        assert stats.total_size_bytes == 1024000

    def test_archive_filters(self) -> None:
        """Test ArchiveFilters dataclass."""
        filters = ArchiveFilters(
            tags=["work", "important"],
            project="alpha",
            date_from="2024-01-01",
            date_to="2024-12-31",
        )
        assert filters.tags == ["work", "important"]
        assert filters.project == "alpha"

    def test_archive_manifest_to_dict(self) -> None:
        """Test manifest serialisation."""
        manifest = ArchiveManifest(
            version="1.0",
            created_at="2024-01-15T10:30:00Z",
            ragd_version="0.2.0",
            statistics=ArchiveStatistics(10, 100),
            embeddings=EmbeddingInfo(True, "voyage-3", 1024),
        )
        data = manifest.to_dict()

        assert data["$schema"] == "ragd-archive-v1"
        assert data["version"] == "1.0"
        assert data["statistics"]["document_count"] == 10
        assert data["embeddings"]["model"] == "voyage-3"

    def test_archive_manifest_from_dict(self) -> None:
        """Test manifest deserialisation."""
        data = {
            "version": "1.0",
            "created_at": "2024-01-15T10:30:00Z",
            "ragd_version": "0.2.0",
            "statistics": {"document_count": 10, "chunk_count": 100},
            "embeddings": {"included": True, "model": "voyage-3", "dimensions": 1024},
        }
        manifest = ArchiveManifest.from_dict(data)

        assert manifest.version == "1.0"
        assert manifest.statistics.document_count == 10
        assert manifest.embeddings.model == "voyage-3"

    def test_archived_document(self) -> None:
        """Test ArchivedDocument dataclass."""
        doc = ArchivedDocument(
            id="doc-001",
            dc_title="Test Document",
            dc_creator=["Author"],
            dc_date="2024-01-15",
            dc_subject=["testing"],
            ragd_source_path="/path/to/doc.pdf",
            ragd_source_hash="abc123",
            ragd_tags=["test"],
            ragd_ingestion_date="2024-01-15T10:30:00Z",
            ragd_chunk_count=10,
        )

        data = doc.to_dict()
        assert data["id"] == "doc-001"
        assert data["dc_title"] == "Test Document"

        restored = ArchivedDocument.from_dict(data)
        assert restored.id == doc.id
        assert restored.dc_title == doc.dc_title

    def test_archived_chunk(self) -> None:
        """Test ArchivedChunk dataclass."""
        chunk = ArchivedChunk(
            id="chunk-001",
            document_id="doc-001",
            text="Sample text content",
            page_numbers=[1, 2],
            section="Introduction",
        )

        data = chunk.to_dict()
        assert data["id"] == "chunk-001"
        assert data["text"] == "Sample text content"

        restored = ArchivedChunk.from_dict(data)
        assert restored.id == chunk.id
        assert restored.text == chunk.text


class TestArchiveExceptions:
    """Tests for archive exceptions."""

    def test_incompatible_version_error(self) -> None:
        """Test IncompatibleVersionError."""
        error = IncompatibleVersionError("2.0")
        assert error.archive_version == "2.0"
        assert "2.0" in str(error)
        assert "not supported" in str(error)

    def test_checksum_mismatch_error(self) -> None:
        """Test ChecksumMismatchError."""
        error = ChecksumMismatchError(
            "test.json",
            "sha256:expected123",
            "sha256:actual456",
        )
        assert error.filename == "test.json"
        assert "mismatch" in str(error).lower()


class TestExportOptions:
    """Tests for ExportOptions."""

    def test_defaults(self) -> None:
        """Test default export options."""
        options = ExportOptions()
        assert options.include_embeddings is True
        assert options.compression == "gzip"
        assert options.tags == []
        assert options.project is None

    def test_custom_options(self) -> None:
        """Test custom export options."""
        options = ExportOptions(
            include_embeddings=False,
            tags=["work"],
            project="alpha",
            since=datetime(2024, 1, 1),
        )
        assert options.include_embeddings is False
        assert options.tags == ["work"]
        assert options.project == "alpha"


class TestImportOptions:
    """Tests for ImportOptions."""

    def test_defaults(self) -> None:
        """Test default import options."""
        options = ImportOptions()
        assert options.conflict_resolution == ConflictResolution.SKIP
        assert options.regenerate_embeddings is False
        assert options.dry_run is False
        assert options.verify_checksums is True

    def test_custom_options(self) -> None:
        """Test custom import options."""
        options = ImportOptions(
            conflict_resolution=ConflictResolution.REPLACE,
            regenerate_embeddings=True,
            dry_run=True,
        )
        assert options.conflict_resolution == ConflictResolution.REPLACE
        assert options.regenerate_embeddings is True
        assert options.dry_run is True


class TestConflictResolution:
    """Tests for ConflictResolution enum."""

    def test_enum_values(self) -> None:
        """Test all resolution strategies exist."""
        assert ConflictResolution.SKIP.value == "skip"
        assert ConflictResolution.REPLACE.value == "replace"
        assert ConflictResolution.MERGE.value == "merge"
        assert ConflictResolution.RENAME.value == "rename"


class TestExportEngine:
    """Tests for ExportEngine."""

    @pytest.fixture
    def chroma_store(self, tmp_path: Path) -> ChromaStore:
        """Create a temporary ChromaDB store."""
        return ChromaStore(tmp_path / "chroma")

    @pytest.fixture
    def engine(self, chroma_store: ChromaStore) -> ExportEngine:
        """Create an export engine."""
        return ExportEngine(
            chroma_store,
            ragd_version="0.2.0",
            embedding_model="test-model",
            embedding_dimensions=384,
        )

    def test_engine_init(self, engine: ExportEngine) -> None:
        """Test engine initialisation."""
        assert engine._ragd_version == "0.2.0"
        assert engine._embedding_model == "test-model"
        assert engine._embedding_dimensions == 384

    def test_export_empty_store(
        self, engine: ExportEngine, tmp_path: Path
    ) -> None:
        """Test exporting empty store."""
        output_path = tmp_path / "export.tar.gz"
        result = engine.export(output_path)

        assert result.success is True
        assert result.document_count == 0
        assert result.chunk_count == 0
        assert output_path.exists()

    def test_export_creates_archive(
        self,
        chroma_store: ChromaStore,
        engine: ExportEngine,
        tmp_path: Path,
    ) -> None:
        """Test export creates valid archive."""
        # Add a document
        record = DocumentRecord(
            document_id="doc-001",
            path="/test/doc.pdf",
            filename="doc.pdf",
            file_type="pdf",
            file_size=1024,
            chunk_count=1,
            indexed_at=datetime.utcnow().isoformat(),
            content_hash="hash123",
        )
        chroma_store.add_document(
            "doc-001",
            chunks=["Test chunk content"],
            embeddings=[[0.1] * 384],
            metadatas=[{"page": 1}],
            document_record=record,
        )

        output_path = tmp_path / "export.tar.gz"
        result = engine.export(output_path)

        assert result.success is True
        assert result.document_count == 1
        assert result.chunk_count == 1

        # Verify archive structure
        with tarfile.open(output_path, "r:gz") as tar:
            names = tar.getnames()
            assert "manifest.json" in names
            assert "documents" in names or any("documents/" in n for n in names)

    def test_export_with_options(
        self,
        engine: ExportEngine,
        tmp_path: Path,
    ) -> None:
        """Test export with custom options."""
        output_path = tmp_path / "export.tar.gz"
        options = ExportOptions(include_embeddings=False)
        result = engine.export(output_path, options=options)

        assert result.success is True
        assert result.manifest is not None
        assert result.manifest.embeddings.included is False

    def test_export_progress_callback(
        self,
        engine: ExportEngine,
        tmp_path: Path,
    ) -> None:
        """Test progress callback is called."""
        output_path = tmp_path / "export.tar.gz"
        progress_stages: list[str] = []

        def callback(progress):
            progress_stages.append(progress.stage)

        result = engine.export(output_path, progress_callback=callback)

        assert result.success is True
        assert len(progress_stages) > 0


class TestImportEngine:
    """Tests for ImportEngine."""

    @pytest.fixture
    def chroma_store(self, tmp_path: Path) -> ChromaStore:
        """Create a temporary ChromaDB store."""
        return ChromaStore(tmp_path / "chroma")

    @pytest.fixture
    def engine(self, chroma_store: ChromaStore) -> ImportEngine:
        """Create an import engine."""
        return ImportEngine(chroma_store)

    @pytest.fixture
    def sample_archive(self, tmp_path: Path) -> Path:
        """Create a sample archive for testing."""
        archive_path = tmp_path / "sample.tar.gz"
        archive_content = tmp_path / "archive_content"
        archive_content.mkdir()

        # Create manifest
        manifest = {
            "$schema": "ragd-archive-v1",
            "version": "1.0",
            "created_at": "2024-01-15T10:30:00Z",
            "ragd_version": "0.2.0",
            "statistics": {"document_count": 1, "chunk_count": 1},
            "embeddings": {
                "included": True,
                "model": "test",
                "dimensions": 384,
                "format": "json",
            },
            "compression": "gzip",
            "filters": {},
            "checksums": {},
        }
        with open(archive_content / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # Create documents directory
        docs_dir = archive_content / "documents" / "metadata"
        docs_dir.mkdir(parents=True)

        doc = {
            "id": "doc-001",
            "dc_title": "Test Doc",
            "dc_creator": [],
            "dc_date": None,
            "dc_subject": [],
            "ragd_source_path": "/test.pdf",
            "ragd_source_hash": "hash123",
            "ragd_tags": [],
            "ragd_ingestion_date": "2024-01-15T10:30:00Z",
            "ragd_chunk_count": 1,
        }
        with open(docs_dir / "doc-001.json", "w") as f:
            json.dump(doc, f)

        # Create index
        with open(archive_content / "documents" / "index.json", "w") as f:
            json.dump({"document_ids": ["doc-001"]}, f)

        # Create chunks directory
        chunks_dir = archive_content / "chunks" / "data" / "doc-001"
        chunks_dir.mkdir(parents=True)

        chunk = {
            "id": "doc-001_chunk_0",
            "document_id": "doc-001",
            "text": "Test chunk text",
            "page_numbers": [1],
        }
        with open(chunks_dir / "doc-001_chunk_0.json", "w") as f:
            json.dump(chunk, f)

        # Create chunk index
        with open(archive_content / "chunks" / "index.json", "w") as f:
            json.dump(
                {"chunks": [{"chunk_id": "doc-001_chunk_0", "document_id": "doc-001"}]},
                f,
            )

        # Create embeddings
        embeddings_dir = archive_content / "embeddings"
        embeddings_dir.mkdir()
        embeddings = [{"chunk_id": "doc-001_chunk_0", "embedding": [0.1] * 384}]
        with open(embeddings_dir / "embeddings.json", "w") as f:
            json.dump(embeddings, f)

        # Create archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in archive_content.iterdir():
                tar.add(item, arcname=item.name)

        return archive_path

    def test_engine_init(self, engine: ImportEngine) -> None:
        """Test engine initialisation."""
        assert engine._chroma is not None

    def test_validate_nonexistent_archive(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test validating non-existent archive."""
        result = engine.validate(tmp_path / "nonexistent.tar.gz")
        assert result.valid is False
        assert "not found" in result.errors[0].lower()

    def test_validate_valid_archive(
        self, engine: ImportEngine, sample_archive: Path
    ) -> None:
        """Test validating a valid archive."""
        result = engine.validate(sample_archive)
        assert result.valid is True
        assert result.manifest is not None
        assert result.manifest.version == "1.0"

    def test_validate_incompatible_version(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test validating archive with incompatible version."""
        archive_path = tmp_path / "bad_version.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        manifest = {"version": "99.0", "statistics": {}}
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        (content_dir / "documents").mkdir()
        (content_dir / "chunks").mkdir()

        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

        result = engine.validate(archive_path)
        assert result.valid is False
        assert any("version" in e.lower() for e in result.errors)

    def test_import_archive(
        self, engine: ImportEngine, sample_archive: Path
    ) -> None:
        """Test importing a valid archive."""
        result = engine.import_archive(sample_archive)

        assert result.success is True
        assert result.documents_imported == 1
        assert result.chunks_imported == 1

    def test_import_dry_run(
        self, engine: ImportEngine, sample_archive: Path
    ) -> None:
        """Test dry run import."""
        options = ImportOptions(dry_run=True)
        result = engine.import_archive(sample_archive, options=options)

        assert result.success is True
        assert result.documents_imported == 1

        # Verify nothing was actually imported
        assert engine._chroma.get_document("doc-001") is None

    def test_import_conflict_skip(
        self,
        chroma_store: ChromaStore,
        engine: ImportEngine,
        sample_archive: Path,
    ) -> None:
        """Test import skips existing documents."""
        # Add existing document
        record = DocumentRecord(
            document_id="doc-001",
            path="/existing.pdf",
            filename="existing.pdf",
            file_type="pdf",
            file_size=1024,
            chunk_count=1,
            indexed_at=datetime.utcnow().isoformat(),
            content_hash="existing_hash",
        )
        chroma_store.add_document(
            "doc-001",
            chunks=["Existing chunk"],
            embeddings=[[0.2] * 384],
            metadatas=[{}],
            document_record=record,
        )

        options = ImportOptions(conflict_resolution=ConflictResolution.SKIP)
        result = engine.import_archive(sample_archive, options=options)

        assert result.success is True
        assert result.documents_skipped == 1
        assert result.documents_imported == 0

    def test_import_progress_callback(
        self, engine: ImportEngine, sample_archive: Path
    ) -> None:
        """Test progress callback during import."""
        progress_stages: list[str] = []

        def callback(progress):
            progress_stages.append(progress.stage)

        result = engine.import_archive(sample_archive, progress_callback=callback)

        assert result.success is True
        assert len(progress_stages) > 0


class TestExportImportRoundtrip:
    """Tests for full export/import roundtrip."""

    @pytest.fixture
    def source_store(self, tmp_path: Path) -> ChromaStore:
        """Create source ChromaDB store with data."""
        store = ChromaStore(tmp_path / "source")

        # Add documents
        for i in range(3):
            record = DocumentRecord(
                document_id=f"doc-{i:03d}",
                path=f"/test/doc{i}.pdf",
                filename=f"doc{i}.pdf",
                file_type="pdf",
                file_size=1024 * (i + 1),
                chunk_count=2,
                indexed_at=datetime.utcnow().isoformat(),
                content_hash=f"hash{i}",
            )
            store.add_document(
                f"doc-{i:03d}",
                chunks=[f"Chunk 1 of doc {i}", f"Chunk 2 of doc {i}"],
                embeddings=[[0.1 * i] * 384, [0.2 * i] * 384],
                metadatas=[{"page": 1}, {"page": 2}],
                document_record=record,
            )

        return store

    @pytest.fixture
    def target_store(self, tmp_path: Path) -> ChromaStore:
        """Create empty target ChromaDB store."""
        return ChromaStore(tmp_path / "target")

    def test_roundtrip_preserves_data(
        self,
        source_store: ChromaStore,
        target_store: ChromaStore,
        tmp_path: Path,
    ) -> None:
        """Test data survives export/import roundtrip."""
        archive_path = tmp_path / "roundtrip.tar.gz"

        # Export
        export_engine = ExportEngine(
            source_store,
            embedding_model="test",
            embedding_dimensions=384,
        )
        export_result = export_engine.export(archive_path)

        assert export_result.success is True
        assert export_result.document_count == 3
        assert export_result.chunk_count == 6

        # Import to new store
        import_engine = ImportEngine(target_store)
        import_result = import_engine.import_archive(archive_path)

        assert import_result.success is True
        assert import_result.documents_imported == 3
        assert import_result.chunks_imported == 6

        # Verify data
        stats = target_store.get_stats()
        assert stats["document_count"] == 3
        assert stats["chunk_count"] == 6

        # Verify document exists
        doc = target_store.get_document("doc-000")
        assert doc is not None
        assert doc.filename == "doc0.pdf"


class TestImportSecurityPathTraversal:
    """Security tests for path traversal prevention in archive import."""

    @pytest.fixture
    def chroma_store(self, tmp_path: Path) -> ChromaStore:
        """Create a temporary ChromaDB store."""
        return ChromaStore(tmp_path / "chroma")

    @pytest.fixture
    def engine(self, chroma_store: ChromaStore) -> ImportEngine:
        """Create an import engine."""
        return ImportEngine(chroma_store)

    def test_rejects_absolute_path(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test archive with absolute path is rejected."""
        archive_path = tmp_path / "malicious_absolute.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create minimal manifest
        manifest = {
            "version": "1.0",
            "statistics": {"document_count": 0, "chunk_count": 0},
            "embeddings": {"included": False},
        }
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        (content_dir / "documents").mkdir()
        (content_dir / "chunks").mkdir()

        # Create archive with absolute path member
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

            # Add malicious member with absolute path
            import io

            evil_content = b"malicious content"
            evil_info = tarfile.TarInfo(name="/etc/passwd")
            evil_info.size = len(evil_content)
            tar.addfile(evil_info, io.BytesIO(evil_content))

        result = engine.validate(archive_path)
        assert result.valid is False
        assert any("absolute" in e.lower() for e in result.errors)

    def test_rejects_path_traversal(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test archive with path traversal is rejected."""
        archive_path = tmp_path / "malicious_traversal.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create minimal manifest
        manifest = {
            "version": "1.0",
            "statistics": {"document_count": 0, "chunk_count": 0},
            "embeddings": {"included": False},
        }
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        (content_dir / "documents").mkdir()
        (content_dir / "chunks").mkdir()

        # Create archive with path traversal
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

            # Add malicious member with path traversal
            import io

            evil_content = b"malicious content"
            evil_info = tarfile.TarInfo(name="../../../tmp/evil.txt")
            evil_info.size = len(evil_content)
            tar.addfile(evil_info, io.BytesIO(evil_content))

        result = engine.validate(archive_path)
        assert result.valid is False
        assert any("traversal" in e.lower() for e in result.errors)

    def test_rejects_symlink_outside_target(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test archive with symlink escaping target is rejected."""
        archive_path = tmp_path / "malicious_symlink.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create minimal manifest
        manifest = {
            "version": "1.0",
            "statistics": {"document_count": 0, "chunk_count": 0},
            "embeddings": {"included": False},
        }
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        (content_dir / "documents").mkdir()
        (content_dir / "chunks").mkdir()

        # Create archive with malicious symlink
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

            # Add symlink pointing outside target
            evil_info = tarfile.TarInfo(name="evil_link")
            evil_info.type = tarfile.SYMTYPE
            evil_info.linkname = "/etc/passwd"
            tar.addfile(evil_info)

        result = engine.validate(archive_path)
        assert result.valid is False
        assert any(
            "symlink" in e.lower() or "absolute" in e.lower()
            for e in result.errors
        )

    def test_accepts_valid_archive(
        self, engine: ImportEngine, tmp_path: Path
    ) -> None:
        """Test valid archive without security issues is accepted."""
        archive_path = tmp_path / "valid.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # Create valid manifest
        manifest = {
            "version": "1.0",
            "statistics": {"document_count": 0, "chunk_count": 0},
            "embeddings": {"included": False},
        }
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        (content_dir / "documents").mkdir()
        (content_dir / "chunks").mkdir()

        # Create clean archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

        result = engine.validate(archive_path)
        assert result.valid is True
