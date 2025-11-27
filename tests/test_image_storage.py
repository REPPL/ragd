"""Tests for image storage module."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragd.storage.images import (
    ImageRecord,
    ImageStore,
    generate_image_content_hash,
    generate_image_id,
)


class TestImageRecord:
    """Tests for ImageRecord dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        record = ImageRecord(
            image_id="img_abc123",
            document_id="doc_123",
            source_path="/path/to/doc.pdf",
            width=800,
            height=600,
            format="png",
            size_bytes=1024,
        )
        assert record.image_id == "img_abc123"
        assert record.document_id == "doc_123"
        assert record.page_number is None
        assert record.indexed_at == ""
        assert record.content_hash == ""
        assert record.caption == ""
        assert record.metadata == {}

    def test_with_page_number(self) -> None:
        """Test with page number."""
        record = ImageRecord(
            image_id="img_abc123",
            document_id="doc_123",
            source_path="/path/to/doc.pdf",
            width=800,
            height=600,
            format="jpeg",
            size_bytes=2048,
            page_number=5,
        )
        assert record.page_number == 5


class TestImageStore:
    """Tests for ImageStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> ImageStore:
        """Create a temporary image store."""
        return ImageStore(tmp_path / "chroma")

    @pytest.fixture
    def sample_record(self) -> ImageRecord:
        """Create a sample image record."""
        return ImageRecord(
            image_id="img_test123",
            document_id="doc_abc",
            source_path="/path/to/test.pdf",
            width=640,
            height=480,
            format="png",
            size_bytes=4096,
            page_number=1,
            indexed_at="2025-01-01T00:00:00",
            content_hash="abcdef123456",
        )

    @pytest.fixture
    def sample_embedding(self) -> list[float]:
        """Create a sample 128-dim embedding."""
        return [0.1] * 128

    def test_init_creates_collections(self, store: ImageStore) -> None:
        """Test that init creates required collections."""
        stats = store.get_stats()
        assert "image_count" in stats
        assert stats["image_count"] == 0

    def test_add_and_get_image(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test adding and retrieving an image."""
        store.add_image("img_test123", sample_embedding, sample_record)

        retrieved = store.get_image("img_test123")
        assert retrieved is not None
        assert retrieved.image_id == "img_test123"
        assert retrieved.document_id == "doc_abc"
        assert retrieved.width == 640
        assert retrieved.height == 480

    def test_get_nonexistent_image(self, store: ImageStore) -> None:
        """Test getting a non-existent image returns None."""
        retrieved = store.get_image("nonexistent")
        assert retrieved is None

    def test_image_exists(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test image existence check."""
        store.add_image("img_test123", sample_embedding, sample_record)

        assert store.image_exists("abcdef123456") is True
        assert store.image_exists("nonexistent_hash") is False

    def test_delete_image(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test deleting an image."""
        store.add_image("img_test123", sample_embedding, sample_record)
        assert store.get_image("img_test123") is not None

        result = store.delete_image("img_test123")
        assert result is True
        assert store.get_image("img_test123") is None

    def test_delete_nonexistent_image(self, store: ImageStore) -> None:
        """Test deleting a non-existent image."""
        result = store.delete_image("nonexistent")
        assert result is False

    def test_search_returns_results(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test searching for images."""
        store.add_image("img_test123", sample_embedding, sample_record)

        # Search with same embedding
        results = store.search(sample_embedding, limit=5)
        assert len(results) == 1
        assert results[0]["image_id"] == "img_test123"
        assert results[0]["score"] > 0.99  # Should be near-identical

    def test_search_with_filter(
        self,
        store: ImageStore,
        sample_embedding: list[float],
    ) -> None:
        """Test searching with document_id filter."""
        # Add two images from different documents
        record1 = ImageRecord(
            image_id="img_1",
            document_id="doc_a",
            source_path="/doc_a.pdf",
            width=100,
            height=100,
            format="png",
            size_bytes=100,
        )
        record2 = ImageRecord(
            image_id="img_2",
            document_id="doc_b",
            source_path="/doc_b.pdf",
            width=100,
            height=100,
            format="png",
            size_bytes=100,
        )

        store.add_image("img_1", sample_embedding, record1)
        store.add_image("img_2", [0.2] * 128, record2)

        # Search with filter
        results = store.search(
            sample_embedding,
            where={"document_id": "doc_a"},
        )
        assert len(results) == 1
        assert results[0]["image_id"] == "img_1"

    def test_get_images_for_document(
        self,
        store: ImageStore,
        sample_embedding: list[float],
    ) -> None:
        """Test getting all images for a document."""
        # Add images to same document
        for i in range(3):
            record = ImageRecord(
                image_id=f"img_{i}",
                document_id="doc_test",
                source_path="/doc_test.pdf",
                width=100,
                height=100,
                format="png",
                size_bytes=100,
                page_number=i + 1,
            )
            store.add_image(f"img_{i}", sample_embedding, record)

        # Add image to different document
        other_record = ImageRecord(
            image_id="img_other",
            document_id="doc_other",
            source_path="/doc_other.pdf",
            width=100,
            height=100,
            format="png",
            size_bytes=100,
        )
        store.add_image("img_other", sample_embedding, other_record)

        images = store.get_images_for_document("doc_test")
        assert len(images) == 3
        assert all(img.document_id == "doc_test" for img in images)

    def test_delete_images_for_document(
        self,
        store: ImageStore,
        sample_embedding: list[float],
    ) -> None:
        """Test deleting all images for a document."""
        # Add images
        for i in range(3):
            record = ImageRecord(
                image_id=f"img_{i}",
                document_id="doc_test",
                source_path="/doc_test.pdf",
                width=100,
                height=100,
                format="png",
                size_bytes=100,
            )
            store.add_image(f"img_{i}", sample_embedding, record)

        # Delete
        count = store.delete_images_for_document("doc_test")
        assert count == 3
        assert len(store.get_images_for_document("doc_test")) == 0

    def test_add_images_batch(self, store: ImageStore) -> None:
        """Test batch adding images."""
        images = []
        for i in range(5):
            record = ImageRecord(
                image_id=f"img_{i}",
                document_id="doc_batch",
                source_path="/batch.pdf",
                width=100,
                height=100,
                format="png",
                size_bytes=100,
                page_number=i + 1,
            )
            images.append((f"img_{i}", [0.1] * 128, record))

        count = store.add_images(images)
        assert count == 5
        assert store.get_stats()["image_count"] == 5

    def test_list_images(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test listing images."""
        store.add_image("img_test123", sample_embedding, sample_record)

        images = store.list_images(limit=10)
        assert len(images) == 1
        assert images[0].image_id == "img_test123"

    def test_reset_clears_data(
        self,
        store: ImageStore,
        sample_record: ImageRecord,
        sample_embedding: list[float],
    ) -> None:
        """Test reset clears all data."""
        store.add_image("img_test123", sample_embedding, sample_record)
        assert store.get_stats()["image_count"] == 1

        store.reset()
        assert store.get_stats()["image_count"] == 0


class TestImageIdGeneration:
    """Tests for image ID and hash generation."""

    def test_generate_image_id_deterministic(self) -> None:
        """Test that same data produces same ID."""
        data = b"test image data"
        id1 = generate_image_id(data)
        id2 = generate_image_id(data)
        assert id1 == id2

    def test_generate_image_id_different_for_different_data(self) -> None:
        """Test that different data produces different ID."""
        id1 = generate_image_id(b"data1")
        id2 = generate_image_id(b"data2")
        assert id1 != id2

    def test_generate_image_id_with_document(self) -> None:
        """Test generating ID with document context."""
        data = b"test"
        id_with_doc = generate_image_id(data, document_id="doc_123", page_number=5)
        id_without = generate_image_id(data)
        assert "doc_123" in id_with_doc
        assert "5" in id_with_doc
        assert "doc_123" not in id_without

    def test_generate_content_hash_deterministic(self) -> None:
        """Test that same data produces same hash."""
        data = b"test image data"
        hash1 = generate_image_content_hash(data)
        hash2 = generate_image_content_hash(data)
        assert hash1 == hash2

    def test_generate_content_hash_length(self) -> None:
        """Test hash length."""
        data = b"test"
        hash_val = generate_image_content_hash(data)
        assert len(hash_val) == 32
