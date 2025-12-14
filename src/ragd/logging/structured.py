"""Structured logging implementation (F-110).

JSON-formatted logging with rotation and third-party suppression.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import warnings
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TextIO


class LogLevel(str, Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """A structured log entry."""

    timestamp: str
    level: str
    message: str
    operation: str | None = None
    file: str | None = None
    duration_ms: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        level: LogLevel,
        message: str,
        operation: str | None = None,
        file: str | None = None,
        duration_ms: float | None = None,
        **extra: Any,
    ) -> LogEntry:
        """Create a log entry with current timestamp.

        Args:
            level: Log level
            message: Log message
            operation: Operation name (index, search, etc.)
            file: Related file path
            duration_ms: Operation duration in milliseconds
            **extra: Additional fields

        Returns:
            LogEntry instance
        """
        return cls(
            timestamp=datetime.now(UTC).isoformat(),
            level=level.value,
            message=message,
            operation=operation,
            file=file,
            duration_ms=duration_ms,
            extra=extra,
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        data = asdict(self)
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        # Flatten extra into main dict
        if "extra" in data:
            extra = data.pop("extra")
            data.update(extra)
        return json.dumps(data)


class StructuredLogger:
    """Logger that outputs JSON-formatted entries.

    Supports file and console output with different levels.
    """

    def __init__(
        self,
        name: str = "ragd",
        console_level: LogLevel = LogLevel.INFO,
        file_level: LogLevel = LogLevel.DEBUG,
        log_file: Path | None = None,
        json_console: bool = False,
    ):
        """Initialise structured logger.

        Args:
            name: Logger name
            console_level: Minimum level for console output
            file_level: Minimum level for file output
            log_file: Path to log file (optional)
            json_console: Whether to use JSON on console
        """
        self.name = name
        self.console_level = console_level
        self.file_level = file_level
        self.log_file = log_file
        self.json_console = json_console
        self._file_handle: TextIO | None = None

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(log_file, "a")

    def _level_value(self, level: LogLevel) -> int:
        """Get numeric value for level comparison."""
        order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return order.index(level)

    def _should_log(self, level: LogLevel, target_level: LogLevel) -> bool:
        """Check if level should be logged."""
        return self._level_value(level) >= self._level_value(target_level)

    def _write_console(self, entry: LogEntry) -> None:
        """Write entry to console."""
        if not self._should_log(LogLevel(entry.level), self.console_level):
            return

        if self.json_console:
            print(entry.to_json())
        else:
            # Human-readable format
            prefix = f"[{entry.level}]"
            if entry.operation:
                prefix = f"[{entry.operation.upper()}]"
            msg = f"{prefix} {entry.message}"
            if entry.file:
                msg += f" ({entry.file})"
            if entry.duration_ms:
                msg += f" [{entry.duration_ms:.0f}ms]"
            print(msg, file=sys.stderr if entry.level in ("ERROR", "CRITICAL") else sys.stdout)

    def _write_file(self, entry: LogEntry) -> None:
        """Write entry to log file."""
        if not self._file_handle:
            return
        if not self._should_log(LogLevel(entry.level), self.file_level):
            return

        self._file_handle.write(entry.to_json() + "\n")
        self._file_handle.flush()

    def log(
        self,
        level: LogLevel,
        message: str,
        operation: str | None = None,
        file: str | None = None,
        duration_ms: float | None = None,
        **extra: Any,
    ) -> None:
        """Log a message.

        Args:
            level: Log level
            message: Log message
            operation: Operation name
            file: Related file path
            duration_ms: Operation duration
            **extra: Additional fields
        """
        entry = LogEntry.create(
            level=level,
            message=message,
            operation=operation,
            file=file,
            duration_ms=duration_ms,
            **extra,
        )
        self._write_console(entry)
        self._write_file(entry)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)

    def close(self) -> None:
        """Close file handle."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


# Global logger instance
_logger: StructuredLogger | None = None


def get_logger() -> StructuredLogger:
    """Get the global logger instance.

    Returns:
        StructuredLogger instance
    """
    global _logger
    if _logger is None:
        _logger = StructuredLogger()
    return _logger


def configure_logging(
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    log_file: Path | None = None,
    json_console: bool = False,
) -> StructuredLogger:
    """Configure the global logger.

    Args:
        console_level: Minimum level for console
        file_level: Minimum level for file
        log_file: Path to log file
        json_console: Use JSON on console

    Returns:
        Configured logger
    """
    global _logger
    if _logger:
        _logger.close()
    _logger = StructuredLogger(
        console_level=console_level,
        file_level=file_level,
        log_file=log_file,
        json_console=json_console,
    )
    return _logger


# Third-party loggers to suppress
SUPPRESSED_LOGGERS = [
    "transformers",
    "tokenizers",
    "sentence_transformers",
    "paddleocr",
    "paddle",
    "ppocr",
    "httpx",
    "httpcore",
    "urllib3",
    "chromadb",
    "onnxruntime",
    "torch",
    "easyocr",
    # Docling document processing library (v1.0.8)
    "docling",
    "docling_core",
    "docling.datamodel",
    "docling.document_converter",
    "docling_parse",
]


def suppress_third_party_logs(
    level: int = logging.WARNING,
    loggers: list[str] | None = None,
    log_file: Path | None = None,
) -> None:
    """Suppress noisy third-party loggers from console, optionally routing to file.

    Also suppresses common UserWarnings from PyTorch/EasyOCR that use the
    warnings module rather than logging.

    Args:
        level: Minimum level for third-party logs on console
        loggers: List of logger names to suppress (defaults to common ones)
        log_file: Optional file path to route suppressed logs to
    """
    target_loggers = loggers or SUPPRESSED_LOGGERS

    # Suppress common UserWarnings from third-party libraries
    # These use Python's warnings module, not logging
    warnings.filterwarnings(
        "ignore",
        message=".*pin_memory.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Using CPU.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=".*ccache.*",
        category=UserWarning,
    )

    # Create file handler if log_file specified
    file_handler: logging.Handler | None = None
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=3,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    for logger_name in target_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        # Route to file if configured
        if file_handler:
            logger.addHandler(file_handler)

    # Also suppress root logger's propagation of warnings
    logging.getLogger().setLevel(level)


class SuppressStdout:
    """Context manager to suppress stdout/stderr from third-party libraries.

    Useful during progress bar displays where library output would disrupt
    the terminal rendering.

    Usage:
        with SuppressStdout():
            # Code that might print to stdout/stderr
            pass

        # Or capture to a file:
        with SuppressStdout(capture_file=Path("~/.ragd/logs/output.log")):
            pass
    """

    def __init__(self, capture_file: Path | None = None) -> None:
        """Initialise suppressor.

        Args:
            capture_file: Optional file to capture suppressed output
        """
        self.capture_file = capture_file
        self._original_stdout: TextIO | None = None
        self._original_stderr: TextIO | None = None
        self._devnull: TextIO | None = None
        self._capture_handle: TextIO | None = None

    def __enter__(self) -> "SuppressStdout":
        """Start suppressing output."""
        import os

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        if self.capture_file:
            self.capture_file.parent.mkdir(parents=True, exist_ok=True)
            self._capture_handle = open(self.capture_file, "a")
            sys.stdout = self._capture_handle
            sys.stderr = self._capture_handle
        else:
            self._devnull = open(os.devnull, "w")
            sys.stdout = self._devnull
            sys.stderr = self._devnull

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore output."""
        sys.stdout = self._original_stdout  # type: ignore
        sys.stderr = self._original_stderr  # type: ignore

        if self._devnull:
            self._devnull.close()
        if self._capture_handle:
            self._capture_handle.close()
