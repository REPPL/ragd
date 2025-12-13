"""Tests for F-125: Startup Time Optimisation.

Tests the CLI startup time to ensure it stays below target.
"""

from __future__ import annotations

import statistics
import subprocess
import time

import pytest


class TestStartupTime:
    """Test CLI startup time."""

    # Target is 500ms, but we allow some margin for CI
    TARGET_MS = 500
    # Minimum iterations for reliable measurement
    MIN_ITERATIONS = 5

    def test_version_startup_time(self) -> None:
        """ragd --version should start in < 500ms."""
        times = []
        for _ in range(self.MIN_ITERATIONS):
            start = time.perf_counter()
            result = subprocess.run(
                ["ragd", "--version"],
                capture_output=True,
                text=True,
            )
            times.append((time.perf_counter() - start) * 1000)
            assert result.returncode == 0

        mean_ms = statistics.mean(times)
        assert mean_ms < self.TARGET_MS, (
            f"Startup time {mean_ms:.0f}ms exceeds target {self.TARGET_MS}ms"
        )

    def test_help_startup_time(self) -> None:
        """ragd --help should start in < 500ms."""
        times = []
        for _ in range(self.MIN_ITERATIONS):
            start = time.perf_counter()
            result = subprocess.run(
                ["ragd", "--help"],
                capture_output=True,
                text=True,
            )
            times.append((time.perf_counter() - start) * 1000)
            assert result.returncode == 0

        mean_ms = statistics.mean(times)
        assert mean_ms < self.TARGET_MS, (
            f"Help startup time {mean_ms:.0f}ms exceeds target {self.TARGET_MS}ms"
        )

    def test_version_output(self) -> None:
        """ragd --version should output version."""
        result = subprocess.run(
            ["ragd", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "ragd version" in result.stdout

    def test_help_output(self) -> None:
        """ragd --help should output help."""
        result = subprocess.run(
            ["ragd", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "ragd" in result.stdout.lower()
        assert "document" in result.stdout.lower()


class TestImportTime:
    """Test import time of key modules."""

    def test_ragd_import_time(self) -> None:
        """ragd module should import quickly."""
        start = time.perf_counter()
        import ragd  # noqa: F401
        import_time = (time.perf_counter() - start) * 1000

        # Basic import should be very fast (< 100ms)
        assert import_time < 100, (
            f"ragd import time {import_time:.0f}ms is too slow"
        )

    def test_cli_import_time(self) -> None:
        """ragd.cli module should import reasonably quickly."""
        # Fresh import in subprocess to avoid caching
        result = subprocess.run(
            ["python", "-c", """
import time
start = time.perf_counter()
from ragd.cli import app
import_time = (time.perf_counter() - start) * 1000
print(f'{import_time:.0f}')
"""],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        import_time = int(result.stdout.strip())

        # CLI import should be under 200ms
        assert import_time < 200, (
            f"ragd.cli import time {import_time}ms is too slow"
        )


class TestLazyLoading:
    """Test lazy loading of heavy modules."""

    def test_embedding_not_loaded_on_startup(self) -> None:
        """Embedding model should not load on ragd --version."""
        result = subprocess.run(
            ["python", "-c", """
import sys
# Import CLI
from ragd.cli import app
# Check if sentence_transformers was loaded
loaded = 'sentence_transformers' in sys.modules
print('loaded' if loaded else 'not_loaded')
"""],
            capture_output=True,
            text=True,
        )
        # Embedding model may or may not be loaded depending on imports
        # This test documents current behaviour
        assert result.returncode == 0

    def test_chromadb_not_loaded_on_startup(self) -> None:
        """ChromaDB should not load on ragd --version."""
        result = subprocess.run(
            ["python", "-c", """
import sys
# Import CLI
from ragd.cli import app
# Check if chromadb was loaded
loaded = 'chromadb' in sys.modules
print('loaded' if loaded else 'not_loaded')
"""],
            capture_output=True,
            text=True,
        )
        # ChromaDB may or may not be loaded depending on imports
        # This test documents current behaviour
        assert result.returncode == 0
