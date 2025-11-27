"""Integration tests for v0.3.1 changes.

Tests end-to-end workflows for:
- Schema v2.1 fields (sensitivity, embedding model tracking)
- Config extensibility (MetadataConfig)
- LLM metadata enhancement integration
- Archive format v1.1 compatibility
"""

from __future__ import annotations

import json
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.archive import (
    ARCHIVE_VERSION,
    ArchiveManifest,
    ArchiveStatistics,
    ArchivedDocument,
    EmbeddingInfo,
    ExportEngine,
    ImportEngine,
)
from ragd.config import (
    EmbeddingConfig,
    MetadataConfig,
    RagdConfig,
    load_config,
)
from ragd.metadata import (
    CURRENT_SCHEMA,
    DocumentMetadata,
    MetadataStore,
    migrate_to_current,
)
from ragd.storage import ChromaStore, DocumentRecord


class TestSchemaV21Integration:
    """Integration tests for schema v2.1 changes."""

    def test_metadata_with_v21_fields_roundtrip(self, tmp_path: Path) -> None:
        """Test that v2.1 fields survive store roundtrip."""
        db_path = tmp_path / "metadata.sqlite"
        store = MetadataStore(db_path)

        # Create metadata with all v2.1 fields
        metadata = DocumentMetadata(
            dc_title="Test Document",
            ragd_source_path="/test/doc.pdf",
            ragd_sensitivity="confidential",
            ragd_embedding_model="all-MiniLM-L6-v2",
            ragd_embedding_dimension=384,
        )

        # Store and retrieve
        store.set("doc-001", metadata)
        retrieved = store.get("doc-001")

        assert retrieved is not None
        assert retrieved.ragd_sensitivity == "confidential"
        assert retrieved.ragd_embedding_model == "all-MiniLM-L6-v2"
        assert retrieved.ragd_embedding_dimension == 384
        assert retrieved.ragd_schema_version == CURRENT_SCHEMA

    def test_v20_to_v21_migration_preserves_data(self, tmp_path: Path) -> None:
        """Test that v2.0 to v2.1 migration preserves existing data."""
        # Simulate v2.0 data
        v2_data = {
            "ragd_schema_version": "2.0",
            "dc_title": "Legacy Document",
            "dc_creator": ["Author One", "Author Two"],
            "ragd_source_path": "/legacy/doc.pdf",
            "ragd_source_hash": "abc123",
            "ragd_tags": ["important", "archived"],
            "ragd_project": "legacy-project",
        }

        # Migrate
        migrated = migrate_to_current(
            v2_data,
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimension=384,
        )

        # Verify original data preserved
        assert migrated.dc_title == "Legacy Document"
        assert migrated.dc_creator == ["Author One", "Author Two"]
        assert migrated.ragd_source_path == "/legacy/doc.pdf"
        assert migrated.ragd_tags == ["important", "archived"]
        assert migrated.ragd_project == "legacy-project"

        # Verify new fields added
        assert migrated.ragd_schema_version == "2.1"
        assert migrated.ragd_sensitivity == "public"  # default
        assert migrated.ragd_embedding_model == "all-MiniLM-L6-v2"
        assert migrated.ragd_embedding_dimension == 384

    def test_sensitivity_values(self, tmp_path: Path) -> None:
        """Test valid sensitivity values."""
        db_path = tmp_path / "metadata.sqlite"
        store = MetadataStore(db_path)

        for sensitivity in ["public", "internal", "confidential"]:
            metadata = DocumentMetadata(
                dc_title=f"Doc with {sensitivity}",
                ragd_sensitivity=sensitivity,
            )
            store.set(f"doc-{sensitivity}", metadata)
            retrieved = store.get(f"doc-{sensitivity}")
            assert retrieved is not None
            assert retrieved.ragd_sensitivity == sensitivity


class TestConfigIntegration:
    """Integration tests for configuration changes."""

    def test_metadata_config_defaults(self) -> None:
        """Test MetadataConfig default values."""
        config = MetadataConfig()
        assert config.llm_summary is False
        assert config.llm_classification is False
        assert config.summary_model == "llama3.2:3b"
        assert config.summary_max_tokens == 150
        assert config.classification_model == "llama3.2:3b"
        assert config.base_url == "http://localhost:11434"

    def test_embedding_config_has_max_context_tokens(self) -> None:
        """Test EmbeddingConfig has max_context_tokens."""
        config = EmbeddingConfig()
        assert hasattr(config, "max_context_tokens")
        assert config.max_context_tokens == 8192

    def test_ragd_config_includes_metadata_config(self) -> None:
        """Test RagdConfig includes metadata configuration."""
        config = RagdConfig()
        assert hasattr(config, "metadata")
        assert isinstance(config.metadata, MetadataConfig)

    def test_config_yaml_roundtrip(self, tmp_path: Path) -> None:
        """Test config saves and loads with new fields."""
        from ragd.config import save_config

        config_path = tmp_path / "config.yaml"

        # Create config with custom metadata settings
        config = RagdConfig()
        config.metadata.llm_summary = True
        config.metadata.summary_max_tokens = 200

        # Save and reload
        save_config(config, config_path)
        loaded = load_config(config_path)

        assert loaded.metadata.llm_summary is True
        assert loaded.metadata.summary_max_tokens == 200


class TestArchiveV11Integration:
    """Integration tests for archive format v1.1."""

    @pytest.fixture
    def chroma_store(self, tmp_path: Path) -> ChromaStore:
        """Create a temporary ChromaDB store with test data."""
        store = ChromaStore(tmp_path / "chroma")

        # Add document with v2.1 metadata fields
        record = DocumentRecord(
            document_id="doc-001",
            path="/test/doc.pdf",
            filename="doc.pdf",
            file_type="pdf",
            file_size=1024,
            chunk_count=2,
            indexed_at=datetime.now().isoformat(),
            content_hash="testhash123",
            metadata={
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimension": 384,
            },
        )

        store.add_document(
            "doc-001",
            chunks=["Chunk 1 content", "Chunk 2 content"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"page": 1}, {"page": 2}],
            document_record=record,
        )

        return store

    def test_archive_version_is_v11(self) -> None:
        """Test current archive version is 1.1."""
        assert ARCHIVE_VERSION == "1.1"

    def test_export_includes_v11_fields(
        self, chroma_store: ChromaStore, tmp_path: Path
    ) -> None:
        """Test exported archive includes v1.1 fields."""
        archive_path = tmp_path / "export.tar.gz"

        engine = ExportEngine(
            chroma_store,
            ragd_version="0.3.1",
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimensions=384,
        )

        result = engine.export(archive_path)
        assert result.success is True
        assert result.manifest.version == "1.1"

        # Extract and verify manifest
        with tarfile.open(archive_path, "r:gz") as tar:
            manifest_file = tar.extractfile("manifest.json")
            assert manifest_file is not None
            manifest_data = json.load(manifest_file)
            assert manifest_data["version"] == "1.1"

    def test_import_v10_archive_compatible(self, tmp_path: Path) -> None:
        """Test v1.0 archives can still be imported."""
        # Create v1.0 format archive
        archive_path = tmp_path / "v10_archive.tar.gz"
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        # v1.0 manifest (no v1.1 fields)
        manifest = {
            "$schema": "ragd-archive-v1",
            "version": "1.0",
            "created_at": "2024-01-15T10:30:00Z",
            "ragd_version": "0.2.0",
            "statistics": {"document_count": 1, "chunk_count": 1},
            "embeddings": {
                "included": True,
                "model": "all-MiniLM-L6-v2",
                "dimensions": 384,
                "format": "json",
            },
            "compression": "gzip",
            "filters": {},
            "checksums": {},
        }
        with open(content_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # v1.0 document (no v1.1 fields)
        docs_dir = content_dir / "documents" / "metadata"
        docs_dir.mkdir(parents=True)
        doc = {
            "id": "doc-001",
            "dc_title": "V1.0 Document",
            "dc_creator": [],
            "dc_date": None,
            "dc_subject": [],
            "ragd_source_path": "/old/doc.pdf",
            "ragd_source_hash": "oldhash",
            "ragd_tags": [],
            "ragd_ingestion_date": "2024-01-15T10:30:00Z",
            "ragd_chunk_count": 1,
            "metadata": {},
            # No ragd_sensitivity, ragd_embedding_model, ragd_embedding_dimension
        }
        with open(docs_dir / "doc-001.json", "w") as f:
            json.dump(doc, f)

        with open(content_dir / "documents" / "index.json", "w") as f:
            json.dump({"document_ids": ["doc-001"]}, f)

        # Create minimal chunks
        chunks_dir = content_dir / "chunks" / "data" / "doc-001"
        chunks_dir.mkdir(parents=True)
        chunk = {
            "id": "doc-001_chunk_0",
            "document_id": "doc-001",
            "text": "Old chunk text",
            "page_numbers": [1],
        }
        with open(chunks_dir / "doc-001_chunk_0.json", "w") as f:
            json.dump(chunk, f)

        with open(content_dir / "chunks" / "index.json", "w") as f:
            json.dump(
                {"chunks": [{"chunk_id": "doc-001_chunk_0", "document_id": "doc-001"}]},
                f,
            )

        # Create embeddings
        embeddings_dir = content_dir / "embeddings"
        embeddings_dir.mkdir()
        embeddings = [{"chunk_id": "doc-001_chunk_0", "embedding": [0.1] * 384}]
        with open(embeddings_dir / "embeddings.json", "w") as f:
            json.dump(embeddings, f)

        # Create archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in content_dir.iterdir():
                tar.add(item, arcname=item.name)

        # Import into new store
        target_store = ChromaStore(tmp_path / "target_chroma")
        engine = ImportEngine(target_store)

        result = engine.validate(archive_path)
        assert result.valid is True
        assert result.manifest.version == "1.0"

        import_result = engine.import_archive(archive_path)
        assert import_result.success is True
        assert import_result.documents_imported == 1

    def test_archived_document_v11_fields(self) -> None:
        """Test ArchivedDocument handles v1.1 fields correctly."""
        doc = ArchivedDocument(
            id="doc-001",
            dc_title="V1.1 Document",
            dc_creator=["Author"],
            dc_date="2024-01-15",
            dc_subject=["testing"],
            ragd_source_path="/new/doc.pdf",
            ragd_source_hash="newhash",
            ragd_tags=["confidential"],
            ragd_ingestion_date="2024-11-27T10:00:00Z",
            ragd_chunk_count=5,
            ragd_sensitivity="confidential",
            ragd_embedding_model="all-MiniLM-L6-v2",
            ragd_embedding_dimension=384,
        )

        # Serialise and deserialise
        data = doc.to_dict()
        restored = ArchivedDocument.from_dict(data)

        assert restored.ragd_sensitivity == "confidential"
        assert restored.ragd_embedding_model == "all-MiniLM-L6-v2"
        assert restored.ragd_embedding_dimension == 384


class TestLLMMetadataIntegration:
    """Integration tests for LLM metadata enhancement."""

    @patch("ragd.llm.metadata.OllamaClient")
    def test_enhancer_with_config(self, mock_client_class: MagicMock) -> None:
        """Test LLM enhancer respects config settings."""
        from ragd.llm.metadata import LLMMetadataEnhancer

        # Create enhancer with custom config values
        config = MetadataConfig(
            summary_model="mistral:7b",
            classification_model="llama2:13b",
            summary_max_tokens=200,
            base_url="http://custom:11434",
        )

        enhancer = LLMMetadataEnhancer(
            base_url=config.base_url,
            summary_model=config.summary_model,
            classification_model=config.classification_model,
            summary_max_tokens=config.summary_max_tokens,
        )

        assert enhancer._base_url == "http://custom:11434"
        assert enhancer._summary_model == "mistral:7b"
        assert enhancer._classification_model == "llama2:13b"
        assert enhancer._summary_max_tokens == 200

    @patch("ragd.llm.metadata.OllamaClient")
    def test_full_enhancement_workflow(self, mock_client_class: MagicMock) -> None:
        """Test complete metadata enhancement workflow."""
        from ragd.llm.metadata import LLMMetadataEnhancer

        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            # Summary response
            MagicMock(content="This document covers Python best practices."),
            # Classification response
            MagicMock(content="documentation"),
        ]
        mock_client_class.return_value = mock_client

        enhancer = LLMMetadataEnhancer()
        result = enhancer.enhance("Python is a programming language...")

        assert result.success is True
        assert result.summary == "This document covers Python best practices."
        assert result.classification == "documentation"
        assert result.error is None


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_metadata_lifecycle(self, tmp_path: Path) -> None:
        """Test complete metadata lifecycle: create -> store -> migrate -> export."""
        # 1. Create v2.1 metadata
        metadata = DocumentMetadata(
            dc_title="Complete Test",
            dc_creator=["Test Author"],
            ragd_source_path="/test/complete.pdf",
            ragd_sensitivity="internal",
            ragd_embedding_model="all-MiniLM-L6-v2",
            ragd_embedding_dimension=384,
            ragd_tags=["test", "integration"],
        )

        # 2. Store in database
        db_path = tmp_path / "metadata.sqlite"
        store = MetadataStore(db_path)
        store.set("doc-complete", metadata)

        # 3. Verify retrieval
        retrieved = store.get("doc-complete")
        assert retrieved is not None
        assert retrieved.ragd_schema_version == "2.1"
        assert retrieved.ragd_sensitivity == "internal"
        assert retrieved.ragd_embedding_model == "all-MiniLM-L6-v2"

        # 4. Convert to archive format
        archived = ArchivedDocument(
            id="doc-complete",
            dc_title=retrieved.dc_title,
            dc_creator=retrieved.dc_creator,
            dc_date=None,
            dc_subject=retrieved.dc_subject,
            ragd_source_path=retrieved.ragd_source_path,
            ragd_source_hash=retrieved.ragd_source_hash,
            ragd_tags=retrieved.ragd_tags,
            ragd_ingestion_date=datetime.now().isoformat(),
            ragd_chunk_count=1,
            ragd_sensitivity=retrieved.ragd_sensitivity,
            ragd_embedding_model=retrieved.ragd_embedding_model,
            ragd_embedding_dimension=retrieved.ragd_embedding_dimension,
        )

        # 5. Verify archive format preserves v1.1 fields
        data = archived.to_dict()
        restored = ArchivedDocument.from_dict(data)

        assert restored.ragd_sensitivity == "internal"
        assert restored.ragd_embedding_model == "all-MiniLM-L6-v2"
        assert restored.ragd_embedding_dimension == 384
