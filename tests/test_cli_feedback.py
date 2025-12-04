"""Tests for CLI user feedback formatters (F-114)."""

from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from ragd.operations.errors import (
    DocumentResult,
    BatchResult,
    IndexingErrorCategory,
)
from ragd.ui.formatters.progress import (
    IndexingProgress,
    create_progress,
    is_interactive,
)
from ragd.ui.formatters.errors import (
    format_error,
    format_errors_summary,
    format_error_simple,
)
from ragd.ui.formatters.summaries import (
    format_summary,
    format_batch_summary,
    format_dry_run_summary,
    format_simple_summary,
    _format_duration,
)


class TestIsInteractive:
    """Tests for terminal detection."""

    def test_returns_bool(self):
        """is_interactive should return a boolean."""
        result = is_interactive()
        assert isinstance(result, bool)


class TestCreateProgress:
    """Tests for progress creation."""

    def test_creates_progress_instance(self):
        """Should create a Progress instance."""
        console = Console(file=StringIO())
        progress = create_progress(console=console)
        assert progress is not None

    def test_quiet_mode_disabled(self):
        """Quiet mode should disable progress."""
        console = Console(file=StringIO())
        progress = create_progress(console=console, quiet=True)
        assert progress.disable is True

    def test_verbose_mode_not_disabled(self):
        """Verbose mode should not disable progress."""
        console = Console(file=StringIO())
        progress = create_progress(console=console, verbose=True)
        assert progress.disable is False


class TestIndexingProgress:
    """Tests for IndexingProgress class."""

    def test_context_manager(self):
        """Should work as context manager."""
        console = Console(file=StringIO(), force_terminal=True)

        with IndexingProgress(total=10, console=console) as progress:
            assert progress.total == 10
            assert progress.current == 0

    def test_update_filename(self):
        """Should update current filename."""
        console = Console(file=StringIO(), force_terminal=True)

        with IndexingProgress(total=10, console=console) as progress:
            progress.update("test.pdf")
            assert progress.current_file == "test.pdf"

    def test_advance(self):
        """Should advance progress counter."""
        console = Console(file=StringIO(), force_terminal=True)

        with IndexingProgress(total=10, console=console) as progress:
            progress.advance()
            assert progress.current == 1
            progress.advance(5)
            assert progress.current == 6

    def test_quiet_mode(self):
        """Quiet mode should suppress output."""
        console = Console(file=StringIO())

        with IndexingProgress(total=10, console=console, quiet=True) as progress:
            progress.update("test.pdf")
            progress.advance()
            # Should complete without error


class TestFormatError:
    """Tests for error formatting."""

    def test_format_error_panel(self):
        """Should create a panel for error."""
        result = DocumentResult.failed(
            Path("/test/doc.pdf"),
            IndexingErrorCategory.ENCRYPTED,
            "PDF is password-protected",
        )

        panel = format_error(result)
        assert panel is not None
        assert panel.title is not None

    def test_format_error_without_hint(self):
        """Should format without hint when requested."""
        result = DocumentResult.failed(
            Path("/test/doc.pdf"),
            IndexingErrorCategory.ENCRYPTED,
            "PDF is password-protected",
        )

        panel = format_error(result, show_hint=False)
        assert panel is not None

    def test_format_error_simple(self):
        """Should format simple string error."""
        error_str = format_error_simple(
            "/test/doc.pdf",
            "PDF is encrypted",
            hint="Remove password protection",
        )

        assert "/test/doc.pdf" in error_str
        assert "PDF is encrypted" in error_str
        assert "Remove password" in error_str


class TestFormatErrorsSummary:
    """Tests for errors summary formatting."""

    def test_empty_batch_no_output(self):
        """Empty batch should produce no error output."""
        batch = BatchResult()
        batch.add(DocumentResult.success(Path("/a.pdf")))

        console = Console(file=StringIO())
        format_errors_summary(batch, console=console)

        # Should complete without error

    def test_shows_failed_count(self):
        """Should show failed document count."""
        batch = BatchResult()
        batch.add(DocumentResult.failed(
            Path("/a.pdf"),
            IndexingErrorCategory.ENCRYPTED,
            "Password",
        ))

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        format_errors_summary(batch, console=console)

        text = output.getvalue()
        assert "Failed" in text or "1" in text


class TestFormatSummary:
    """Tests for summary formatting."""

    def test_format_summary_panel(self):
        """Should create summary panel."""
        panel = format_summary(
            succeeded=10,
            failed=2,
            skipped=3,
            chunks=150,
            duration_seconds=45.5,
        )

        assert panel is not None
        assert panel.title is not None

    def test_format_summary_success_style(self):
        """Successful summary should have green style."""
        panel = format_summary(
            succeeded=10,
            failed=0,
            skipped=0,
            chunks=150,
            duration_seconds=45.5,
        )

        assert "green" in panel.border_style

    def test_format_summary_with_errors_style(self):
        """Summary with errors should have yellow style."""
        panel = format_summary(
            succeeded=8,
            failed=2,
            skipped=0,
            chunks=100,
            duration_seconds=30.0,
        )

        assert "yellow" in panel.border_style


class TestFormatDryRunSummary:
    """Tests for dry-run summary formatting."""

    def test_dry_run_summary(self):
        """Should format dry-run summary."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        format_dry_run_summary(
            would_index=10,
            would_skip=5,
            would_fail=2,
            console=console,
        )

        text = output.getvalue()
        assert "DRY RUN" in text
        assert "No changes made" in text


class TestFormatDuration:
    """Tests for duration formatting."""

    def test_milliseconds(self):
        """Sub-second should show milliseconds."""
        assert "ms" in _format_duration(0.5)

    def test_seconds(self):
        """Seconds should show seconds."""
        result = _format_duration(30.5)
        assert "s" in result
        assert "m" not in result or "ms" in result

    def test_minutes(self):
        """Minutes should show minutes and seconds."""
        result = _format_duration(125)
        assert "m" in result

    def test_hours(self):
        """Hours should show hours and minutes."""
        result = _format_duration(7500)
        assert "h" in result


class TestFormatSimpleSummary:
    """Tests for simple text summary."""

    def test_simple_summary_format(self):
        """Should format simple text summary."""
        summary = format_simple_summary(
            succeeded=10,
            failed=2,
            skipped=3,
            chunks=150,
            duration_seconds=45.5,
        )

        assert "Indexing Complete" in summary
        assert "10" in summary
        assert "150" in summary
