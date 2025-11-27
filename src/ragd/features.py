"""Feature detection for optional dependencies.

This module provides detection of optional features that may or may not be
installed, enabling graceful degradation and helpful error messages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeatureStatus:
    """Status of an optional feature.

    Contains availability information and helpful installation instructions
    for features that are not available.
    """

    available: bool
    name: str
    install_command: str | None = None
    extra_steps: str | None = None

    def __str__(self) -> str:
        """Human-readable status."""
        status = "✓" if self.available else "✗"
        return f"{status} {self.name}"

    def __bool__(self) -> bool:
        """Allow direct boolean checks."""
        return self.available


class DependencyError(Exception):
    """Raised when an optional dependency is required but missing.

    Provides user-friendly error messages with installation instructions.
    """

    def __init__(
        self,
        message: str,
        feature: str,
        install_command: str | None = None,
        extra_steps: str | None = None,
    ) -> None:
        self.feature = feature
        self.install_command = install_command
        self.extra_steps = extra_steps
        super().__init__(message)

    def user_message(self) -> str:
        """Format user-friendly error message."""
        msg = f"{self.args[0]}\n"
        if self.install_command:
            msg += f"\nInstall with: {self.install_command}"
        if self.extra_steps:
            msg += f"\nThen run: {self.extra_steps}"
        return msg


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported.

    Args:
        module_name: Name of the module to check

    Returns:
        True if module can be imported
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _check_with_callback(callback: Callable[[], bool]) -> bool:
    """Check feature availability with a callback.

    Args:
        callback: Function that returns True if feature is available

    Returns:
        Result of callback, or False if exception raised
    """
    try:
        return callback()
    except Exception:
        return False


class FeatureDetector:
    """Detect availability of optional features.

    Provides lazy detection of optional dependencies with caching.
    Use this to check feature availability before attempting to use
    optional functionality.

    Example:
        >>> detector = FeatureDetector()
        >>> if detector.docling.available:
        ...     from docling import DocumentConverter
        ... else:
        ...     print(detector.docling.install_command)
    """

    def __init__(self) -> None:
        """Initialise the feature detector."""
        self._cache: dict[str, FeatureStatus] = {}

    def _get_cached(
        self,
        key: str,
        check: Callable[[], bool],
        name: str,
        install_command: str | None = None,
        extra_steps: str | None = None,
    ) -> FeatureStatus:
        """Get cached feature status or check and cache.

        Args:
            key: Cache key
            check: Function to check availability
            name: Human-readable feature name
            install_command: Installation command if not available
            extra_steps: Additional steps after installation

        Returns:
            FeatureStatus for the feature
        """
        if key not in self._cache:
            available = check()
            self._cache[key] = FeatureStatus(
                available=available,
                name=name,
                install_command=install_command if not available else None,
                extra_steps=extra_steps if not available else None,
            )
        return self._cache[key]

    @property
    def docling(self) -> FeatureStatus:
        """Check Docling availability."""
        return self._get_cached(
            "docling",
            lambda: _check_import("docling"),
            "Docling (PDF structure extraction)",
            install_command="pip install 'ragd[pdf]'",
        )

    @property
    def paddleocr(self) -> FeatureStatus:
        """Check PaddleOCR availability."""
        return self._get_cached(
            "paddleocr",
            lambda: _check_import("paddleocr"),
            "PaddleOCR",
            install_command="pip install 'ragd[ocr]'",
        )

    @property
    def easyocr(self) -> FeatureStatus:
        """Check EasyOCR availability."""
        return self._get_cached(
            "easyocr",
            lambda: _check_import("easyocr"),
            "EasyOCR",
            install_command="pip install easyocr",
        )

    @property
    def ocr(self) -> FeatureStatus:
        """Check any OCR availability (PaddleOCR or EasyOCR)."""
        return self._get_cached(
            "ocr",
            lambda: _check_import("paddleocr") or _check_import("easyocr"),
            "OCR (PaddleOCR or EasyOCR)",
            install_command="pip install 'ragd[ocr]'",
        )

    @property
    def keybert(self) -> FeatureStatus:
        """Check KeyBERT availability."""
        return self._get_cached(
            "keybert",
            lambda: _check_import("keybert"),
            "KeyBERT (keyword extraction)",
            install_command="pip install 'ragd[metadata]'",
        )

    @property
    def spacy(self) -> FeatureStatus:
        """Check spaCy availability."""
        return self._get_cached(
            "spacy",
            lambda: _check_import("spacy"),
            "spaCy (entity extraction)",
            install_command="pip install 'ragd[metadata]'",
            extra_steps="python -m spacy download en_core_web_sm",
        )

    @property
    def spacy_model(self) -> FeatureStatus:
        """Check spaCy model availability."""

        def check_model() -> bool:
            try:
                import spacy

                spacy.load("en_core_web_sm")
                return True
            except Exception:
                return False

        return self._get_cached(
            "spacy_model",
            check_model,
            "spaCy English model",
            install_command="python -m spacy download en_core_web_sm",
        )

    @property
    def langdetect(self) -> FeatureStatus:
        """Check langdetect availability."""
        return self._get_cached(
            "langdetect",
            lambda: _check_import("langdetect"),
            "langdetect (language detection)",
            install_command="pip install langdetect",
        )

    @property
    def metadata(self) -> FeatureStatus:
        """Check full metadata extraction availability (KeyBERT + spaCy)."""
        return self._get_cached(
            "metadata",
            lambda: _check_import("keybert") and _check_import("spacy"),
            "Metadata extraction (KeyBERT + spaCy)",
            install_command="pip install 'ragd[metadata]'",
            extra_steps="python -m spacy download en_core_web_sm",
        )

    @property
    def pyarrow(self) -> FeatureStatus:
        """Check PyArrow availability (for Parquet export)."""
        return self._get_cached(
            "pyarrow",
            lambda: _check_import("pyarrow"),
            "PyArrow (Parquet export)",
            install_command="pip install pyarrow",
        )

    def all_features(self) -> dict[str, FeatureStatus]:
        """Get status of all optional features.

        Returns:
            Dictionary mapping feature names to their status
        """
        return {
            "docling": self.docling,
            "paddleocr": self.paddleocr,
            "easyocr": self.easyocr,
            "ocr": self.ocr,
            "keybert": self.keybert,
            "spacy": self.spacy,
            "spacy_model": self.spacy_model,
            "langdetect": self.langdetect,
            "metadata": self.metadata,
            "pyarrow": self.pyarrow,
        }

    def available_features(self) -> list[str]:
        """Get list of available feature names.

        Returns:
            List of available feature names
        """
        return [name for name, status in self.all_features().items() if status.available]

    def missing_features(self) -> list[str]:
        """Get list of missing feature names.

        Returns:
            List of missing feature names
        """
        return [
            name for name, status in self.all_features().items() if not status.available
        ]


# Module-level convenience functions
_detector: FeatureDetector | None = None


def get_detector() -> FeatureDetector:
    """Get the shared feature detector instance.

    Returns:
        Shared FeatureDetector instance
    """
    global _detector
    if _detector is None:
        _detector = FeatureDetector()
    return _detector


def is_available(feature: str) -> bool:
    """Check if a feature is available.

    Args:
        feature: Feature name (e.g., 'docling', 'ocr', 'metadata')

    Returns:
        True if the feature is available
    """
    detector = get_detector()
    all_features = detector.all_features()
    if feature in all_features:
        return all_features[feature].available
    return False


def require(feature: str) -> None:
    """Require a feature to be available, raising DependencyError if not.

    Args:
        feature: Feature name to require

    Raises:
        DependencyError: If the feature is not available
    """
    detector = get_detector()
    all_features = detector.all_features()

    if feature not in all_features:
        raise ValueError(f"Unknown feature: {feature}")

    status = all_features[feature]
    if not status.available:
        raise DependencyError(
            f"{status.name} is required but not installed.",
            feature=feature,
            install_command=status.install_command,
            extra_steps=status.extra_steps,
        )


# Feature availability constants (evaluated at import time)
DOCLING_AVAILABLE = _check_import("docling")
PADDLEOCR_AVAILABLE = _check_import("paddleocr")
EASYOCR_AVAILABLE = _check_import("easyocr")
OCR_AVAILABLE = PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE
KEYBERT_AVAILABLE = _check_import("keybert")
SPACY_AVAILABLE = _check_import("spacy")
LANGDETECT_AVAILABLE = _check_import("langdetect")
PYARROW_AVAILABLE = _check_import("pyarrow")
