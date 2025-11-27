"""Export engine for ragd archives.

This module implements F-032: Export Engine, creating portable archives
of ragd knowledge bases.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
import tarfile
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ragd.archive.format import (
    ARCHIVE_VERSION,
    ArchiveFilters,
    ArchiveManifest,
    ArchiveStatistics,
    ArchivedChunk,
    ArchivedDocument,
    EmbeddingInfo,
)

if TYPE_CHECKING:
    from ragd.metadata.store import MetadataStore
    from ragd.storage.chromadb import ChromaStore

logger = logging.getLogger(__name__)


@dataclass
class ExportProgress:
    """Progress information during export."""

    stage: str
    current: int
    total: int
    message: str = ""


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    archive_path: Path | None = None
    manifest: ArchiveManifest | None = None
    error: str | None = None
    document_count: int = 0
    chunk_count: int = 0
    archive_size_bytes: int = 0
    duration_ms: int = 0


@dataclass
class ExportOptions:
    """Options for export operation."""

    include_embeddings: bool = True
    compression: str = "gzip"
    tags: list[str] = field(default_factory=list)
    project: str | None = None
    since: datetime | None = None
    until: datetime | None = None


class ExportEngine:
    """Engine for exporting ragd knowledge bases to archives.

    Creates portable tar.gz archives containing documents, chunks,
    embeddings, and metadata.

    Example:
        >>> from ragd.storage import ChromaStore
        >>> from ragd.metadata import MetadataStore
        >>> store = ChromaStore(Path("~/.ragd/chroma"))
        >>> metadata = MetadataStore(Path("~/.ragd/metadata.sqlite"))
        >>> engine = ExportEngine(store, metadata)
        >>> result = engine.export(Path("~/backup.tar.gz"))
        >>> print(f"Exported {result.document_count} documents")
    """

    def __init__(
        self,
        chroma_store: ChromaStore,
        metadata_store: MetadataStore | None = None,
        ragd_version: str = "0.2.0",
        embedding_model: str = "voyage-3",
        embedding_dimensions: int = 1024,
    ) -> None:
        """Initialise the export engine.

        Args:
            chroma_store: ChromaDB storage instance
            metadata_store: Optional metadata store for extended metadata
            ragd_version: Version string for ragd
            embedding_model: Name of embedding model used
            embedding_dimensions: Dimensions of embeddings
        """
        self._chroma = chroma_store
        self._metadata = metadata_store
        self._ragd_version = ragd_version
        self._embedding_model = embedding_model
        self._embedding_dimensions = embedding_dimensions
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def export(
        self,
        output_path: Path,
        options: ExportOptions | None = None,
        progress_callback: Callable[[ExportProgress], None] | None = None,
    ) -> ExportResult:
        """Export knowledge base to archive.

        Args:
            output_path: Path for output archive file
            options: Export configuration options
            progress_callback: Optional callback for progress updates

        Returns:
            ExportResult with status and statistics
        """
        import time

        start_time = time.time()
        options = options or ExportOptions()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Stage 1: Export documents
                if progress_callback:
                    progress_callback(
                        ExportProgress("documents", 0, 1, "Exporting documents...")
                    )

                documents, doc_count = self._export_documents(temp_path, options)

                # Stage 2: Export chunks
                if progress_callback:
                    progress_callback(
                        ExportProgress("chunks", 0, 1, "Exporting chunks...")
                    )

                chunks, chunk_count = self._export_chunks(
                    temp_path, documents, options, progress_callback
                )

                # Stage 3: Export embeddings
                if options.include_embeddings:
                    if progress_callback:
                        progress_callback(
                            ExportProgress(
                                "embeddings", 0, 1, "Exporting embeddings..."
                            )
                        )
                    self._export_embeddings(temp_path, chunks)

                # Stage 4: Export config
                self._export_config(temp_path)

                # Stage 5: Calculate checksums
                checksums = self._calculate_checksums(temp_path)

                # Stage 6: Create manifest
                manifest = self._create_manifest(
                    doc_count, chunk_count, options, checksums
                )
                self._write_manifest(temp_path, manifest)

                # Stage 7: Create archive
                if progress_callback:
                    progress_callback(
                        ExportProgress("archive", 0, 1, "Creating archive...")
                    )

                self._create_archive(temp_path, output_path, options.compression)

                duration_ms = int((time.time() - start_time) * 1000)
                archive_size = output_path.stat().st_size

                self._logger.info(
                    "Export completed: %d documents, %d chunks, %d bytes",
                    doc_count,
                    chunk_count,
                    archive_size,
                )

                return ExportResult(
                    success=True,
                    archive_path=output_path,
                    manifest=manifest,
                    document_count=doc_count,
                    chunk_count=chunk_count,
                    archive_size_bytes=archive_size,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            self._logger.exception("Export failed: %s", e)
            return ExportResult(
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _export_documents(
        self, temp_path: Path, options: ExportOptions
    ) -> tuple[list[ArchivedDocument], int]:
        """Export document metadata to temp directory."""
        docs_dir = temp_path / "documents" / "metadata"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Get all documents from ChromaDB
        doc_records = self._chroma.list_documents()

        # Filter if needed
        if options.tags or options.project or options.since or options.until:
            doc_records = self._filter_documents(doc_records, options)

        documents: list[ArchivedDocument] = []
        doc_ids: list[str] = []

        for record in doc_records:
            # Get extended metadata if available
            metadata_dict: dict[str, Any] = {}
            if self._metadata:
                meta = self._metadata.get(record.document_id)
                if meta:
                    metadata_dict = meta.to_dict()

            archived_doc = ArchivedDocument(
                id=record.document_id,
                dc_title=metadata_dict.get("dc_title", record.filename),
                dc_creator=metadata_dict.get("dc_creator", []),
                dc_date=metadata_dict.get("dc_date"),
                dc_subject=metadata_dict.get("dc_subject", []),
                ragd_source_path=record.path,
                ragd_source_hash=record.content_hash,
                ragd_tags=metadata_dict.get("ragd_tags", []),
                ragd_ingestion_date=record.indexed_at,
                ragd_chunk_count=record.chunk_count,
                metadata={
                    "file_type": record.file_type,
                    "file_size": record.file_size,
                },
            )

            # Write individual document metadata
            doc_file = docs_dir / f"{record.document_id}.json"
            with open(doc_file, "w") as f:
                json.dump(archived_doc.to_dict(), f, indent=2)

            documents.append(archived_doc)
            doc_ids.append(record.document_id)

        # Write index
        index_file = temp_path / "documents" / "index.json"
        with open(index_file, "w") as f:
            json.dump({"document_ids": doc_ids}, f, indent=2)

        return documents, len(documents)

    def _filter_documents(
        self, doc_records: list[Any], options: ExportOptions
    ) -> list[Any]:
        """Filter documents based on options."""
        filtered = []

        for record in doc_records:
            # Check tags filter
            if options.tags and self._metadata:
                meta = self._metadata.get(record.document_id)
                if meta:
                    doc_tags = set(meta.ragd_tags)
                    if not any(t in doc_tags for t in options.tags):
                        continue

            # Check project filter
            if options.project and self._metadata:
                meta = self._metadata.get(record.document_id)
                if meta and meta.ragd_project != options.project:
                    continue

            # Check date filters
            if options.since or options.until:
                indexed_at = datetime.fromisoformat(
                    record.indexed_at.replace("Z", "+00:00")
                )
                if options.since and indexed_at < options.since:
                    continue
                if options.until and indexed_at > options.until:
                    continue

            filtered.append(record)

        return filtered

    def _export_chunks(
        self,
        temp_path: Path,
        documents: list[ArchivedDocument],
        options: ExportOptions,
        progress_callback: Callable[[ExportProgress], None] | None = None,
    ) -> tuple[list[ArchivedChunk], int]:
        """Export chunk data to temp directory."""
        chunks_dir = temp_path / "chunks" / "data"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        all_chunks: list[ArchivedChunk] = []
        chunk_index: list[dict[str, str]] = []

        total_docs = len(documents)
        for i, doc in enumerate(documents):
            if progress_callback and i % 10 == 0:
                progress_callback(
                    ExportProgress(
                        "chunks",
                        i,
                        total_docs,
                        f"Exporting chunks for {doc.id}...",
                    )
                )

            # Get chunks for this document from ChromaDB
            result = self._chroma._collection.get(
                where={"document_id": doc.id},
                include=["documents", "metadatas"],
            )

            if not result["ids"]:
                continue

            doc_chunks_dir = chunks_dir / doc.id
            doc_chunks_dir.mkdir(parents=True, exist_ok=True)

            for j, chunk_id in enumerate(result["ids"]):
                text = result["documents"][j] if result["documents"] else ""
                metadata = result["metadatas"][j] if result["metadatas"] else {}

                archived_chunk = ArchivedChunk(
                    id=chunk_id,
                    document_id=doc.id,
                    text=text,
                    page_numbers=metadata.get("page_numbers", []),
                    section=metadata.get("section", ""),
                    char_start=metadata.get("char_start", 0),
                    char_end=metadata.get("char_end", 0),
                    metadata={
                        k: v
                        for k, v in metadata.items()
                        if k
                        not in [
                            "document_id",
                            "page_numbers",
                            "section",
                            "char_start",
                            "char_end",
                        ]
                    },
                )

                # Write chunk file
                chunk_file = doc_chunks_dir / f"{chunk_id}.json"
                with open(chunk_file, "w") as f:
                    json.dump(archived_chunk.to_dict(), f, indent=2)

                all_chunks.append(archived_chunk)
                chunk_index.append({"chunk_id": chunk_id, "document_id": doc.id})

        # Write index
        index_file = temp_path / "chunks" / "index.json"
        with open(index_file, "w") as f:
            json.dump({"chunks": chunk_index}, f, indent=2)

        return all_chunks, len(all_chunks)

    def _export_embeddings(
        self, temp_path: Path, chunks: list[ArchivedChunk]
    ) -> None:
        """Export embeddings to Parquet format."""
        embeddings_dir = temp_path / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)

        # Collect embeddings from ChromaDB
        chunk_ids = [c.id for c in chunks]
        embeddings_data: list[dict[str, Any]] = []

        # Batch fetch embeddings
        batch_size = 100
        for i in range(0, len(chunk_ids), batch_size):
            batch_ids = chunk_ids[i : i + batch_size]
            result = self._chroma._collection.get(
                ids=batch_ids, include=["embeddings"]
            )

            if result["embeddings"] is not None and len(result["embeddings"]) > 0:
                for j, chunk_id in enumerate(result["ids"]):
                    embeddings_data.append(
                        {
                            "chunk_id": chunk_id,
                            "embedding": list(result["embeddings"][j]),
                        }
                    )

        # Try to use pyarrow for Parquet, fall back to JSON
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            # Create table
            table = pa.table(
                {
                    "chunk_id": [e["chunk_id"] for e in embeddings_data],
                    "embedding": [e["embedding"] for e in embeddings_data],
                }
            )

            pq.write_table(
                table,
                embeddings_dir / "embeddings.parquet",
                compression="zstd",
            )
        except ImportError:
            # Fall back to JSON
            self._logger.warning(
                "pyarrow not available, using JSON for embeddings"
            )
            with open(embeddings_dir / "embeddings.json", "w") as f:
                json.dump(embeddings_data, f)

    def _export_config(self, temp_path: Path) -> None:
        """Export ragd configuration."""
        config = {
            "ragd_version": self._ragd_version,
            "embedding_model": self._embedding_model,
            "embedding_dimensions": self._embedding_dimensions,
        }

        # Try YAML, fall back to JSON
        try:
            import yaml

            config_file = temp_path / "config.yaml"
            with open(config_file, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
        except ImportError:
            config_file = temp_path / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

    def _calculate_checksums(self, temp_path: Path) -> dict[str, str]:
        """Calculate SHA256 checksums for archive contents."""
        checksums: dict[str, str] = {}

        for root, dirs, files in os.walk(temp_path):
            for filename in files:
                filepath = Path(root) / filename
                relative_path = filepath.relative_to(temp_path)

                with open(filepath, "rb") as f:
                    content = f.read()
                    checksum = hashlib.sha256(content).hexdigest()
                    checksums[str(relative_path)] = f"sha256:{checksum}"

        # Write checksums file
        checksums_file = temp_path / "checksums.sha256"
        with open(checksums_file, "w") as f:
            for path, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {path}\n")

        return checksums

    def _create_manifest(
        self,
        doc_count: int,
        chunk_count: int,
        options: ExportOptions,
        checksums: dict[str, str],
    ) -> ArchiveManifest:
        """Create archive manifest."""
        return ArchiveManifest(
            version=ARCHIVE_VERSION,
            created_at=datetime.utcnow().isoformat() + "Z",
            ragd_version=self._ragd_version,
            statistics=ArchiveStatistics(
                document_count=doc_count,
                chunk_count=chunk_count,
                total_size_bytes=0,  # Will be updated after archive creation
            ),
            embeddings=EmbeddingInfo(
                included=options.include_embeddings,
                model=self._embedding_model,
                dimensions=self._embedding_dimensions,
            ),
            compression=options.compression,
            filters=ArchiveFilters(
                tags=options.tags,
                project=options.project,
                date_from=options.since.isoformat() if options.since else None,
                date_to=options.until.isoformat() if options.until else None,
            ),
            checksums=checksums,
        )

    def _write_manifest(self, temp_path: Path, manifest: ArchiveManifest) -> None:
        """Write manifest to temp directory."""
        manifest_file = temp_path / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)

    def _create_archive(
        self, temp_path: Path, output_path: Path, compression: str
    ) -> None:
        """Create tar.gz archive from temp directory."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "w:gz" if compression == "gzip" else "w"

        with tarfile.open(output_path, mode) as tar:
            for item in temp_path.iterdir():
                tar.add(item, arcname=item.name)
