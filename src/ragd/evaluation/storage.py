"""Evaluation history storage for ragd.

Provides persistent storage for evaluation results.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ragd.evaluation.evaluator import EvaluationReport, EvaluationResult


class EvaluationStorage:
    """Storage for evaluation history."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        """Initialise storage.

        Args:
            storage_dir: Directory to store evaluations.
                        Defaults to ~/.ragd/evaluations/
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".ragd" / "evaluations"
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: EvaluationResult) -> Path:
        """Save a single evaluation result.

        Args:
            result: Evaluation result to save

        Returns:
            Path to saved file
        """
        # Include microseconds for uniqueness
        filename = f"eval_{result.timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        filepath = self.storage_dir / filename

        with open(filepath, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        return filepath

    def save_report(self, report: EvaluationReport) -> Path:
        """Save an evaluation report.

        Args:
            report: Evaluation report to save

        Returns:
            Path to saved file
        """
        # Include microseconds for uniqueness
        filename = f"report_{report.timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
        filepath = self.storage_dir / filename

        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        return filepath

    def load_result(self, filepath: Path | str) -> EvaluationResult:
        """Load an evaluation result from file.

        Args:
            filepath: Path to result file

        Returns:
            Loaded EvaluationResult
        """
        with open(filepath) as f:
            data = json.load(f)
        return EvaluationResult.from_dict(data)

    def list_results(self, limit: int | None = None) -> list[Path]:
        """List available evaluation result files.

        Args:
            limit: Maximum number of results to return (most recent first)

        Returns:
            List of result file paths
        """
        results = sorted(
            self.storage_dir.glob("eval_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if limit:
            results = results[:limit]

        return results

    def list_reports(self, limit: int | None = None) -> list[Path]:
        """List available evaluation report files.

        Args:
            limit: Maximum number of reports to return (most recent first)

        Returns:
            List of report file paths
        """
        reports = sorted(
            self.storage_dir.glob("report_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if limit:
            reports = reports[:limit]

        return reports

    def get_history(self, days: int = 30) -> list[EvaluationResult]:
        """Get evaluation history for the specified number of days.

        Args:
            days: Number of days to include in history

        Returns:
            List of EvaluationResults
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        results = []

        for filepath in self.list_results():
            if filepath.stat().st_mtime >= cutoff:
                try:
                    results.append(self.load_result(filepath))
                except (json.JSONDecodeError, KeyError):
                    # Skip corrupted files
                    continue

        return results

    def compare_with_previous(
        self,
        current: EvaluationReport,
    ) -> dict[str, float] | None:
        """Compare current report with the most recent previous report.

        Args:
            current: Current evaluation report

        Returns:
            Dictionary of metric differences or None if no previous report
        """
        previous_reports = self.list_reports(limit=2)

        # Find a previous report (not the current one)
        previous_report = None
        for report_path in previous_reports:
            if report_path.stem != f"report_{current.timestamp.strftime('%Y%m%d_%H%M%S_%f')}":
                try:
                    with open(report_path) as f:
                        data = json.load(f)
                    previous_report = data.get("summary", {})
                    break
                except (json.JSONDecodeError, KeyError):
                    continue

        if not previous_report or not current.summary:
            return None

        # Compute differences
        comparison = {}
        for key, current_value in current.summary.items():
            if current_value is not None and key in previous_report:
                previous_value = previous_report.get(key)
                if previous_value is not None:
                    comparison[key] = current_value - previous_value

        return comparison if comparison else None


def save_evaluation_result(
    result: EvaluationResult,
    storage_dir: Path | str | None = None,
) -> Path:
    """Convenience function to save an evaluation result.

    Args:
        result: Result to save
        storage_dir: Optional storage directory

    Returns:
        Path to saved file
    """
    storage = EvaluationStorage(storage_dir)
    return storage.save_result(result)


def load_evaluation_history(
    days: int = 30,
    storage_dir: Path | str | None = None,
) -> list[EvaluationResult]:
    """Convenience function to load evaluation history.

    Args:
        days: Number of days to include
        storage_dir: Optional storage directory

    Returns:
        List of EvaluationResults
    """
    storage = EvaluationStorage(storage_dir)
    return storage.get_history(days)
