"""Profile CLI commands for ragd (F-123).

This module contains commands for profiling ragd performance:
- `ragd profile index` - Profile document indexing
- `ragd profile search` - Profile search operations
- `ragd profile chat` - Profile chat response times
- `ragd profile all` - Run full profile suite
- `ragd profile compare` - Compare against baseline
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from ragd.ui.cli.utils import get_console


def profile_index_command(
    path: Annotated[Path, typer.Argument(help="File or directory to profile indexing")],
    iterations: Annotated[int, typer.Option("--iterations", "-n", help="Number of iterations")] = 3,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output JSON file")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Profile document indexing performance.

    Measures timing and memory usage for indexing operations.
    """
    from ragd.config import load_config
    from ragd.performance import OperationProfiler, ProfileSession
    from ragd.performance.reports import print_profile_report

    con = get_console(no_color)
    config = load_config()

    if not path.exists():
        con.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    con.print(f"[bold]Profiling indexing: {path}[/bold]")
    con.print(f"Iterations: {iterations}")
    con.print()

    with ProfileSession(f"index_profile_{path.name}", track_memory=True) as session:
        for i in range(iterations):
            con.print(f"[dim]Iteration {i + 1}/{iterations}...[/dim]")

            # Import indexing components
            from ragd.chunking import chunk_document
            from ragd.embedding import get_embedder
            from ragd.ingestion import DocumentProcessor
            from ragd.storage import ChromaStore

            processor = DocumentProcessor(config=config)
            embedder = get_embedder(
                model_name=config.embedding.model,
                device=config.embedding.device,
            )

            # Profile parsing
            with OperationProfiler("parsing", session):
                result = processor.process_file(path)

            if result.success and result.document:
                # Profile chunking
                with OperationProfiler("chunking", session):
                    chunks = chunk_document(
                        result.document,
                        config.chunking.strategy,
                        config.chunking.chunk_size,
                        config.chunking.chunk_overlap,
                    )

                # Profile embedding
                with OperationProfiler("embedding", session):
                    texts = [c.content for c in chunks]
                    _embeddings = embedder.embed(texts)  # noqa: F841

                # Profile storage (dry run - don't actually store)
                with OperationProfiler("storage", session, track_memory=False):
                    # Just measure time to create store connection
                    store = ChromaStore(config.chroma_path)
                    _ = store.get_stats()

        session.metadata["path"] = str(path)
        session.metadata["iterations"] = iterations

    print_profile_report(session, console=con)

    if output:
        session.export_json(output)
        con.print(f"[dim]Profile saved to {output}[/dim]")


def profile_search_command(
    query: Annotated[str, typer.Argument(help="Search query to profile")],
    iterations: Annotated[int, typer.Option("--iterations", "-n", help="Number of iterations")] = 10,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output JSON file")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Profile search performance.

    Measures search latency across multiple iterations.
    """
    from ragd.config import load_config
    from ragd.performance import OperationProfiler, ProfileSession
    from ragd.performance.metrics import calculate_percentiles
    from ragd.performance.reports import print_profile_report

    con = get_console(no_color)
    config = load_config()

    con.print(f"[bold]Profiling search: \"{query}\"[/bold]")
    con.print(f"Iterations: {iterations}")
    con.print()

    with ProfileSession("search_profile", track_memory=True) as session:
        from ragd.embedding import get_embedder
        from ragd.storage import ChromaStore

        embedder = get_embedder(
            model_name=config.embedding.model,
            device=config.embedding.device,
        )
        store = ChromaStore(config.chroma_path)

        for i in range(iterations):
            # Profile embedding
            with OperationProfiler("query_embedding", session):
                query_vec = embedder.embed([query])[0]

            # Profile search
            with OperationProfiler("vector_search", session):
                results = store.search(query_vec, limit=10)

            # Profile total latency
            with OperationProfiler("total_latency", session):
                query_vec = embedder.embed([query])[0]
                results = store.search(query_vec, limit=10)

        session.metadata["query"] = query
        session.metadata["iterations"] = iterations
        session.metadata["result_count"] = len(results)

    print_profile_report(session, console=con)

    # Show percentiles
    summary = session.get_summary()
    if "total_latency" in summary:
        times = [r.duration_ms for r in session.get_results_by_operation("total_latency")]
        percentiles = calculate_percentiles(times)
        con.print("\n[bold]Latency Percentiles:[/bold]")
        con.print(f"  p50: {percentiles['p50']:.1f}ms")
        con.print(f"  p95: {percentiles['p95']:.1f}ms")
        con.print(f"  p99: {percentiles['p99']:.1f}ms")

    if output:
        session.export_json(output)
        con.print(f"\n[dim]Profile saved to {output}[/dim]")


def profile_chat_command(
    question: Annotated[str, typer.Argument(help="Question to profile")],
    iterations: Annotated[int, typer.Option("--iterations", "-n", help="Number of iterations")] = 3,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output JSON file")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Profile chat/ask response time.

    Measures timing for context retrieval and LLM response.
    """
    from ragd.config import load_config
    from ragd.performance import OperationProfiler, ProfileSession
    from ragd.performance.reports import print_profile_report

    con = get_console(no_color)
    config = load_config()

    con.print(f"[bold]Profiling chat: \"{question}\"[/bold]")
    con.print(f"Iterations: {iterations}")
    con.print()

    with ProfileSession("chat_profile", track_memory=True) as session:
        from ragd.embedding import get_embedder
        from ragd.llm.ollama import OllamaLLM, check_ollama_available
        from ragd.storage import ChromaStore

        embedder = get_embedder(
            model_name=config.embedding.model,
            device=config.embedding.device,
        )
        store = ChromaStore(config.chroma_path)

        # Check Ollama
        ollama_available, _ = check_ollama_available()
        if not ollama_available:
            con.print("[yellow]Warning: Ollama not available, skipping LLM profiling[/yellow]")
            llm = None
        else:
            llm = OllamaLLM(
                model=config.llm.model,
                base_url=config.llm.base_url,
            )

        for i in range(iterations):
            con.print(f"[dim]Iteration {i + 1}/{iterations}...[/dim]")

            # Profile context retrieval
            with OperationProfiler("context_retrieval", session):
                query_vec = embedder.embed([question])[0]
                results = store.search(query_vec, limit=5)

            # Profile LLM response
            if llm:
                context = "\n".join([r.content for r in results[:3]])
                with OperationProfiler("llm_response", session):
                    _response = llm.chat(  # noqa: F841
                        messages=[{"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}],
                    )

        session.metadata["question"] = question
        session.metadata["iterations"] = iterations
        session.metadata["ollama_available"] = ollama_available

    print_profile_report(session, console=con)

    if output:
        session.export_json(output)
        con.print(f"\n[dim]Profile saved to {output}[/dim]")


def profile_all_command(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output JSON file")] = Path("profile.json"),
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Run full profile suite.

    Profiles indexing, search, and chat operations.
    """
    from ragd.config import load_config
    from ragd.performance import OperationProfiler, ProfileSession
    from ragd.performance.reports import print_profile_report

    con = get_console(no_color)
    config = load_config()

    con.print("[bold]Running full profile suite...[/bold]\n")

    with ProfileSession("full_profile", track_memory=True) as session:
        from ragd.embedding import get_embedder
        from ragd.storage import ChromaStore

        # Profile embedding model load
        with OperationProfiler("model_load", session):
            embedder = get_embedder(
                model_name=config.embedding.model,
                device=config.embedding.device,
            )

        # Profile storage init
        with OperationProfiler("storage_init", session):
            store = ChromaStore(config.chroma_path)

        # Profile embedding
        test_texts = ["This is a test query for profiling embedding performance."]
        with OperationProfiler("embedding", session):
            embedder.embed(test_texts)

        # Profile search
        query_vec = embedder.embed(test_texts)[0]
        with OperationProfiler("search", session):
            store.search(query_vec, limit=10)

        # Profile stats
        with OperationProfiler("get_stats", session):
            store.get_stats()

    print_profile_report(session, console=con)
    session.export_json(output)
    con.print(f"[dim]Full profile saved to {output}[/dim]")


def profile_compare_command(
    baseline: Annotated[Path, typer.Argument(help="Baseline profile JSON")],
    current: Annotated[Path | None, typer.Argument(help="Current profile JSON (optional, runs new profile if omitted)")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Compare profile against baseline.

    Shows regression/improvement analysis.
    """
    from ragd.performance import ProfileSession
    from ragd.performance.profiler import compare_profiles
    from ragd.performance.reports import print_comparison_report

    con = get_console(no_color)

    if not baseline.exists():
        con.print(f"[red]Error: Baseline file not found: {baseline}[/red]")
        raise typer.Exit(1)

    baseline_session = ProfileSession.import_json(baseline)

    if current:
        if not current.exists():
            con.print(f"[red]Error: Current file not found: {current}[/red]")
            raise typer.Exit(1)
        current_session = ProfileSession.import_json(current)
    else:
        # Run a new profile
        con.print("[dim]Running new profile for comparison...[/dim]\n")
        profile_all_command(output=Path("current_profile.json"), no_color=no_color)
        current_session = ProfileSession.import_json(Path("current_profile.json"))

    comparison = compare_profiles(baseline_session, current_session)
    print_comparison_report(comparison, console=con)

    # Exit with error if regressions detected
    operations = comparison.get("operations", {})
    regressions = sum(1 for op in operations.values() if op.get("status") == "regression")
    if regressions > 0:
        con.print(f"\n[red]Error: {regressions} performance regression(s) detected[/red]")
        raise typer.Exit(1)


def profile_startup_command(
    iterations: Annotated[int, typer.Option("--iterations", "-n", help="Number of iterations")] = 10,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output JSON file")] = None,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Profile CLI startup time.

    Measures cold and warm startup performance.
    """
    import statistics
    import subprocess
    import time

    con = get_console(no_color)

    con.print("[bold]Profiling CLI startup time...[/bold]")
    con.print(f"Iterations: {iterations}")
    con.print()

    # Measure ragd --version startup time
    version_times = []
    help_times = []

    for i in range(iterations):
        # Cold start (version)
        start = time.perf_counter()
        subprocess.run(["ragd", "--version"], capture_output=True)
        version_times.append((time.perf_counter() - start) * 1000)

        # Cold start (help)
        start = time.perf_counter()
        subprocess.run(["ragd", "--help"], capture_output=True)
        help_times.append((time.perf_counter() - start) * 1000)

    # Results
    con.print("\n[bold]Results:[/bold]")

    con.print("\nragd --version:")
    con.print(f"  Mean: {statistics.mean(version_times):.0f}ms")
    con.print(f"  Median: {statistics.median(version_times):.0f}ms")
    con.print(f"  Min: {min(version_times):.0f}ms")
    con.print(f"  Max: {max(version_times):.0f}ms")

    con.print("\nragd --help:")
    con.print(f"  Mean: {statistics.mean(help_times):.0f}ms")
    con.print(f"  Median: {statistics.median(help_times):.0f}ms")
    con.print(f"  Min: {min(help_times):.0f}ms")
    con.print(f"  Max: {max(help_times):.0f}ms")

    # Check against target
    version_mean = statistics.mean(version_times)
    target = 500
    if version_mean < target:
        con.print(f"\n[green]SUCCESS: Startup time ({version_mean:.0f}ms) is below target ({target}ms)[/green]")
    else:
        con.print(f"\n[red]FAIL: Startup time ({version_mean:.0f}ms) exceeds target ({target}ms)[/red]")

    if output:
        data = {
            "version_times_ms": version_times,
            "help_times_ms": help_times,
            "version_mean_ms": statistics.mean(version_times),
            "help_mean_ms": statistics.mean(help_times),
            "iterations": iterations,
            "target_ms": target,
            "passed": version_mean < target,
        }
        output.write_text(json.dumps(data, indent=2))
        con.print(f"\n[dim]Results saved to {output}[/dim]")


__all__ = [
    "profile_index_command",
    "profile_search_command",
    "profile_chat_command",
    "profile_all_command",
    "profile_compare_command",
    "profile_startup_command",
]
