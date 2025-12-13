"""Rich report generation for profile data (F-123).

Provides formatted terminal output for profile sessions
and comparison reports.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragd.performance.profiler import ProfileSession


def format_duration(ms: float) -> str:
    """Format duration for display.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted string (e.g., "123.4ms" or "1.23s")
    """
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.1f}ms"


def format_memory(mb: float | None) -> str:
    """Format memory for display.

    Args:
        mb: Memory in megabytes

    Returns:
        Formatted string (e.g., "123.4MB" or "1.2GB")
    """
    if mb is None:
        return "-"
    if mb >= 1024:
        return f"{mb / 1024:.2f}GB"
    return f"{mb:.1f}MB"


def format_profile_report(session: ProfileSession) -> Table:
    """Format a profile session as a Rich table.

    Args:
        session: ProfileSession to format

    Returns:
        Rich Table object
    """
    summary = session.get_summary()

    table = Table(
        title=f"Profile: {session.name}",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Operation", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Mean", justify="right")
    table.add_column("Median", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Std Dev", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Ops/s", justify="right")

    for op_name, stats in summary.items():
        memory_str = format_memory(stats.get("memory_delta_mean_mb"))
        table.add_row(
            op_name,
            str(stats["count"]),
            format_duration(stats["mean_ms"]),
            format_duration(stats["median_ms"]),
            format_duration(stats["min_ms"]),
            format_duration(stats["max_ms"]),
            format_duration(stats.get("stdev_ms", 0)),
            memory_str,
            f"{1000 / stats['mean_ms']:.1f}" if stats["mean_ms"] > 0 else "-",
        )

    return table


def format_comparison_report(comparison: dict[str, Any]) -> Table:
    """Format a profile comparison as a Rich table.

    Args:
        comparison: Comparison dictionary from compare_profiles()

    Returns:
        Rich Table object
    """
    table = Table(
        title=f"Comparison: {comparison['baseline']} vs {comparison['current']}",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Operation", style="bold")
    table.add_column("Baseline", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Status", justify="center")

    for op_name, op_data in comparison.get("operations", {}).items():
        status = op_data.get("status", "unknown")

        # Format baseline/current
        baseline_str = (
            format_duration(op_data.get("baseline_mean_ms", 0))
            if "baseline_mean_ms" in op_data
            else "-"
        )
        current_str = (
            format_duration(op_data.get("current_mean_ms", 0))
            if "current_mean_ms" in op_data
            else "-"
        )

        # Format delta
        delta_ms = op_data.get("delta_ms")
        delta_str = format_duration(delta_ms) if delta_ms is not None else "-"
        if delta_ms is not None and delta_ms > 0:
            delta_str = f"+{delta_str}"

        # Format change percentage
        change_pct = op_data.get("change_pct")
        if change_pct is not None:
            change_str = f"{change_pct:+.1f}%"
        else:
            change_str = "-"

        # Format status with colour
        if status == "regression":
            status_text = Text("SLOWER", style="bold red")
        elif status == "improvement":
            status_text = Text("FASTER", style="bold green")
        elif status == "stable":
            status_text = Text("STABLE", style="dim")
        elif status == "new":
            status_text = Text("NEW", style="bold yellow")
        else:
            status_text = Text(status.upper(), style="dim")

        table.add_row(
            op_name,
            baseline_str,
            current_str,
            delta_str,
            change_str,
            status_text,
        )

    return table


def format_environment_panel(session: ProfileSession) -> Panel:
    """Format environment information as a Rich panel.

    Args:
        session: ProfileSession with environment metadata

    Returns:
        Rich Panel object
    """
    env = session.metadata.get("environment", {})

    lines = [
        f"Python: {env.get('python_version', 'unknown').split()[0]}",
        f"Platform: {env.get('platform', 'unknown')}",
        f"CPU Cores: {env.get('cpu_count', 'unknown')}",
        f"Memory: {env.get('memory_total_gb', 0):.1f}GB",
    ]

    return Panel(
        "\n".join(lines),
        title="Environment",
        border_style="dim",
    )


def format_session_summary(session: ProfileSession) -> Text:
    """Format session summary as Rich text.

    Args:
        session: ProfileSession to summarise

    Returns:
        Rich Text object
    """
    summary = session.get_summary()
    total_ops = sum(stats["count"] for stats in summary.values())
    total_time = sum(stats["total_ms"] for stats in summary.values())

    text = Text()
    text.append("Session: ", style="bold")
    text.append(f"{session.name}\n")
    text.append("Operations: ", style="bold")
    text.append(f"{total_ops}\n")
    text.append("Total time: ", style="bold")
    text.append(f"{format_duration(total_time)}\n")

    if session.description:
        text.append("Description: ", style="bold")
        text.append(f"{session.description}\n")

    return text


def print_profile_report(
    session: ProfileSession,
    console: Console | None = None,
    show_environment: bool = True,
) -> None:
    """Print a profile report to the console.

    Args:
        session: ProfileSession to report
        console: Rich Console (creates new if None)
        show_environment: Whether to show environment info
    """
    if console is None:
        console = Console()

    console.print()

    if show_environment:
        console.print(format_environment_panel(session))
        console.print()

    console.print(format_session_summary(session))
    console.print()
    console.print(format_profile_report(session))
    console.print()


def print_comparison_report(
    comparison: dict[str, Any],
    console: Console | None = None,
) -> None:
    """Print a comparison report to the console.

    Args:
        comparison: Comparison dictionary
        console: Rich Console (creates new if None)
    """
    if console is None:
        console = Console()

    console.print()
    console.print(format_comparison_report(comparison))
    console.print()

    # Summary
    operations = comparison.get("operations", {})
    regressions = sum(
        1 for op in operations.values() if op.get("status") == "regression"
    )
    improvements = sum(
        1 for op in operations.values() if op.get("status") == "improvement"
    )
    stable = sum(1 for op in operations.values() if op.get("status") == "stable")

    summary = Text()
    if regressions > 0:
        summary.append(f"{regressions} regressions", style="bold red")
        summary.append(", ")
    if improvements > 0:
        summary.append(f"{improvements} improvements", style="bold green")
        summary.append(", ")
    if stable > 0:
        summary.append(f"{stable} stable", style="dim")

    console.print(summary)
    console.print()


def format_latency_histogram(
    times_ms: list[float],
    buckets: int = 10,
    width: int = 40,
) -> str:
    """Format latency distribution as ASCII histogram.

    Args:
        times_ms: List of latencies in milliseconds
        buckets: Number of histogram buckets
        width: Width of histogram bars

    Returns:
        ASCII histogram string
    """
    if not times_ms:
        return "No data"

    min_val = min(times_ms)
    max_val = max(times_ms)
    bucket_size = (max_val - min_val) / buckets if max_val > min_val else 1

    # Count values in each bucket
    counts = [0] * buckets
    for val in times_ms:
        bucket_idx = min(int((val - min_val) / bucket_size), buckets - 1)
        counts[bucket_idx] += 1

    max_count = max(counts)
    lines = []

    for i, count in enumerate(counts):
        bucket_start = min_val + i * bucket_size
        bucket_end = bucket_start + bucket_size
        bar_len = int((count / max_count) * width) if max_count > 0 else 0
        bar = "█" * bar_len

        lines.append(
            f"{format_duration(bucket_start):>8s} - {format_duration(bucket_end):<8s} | "
            f"{bar:<{width}s} ({count})"
        )

    return "\n".join(lines)
