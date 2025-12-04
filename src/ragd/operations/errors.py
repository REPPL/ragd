"""Error logging and recovery for ragd operations.

This module provides comprehensive error tracking for document indexing
and other operations, with categorised errors and remediation hints.

Features:
- Per-document success/failure tracking
- Categorised failure reasons
- Remediation hints for common errors
- Batch result aggregation
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal


class IndexingErrorCategory(Enum):
    """Categories for document indexing errors.

    Extends the basic FailureCategory from pipeline with additional
    file-system and dependency-related categories.
    """

    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    SIZE_EXCEEDED = "size_exceeded"

    # Content errors
    UNSUPPORTED_FORMAT = "unsupported_format"
    EXTRACTION_FAILED = "extraction_failed"
    ENCODING_ERROR = "encoding_error"
    CORRUPT_FILE = "corrupt_file"
    EMPTY_FILE = "empty_file"
    TEXT_TOO_SHORT = "text_too_short"

    # PDF-specific
    IMAGE_ONLY = "image_only"
    ENCRYPTED = "encrypted"
    MALFORMED = "malformed"

    # HTML-specific
    JS_CONTENT = "js_content"

    # System errors
    DEPENDENCY_MISSING = "dependency_missing"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"

    # Unknown
    UNKNOWN = "unknown"


# Remediation hints for each error category
REMEDIATION_HINTS: dict[IndexingErrorCategory, str] = {
    # File system
    IndexingErrorCategory.FILE_NOT_FOUND: (
        "Verify the file exists and the path is correct. "
        "Use 'ls -la <path>' to check."
    ),
    IndexingErrorCategory.PERMISSION_DENIED: (
        "Check file permissions with 'ls -l <path>'. "
        "You may need to run 'chmod +r <file>' to add read permission."
    ),
    IndexingErrorCategory.SIZE_EXCEEDED: (
        "File exceeds maximum size limit. Try splitting large files "
        "or increasing the size limit in config.yaml."
    ),
    # Content errors
    IndexingErrorCategory.UNSUPPORTED_FORMAT: (
        "This file format is not supported. Supported formats: "
        "PDF, HTML, TXT, MD, DOCX, XLSX, EPUB. Convert to a supported format."
    ),
    IndexingErrorCategory.EXTRACTION_FAILED: (
        "Text extraction failed. The file may be corrupted or use an "
        "unsupported encoding. Try re-saving the file."
    ),
    IndexingErrorCategory.ENCODING_ERROR: (
        "File uses an unsupported text encoding. Try converting to UTF-8 "
        "using a text editor or 'iconv' command."
    ),
    IndexingErrorCategory.CORRUPT_FILE: (
        "File appears to be corrupted or malformed. Try re-downloading "
        "or re-exporting from the source application."
    ),
    IndexingErrorCategory.EMPTY_FILE: (
        "File contains no extractable content. Verify the file has content."
    ),
    IndexingErrorCategory.TEXT_TOO_SHORT: (
        "Extracted text is too short to generate meaningful chunks. "
        "Try using OCR if the document contains images, or verify content."
    ),
    # PDF-specific
    IndexingErrorCategory.IMAGE_ONLY: (
        "This PDF appears to be scanned/image-only. OCR was attempted but "
        "may have failed. Ensure PaddleOCR is installed: pip install ragd[ocr]"
    ),
    IndexingErrorCategory.ENCRYPTED: (
        "This PDF is password-protected. Remove the password protection "
        "before indexing, or use a PDF tool to decrypt it."
    ),
    IndexingErrorCategory.MALFORMED: (
        "This PDF is corrupted or malformed. Try re-downloading or "
        "re-exporting from the source application."
    ),
    # HTML-specific
    IndexingErrorCategory.JS_CONTENT: (
        "This HTML page uses JavaScript to render content. Try saving as "
        "'Complete webpage' or use a browser extension like SingleFile."
    ),
    # System errors
    IndexingErrorCategory.DEPENDENCY_MISSING: (
        "A required dependency is not installed. Run 'pip install ragd[all]' "
        "to install all optional dependencies."
    ),
    IndexingErrorCategory.TIMEOUT: (
        "Operation timed out. Try again, or increase timeout in config. "
        "For large files, consider splitting into smaller parts."
    ),
    IndexingErrorCategory.MEMORY_ERROR: (
        "Ran out of memory processing this file. Try closing other "
        "applications or processing smaller files."
    ),
    # Unknown
    IndexingErrorCategory.UNKNOWN: (
        "An unexpected error occurred. Check the error message for details. "
        "Run with --verbose for more information."
    ),
}


@dataclass
class DocumentResult:
    """Result of processing a single document.

    Tracks success/failure status, timing, and categorised errors
    with remediation hints.
    """

    path: Path
    status: Literal["success", "failed", "skipped"]
    category: IndexingErrorCategory | None = None
    message: str | None = None
    duration_ms: int = 0
    chunks_created: int = 0
    images_extracted: int = 0

    @property
    def hint(self) -> str | None:
        """Get remediation hint for this error category."""
        if self.category is None:
            return None
        return REMEDIATION_HINTS.get(self.category)

    @classmethod
    def success(
        cls,
        path: Path,
        chunks: int = 0,
        images: int = 0,
        duration_ms: int = 0,
    ) -> DocumentResult:
        """Create a successful result."""
        return cls(
            path=path,
            status="success",
            chunks_created=chunks,
            images_extracted=images,
            duration_ms=duration_ms,
        )

    @classmethod
    def failed(
        cls,
        path: Path,
        category: IndexingErrorCategory,
        message: str,
        duration_ms: int = 0,
    ) -> DocumentResult:
        """Create a failed result with categorised error."""
        return cls(
            path=path,
            status="failed",
            category=category,
            message=message,
            duration_ms=duration_ms,
        )

    @classmethod
    def skipped(
        cls,
        path: Path,
        reason: str = "duplicate",
        duration_ms: int = 0,
    ) -> DocumentResult:
        """Create a skipped result."""
        return cls(
            path=path,
            status="skipped",
            message=reason,
            duration_ms=duration_ms,
        )


@dataclass
class BatchResult:
    """Aggregated results from batch operations.

    Provides summary statistics and access to individual results.
    """

    results: list[DocumentResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    def add(self, result: DocumentResult) -> None:
        """Add a result to the batch."""
        self.results.append(result)

    def complete(self) -> None:
        """Mark batch as complete."""
        self.end_time = time.time()

    @property
    def total(self) -> int:
        """Total number of documents processed."""
        return len(self.results)

    @property
    def succeeded(self) -> int:
        """Number of successful documents."""
        return sum(1 for r in self.results if r.status == "success")

    @property
    def failed(self) -> int:
        """Number of failed documents."""
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def skipped(self) -> int:
        """Number of skipped documents."""
        return sum(1 for r in self.results if r.status == "skipped")

    @property
    def total_chunks(self) -> int:
        """Total chunks created across all documents."""
        return sum(r.chunks_created for r in self.results)

    @property
    def total_images(self) -> int:
        """Total images extracted across all documents."""
        return sum(r.images_extracted for r in self.results)

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def failures_by_category(self) -> dict[IndexingErrorCategory, int]:
        """Count of failures by category."""
        counts: dict[IndexingErrorCategory, int] = {}
        for result in self.results:
            if result.status == "failed" and result.category:
                counts[result.category] = counts.get(result.category, 0) + 1
        return counts

    def get_failed(self) -> list[DocumentResult]:
        """Get all failed results."""
        return [r for r in self.results if r.status == "failed"]

    def get_by_category(
        self, category: IndexingErrorCategory
    ) -> list[DocumentResult]:
        """Get results with a specific error category."""
        return [r for r in self.results if r.category == category]


def categorise_error(
    error: Exception,
    path: Path | None = None,
) -> tuple[IndexingErrorCategory, str]:
    """Categorise an exception into an IndexingErrorCategory.

    Args:
        error: The exception that occurred
        path: Optional path for file-related errors

    Returns:
        Tuple of (category, error message)
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()

    # File not found
    if isinstance(error, FileNotFoundError):
        return IndexingErrorCategory.FILE_NOT_FOUND, str(error)

    # Permission denied
    if isinstance(error, PermissionError):
        return IndexingErrorCategory.PERMISSION_DENIED, str(error)

    # Memory error
    if isinstance(error, MemoryError):
        return IndexingErrorCategory.MEMORY_ERROR, str(error)

    # Timeout
    if "timeout" in error_msg or "timed out" in error_msg:
        return IndexingErrorCategory.TIMEOUT, str(error)

    # Encoding error
    if isinstance(error, (UnicodeDecodeError, UnicodeEncodeError)):
        return IndexingErrorCategory.ENCODING_ERROR, str(error)
    if "encoding" in error_msg or "decode" in error_msg:
        return IndexingErrorCategory.ENCODING_ERROR, str(error)

    # Import/dependency error
    if isinstance(error, ImportError) or isinstance(error, ModuleNotFoundError):
        return IndexingErrorCategory.DEPENDENCY_MISSING, str(error)

    # PDF-specific errors
    if "encrypted" in error_msg or "password" in error_msg:
        return IndexingErrorCategory.ENCRYPTED, str(error)
    if "corrupt" in error_msg or "malformed" in error_msg or "invalid" in error_msg:
        return IndexingErrorCategory.CORRUPT_FILE, str(error)

    # Extraction failed
    if "extract" in error_msg or "parse" in error_msg:
        return IndexingErrorCategory.EXTRACTION_FAILED, str(error)

    # Unknown
    return IndexingErrorCategory.UNKNOWN, f"{error_type}: {error}"
