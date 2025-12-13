"""Quality CLI commands for ragd.

This module contains commands for evaluating RAG quality and document extraction.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import get_console


def evaluate_command(
    query: str | None = None,
    test_file: Path | None = None,
    expected: str | None = None,
    limit: int = 5,
    threshold: float = 0.5,
    include_llm: bool = False,
    save: bool = True,
    output_format: str = "rich",
    no_color: bool = False,
) -> None:
    """Evaluate RAG quality.

    Computes retrieval metrics for a query or batch of queries.
    When --include-llm is set, also computes faithfulness and answer_relevancy.
    """
    import json

    import yaml
    from rich.table import Table

    from ragd.config import load_config
    from ragd.evaluation import (
        EvaluationConfig,
        EvaluationStorage,
        Evaluator,
        MetricType,
    )

    con = get_console(no_color)
    config = load_config()

    # Check inputs
    if query is None and test_file is None:
        con.print("[red]Error: Must provide either --query or --test-file[/red]")
        raise typer.Exit(1)

    # Create evaluation config
    metrics = [
        MetricType.CONTEXT_PRECISION,
        MetricType.RELEVANCE_SCORE,
    ]

    eval_config = EvaluationConfig(
        metrics=metrics,
        relevance_threshold=threshold,
        search_limit=limit,
        include_llm_metrics=include_llm,
    )

    evaluator = Evaluator(config=config, eval_config=eval_config)
    storage = EvaluationStorage() if save else None

    try:
        if test_file:
            # Batch evaluation from file
            if not test_file.exists():
                con.print(f"[red]Error: File not found: {test_file}[/red]")
                raise typer.Exit(1)

            with open(test_file) as f:
                if test_file.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            queries = data.get("evaluations", data.get("queries", []))
            if not queries:
                con.print("[red]Error: No queries found in test file[/red]")
                raise typer.Exit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=con,
            ) as progress:
                task = progress.add_task("Evaluating queries...", total=len(queries))
                report = evaluator.evaluate_batch(queries)
                progress.update(task, completed=len(queries))

            # Compute summary and comparison
            report.compute_summary()
            if storage:
                report.comparison = storage.compare_with_previous(report)
                storage.save_report(report)

            # Output
            if output_format == "json":
                con.print_json(data=report.to_dict())
            else:
                con.print("\n[bold]Evaluation Report[/bold]\n")

                # Summary table
                summary_table = Table(title="Summary Metrics")
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", justify="right")
                if report.comparison:
                    summary_table.add_column("Change", justify="right")

                for key, value in report.summary.items():
                    if value is not None:
                        formatted = f"{value:.3f}" if isinstance(value, float) else str(value)
                        row = [key, formatted]
                        if report.comparison and key in report.comparison:
                            change = report.comparison[key]
                            change_str = f"+{change:.3f}" if change > 0 else f"{change:.3f}"
                            colour = "green" if change > 0 else "red"
                            row.append(f"[{colour}]{change_str}[/{colour}]")
                        elif report.comparison:
                            row.append("-")
                        summary_table.add_row(*row)

                con.print(summary_table)

                # Individual results
                con.print(f"\n[dim]Evaluated {len(report.results)} queries[/dim]")

        else:
            # Single query evaluation
            expected_docs = None
            if expected:
                expected_docs = [expected]

            result = evaluator.evaluate(
                query=query,
                expected_docs=expected_docs,
            )

            if storage:
                storage.save_result(result)

            # Output
            if output_format == "json":
                con.print_json(data=result.to_dict())
            else:
                con.print("\n[bold]Evaluation Result[/bold]\n")

                metrics_table = Table(title=f"Query: {query[:50]}..." if len(query) > 50 else f"Query: {query}")
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Score", justify="right")

                metrics = result.metrics
                if metrics.context_precision is not None:
                    metrics_table.add_row("Context Precision", f"{metrics.context_precision:.3f}")
                if metrics.relevance_score is not None:
                    metrics_table.add_row("Relevance Score", f"{metrics.relevance_score:.3f}")
                if metrics.context_recall is not None:
                    metrics_table.add_row("Context Recall", f"{metrics.context_recall:.3f}")

                metrics_table.add_row("Overall Score", f"[bold]{metrics.overall_score:.3f}[/bold]")

                con.print(metrics_table)
                con.print(f"\n[dim]Retrieved {result.retrieved_chunks} chunks in {result.evaluation_time_ms:.0f}ms[/dim]")

    finally:
        evaluator.close()


def quality_command(
    document_id: str | None = None,
    below: float | None = None,
    file_type: str | None = None,
    test_corpus: Path | None = None,
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Assess extraction quality for indexed documents.

    Shows quality metrics for document extraction including completeness,
    character quality, structure preservation, and image/table handling.
    """
    from ragd.config import load_config
    from ragd.quality import QualityScorer
    from ragd.quality.report import (
        generate_corpus_report,
        generate_quality_report,
        get_quality_summary,
    )
    from ragd.storage import ChromaStore

    con = get_console(no_color)
    config = load_config()

    # Test corpus mode (CI/batch testing)
    if test_corpus:
        if not test_corpus.exists():
            con.print(f"[red]Error: Corpus path does not exist: {test_corpus}[/red]")
            raise typer.Exit(1)

        con.print(f"[bold]Testing corpus: {test_corpus}[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=con,
        ) as progress:
            task = progress.add_task("Scoring documents...", total=None)

            def progress_cb(current: int, total: int, filename: str) -> None:
                progress.update(task, total=total, completed=current, description=f"Scoring {filename}...")

            report = generate_corpus_report(
                path=test_corpus,
                config=config,
                threshold=below or 0.7,
                progress_callback=progress_cb,
            )

        if output_format == "json":
            con.print_json(data=report.to_dict())
        else:
            con.print(get_quality_summary(report))

            # CI exit code
            if report.low_quality_count > 0 or report.errors:
                con.print(f"\n[yellow]Warning: {report.low_quality_count} low-quality documents[/yellow]")
                raise typer.Exit(1)
        return

    # Database mode - score indexed documents
    store = ChromaStore(config.chroma_path)

    try:
        # Single document mode
        if document_id:
            scorer = QualityScorer(config)
            result = scorer.score_stored_document(document_id, store)

            if result is None:
                con.print(f"[red]Document not found: {document_id}[/red]")
                raise typer.Exit(1)

            if output_format == "json":
                con.print_json(data={
                    "document_id": result.document_id,
                    "filename": result.filename,
                    "file_type": result.file_type,
                    "success": result.success,
                    "error": result.error,
                    "metrics": result.metrics.to_dict(),
                })
            else:
                _display_document_quality(con, result, verbose)
            return

        # All documents mode
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=con,
        ) as progress:
            task = progress.add_task("Analysing quality...", total=None)

            def progress_cb(current: int, total: int, filename: str) -> None:
                progress.update(task, total=total, completed=current, description=f"Scoring {filename}...")

            report = generate_quality_report(
                store=store,
                config=config,
                threshold=below or 0.7,
                progress_callback=progress_cb,
            )

        # Filter by file type if specified
        if file_type:
            report.documents = [d for d in report.documents if d.file_type == file_type]

        # Filter by threshold if specified
        if below:
            report.documents = [d for d in report.documents if d.metrics.overall < below]

        if output_format == "json":
            con.print_json(data=report.to_dict())
        else:
            con.print(get_quality_summary(report))

            # Show worst documents
            if report.documents and verbose:
                con.print("\n[bold]Documents (worst first):[/bold]")
                from rich.table import Table

                table = Table()
                table.add_column("Document", style="cyan")
                table.add_column("Type")
                table.add_column("Overall", justify="right")
                table.add_column("Completeness", justify="right")
                table.add_column("Chars", justify="right")
                table.add_column("Structure", justify="right")

                for doc in report.documents[:20]:  # Top 20 worst
                    m = doc.metrics
                    score_colour = "red" if m.overall < 0.5 else "yellow" if m.overall < 0.7 else "green"
                    table.add_row(
                        doc.filename[:40] + "..." if len(doc.filename) > 40 else doc.filename,
                        doc.file_type,
                        f"[{score_colour}]{m.overall:.0%}[/{score_colour}]",
                        f"{m.completeness:.0%}",
                        f"{m.character_quality:.0%}",
                        f"{m.structure:.0%}",
                    )

                con.print(table)

    finally:
        pass  # Store doesn't need explicit close


def _display_document_quality(
    con: Console,
    result,  # DocumentQuality
    verbose: bool = False,
) -> None:
    """Display quality metrics for a single document."""
    from rich.table import Table

    m = result.metrics

    # Overall score with colour
    score = m.overall
    if score >= 0.9:
        score_style = "bold green"
        rating = "Excellent"
    elif score >= 0.7:
        score_style = "bold yellow"
        rating = "Good"
    elif score >= 0.5:
        score_style = "bold orange1"
        rating = "Fair"
    else:
        score_style = "bold red"
        rating = "Poor"

    con.print(f"\n[bold]Quality Report: {result.filename}[/bold]")
    con.print(f"Document ID: [dim]{result.document_id}[/dim]")
    con.print(f"File type: [dim]{result.file_type}[/dim]")
    con.print(f"Overall: [{score_style}]{score:.0%}[/{score_style}] ({rating})")

    if not result.success:
        con.print(f"\n[red]Error: {result.error}[/red]")
        return

    # Metrics table
    table = Table(title="Quality Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Assessment")

    metrics_data = [
        ("Completeness", m.completeness, m.details.get("completeness", {}).get("assessment", "")),
        ("Character Quality", m.character_quality, m.details.get("character_quality", {}).get("assessment", "")),
        ("Structure", m.structure, m.details.get("structure", {}).get("assessment", "")),
        ("Image Handling", m.images, m.details.get("images", {}).get("assessment", "")),
        ("Table Handling", m.tables, m.details.get("tables", {}).get("assessment", "")),
    ]

    for name, score_val, assessment in metrics_data:
        colour = "green" if score_val >= 0.7 else "yellow" if score_val >= 0.5 else "red"
        table.add_row(
            name,
            f"[{colour}]{score_val:.0%}[/{colour}]",
            assessment[:50] if assessment else "",
        )

    con.print(table)

    if verbose and m.details:
        con.print("\n[bold]Detailed Analysis:[/bold]")
        for key, detail in m.details.items():
            if isinstance(detail, dict) and key != "extraction_method":
                con.print(f"\n[cyan]{key}:[/cyan]")
                for k, v in detail.items():
                    if k != "assessment":
                        con.print(f"  {k}: {v}")


__all__ = [
    "evaluate_command",
    "quality_command",
]
