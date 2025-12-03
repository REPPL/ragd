"""Backend CLI commands for ragd.

This module provides CLI commands for managing vector store backends,
including show, list, set, health checks, and migration.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragd.config import load_config
from ragd.storage import (
    BackendType,
    VectorStoreFactory,
    create_vector_store,
    get_factory,
)

if TYPE_CHECKING:
    from ragd.storage.protocols import VectorStore


def get_console(no_color: bool = False) -> Console:
    """Get Rich console with optional colour."""
    return Console(force_terminal=not no_color, no_color=no_color)


def backend_show_command(
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """Show current backend information.

    Args:
        output_format: Output format (rich, plain, json)
        no_color: Disable colour output
    """
    console = get_console(no_color)
    config = load_config()

    # Get current backend from config or default
    current_backend = getattr(config, "storage_backend", "chromadb")
    if isinstance(current_backend, BackendType):
        current_backend = current_backend.value

    # Create store to get stats
    try:
        store = create_vector_store(
            backend=current_backend,
            persist_directory=config.chroma_path,
            dimension=config.embedding.dimension,
        )
        stats = store.get_stats()
        health = store.health_check()
    except Exception as e:
        if output_format == "json":
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error accessing backend: {e}[/red]")
        return

    if output_format == "json":
        console.print(
            json.dumps(
                {
                    "backend": current_backend,
                    "status": health.status.value,
                    "document_count": stats.document_count,
                    "chunk_count": stats.chunk_count,
                    "dimension": stats.dimension,
                    "index_size_bytes": stats.index_size_bytes,
                    "path": str(config.chroma_path),
                }
            )
        )
        return

    if output_format == "plain":
        console.print(f"Backend: {current_backend}")
        console.print(f"Status: {health.status.value}")
        console.print(f"Documents: {stats.document_count}")
        console.print(f"Chunks: {stats.chunk_count}")
        console.print(f"Dimension: {stats.dimension}")
        console.print(f"Path: {config.chroma_path}")
        return

    # Rich format
    status_colour = {
        "healthy": "green",
        "degraded": "yellow",
        "unhealthy": "red",
        "unknown": "dim",
    }.get(health.status.value, "white")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    table.add_row("Backend", Text(current_backend, style="bold"))
    table.add_row("Status", Text(health.status.value.upper(), style=status_colour))
    table.add_row("Documents", str(stats.document_count))
    table.add_row("Chunks", str(stats.chunk_count))
    table.add_row("Dimension", str(stats.dimension or "N/A"))
    if stats.index_size_bytes:
        size_mb = stats.index_size_bytes / (1024 * 1024)
        table.add_row("Index Size", f"{size_mb:.1f} MB")
    table.add_row("Path", str(config.chroma_path))

    console.print(Panel(table, title="Current Backend", border_style="blue"))


def backend_list_command(
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """List available backends.

    Args:
        output_format: Output format (rich, plain, json)
        no_color: Disable colour output
    """
    console = get_console(no_color)
    factory = get_factory()
    config = load_config()

    # Get current backend
    current_backend = getattr(config, "storage_backend", "chromadb")
    if isinstance(current_backend, BackendType):
        current_backend = current_backend.value

    backends = []
    for backend in BackendType:
        available = factory.is_available(backend)
        is_current = backend.value == current_backend

        backends.append(
            {
                "name": backend.value,
                "available": available,
                "current": is_current,
                "install": (
                    f"pip install ragd[{backend.value}]" if not available else None
                ),
            }
        )

    if output_format == "json":
        console.print(json.dumps(backends))
        return

    if output_format == "plain":
        for b in backends:
            status = "✓" if b["available"] else "✗"
            current = " (current)" if b["current"] else ""
            console.print(f"{status} {b['name']}{current}")
        return

    # Rich format
    table = Table(title="Available Backends")
    table.add_column("Backend", style="cyan")
    table.add_column("Status")
    table.add_column("Install Command", style="dim")

    for b in backends:
        name = b["name"]
        if b["current"]:
            name += " [bold](current)[/bold]"

        if b["available"]:
            status = Text("✓ Available", style="green")
            install = "-"
        else:
            status = Text("✗ Not installed", style="red")
            install = b["install"] or ""

        table.add_row(name, status, install)

    console.print(table)


def backend_health_command(
    backend: str | None = None,
    all_backends: bool = False,
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """Run health checks on backends.

    Args:
        backend: Specific backend to check (or current if None)
        all_backends: Check all available backends
        output_format: Output format (rich, plain, json)
        no_color: Disable colour output
    """
    console = get_console(no_color)
    factory = get_factory()
    config = load_config()

    backends_to_check = []

    if all_backends:
        backends_to_check = factory.list_available()
    elif backend:
        try:
            backends_to_check = [BackendType(backend)]
        except ValueError:
            console.print(f"[red]Unknown backend: {backend}[/red]")
            return
    else:
        # Current backend
        current = getattr(config, "storage_backend", "chromadb")
        if isinstance(current, str):
            current = BackendType(current)
        backends_to_check = [current]

    results = []
    for bt in backends_to_check:
        if not factory.is_available(bt):
            results.append(
                {
                    "backend": bt.value,
                    "status": "unavailable",
                    "message": f"Not installed. Install with: pip install ragd[{bt.value}]",
                }
            )
            continue

        try:
            store = factory.create(
                backend=bt,
                persist_directory=config.chroma_path,
                dimension=config.embedding.dimension,
            )
            health = store.health_check()
            results.append(
                {
                    "backend": bt.value,
                    "status": health.status.value,
                    "message": health.message,
                    "latency_ms": health.latency_ms,
                    "details": health.details,
                }
            )
        except Exception as e:
            results.append(
                {
                    "backend": bt.value,
                    "status": "error",
                    "message": str(e),
                }
            )

    if output_format == "json":
        console.print(json.dumps(results))
        return

    if output_format == "plain":
        for r in results:
            console.print(f"{r['backend']}: {r['status']} - {r['message']}")
        return

    # Rich format
    for r in results:
        status_colour = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red",
            "unavailable": "dim",
            "error": "red",
        }.get(r["status"], "white")

        lines = [
            f"[{status_colour}]Status: {r['status'].upper()}[/{status_colour}]",
            f"Message: {r['message']}",
        ]

        if r.get("latency_ms"):
            lines.append(f"Latency: {r['latency_ms']:.1f}ms")

        if r.get("details"):
            for k, v in r["details"].items():
                lines.append(f"{k}: {v}")

        console.print(
            Panel(
                "\n".join(lines),
                title=f"Backend: {r['backend']}",
                border_style=status_colour,
            )
        )


def backend_set_command(
    backend: str,
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """Set the default backend.

    Args:
        backend: Backend to set as default
        output_format: Output format (rich, plain, json)
        no_color: Disable colour output
    """
    console = get_console(no_color)
    factory = get_factory()

    # Validate backend
    try:
        backend_type = BackendType(backend)
    except ValueError:
        console.print(f"[red]Unknown backend: {backend}[/red]")
        console.print(f"Available: {', '.join(b.value for b in BackendType)}")
        return

    if not factory.is_available(backend_type):
        console.print(
            f"[red]Backend '{backend}' is not installed.[/red]\n"
            f"Install with: pip install ragd[{backend}]"
        )
        return

    # Update config
    config = load_config()
    config_path = config.get_config_path()

    # Read current config
    import yaml

    if config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f) or {}
    else:
        config_data = {}

    # Update storage backend
    config_data["storage_backend"] = backend

    # Write back
    with open(config_path, "w") as f:
        yaml.safe_dump(config_data, f, default_flow_style=False)

    if output_format == "json":
        console.print(json.dumps({"backend": backend, "status": "set"}))
    elif output_format == "plain":
        console.print(f"Backend set to: {backend}")
    else:
        console.print(f"[green]✓[/green] Default backend set to [bold]{backend}[/bold]")
        console.print("\nNote: Existing data will remain in the previous backend.")
        console.print("Use 'ragd backend migrate' to move data between backends.")


def backend_benchmark_command(
    backend: str | None = None,
    vectors: int = 1000,
    queries: int = 100,
    dimension: int = 768,
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """Run performance benchmarks on a backend.

    Args:
        backend: Backend to benchmark (or current if None)
        vectors: Number of vectors to add
        queries: Number of search queries
        dimension: Vector dimension
        output_format: Output format (rich, plain, json)
        no_color: Disable colour output
    """
    import random
    import tempfile
    from pathlib import Path

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from ragd.storage import StorageProfiler

    console = get_console(no_color)
    factory = get_factory()
    config = load_config()

    # Determine backend
    if backend:
        try:
            backend_type = BackendType(backend)
        except ValueError:
            console.print(f"[red]Unknown backend: {backend}[/red]")
            return
    else:
        backend_str = getattr(config, "storage_backend", "chromadb")
        if isinstance(backend_str, BackendType):
            backend_type = backend_str
        else:
            backend_type = BackendType(backend_str)

    if not factory.is_available(backend_type):
        console.print(f"[red]Backend '{backend_type.value}' is not available.[/red]")
        return

    console.print(f"[bold]Benchmarking {backend_type.value}...[/bold]")
    console.print(f"  Vectors: {vectors}")
    console.print(f"  Queries: {queries}")
    console.print(f"  Dimension: {dimension}")
    console.print()

    # Create temporary store for benchmarking
    with tempfile.TemporaryDirectory() as tmpdir:
        store = factory.create(
            backend=backend_type,
            persist_directory=Path(tmpdir),
            dimension=dimension,
        )

        profiler = StorageProfiler(store, backend_type.value)

        # Generate test data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Generate vectors
            progress.add_task("Generating test data...", total=None)
            test_vectors = [
                [random.random() for _ in range(dimension)]
                for _ in range(vectors)
            ]
            test_ids = [f"bench-{i}" for i in range(vectors)]
            test_contents = [f"Benchmark content {i}" for i in range(vectors)]
            test_metadatas = [{"index": i} for i in range(vectors)]

            query_vectors = [
                [random.random() for _ in range(dimension)]
                for _ in range(queries)
            ]

        # Run benchmarks
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Add benchmark
            task = progress.add_task("Benchmarking add...", total=None)
            profiler.benchmark_add(
                vectors=test_vectors,
                ids=test_ids,
                contents=test_contents,
                metadatas=test_metadatas,
                batch_size=100,
            )
            progress.remove_task(task)

            # Search benchmark
            task = progress.add_task("Benchmarking search...", total=None)
            profiler.benchmark_search(query_vectors, limit=10, iterations=1)
            progress.remove_task(task)

            # Health check benchmark
            task = progress.add_task("Benchmarking health check...", total=None)
            profiler.benchmark_health_check(iterations=10)
            progress.remove_task(task)

            # Stats benchmark
            task = progress.add_task("Benchmarking get_stats...", total=None)
            profiler.benchmark_get_stats(iterations=10)
            progress.remove_task(task)

            # Delete benchmark
            task = progress.add_task("Benchmarking delete...", total=None)
            profiler.benchmark_delete(test_ids[:100], batch_size=50)
            progress.remove_task(task)

    # Get results
    result = profiler.get_results()

    if output_format == "json":
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    if output_format == "plain":
        for name, metric in result.metrics.items():
            console.print(
                f"{name}: mean={metric.mean_ms:.2f}ms "
                f"median={metric.median_ms:.2f}ms "
                f"throughput={metric.ops_per_second:.1f} ops/sec"
            )
        return

    # Rich output
    table = Table(title=f"Benchmark Results: {backend_type.value}")
    table.add_column("Operation", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Mean (ms)", justify="right")
    table.add_column("Median (ms)", justify="right")
    table.add_column("Min/Max (ms)", justify="right")
    table.add_column("Throughput", justify="right")

    for name, metric in result.metrics.items():
        table.add_row(
            name,
            str(metric.count),
            f"{metric.mean_ms:.2f}",
            f"{metric.median_ms:.2f}",
            f"{metric.min_ms:.2f} / {metric.max_ms:.2f}",
            f"{metric.ops_per_second:.1f} ops/s",
        )

    console.print(table)

    # Summary
    if "search" in result.metrics:
        search = result.metrics["search"]
        console.print(
            f"\n[bold]Search performance:[/bold] "
            f"{search.ops_per_second:.0f} queries/second "
            f"({search.mean_ms:.2f}ms average latency)"
        )

    if "add" in result.metrics:
        add = result.metrics["add"]
        vectors_per_sec = vectors / (add.total_time_ms / 1000)
        console.print(
            f"[bold]Indexing performance:[/bold] "
            f"{vectors_per_sec:.0f} vectors/second"
        )
