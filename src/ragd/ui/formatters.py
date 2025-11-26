"""Output formatting for ragd.

This module provides formatters for different output modes (Rich, Plain, JSON).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ragd.health.checker import HealthResult
    from ragd.ingestion.pipeline import IndexResult
    from ragd.search.searcher import SearchResult

OutputFormat = Literal["rich", "plain", "json"]


def format_search_results(
    results: list[SearchResult],
    query: str,
    output_format: OutputFormat = "rich",
    console: Console | None = None,
) -> str | None:
    """Format search results for display.

    Args:
        results: List of search results
        query: Original query string
        output_format: Output format (rich, plain, json)
        console: Rich console for rich output

    Returns:
        Formatted string for plain/json, None for rich (printed directly)
    """
    if output_format == "json":
        return json.dumps(
            {
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "content": r.content,
                        "score": round(r.score, 4),
                        "document": r.document_name,
                        "chunk_index": r.chunk_index,
                    }
                    for r in results
                ],
            },
            indent=2,
        )

    if output_format == "plain":
        lines = [f"Query: {query}", f"Results: {len(results)}", ""]
        for i, r in enumerate(results, 1):
            lines.extend(
                [
                    f"[{i}] Score: {r.score:.4f} | Source: {r.document_name}",
                    r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "",
                ]
            )
        return "\n".join(lines)

    # Rich format
    if console is None:
        console = Console()

    if not results:
        console.print(f"[yellow]No results found for:[/yellow] {query}")
        return None

    console.print(f"\n[bold]Search results for:[/bold] {query}")
    console.print(f"[dim]Found {len(results)} results[/dim]\n")

    for i, r in enumerate(results, 1):
        # Create score colour based on value
        if r.score >= 0.8:
            score_colour = "green"
        elif r.score >= 0.6:
            score_colour = "yellow"
        else:
            score_colour = "red"

        # Truncate content for display
        content = r.content[:500] + "..." if len(r.content) > 500 else r.content

        panel = Panel(
            content,
            title=f"[{score_colour}]{r.score:.4f}[/{score_colour}] | {r.document_name}",
            subtitle=f"Chunk {r.chunk_index}",
            border_style="dim",
        )
        console.print(panel)

    return None


def format_status(
    stats: dict[str, Any],
    config: dict[str, Any],
    output_format: OutputFormat = "rich",
    console: Console | None = None,
) -> str | None:
    """Format status information for display.

    Args:
        stats: Storage statistics
        config: Configuration summary
        output_format: Output format
        console: Rich console

    Returns:
        Formatted string for plain/json, None for rich
    """
    if output_format == "json":
        return json.dumps(
            {
                "status": "ready",
                "stats": stats,
                "config": config,
            },
            indent=2,
        )

    if output_format == "plain":
        lines = [
            "ragd Status",
            "=" * 40,
            f"Documents indexed: {stats.get('document_count', 0)}",
            f"Chunks stored: {stats.get('chunk_count', 0)}",
            f"Embedding model: {config.get('embedding_model', 'unknown')}",
            f"Hardware tier: {config.get('tier', 'unknown')}",
            f"Data directory: {config.get('data_dir', 'unknown')}",
        ]
        return "\n".join(lines)

    # Rich format
    if console is None:
        console = Console()

    console.print("\n[bold green]ragd Status[/bold green]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("Documents indexed", str(stats.get("document_count", 0)))
    table.add_row("Chunks stored", str(stats.get("chunk_count", 0)))
    table.add_row("Embedding model", config.get("embedding_model", "unknown"))
    table.add_row("Hardware tier", config.get("tier", "unknown"))
    table.add_row("Data directory", config.get("data_dir", "unknown"))

    console.print(table)
    return None


def format_index_results(
    results: list[IndexResult],
    output_format: OutputFormat = "rich",
    console: Console | None = None,
) -> str | None:
    """Format indexing results for display.

    Args:
        results: List of index results
        output_format: Output format
        console: Rich console

    Returns:
        Formatted string for plain/json, None for rich
    """
    successful = [r for r in results if r.success and not r.skipped]
    skipped = [r for r in results if r.skipped]
    failed = [r for r in results if not r.success]

    total_chunks = sum(r.chunk_count for r in successful)

    if output_format == "json":
        return json.dumps(
            {
                "indexed": len(successful),
                "skipped": len(skipped),
                "failed": len(failed),
                "total_chunks": total_chunks,
                "results": [
                    {
                        "path": r.path,
                        "filename": r.filename,
                        "success": r.success,
                        "skipped": r.skipped,
                        "chunks": r.chunk_count,
                        "error": r.error,
                    }
                    for r in results
                ],
            },
            indent=2,
        )

    if output_format == "plain":
        lines = [
            "Indexing Complete",
            "=" * 40,
            f"Indexed: {len(successful)} documents ({total_chunks} chunks)",
            f"Skipped: {len(skipped)} (already indexed)",
            f"Failed: {len(failed)}",
        ]
        if failed:
            lines.append("\nFailures:")
            for r in failed:
                lines.append(f"  - {r.filename}: {r.error}")
        return "\n".join(lines)

    # Rich format
    if console is None:
        console = Console()

    console.print("\n[bold]Indexing Complete[/bold]\n")

    summary = Table(show_header=False, box=None)
    summary.add_column("Status", style="dim")
    summary.add_column("Count")

    summary.add_row("[green]Indexed[/green]", f"{len(successful)} ({total_chunks} chunks)")
    summary.add_row("[yellow]Skipped[/yellow]", str(len(skipped)))
    summary.add_row("[red]Failed[/red]", str(len(failed)))

    console.print(summary)

    if failed:
        console.print("\n[red]Failures:[/red]")
        for r in failed:
            console.print(f"  • {r.filename}: {r.error}")

    return None


def format_health_results(
    results: list[HealthResult],
    output_format: OutputFormat = "rich",
    console: Console | None = None,
) -> str | None:
    """Format health check results for display.

    Args:
        results: List of health results
        output_format: Output format
        console: Rich console

    Returns:
        Formatted string for plain/json, None for rich
    """
    all_healthy = all(r.status == "healthy" for r in results)

    if output_format == "json":
        return json.dumps(
            {
                "overall": "healthy" if all_healthy else "unhealthy",
                "checks": [
                    {
                        "name": r.name,
                        "status": r.status,
                        "message": r.message,
                        "duration_ms": round(r.duration_ms, 2),
                        "details": r.details,
                    }
                    for r in results
                ],
            },
            indent=2,
        )

    if output_format == "plain":
        status = "HEALTHY" if all_healthy else "UNHEALTHY"
        lines = [f"Health Status: {status}", "=" * 40]
        for r in results:
            icon = "OK" if r.status == "healthy" else "FAIL"
            lines.append(f"[{icon}] {r.name}: {r.message} ({r.duration_ms:.1f}ms)")
        return "\n".join(lines)

    # Rich format
    if console is None:
        console = Console()

    overall_status = "[green]HEALTHY[/green]" if all_healthy else "[red]UNHEALTHY[/red]"
    console.print(f"\n[bold]Health Status:[/bold] {overall_status}\n")

    table = Table()
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Message")
    table.add_column("Time", justify="right")

    for r in results:
        if r.status == "healthy":
            status_text = Text("✓", style="green")
        elif r.status == "degraded":
            status_text = Text("⚠", style="yellow")
        else:
            status_text = Text("✗", style="red")

        table.add_row(
            r.name,
            status_text,
            r.message,
            f"{r.duration_ms:.1f}ms",
        )

    console.print(table)
    return None
