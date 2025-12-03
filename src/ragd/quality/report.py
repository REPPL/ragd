"""Quality report generation for ragd.

Provides functions to generate quality reports for indexed documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ragd.config import RagdConfig, load_config
from ragd.quality.scorer import DocumentQuality, QualityScorer
from ragd.storage import ChromaStore


@dataclass
class QualityReport:
    """Quality report for a collection of documents.

    Attributes:
        total_documents: Number of documents assessed
        average_score: Average overall quality score
        low_quality_count: Documents below threshold
        by_score: Documents grouped by score range
        by_file_type: Average scores by file type
        documents: Individual document results
        errors: Documents that failed assessment
    """

    total_documents: int
    average_score: float
    low_quality_count: int
    by_score: dict[str, list[DocumentQuality]]
    by_file_type: dict[str, dict[str, float]]
    documents: list[DocumentQuality]
    errors: list[DocumentQuality]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total_documents": self.total_documents,
            "average_score": self.average_score,
            "low_quality_count": self.low_quality_count,
            "by_score": {
                k: [d.filename for d in v]
                for k, v in self.by_score.items()
            },
            "by_file_type": self.by_file_type,
            "documents": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "overall_score": d.metrics.overall,
                    "metrics": d.metrics.to_dict(),
                }
                for d in self.documents
            ],
            "errors": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "error": d.error,
                }
                for d in self.errors
            ],
        }


def generate_quality_report(
    store: ChromaStore,
    config: RagdConfig | None = None,
    threshold: float = 0.7,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> QualityReport:
    """Generate quality report for all indexed documents.

    Args:
        store: ChromaDB store
        config: ragd configuration
        threshold: Score threshold for "low quality"
        progress_callback: Progress callback (current, total, filename)

    Returns:
        QualityReport with all assessments
    """
    config = config or load_config()
    scorer = QualityScorer(config)

    # Get all document records
    records = store.list_documents()

    documents: list[DocumentQuality] = []
    errors: list[DocumentQuality] = []

    total = len(records)
    for i, record in enumerate(records):
        if progress_callback:
            progress_callback(i + 1, total, record.filename)

        result = scorer.score_stored_document(record.document_id, store)

        if result is None:
            errors.append(DocumentQuality(
                document_id=record.document_id,
                path=record.path,
                filename=record.filename,
                file_type=record.file_type,
                metrics=result.metrics if result else None,
                success=False,
                error="Could not retrieve document",
            ))
        elif not result.success:
            errors.append(result)
        else:
            documents.append(result)

    return _build_report(documents, errors, threshold)


def generate_corpus_report(
    path: Path,
    config: RagdConfig | None = None,
    threshold: float = 0.7,
    recursive: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> QualityReport:
    """Generate quality report for a corpus of files (batch testing).

    This is useful for CI/regression testing of extraction quality.

    Args:
        path: Path to corpus directory
        config: ragd configuration
        threshold: Score threshold for "low quality"
        recursive: Search directories recursively
        progress_callback: Progress callback (current, total, filename)

    Returns:
        QualityReport with all assessments
    """
    from ragd.utils.paths import discover_files

    config = config or load_config()
    scorer = QualityScorer(config)

    # Discover files
    files = discover_files(path, recursive=recursive)

    documents: list[DocumentQuality] = []
    errors: list[DocumentQuality] = []

    total = len(files)
    for i, file_path in enumerate(files):
        if progress_callback:
            progress_callback(i + 1, total, file_path.name)

        result = scorer.score_file(file_path)

        if not result.success:
            errors.append(result)
        else:
            documents.append(result)

    return _build_report(documents, errors, threshold)


def _build_report(
    documents: list[DocumentQuality],
    errors: list[DocumentQuality],
    threshold: float,
) -> QualityReport:
    """Build quality report from document assessments.

    Args:
        documents: Successful assessments
        errors: Failed assessments
        threshold: Low quality threshold

    Returns:
        QualityReport
    """
    # Calculate statistics
    if documents:
        average_score = sum(d.metrics.overall for d in documents) / len(documents)
    else:
        average_score = 0.0

    low_quality = [d for d in documents if d.metrics.overall < threshold]

    # Group by score ranges
    by_score: dict[str, list[DocumentQuality]] = {
        "excellent": [],   # >= 0.9
        "good": [],        # >= 0.7
        "fair": [],        # >= 0.5
        "poor": [],        # < 0.5
    }

    for doc in documents:
        score = doc.metrics.overall
        if score >= 0.9:
            by_score["excellent"].append(doc)
        elif score >= 0.7:
            by_score["good"].append(doc)
        elif score >= 0.5:
            by_score["fair"].append(doc)
        else:
            by_score["poor"].append(doc)

    # Group by file type
    by_file_type: dict[str, dict[str, float]] = {}
    file_type_docs: dict[str, list[DocumentQuality]] = {}

    for doc in documents:
        ft = doc.file_type
        if ft not in file_type_docs:
            file_type_docs[ft] = []
        file_type_docs[ft].append(doc)

    for ft, docs in file_type_docs.items():
        by_file_type[ft] = {
            "count": len(docs),
            "average": sum(d.metrics.overall for d in docs) / len(docs),
            "completeness": sum(d.metrics.completeness for d in docs) / len(docs),
            "character_quality": sum(d.metrics.character_quality for d in docs) / len(docs),
            "structure": sum(d.metrics.structure for d in docs) / len(docs),
            "images": sum(d.metrics.images for d in docs) / len(docs),
            "tables": sum(d.metrics.tables for d in docs) / len(docs),
        }

    # Sort documents by score (worst first for review)
    documents.sort(key=lambda d: d.metrics.overall)

    return QualityReport(
        total_documents=len(documents) + len(errors),
        average_score=round(average_score, 4),
        low_quality_count=len(low_quality),
        by_score=by_score,
        by_file_type=by_file_type,
        documents=documents,
        errors=errors,
    )


def get_quality_summary(report: QualityReport) -> str:
    """Generate a text summary of the quality report.

    Args:
        report: Quality report

    Returns:
        Human-readable summary
    """
    lines = [
        f"Quality Report",
        f"=" * 50,
        f"Total documents: {report.total_documents}",
        f"Average score: {report.average_score:.2%}",
        f"Low quality (< 70%): {report.low_quality_count}",
        f"Errors: {len(report.errors)}",
        "",
        "Score Distribution:",
        f"  Excellent (≥90%): {len(report.by_score['excellent'])}",
        f"  Good (≥70%):      {len(report.by_score['good'])}",
        f"  Fair (≥50%):      {len(report.by_score['fair'])}",
        f"  Poor (<50%):      {len(report.by_score['poor'])}",
        "",
    ]

    if report.by_file_type:
        lines.append("By File Type:")
        for ft, stats in sorted(report.by_file_type.items()):
            lines.append(f"  {ft}: {stats['count']} docs, avg {stats['average']:.2%}")

    if report.errors:
        lines.append("")
        lines.append("Errors:")
        for err in report.errors[:5]:  # Show first 5
            lines.append(f"  - {err.filename}: {err.error}")
        if len(report.errors) > 5:
            lines.append(f"  ... and {len(report.errors) - 5} more")

    return "\n".join(lines)
