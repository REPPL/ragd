"""Index statistics functionality (F-109).

Provides detailed statistics about the ragd index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


@dataclass
class IndexStatistics:
    """Detailed statistics about the index."""

    # Document counts
    total_documents: int = 0
    total_chunks: int = 0

    # By file type
    documents_by_type: dict[str, int] = field(default_factory=dict)

    # Size information
    total_size_bytes: int = 0
    index_size_bytes: int = 0

    # Timing
    last_indexed_at: str | None = None
    oldest_document: str | None = None
    newest_document: str | None = None

    # Health metrics
    orphaned_chunks: int = 0
    missing_embeddings: int = 0

    @property
    def total_size_mb(self) -> float:
        """Total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)

    @property
    def index_size_mb(self) -> float:
        """Index size in megabytes."""
        return self.index_size_bytes / (1024 * 1024)

    @property
    def average_chunks_per_doc(self) -> float:
        """Average chunks per document."""
        if self.total_documents == 0:
            return 0.0
        return self.total_chunks / self.total_documents


def get_index_statistics(data_dir: Path | None = None) -> IndexStatistics:
    """Gather detailed statistics about the index.

    Args:
        data_dir: Path to ragd data directory

    Returns:
        IndexStatistics with all metrics
    """
    if data_dir is None:
        data_dir = Path.home() / ".ragd"

    stats = IndexStatistics()

    # Check database
    db_path = data_dir / "ragd.db"
    if not db_path.exists():
        return stats

    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Document counts
        cursor.execute("SELECT COUNT(*) FROM documents")
        row = cursor.fetchone()
        stats.total_documents = row[0] if row else 0

        # Chunk counts
        cursor.execute("SELECT COUNT(*) FROM chunks")
        row = cursor.fetchone()
        stats.total_chunks = row[0] if row else 0

        # Documents by file type
        cursor.execute("""
            SELECT
                COALESCE(
                    SUBSTR(path, INSTR(path, '.') + 1),
                    'unknown'
                ) as ext,
                COUNT(*) as count
            FROM documents
            GROUP BY ext
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            ext = row[0].lower() if row[0] else "unknown"
            stats.documents_by_type[ext] = row[1]

        # Timing information
        cursor.execute("SELECT MAX(indexed_at), MIN(indexed_at) FROM documents")
        row = cursor.fetchone()
        if row:
            stats.last_indexed_at = row[0]
            stats.oldest_document = row[1]

    except sqlite3.OperationalError:
        # Table doesn't exist or schema mismatch
        pass
    finally:
        conn.close()

    # File sizes
    if db_path.exists():
        stats.index_size_bytes = db_path.stat().st_size

    # Vector store size
    vector_path = data_dir / "chroma"
    if vector_path.exists():
        for file in vector_path.rglob("*"):
            if file.is_file():
                stats.index_size_bytes += file.stat().st_size

    return stats


def format_statistics_table(stats: IndexStatistics, console: Console) -> None:
    """Format statistics as a rich table.

    Args:
        stats: Index statistics
        console: Console for output
    """
    # Main statistics panel
    main_table = Table(show_header=False, box=None, padding=(0, 2))
    main_table.add_column("Metric", style="bold")
    main_table.add_column("Value", style="cyan")

    main_table.add_row("Total Documents", f"{stats.total_documents:,}")
    main_table.add_row("Total Chunks", f"{stats.total_chunks:,}")
    main_table.add_row("Avg Chunks/Doc", f"{stats.average_chunks_per_doc:.1f}")
    main_table.add_row("Index Size", f"{stats.index_size_mb:.2f} MB")

    if stats.last_indexed_at:
        main_table.add_row("Last Indexed", stats.last_indexed_at[:19])

    console.print(Panel(main_table, title="Index Statistics", border_style="blue"))

    # Documents by type
    if stats.documents_by_type:
        type_table = Table(title="Documents by Type")
        type_table.add_column("Type", style="bold")
        type_table.add_column("Count", justify="right", style="cyan")
        type_table.add_column("Percentage", justify="right")

        total = stats.total_documents
        for ext, count in sorted(stats.documents_by_type.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            type_table.add_row(ext.upper(), f"{count:,}", f"{pct:.1f}%")

        console.print()
        console.print(type_table)


def format_statistics_json(stats: IndexStatistics) -> dict[str, Any]:
    """Format statistics as JSON-serialisable dict.

    Args:
        stats: Index statistics

    Returns:
        Dictionary for JSON output
    """
    return {
        "documents": {
            "total": stats.total_documents,
            "by_type": stats.documents_by_type,
        },
        "chunks": {
            "total": stats.total_chunks,
            "average_per_document": stats.average_chunks_per_doc,
        },
        "storage": {
            "index_size_bytes": stats.index_size_bytes,
            "index_size_mb": stats.index_size_mb,
        },
        "timing": {
            "last_indexed": stats.last_indexed_at,
            "oldest_document": stats.oldest_document,
        },
        "health": {
            "orphaned_chunks": stats.orphaned_chunks,
            "missing_embeddings": stats.missing_embeddings,
        },
    }


def format_statistics_plain(stats: IndexStatistics) -> str:
    """Format statistics as plain text.

    Args:
        stats: Index statistics

    Returns:
        Plain text output
    """
    lines = [
        "Index Statistics",
        "================",
        f"Documents: {stats.total_documents:,}",
        f"Chunks: {stats.total_chunks:,}",
        f"Avg chunks/doc: {stats.average_chunks_per_doc:.1f}",
        f"Index size: {stats.index_size_mb:.2f} MB",
    ]

    if stats.last_indexed_at:
        lines.append(f"Last indexed: {stats.last_indexed_at[:19]}")

    if stats.documents_by_type:
        lines.append("")
        lines.append("By Type:")
        for ext, count in sorted(stats.documents_by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  {ext.upper()}: {count:,}")

    return "\n".join(lines)
