"""Index health check and repair (F-116, F-117).

Provides index integrity checking and self-healing capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: str  # "ok", "warning", "error"
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fixable: bool = False


@dataclass
class HealthReport:
    """Complete health report for the index."""

    checks: list[HealthCheckResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any errors exist."""
        return any(c.status == "error" for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist."""
        return any(c.status == "warning" for c in self.checks)

    @property
    def is_healthy(self) -> bool:
        """Check if index is fully healthy."""
        return not self.has_errors and not self.has_warnings

    @property
    def fixable_issues(self) -> list[HealthCheckResult]:
        """Get issues that can be auto-fixed."""
        return [c for c in self.checks if c.fixable and c.status != "ok"]


def check_database_exists(data_dir: Path) -> HealthCheckResult:
    """Check if database file exists.

    Args:
        data_dir: Path to data directory

    Returns:
        Health check result
    """
    db_path = data_dir / "ragd.db"

    if not db_path.exists():
        return HealthCheckResult(
            name="Database",
            status="error",
            message="Database file not found",
            details={"path": str(db_path)},
            fixable=False,
        )

    return HealthCheckResult(
        name="Database",
        status="ok",
        message="Database file exists",
        details={"path": str(db_path), "size_mb": db_path.stat().st_size / (1024 * 1024)},
    )


def check_vector_store(data_dir: Path) -> HealthCheckResult:
    """Check vector store health.

    Args:
        data_dir: Path to data directory

    Returns:
        Health check result
    """
    chroma_path = data_dir / "chroma"

    if not chroma_path.exists():
        return HealthCheckResult(
            name="Vector Store",
            status="warning",
            message="Vector store directory not found",
            details={"path": str(chroma_path)},
            fixable=True,
        )

    # Count files
    file_count = sum(1 for _ in chroma_path.rglob("*") if _.is_file())

    return HealthCheckResult(
        name="Vector Store",
        status="ok",
        message="Vector store exists",
        details={"path": str(chroma_path), "files": file_count},
    )


def check_document_integrity(data_dir: Path) -> HealthCheckResult:
    """Check document-chunk integrity.

    Args:
        data_dir: Path to data directory

    Returns:
        Health check result
    """
    db_path = data_dir / "ragd.db"

    if not db_path.exists():
        return HealthCheckResult(
            name="Document Integrity",
            status="error",
            message="Cannot check - database not found",
        )

    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check for orphaned chunks
        cursor.execute("""
            SELECT COUNT(*)
            FROM chunks c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE d.id IS NULL
        """)
        row = cursor.fetchone()
        orphaned = row[0] if row else 0

    except sqlite3.OperationalError:
        conn.close()
        return HealthCheckResult(
            name="Document Integrity",
            status="warning",
            message="Could not verify integrity (schema mismatch)",
        )

    conn.close()

    if orphaned > 0:
        return HealthCheckResult(
            name="Document Integrity",
            status="warning",
            message=f"{orphaned} orphaned chunks found",
            details={"orphaned_chunks": orphaned},
            fixable=True,
        )

    return HealthCheckResult(
        name="Document Integrity",
        status="ok",
        message="All chunks have valid documents",
    )


def check_config(data_dir: Path) -> HealthCheckResult:
    """Check configuration file.

    Args:
        data_dir: Path to data directory

    Returns:
        Health check result
    """
    config_path = data_dir / "config.yaml"

    if not config_path.exists():
        return HealthCheckResult(
            name="Configuration",
            status="warning",
            message="Configuration file not found (using defaults)",
            details={"path": str(config_path)},
        )

    return HealthCheckResult(
        name="Configuration",
        status="ok",
        message="Configuration file exists",
        details={"path": str(config_path)},
    )


def run_health_checks(data_dir: Path | None = None) -> HealthReport:
    """Run all health checks.

    Args:
        data_dir: Path to data directory

    Returns:
        Complete health report
    """
    if data_dir is None:
        data_dir = Path.home() / ".ragd"

    report = HealthReport()

    # Run each check
    report.checks.append(check_database_exists(data_dir))
    report.checks.append(check_vector_store(data_dir))
    report.checks.append(check_document_integrity(data_dir))
    report.checks.append(check_config(data_dir))

    return report


def format_health_report(report: HealthReport, console: Console) -> None:
    """Format health report for display.

    Args:
        report: Health report
        console: Console for output
    """
    table = Table(title="Index Health Check")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Message")

    for check in report.checks:
        if check.status == "ok":
            status = "[green]✓ OK[/green]"
        elif check.status == "warning":
            status = "[yellow]⚠ Warning[/yellow]"
        else:
            status = "[red]✗ Error[/red]"

        table.add_row(check.name, status, check.message)

    console.print(table)

    if report.is_healthy:
        console.print("\n[green]Index is healthy![/green]")
    elif report.has_errors:
        console.print("\n[red]Index has errors that need attention.[/red]")
    else:
        console.print("\n[yellow]Index has warnings.[/yellow]")

    fixable = report.fixable_issues
    if fixable:
        console.print(f"\n[dim]{len(fixable)} issue(s) can be auto-fixed with --fix[/dim]")


def fix_orphaned_chunks(data_dir: Path) -> int:
    """Remove orphaned chunks.

    Args:
        data_dir: Path to data directory

    Returns:
        Number of chunks removed
    """
    db_path = data_dir / "ragd.db"

    if not db_path.exists():
        return 0

    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM chunks
            WHERE document_id NOT IN (SELECT id FROM documents)
        """)
        removed = cursor.rowcount
        conn.commit()
    except sqlite3.OperationalError:
        removed = 0
    finally:
        conn.close()

    return removed


def run_auto_fix(data_dir: Path | None = None, console: Console | None = None) -> int:
    """Run auto-fix for fixable issues.

    Args:
        data_dir: Path to data directory
        console: Console for output

    Returns:
        Number of issues fixed
    """
    if data_dir is None:
        data_dir = Path.home() / ".ragd"

    if console is None:
        console = Console()

    fixed = 0

    # Fix orphaned chunks
    console.print("[dim]Checking for orphaned chunks...[/dim]")
    removed = fix_orphaned_chunks(data_dir)
    if removed > 0:
        console.print(f"[green]✓[/green] Removed {removed} orphaned chunks")
        fixed += 1

    # Create missing directories
    chroma_path = data_dir / "chroma"
    if not chroma_path.exists():
        chroma_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created vector store directory")
        fixed += 1

    if fixed == 0:
        console.print("[dim]No issues to fix.[/dim]")

    return fixed
