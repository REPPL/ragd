"""Import engine for ragd archives.

This module implements F-033: Import Engine, restoring ragd knowledge
bases from portable archives.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tarfile
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ragd.archive.format import (
    COMPATIBLE_VERSIONS,
    ArchiveManifest,
    ArchiveValidationError,
    ArchivedChunk,
    ArchivedDocument,
    ChecksumMismatchError,
    IncompatibleVersionError,
    is_version_compatible,
)

if TYPE_CHECKING:
    from ragd.metadata.schema import DocumentMetadata
    from ragd.metadata.store import MetadataStore
    from ragd.storage.chromadb import ChromaStore

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """How to handle conflicts during import."""

    SKIP = "skip"  # Skip documents that already exist
    REPLACE = "replace"  # Replace existing with imported version
    MERGE = "merge"  # Merge metadata, keep latest chunks
    RENAME = "rename"  # Import with new ID, keep both


@dataclass
class ImportProgress:
    """Progress information during import."""

    stage: str
    current: int
    total: int
    message: str = ""


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""

    document_id: str
    existing_hash: str
    imported_hash: str
    existing_date: str
    imported_date: str


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    error: str | None = None
    documents_imported: int = 0
    documents_skipped: int = 0
    documents_replaced: int = 0
    chunks_imported: int = 0
    conflicts: list[ConflictInfo] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class ImportOptions:
    """Options for import operation."""

    conflict_resolution: ConflictResolution = ConflictResolution.SKIP
    regenerate_embeddings: bool = False
    dry_run: bool = False
    verify_checksums: bool = True


@dataclass
class ValidationResult:
    """Result of archive validation."""

    valid: bool
    manifest: ArchiveManifest | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ImportEngine:
    """Engine for importing ragd archives.

    Restores knowledge bases from portable tar.gz archives with
    conflict detection and resolution.

    Example:
        >>> from ragd.storage import ChromaStore
        >>> from ragd.metadata import MetadataStore
        >>> store = ChromaStore(Path("~/.ragd/chroma"))
        >>> metadata = MetadataStore(Path("~/.ragd/metadata.sqlite"))
        >>> engine = ImportEngine(store, metadata)
        >>> result = engine.import_archive(Path("~/backup.tar.gz"))
        >>> print(f"Imported {result.documents_imported} documents")
    """

    def __init__(
        self,
        chroma_store: ChromaStore,
        metadata_store: MetadataStore | None = None,
        embedding_func: Callable[[str], list[float]] | None = None,
    ) -> None:
        """Initialise the import engine.

        Args:
            chroma_store: ChromaDB storage instance
            metadata_store: Optional metadata store for extended metadata
            embedding_func: Function to generate embeddings (for regeneration)
        """
        self._chroma = chroma_store
        self._metadata = metadata_store
        self._embed = embedding_func
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate(self, archive_path: Path) -> ValidationResult:
        """Validate an archive without importing.

        Args:
            archive_path: Path to archive file

        Returns:
            ValidationResult with status and any issues found
        """
        errors: list[str] = []
        warnings: list[str] = []
        manifest: ArchiveManifest | None = None

        if not archive_path.exists():
            return ValidationResult(
                valid=False, errors=[f"Archive not found: {archive_path}"]
            )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract archive
                with tarfile.open(archive_path, "r:*") as tar:
                    tar.extractall(temp_path)

                # Check manifest exists
                manifest_path = temp_path / "manifest.json"
                if not manifest_path.exists():
                    errors.append("Missing manifest.json")
                    return ValidationResult(valid=False, errors=errors)

                # Parse manifest
                with open(manifest_path) as f:
                    manifest_data = json.load(f)
                manifest = ArchiveManifest.from_dict(manifest_data)

                # Check version compatibility
                if not is_version_compatible(manifest.version):
                    errors.append(
                        f"Incompatible version: {manifest.version}. "
                        f"Supported: {COMPATIBLE_VERSIONS}"
                    )

                # Check required directories
                required_dirs = ["documents", "chunks"]
                for dir_name in required_dirs:
                    if not (temp_path / dir_name).exists():
                        errors.append(f"Missing required directory: {dir_name}")

                # Verify checksums if available
                checksums_path = temp_path / "checksums.sha256"
                if checksums_path.exists():
                    checksum_errors = self._verify_checksums(temp_path, checksums_path)
                    errors.extend(checksum_errors)
                else:
                    warnings.append("No checksums.sha256 file found")

                # Check document/chunk counts match manifest
                doc_count = self._count_documents(temp_path)
                if doc_count != manifest.statistics.document_count:
                    warnings.append(
                        f"Document count mismatch: manifest says "
                        f"{manifest.statistics.document_count}, found {doc_count}"
                    )

        except tarfile.TarError as e:
            errors.append(f"Invalid archive format: {e}")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid manifest JSON: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return ValidationResult(
            valid=len(errors) == 0,
            manifest=manifest,
            errors=errors,
            warnings=warnings,
        )

    def import_archive(
        self,
        archive_path: Path,
        options: ImportOptions | None = None,
        progress_callback: Callable[[ImportProgress], None] | None = None,
    ) -> ImportResult:
        """Import archive into ragd.

        Args:
            archive_path: Path to archive file
            options: Import configuration options
            progress_callback: Optional callback for progress updates

        Returns:
            ImportResult with status and statistics
        """
        import time

        start_time = time.time()
        options = options or ImportOptions()

        # Validate first
        validation = self.validate(archive_path)
        if not validation.valid:
            return ImportResult(
                success=False,
                error=f"Validation failed: {'; '.join(validation.errors)}",
            )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract archive
                if progress_callback:
                    progress_callback(
                        ImportProgress("extract", 0, 1, "Extracting archive...")
                    )

                with tarfile.open(archive_path, "r:*") as tar:
                    tar.extractall(temp_path)

                manifest = validation.manifest
                assert manifest is not None

                # Stage 1: Detect conflicts
                if progress_callback:
                    progress_callback(
                        ImportProgress("conflicts", 0, 1, "Detecting conflicts...")
                    )

                conflicts = self._detect_conflicts(temp_path)

                if options.dry_run:
                    duration_ms = int((time.time() - start_time) * 1000)
                    return ImportResult(
                        success=True,
                        documents_imported=manifest.statistics.document_count
                        - len(conflicts),
                        documents_skipped=len(conflicts)
                        if options.conflict_resolution == ConflictResolution.SKIP
                        else 0,
                        chunks_imported=manifest.statistics.chunk_count,
                        conflicts=conflicts,
                        duration_ms=duration_ms,
                    )

                # Stage 2: Import documents
                if progress_callback:
                    progress_callback(
                        ImportProgress("documents", 0, 1, "Importing documents...")
                    )

                doc_stats = self._import_documents(
                    temp_path, conflicts, options, progress_callback
                )

                # Stage 3: Import chunks
                if progress_callback:
                    progress_callback(
                        ImportProgress("chunks", 0, 1, "Importing chunks...")
                    )

                chunk_count = self._import_chunks(
                    temp_path,
                    doc_stats["imported_ids"],
                    doc_stats["doc_records"],
                    manifest,
                    options,
                    progress_callback,
                )

                duration_ms = int((time.time() - start_time) * 1000)

                self._logger.info(
                    "Import completed: %d documents, %d chunks",
                    doc_stats["imported"],
                    chunk_count,
                )

                return ImportResult(
                    success=True,
                    documents_imported=doc_stats["imported"],
                    documents_skipped=doc_stats["skipped"],
                    documents_replaced=doc_stats["replaced"],
                    chunks_imported=chunk_count,
                    conflicts=conflicts,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            self._logger.exception("Import failed: %s", e)
            return ImportResult(
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _verify_checksums(
        self, temp_path: Path, checksums_path: Path
    ) -> list[str]:
        """Verify file checksums."""
        errors: list[str] = []

        with open(checksums_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split("  ", 1)
                if len(parts) != 2:
                    continue

                expected_checksum, filepath = parts
                full_path = temp_path / filepath

                if not full_path.exists():
                    errors.append(f"Missing file: {filepath}")
                    continue

                # Skip the checksums file itself
                if filepath == "checksums.sha256":
                    continue

                with open(full_path, "rb") as file:
                    actual = f"sha256:{hashlib.sha256(file.read()).hexdigest()}"

                if actual != expected_checksum:
                    errors.append(
                        f"Checksum mismatch for {filepath}: "
                        f"expected {expected_checksum[:24]}..., got {actual[:24]}..."
                    )

        return errors

    def _count_documents(self, temp_path: Path) -> int:
        """Count documents in extracted archive."""
        metadata_dir = temp_path / "documents" / "metadata"
        if not metadata_dir.exists():
            return 0
        return len(list(metadata_dir.glob("*.json")))

    def _detect_conflicts(self, temp_path: Path) -> list[ConflictInfo]:
        """Detect documents that would conflict with existing."""
        conflicts: list[ConflictInfo] = []

        metadata_dir = temp_path / "documents" / "metadata"
        if not metadata_dir.exists():
            return conflicts

        for doc_file in metadata_dir.glob("*.json"):
            with open(doc_file) as f:
                doc_data = json.load(f)

            doc_id = doc_data.get("id", "")
            existing = self._chroma.get_document(doc_id)

            if existing:
                conflicts.append(
                    ConflictInfo(
                        document_id=doc_id,
                        existing_hash=existing.content_hash,
                        imported_hash=doc_data.get("ragd_source_hash", ""),
                        existing_date=existing.indexed_at,
                        imported_date=doc_data.get("ragd_ingestion_date", ""),
                    )
                )

        return conflicts

    def _import_documents(
        self,
        temp_path: Path,
        conflicts: list[ConflictInfo],
        options: ImportOptions,
        progress_callback: Callable[[ImportProgress], None] | None = None,
    ) -> dict[str, Any]:
        """Import document metadata."""
        conflict_ids = {c.document_id for c in conflicts}
        imported_ids: list[str] = []
        doc_records_data: dict[str, dict[str, Any]] = {}
        skipped = 0
        replaced = 0

        metadata_dir = temp_path / "documents" / "metadata"
        if not metadata_dir.exists():
            return {"imported": 0, "skipped": 0, "replaced": 0, "imported_ids": [], "doc_records": {}}

        doc_files = list(metadata_dir.glob("*.json"))
        total = len(doc_files)

        for i, doc_file in enumerate(doc_files):
            if progress_callback and i % 10 == 0:
                progress_callback(
                    ImportProgress("documents", i, total, f"Importing {doc_file.stem}...")
                )

            with open(doc_file) as f:
                doc_data = json.load(f)

            doc_id = doc_data.get("id", "")

            # Handle conflicts
            if doc_id in conflict_ids:
                if options.conflict_resolution == ConflictResolution.SKIP:
                    skipped += 1
                    continue
                elif options.conflict_resolution == ConflictResolution.REPLACE:
                    self._chroma.delete_document(doc_id)
                    replaced += 1
                elif options.conflict_resolution == ConflictResolution.RENAME:
                    # Generate new ID
                    doc_id = f"{doc_id}_imported_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    doc_data["id"] = doc_id

            # Store document record info for later when we import chunks
            doc_records_data[doc_id] = doc_data

            # Import to extended metadata store if available
            if self._metadata:
                from ragd.metadata.schema import DocumentMetadata

                meta = DocumentMetadata(
                    dc_title=doc_data.get("dc_title", ""),
                    dc_creator=doc_data.get("dc_creator", []),
                    dc_subject=doc_data.get("dc_subject", []),
                    ragd_source_path=doc_data.get("ragd_source_path", ""),
                    ragd_source_hash=doc_data.get("ragd_source_hash", ""),
                    ragd_tags=doc_data.get("ragd_tags", []),
                )

                # Parse date if present
                if doc_data.get("dc_date"):
                    try:
                        meta = DocumentMetadata(
                            dc_title=meta.dc_title,
                            dc_creator=meta.dc_creator,
                            dc_date=datetime.fromisoformat(
                                doc_data["dc_date"].replace("Z", "+00:00")
                            ),
                            dc_subject=meta.dc_subject,
                            ragd_source_path=meta.ragd_source_path,
                            ragd_source_hash=meta.ragd_source_hash,
                            ragd_tags=meta.ragd_tags,
                        )
                    except (ValueError, TypeError):
                        pass

                self._metadata.set(doc_id, meta)

            imported_ids.append(doc_id)

        return {
            "imported": len(imported_ids),
            "skipped": skipped,
            "replaced": replaced,
            "imported_ids": imported_ids,
            "doc_records": doc_records_data,
        }

    def _import_chunks(
        self,
        temp_path: Path,
        imported_doc_ids: list[str],
        doc_records: dict[str, dict[str, Any]],
        manifest: ArchiveManifest,
        options: ImportOptions,
        progress_callback: Callable[[ImportProgress], None] | None = None,
    ) -> int:
        """Import chunks and embeddings."""
        chunks_dir = temp_path / "chunks" / "data"
        embeddings_dir = temp_path / "embeddings"

        # Load embeddings if available and not regenerating
        embeddings: dict[str, list[float]] = {}
        if not options.regenerate_embeddings and manifest.embeddings.included:
            embeddings = self._load_embeddings(embeddings_dir)

        chunk_count = 0
        imported_doc_ids_set = set(imported_doc_ids)

        for doc_dir in chunks_dir.iterdir():
            if not doc_dir.is_dir():
                continue

            doc_id = doc_dir.name

            # Skip chunks for documents we didn't import
            # But handle renamed documents
            original_doc_id = doc_id
            if doc_id not in imported_doc_ids_set:
                # Check if this was renamed
                renamed = [
                    did
                    for did in imported_doc_ids
                    if did.startswith(f"{doc_id}_imported_")
                ]
                if renamed:
                    doc_id = renamed[0]
                else:
                    continue

            chunk_files = list(doc_dir.glob("*.json"))

            if progress_callback:
                progress_callback(
                    ImportProgress(
                        "chunks",
                        chunk_count,
                        manifest.statistics.chunk_count,
                        f"Importing chunks for {doc_id}...",
                    )
                )

            chunks: list[str] = []
            chunk_embeddings: list[list[float]] = []
            chunk_metadatas: list[dict[str, Any]] = []
            chunk_ids: list[str] = []

            for chunk_file in chunk_files:
                with open(chunk_file) as f:
                    chunk_data = json.load(f)

                chunk_id = chunk_data.get("id", "")
                text = chunk_data.get("text", "")

                # Get or generate embedding
                if chunk_id in embeddings:
                    embedding = embeddings[chunk_id]
                elif options.regenerate_embeddings and self._embed:
                    embedding = self._embed(text)
                else:
                    # Skip if no embedding available
                    self._logger.warning("No embedding for chunk %s", chunk_id)
                    continue

                # Update chunk ID if document was renamed
                if doc_id != original_doc_id:
                    chunk_id = chunk_id.replace(original_doc_id, doc_id)

                chunks.append(text)
                chunk_embeddings.append(embedding)
                chunk_ids.append(chunk_id)

                # Build metadata - convert lists to JSON strings for ChromaDB compatibility
                chunk_meta: dict[str, Any] = {
                    "document_id": doc_id,
                    "section": chunk_data.get("section", ""),
                }

                # Handle page_numbers as JSON string (ChromaDB doesn't accept lists)
                page_nums = chunk_data.get("page_numbers", [])
                if page_nums:
                    chunk_meta["page_numbers"] = json.dumps(page_nums)

                # Add other metadata, filtering out non-primitive types
                for k, v in chunk_data.get("metadata", {}).items():
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        chunk_meta[k] = v
                    elif isinstance(v, list):
                        chunk_meta[k] = json.dumps(v)

                chunk_metadatas.append(chunk_meta)

            if chunks:
                # Add chunks to ChromaDB main collection
                self._chroma._collection.add(
                    ids=chunk_ids,
                    documents=chunks,
                    embeddings=chunk_embeddings,
                    metadatas=chunk_metadatas,
                )
                chunk_count += len(chunks)

                # Add document record to ChromaDB metadata collection
                # Use original doc_id for lookup since that's the key in doc_records
                record_key = original_doc_id if original_doc_id in doc_records else doc_id
                if record_key in doc_records:
                    doc_data = doc_records[record_key]
                    # Extract filename from source path
                    source_path = doc_data.get("ragd_source_path", "")
                    filename = Path(source_path).name if source_path else ""

                    self._chroma._metadata.add(
                        ids=[doc_id],
                        documents=[source_path],
                        metadatas=[
                            {
                                "filename": filename or doc_data.get("dc_title", ""),
                                "file_type": doc_data.get("metadata", {}).get("file_type", "unknown"),
                                "file_size": doc_data.get("metadata", {}).get("file_size", 0),
                                "chunk_count": len(chunks),
                                "indexed_at": doc_data.get("ragd_ingestion_date", ""),
                                "content_hash": doc_data.get("ragd_source_hash", ""),
                            }
                        ],
                    )

        return chunk_count

    def _load_embeddings(self, embeddings_dir: Path) -> dict[str, list[float]]:
        """Load embeddings from archive."""
        embeddings: dict[str, list[float]] = {}

        parquet_path = embeddings_dir / "embeddings.parquet"
        json_path = embeddings_dir / "embeddings.json"

        if parquet_path.exists():
            try:
                import pyarrow.parquet as pq

                table = pq.read_table(parquet_path)
                df = table.to_pandas()

                for _, row in df.iterrows():
                    embeddings[row["chunk_id"]] = list(row["embedding"])

            except ImportError:
                self._logger.warning("pyarrow not available, cannot read Parquet")

        elif json_path.exists():
            with open(json_path) as f:
                data = json.load(f)

            for item in data:
                embeddings[item["chunk_id"]] = item["embedding"]

        return embeddings
