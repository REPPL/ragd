"""Audit commands for ragd.

This module provides commands for auditing indexed content.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ragd.ui.cli.utils import get_console


@dataclass
class ContentAuditResult:
    """Result of auditing a single document."""

    document_id: str
    filename: str
    source_path: str
    source_exists: bool
    source_size: int | None
    indexed_chunks: int
    extraction_method: str | None
    quality_warning: str | None
    issues: list[str]


def audit_content_command(
    path: Path | None = None,
    document_id: str | None = None,
    show_missing: bool = False,
    show_quality: bool = False,
    output_json: bool = False,
    no_color: bool = False,
) -> None:
    """Audit indexed content against source files.

    Compares source files on disk with what's stored in the database.
    Shows extraction quality, chunk counts, and identifies any data loss.

    Args:
        path: Filter by source path
        document_id: Filter by document ID prefix
        show_missing: Only show documents with missing sources
        show_quality: Include quality scores (slower)
        output_json: Output as JSON
        no_color: Disable colour output
    """
    from ragd.config import load_config
    from ragd.storage import ChromaStore

    con = get_console(no_color)
    config = load_config()

    store = ChromaStore(config.chroma_path)

    # Get all indexed documents
    documents = store.list_documents()

    if not documents:
        if output_json:
            con.print(json.dumps({"total": 0, "results": []}, indent=2))
        else:
            con.print("[yellow]No documents indexed yet.[/yellow]")
        return

    results: list[ContentAuditResult] = []

    for doc in documents:
        source_path = Path(doc.path)
        source_exists = source_path.exists()
        source_size = source_path.stat().st_size if source_exists else None

        # Get extraction method and quality warning from metadata
        extraction_method = None
        quality_warning = None
        if doc.metadata:
            extraction_method = doc.metadata.get("extraction_method")
            quality_warning = doc.metadata.get("quality_warning")
            # Also check for OCR quality in nested metadata
            if not quality_warning and doc.metadata.get("ocr_quality") == "poor":
                quality_warning = "OCR quality poor - text may be unreliable"

        # Identify issues
        issues: list[str] = []
        if not source_exists:
            issues.append("Source file missing")
        if doc.chunk_count == 0:
            issues.append("No chunks extracted")
        if quality_warning:
            issues.append(quality_warning)

        results.append(
            ContentAuditResult(
                document_id=doc.document_id,
                filename=doc.filename,
                source_path=str(source_path),
                source_exists=source_exists,
                source_size=source_size,
                indexed_chunks=doc.chunk_count,
                extraction_method=extraction_method,
                quality_warning=quality_warning,
                issues=issues,
            )
        )

    # Apply filters
    if show_missing:
        results = [r for r in results if not r.source_exists]
    if path:
        path_str = str(path.resolve())
        results = [r for r in results if r.source_path.startswith(path_str)]
    if document_id:
        results = [r for r in results if r.document_id.startswith(document_id)]

    # Output
    if output_json:
        output_data = {
            "total": len(results),
            "missing": sum(1 for r in results if not r.source_exists),
            "with_issues": sum(1 for r in results if r.issues),
            "results": [asdict(r) for r in results],
        }
        con.print(json.dumps(output_data, indent=2))
        return

    # Summary statistics
    total = len(results)
    missing = sum(1 for r in results if not r.source_exists)
    issues_count = sum(1 for r in results if r.issues)

    con.print("\n[bold]Content Audit[/bold]\n")
    con.print(f"Total documents: {total}")
    con.print(f"Missing sources: {missing}")
    con.print(f"Documents with issues: {issues_count}")

    if not results:
        con.print("\n[dim]No documents match the filter criteria.[/dim]")
        return

    # Detailed table
    table = Table(title="Document Status", show_lines=False)
    table.add_column("Document", style="cyan", max_width=35)
    table.add_column("Source", justify="center", width=6)
    table.add_column("Chunks", justify="right", width=6)
    table.add_column("Method", max_width=15)
    table.add_column("Issues", style="yellow")

    display_limit = 50
    for r in results[:display_limit]:
        source_status = "[green]✓[/green]" if r.source_exists else "[red]✗[/red]"
        issues_str = "; ".join(r.issues) if r.issues else "[green]OK[/green]"

        # Truncate filename if too long
        filename = r.filename
        if len(filename) > 35:
            filename = filename[:32] + "..."

        table.add_row(
            filename,
            source_status,
            str(r.indexed_chunks),
            r.extraction_method or "-",
            issues_str,
        )

    con.print()
    con.print(table)

    if len(results) > display_limit:
        con.print(f"\n[dim]... and {len(results) - display_limit} more documents[/dim]")
