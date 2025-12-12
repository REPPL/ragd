"""Output formatting for ragd.

This module provides formatters for different output modes (Rich, Plain, JSON).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from ragd.health.checker import HealthResult
    from ragd.ingestion.pipeline import IndexResult
    from ragd.search.searcher import SearchResult

OutputFormat = Literal["rich", "plain", "json"]
CitationStyleOption = Literal["none", "inline", "apa", "mla", "chicago", "bibtex", "markdown"]


def format_search_results(
    results: list[SearchResult],
    query: str,
    output_format: OutputFormat = "rich",
    console: Console | None = None,
    citation_style: CitationStyleOption = "none",
) -> str | None:
    """Format search results for display.

    Args:
        results: List of search results
        query: Original query string
        output_format: Output format (rich, plain, json)
        console: Rich console for rich output
        citation_style: Citation format to include (none disables)

    Returns:
        Formatted string for plain/json, None for rich (printed directly)
    """
    # Generate citations if requested
    citations = []
    if citation_style != "none" and results:
        from ragd.citation import Citation, format_citation

        citations = [
            format_citation(Citation.from_search_result(r), citation_style)
            for r in results
        ]

    if output_format == "json":
        result_data = []
        for i, r in enumerate(results):
            item = {
                "content": r.content,
                "score": round(r.score, 4),
                "document": r.document_name,
                "chunk_index": r.chunk_index,
            }
            if citations:
                item["citation"] = citations[i]
            result_data.append(item)

        return json.dumps(
            {
                "query": query,
                "count": len(results),
                "citation_style": citation_style,
                "results": result_data,
            },
            indent=2,
        )

    if output_format == "plain":
        lines = [f"Query: {query}", f"Results: {len(results)}", ""]
        for i, r in enumerate(results):
            lines.extend(
                [
                    f"[{i + 1}] Score: {r.score:.4f} | Source: {r.document_name}",
                    r.content[:500] + "..." if len(r.content) > 500 else r.content,
                ]
            )
            if citations:
                lines.append(f"    Citation: {citations[i]}")
            lines.append("")
        return "\n".join(lines)

    # Rich format
    if console is None:
        console = Console()

    if not results:
        console.print(f"[yellow]No results found for:[/yellow] {query}")
        return None

    from ragd.ui.styles import print_search_header

    print_search_header(console, query, len(results))

    for i, r in enumerate(results):
        # Create score colour based on value
        if r.score >= 0.8:
            score_colour = "green"
        elif r.score >= 0.6:
            score_colour = "yellow"
        else:
            score_colour = "red"

        # Truncate content for display
        content = r.content[:500] + "..." if len(r.content) > 500 else r.content

        # Add citation if enabled
        subtitle = f"Chunk {r.chunk_index}"
        if citations:
            subtitle = f"{subtitle} | {citations[i]}"

        panel = Panel(
            content,
            title=f"[{score_colour}]{r.score:.4f}[/{score_colour}] | {r.document_name}",
            subtitle=subtitle,
            border_style="dim",
        )
        console.print(panel)

    # Print citation list at end if BibTeX
    if citation_style == "bibtex" and citations:
        console.print("\n[bold]BibTeX Citations:[/bold]")
        for citation in citations:
            console.print(f"[dim]{citation}[/dim]")

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

    # Rich format with Table
    if console is None:
        console = Console()

    # Determine overall status
    has_unhealthy = any(r.status == "unhealthy" for r in results)
    has_degraded = any(r.status == "degraded" for r in results)

    if has_unhealthy:
        overall = "UNHEALTHY"
        overall_colour = "red"
    elif has_degraded:
        overall = "DEGRADED"
        overall_colour = "yellow"
    else:
        overall = "HEALTHY"
        overall_colour = "green"

    # Categorise checks
    core_checks = ["Configuration", "Storage", "Embedding Model", "Dependencies"]
    optional_checks = ["Docling", "OCR", "Ollama", "NLTK Data"]

    # Build table
    table = Table(
        title="System Health",
        show_header=False,
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Icon", width=4)
    table.add_column("Component", width=20)
    table.add_column("Message")

    # Overall status row
    table.add_row("", f"Overall: [{overall_colour}]{overall}[/{overall_colour}]", "")
    table.add_section()

    # Core components header
    table.add_row("", "[bold]Core Components:[/bold]", "")

    for r in results:
        if r.name in core_checks or r.name not in optional_checks:
            if r.status == "healthy":
                icon = "[green][OK][/green]"
            elif r.status == "degraded":
                icon = "[yellow][!!][/yellow]"
            else:
                icon = "[red][XX][/red]"

            msg = r.message[:40] + "..." if len(r.message) > 40 else r.message
            table.add_row(icon, r.name, msg)

    # Optional features if any exist
    optional_results = [r for r in results if r.name in optional_checks]
    if optional_results:
        table.add_section()
        table.add_row("", "[bold]Optional Features:[/bold]", "")

        for r in optional_results:
            if r.status == "healthy":
                icon = "[green][OK][/green]"
            elif r.status == "degraded":
                icon = "[yellow][!!][/yellow]"
            else:
                icon = "[red][XX][/red]"

            msg = r.message[:40] + "..." if len(r.message) > 40 else r.message
            table.add_row(icon, r.name, msg)

    console.print()
    console.print(table)
    return None
