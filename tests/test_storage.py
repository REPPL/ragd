"""Tests for storage module."""

import tempfile
from pathlib import Path

from ragd.storage.chromadb import (
    ChromaStore,
    DocumentRecord,
    generate_document_id,
    generate_content_hash,
)


class TestChromaStore:
    """Tests for ChromaStore."""

    def test_init(self) -> None:
        """Test store initialisation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaStore(Path(tmpdir))
            stats = store.get_stats()
            assert stats["document_count"] == 0
            assert stats["chunk_count"] == 0

    def test_add_and_search(self) -> None:
        """Test adding document and searching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaStore(Path(tmpdir))

            doc_record = DocumentRecord(
                document_id="test_doc",
                path="/test/path.txt",
                filename="path.txt",
                file_type="txt",
                file_size=100,
                chunk_count=2,
                indexed_at="2024-01-01T00:00:00",
                content_hash="abc123",
            )

            chunks = ["This is chunk one.", "This is chunk two."]
            embeddings = [[0.1] * 384, [0.2] * 384]
            metadatas = [{"chunk_index": 0}, {"chunk_index": 1}]

            store.add_document(
                document_id="test_doc",
                chunks=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                document_record=doc_record,
            )

            stats = store.get_stats()
            assert stats["document_count"] == 1
            assert stats["chunk_count"] == 2

            # Search
            query_embedding = [0.15] * 384
            results = store.search(query_embedding, limit=2)
            assert len(results) <= 2

    def test_list_documents(self) -> None:
        """Test listing documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaStore(Path(tmpdir))

            doc_record = DocumentRecord(
                document_id="test_doc",
                path="/test/path.txt",
                filename="path.txt",
                file_type="txt",
                file_size=100,
                chunk_count=1,
                indexed_at="2024-01-01T00:00:00",
                content_hash="abc123",
            )

            store.add_document(
                document_id="test_doc",
                chunks=["Test chunk"],
                embeddings=[[0.1] * 384],
                metadatas=[{}],
                document_record=doc_record,
            )

            docs = store.list_documents()
            assert len(docs) == 1
            assert docs[0].document_id == "test_doc"

    def test_document_exists(self) -> None:
        """Test duplicate detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaStore(Path(tmpdir))

            doc_record = DocumentRecord(
                document_id="test_doc",
                path="/test/path.txt",
                filename="path.txt",
                file_type="txt",
                file_size=100,
                chunk_count=1,
                indexed_at="2024-01-01T00:00:00",
                content_hash="unique_hash_123",
            )

            store.add_document(
                document_id="test_doc",
                chunks=["Test chunk"],
                embeddings=[[0.1] * 384],
                metadatas=[{}],
                document_record=doc_record,
            )

            assert store.document_exists("unique_hash_123")
            assert not store.document_exists("nonexistent_hash")

    def test_delete_document(self) -> None:
        """Test document deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaStore(Path(tmpdir))

            doc_record = DocumentRecord(
                document_id="test_doc",
                path="/test/path.txt",
                filename="path.txt",
                file_type="txt",
                file_size=100,
                chunk_count=1,
                indexed_at="2024-01-01T00:00:00",
                content_hash="abc123",
            )

            store.add_document(
                document_id="test_doc",
                chunks=["Test chunk"],
                embeddings=[[0.1] * 384],
                metadatas=[{}],
                document_record=doc_record,
            )

            assert store.delete_document("test_doc")
            assert not store.delete_document("nonexistent")
            assert store.get_stats()["document_count"] == 0


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_generate_document_id(self) -> None:
        """Test document ID generation."""
        path = Path("/test/path/document.pdf")
        doc_id = generate_document_id(path)
        assert len(doc_id) == 16
        assert doc_id.isalnum()

    def test_generate_document_id_deterministic(self) -> None:
        """Test document ID is deterministic."""
        path = Path("/test/path/document.pdf")
        id1 = generate_document_id(path)
        id2 = generate_document_id(path)
        assert id1 == id2

    def test_generate_content_hash(self) -> None:
        """Test content hash generation."""
        content = "Test content"
        hash1 = generate_content_hash(content)
        assert len(hash1) == 32
        assert hash1.isalnum()

    def test_generate_content_hash_deterministic(self) -> None:
        """Test content hash is deterministic."""
        content = "Test content"
        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)
        assert hash1 == hash2

    def test_generate_content_hash_different(self) -> None:
        """Test different content produces different hashes."""
        hash1 = generate_content_hash("Content A")
        hash2 = generate_content_hash("Content B")
        assert hash1 != hash2
