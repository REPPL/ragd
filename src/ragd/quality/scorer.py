"""Document quality scoring orchestration.

Coordinates quality assessment across multiple metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ragd.config import RagdConfig, load_config
from ragd.ingestion.extractor import extract_text, ExtractionResult
from ragd.quality.metrics import (
    QualityMetrics,
    compute_completeness,
    compute_character_quality,
    compute_structure_score,
    compute_image_handling,
    compute_table_handling,
    compute_overall_score,
)
from ragd.storage import ChromaStore, DocumentRecord
from ragd.utils.paths import get_file_type


@dataclass
class DocumentQuality:
    """Quality assessment result for a document.

    Attributes:
        document_id: Document identifier
        path: File path
        filename: File name
        file_type: File type
        metrics: Quality metrics
        success: Whether assessment succeeded
        error: Error message if failed
    """

    document_id: str
    path: str
    filename: str
    file_type: str
    metrics: QualityMetrics
    success: bool = True
    error: str | None = None


class QualityScorer:
    """Orchestrates quality assessment for documents."""

    def __init__(self, config: RagdConfig | None = None) -> None:
        """Initialise quality scorer.

        Args:
            config: ragd configuration
        """
        self.config = config or load_config()

    def score_file(self, path: Path) -> DocumentQuality:
        """Score quality of a file.

        Args:
            path: Path to file

        Returns:
            DocumentQuality with metrics
        """
        # Extract text
        result = extract_text(path)

        return self._score_extraction_result(
            document_id=path.stem,
            path=str(path),
            filename=path.name,
            result=result,
            file_size=path.stat().st_size if path.exists() else 0,
        )

    def score_stored_document(
        self,
        document_id: str,
        store: ChromaStore,
    ) -> DocumentQuality | None:
        """Score quality of an already-indexed document.

        Args:
            document_id: Document ID
            store: ChromaDB store

        Returns:
            DocumentQuality or None if not found
        """
        record = store.get_document_record(document_id)
        if record is None:
            return None

        # Get all chunks for this document
        chunks = store.get_document_chunks(document_id)
        if not chunks:
            return DocumentQuality(
                document_id=document_id,
                path=record.path,
                filename=record.filename,
                file_type=record.file_type,
                metrics=QualityMetrics(),
                success=False,
                error="No chunks found for document",
            )

        # Reconstruct text from chunks
        text = "\n\n".join(c["content"] for c in chunks)

        # Score based on stored content
        metrics = self._compute_metrics(
            text=text,
            file_size=record.file_size,
            file_type=record.file_type,
        )

        return DocumentQuality(
            document_id=document_id,
            path=record.path,
            filename=record.filename,
            file_type=record.file_type,
            metrics=metrics,
            success=True,
        )

    def _score_extraction_result(
        self,
        document_id: str,
        path: str,
        filename: str,
        result: ExtractionResult,
        file_size: int,
    ) -> DocumentQuality:
        """Score an extraction result.

        Args:
            document_id: Document identifier
            path: File path
            filename: File name
            result: Extraction result
            file_size: Original file size

        Returns:
            DocumentQuality with metrics
        """
        file_type = get_file_type(Path(path))

        if not result.success:
            return DocumentQuality(
                document_id=document_id,
                path=path,
                filename=filename,
                file_type=file_type,
                metrics=QualityMetrics(),
                success=False,
                error=result.error,
            )

        if not result.text.strip():
            return DocumentQuality(
                document_id=document_id,
                path=path,
                filename=filename,
                file_type=file_type,
                metrics=QualityMetrics(
                    details={"reason": "No text extracted"},
                ),
                success=False,
                error="No text extracted from document",
            )

        metrics = self._compute_metrics(
            text=result.text,
            file_size=file_size,
            file_type=file_type,
            extraction_method=result.extraction_method,
        )

        return DocumentQuality(
            document_id=document_id,
            path=path,
            filename=filename,
            file_type=file_type,
            metrics=metrics,
            success=True,
        )

    def _compute_metrics(
        self,
        text: str,
        file_size: int,
        file_type: str,
        extraction_method: str | None = None,
    ) -> QualityMetrics:
        """Compute all quality metrics for text.

        Args:
            text: Extracted text
            file_size: Original file size
            file_type: File type
            extraction_method: Method used for extraction

        Returns:
            QualityMetrics with all scores
        """
        # Compute individual metrics
        completeness, comp_details = compute_completeness(text, file_size, file_type)
        char_quality, char_details = compute_character_quality(text)
        structure, struct_details = compute_structure_score(text, file_type)
        images, img_details = compute_image_handling(text, file_type)
        tables, table_details = compute_table_handling(text, file_type)

        # Create metrics object
        metrics = QualityMetrics(
            completeness=completeness,
            character_quality=char_quality,
            structure=structure,
            images=images,
            tables=tables,
            details={
                "completeness": comp_details,
                "character_quality": char_details,
                "structure": struct_details,
                "images": img_details,
                "tables": table_details,
                "extraction_method": extraction_method,
            },
        )

        # Compute overall score
        metrics.overall = compute_overall_score(metrics)

        return metrics


def score_document(path: Path, config: RagdConfig | None = None) -> DocumentQuality:
    """Score quality of a document file (convenience function).

    Args:
        path: Path to document
        config: ragd configuration

    Returns:
        DocumentQuality with metrics
    """
    scorer = QualityScorer(config)
    return scorer.score_file(path)


def score_extraction(
    text: str,
    file_size: int,
    file_type: str,
    document_id: str = "unknown",
    path: str = "unknown",
    filename: str = "unknown",
) -> DocumentQuality:
    """Score quality of extracted text directly.

    Args:
        text: Extracted text
        file_size: Original file size
        file_type: File type
        document_id: Document identifier
        path: File path
        filename: File name

    Returns:
        DocumentQuality with metrics
    """
    scorer = QualityScorer()
    metrics = scorer._compute_metrics(text, file_size, file_type)

    return DocumentQuality(
        document_id=document_id,
        path=path,
        filename=filename,
        file_type=file_type,
        metrics=metrics,
        success=True,
    )
