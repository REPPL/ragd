#!/usr/bin/env python3
"""Measure CLI startup time (F-125).

This script measures the startup time of ragd commands and can be used
for regression testing during development.

Usage:
    python scripts/measure_startup.py
    python scripts/measure_startup.py --iterations 20
    python scripts/measure_startup.py --target 300
"""

from __future__ import annotations

import argparse
import json
import subprocess
import statistics
import sys
import time
from pathlib import Path


def measure_command(command: list[str], iterations: int) -> dict[str, float]:
    """Measure command startup time.

    Args:
        command: Command to run
        iterations: Number of iterations

    Returns:
        Dictionary with timing statistics
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        subprocess.run(command, capture_output=True)
        times.append((time.perf_counter() - start) * 1000)

    return {
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "times_ms": times,
    }


def main() -> int:
    """Run startup time measurements."""
    parser = argparse.ArgumentParser(description="Measure ragd CLI startup time")
    parser.add_argument(
        "--iterations", "-n", type=int, default=10,
        help="Number of iterations (default: 10)"
    )
    parser.add_argument(
        "--target", "-t", type=int, default=500,
        help="Target startup time in ms (default: 500)"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output JSON file for results"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Only output pass/fail status"
    )
    args = parser.parse_args()

    # Measure commands
    version_stats = measure_command(["ragd", "--version"], args.iterations)
    help_stats = measure_command(["ragd", "--help"], args.iterations)

    results = {
        "version": version_stats,
        "help": help_stats,
        "iterations": args.iterations,
        "target_ms": args.target,
        "passed": version_stats["mean_ms"] < args.target,
    }

    if not args.quiet:
        print("ragd Startup Time Measurement (F-125)")
        print("=" * 40)
        print()
        print(f"Iterations: {args.iterations}")
        print(f"Target: {args.target}ms")
        print()
        print("ragd --version:")
        print(f"  Mean:   {version_stats['mean_ms']:.0f}ms")
        print(f"  Median: {version_stats['median_ms']:.0f}ms")
        print(f"  Min:    {version_stats['min_ms']:.0f}ms")
        print(f"  Max:    {version_stats['max_ms']:.0f}ms")
        print()
        print("ragd --help:")
        print(f"  Mean:   {help_stats['mean_ms']:.0f}ms")
        print(f"  Median: {help_stats['median_ms']:.0f}ms")
        print(f"  Min:    {help_stats['min_ms']:.0f}ms")
        print(f"  Max:    {help_stats['max_ms']:.0f}ms")
        print()

    # Output result
    if results["passed"]:
        if not args.quiet:
            print(f"✅ SUCCESS: Startup ({version_stats['mean_ms']:.0f}ms) < target ({args.target}ms)")
        exit_code = 0
    else:
        if not args.quiet:
            print(f"❌ FAIL: Startup ({version_stats['mean_ms']:.0f}ms) >= target ({args.target}ms)")
        exit_code = 1

    if args.output:
        # Remove raw times for cleaner output
        output_data = {
            k: {kk: vv for kk, vv in v.items() if kk != "times_ms"} if isinstance(v, dict) else v
            for k, v in results.items()
        }
        args.output.write_text(json.dumps(output_data, indent=2))
        if not args.quiet:
            print(f"\nResults saved to {args.output}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
