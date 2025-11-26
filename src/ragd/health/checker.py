"""Health check system for ragd.

This module provides comprehensive health checks for all ragd components.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from ragd.config import RagdConfig, config_exists, load_config

HealthStatus = Literal["healthy", "degraded", "unhealthy"]


@dataclass
class HealthResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    details: dict[str, Any] | None = None


HealthCheck = Callable[[RagdConfig], HealthResult]


def check_config(config: RagdConfig) -> HealthResult:
    """Check configuration validity.

    Args:
        config: Configuration to check

    Returns:
        HealthResult
    """
    start = time.perf_counter()

    try:
        if not config_exists():
            return HealthResult(
                name="Configuration",
                status="degraded",
                message="No configuration file found, using defaults",
                duration_ms=(time.perf_counter() - start) * 1000,
                details={"config_exists": False},
            )

        # Validate paths
        data_dir = config.storage.data_dir
        if not data_dir.exists():
            return HealthResult(
                name="Configuration",
                status="degraded",
                message=f"Data directory does not exist: {data_dir}",
                duration_ms=(time.perf_counter() - start) * 1000,
                details={"data_dir": str(data_dir), "exists": False},
            )

        return HealthResult(
            name="Configuration",
            status="healthy",
            message="Configuration valid",
            duration_ms=(time.perf_counter() - start) * 1000,
            details={
                "data_dir": str(data_dir),
                "tier": config.hardware.tier.value,
            },
        )

    except Exception as e:
        return HealthResult(
            name="Configuration",
            status="unhealthy",
            message=f"Configuration error: {e}",
            duration_ms=(time.perf_counter() - start) * 1000,
        )


def check_storage(config: RagdConfig) -> HealthResult:
    """Check storage accessibility.

    Args:
        config: Configuration

    Returns:
        HealthResult
    """
    start = time.perf_counter()

    try:
        from ragd.storage import ChromaStore

        store = ChromaStore(config.chroma_path)
        stats = store.get_stats()

        return HealthResult(
            name="Storage",
            status="healthy",
            message=f"{stats['document_count']} documents, {stats['chunk_count']} chunks",
            duration_ms=(time.perf_counter() - start) * 1000,
            details=stats,
        )

    except Exception as e:
        return HealthResult(
            name="Storage",
            status="unhealthy",
            message=f"Storage error: {e}",
            duration_ms=(time.perf_counter() - start) * 1000,
        )


def check_embedding_model(config: RagdConfig) -> HealthResult:
    """Check embedding model availability.

    Args:
        config: Configuration

    Returns:
        HealthResult
    """
    start = time.perf_counter()

    try:
        from ragd.embedding import get_embedder

        embedder = get_embedder(
            model_name=config.embedding.model,
            device=config.embedding.device,
        )

        # Test embedding
        test_result = embedder.embed(["test"])
        if not test_result or len(test_result[0]) != embedder.dimension:
            return HealthResult(
                name="Embedding Model",
                status="unhealthy",
                message="Embedding generation failed",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        return HealthResult(
            name="Embedding Model",
            status="healthy",
            message=f"Model {config.embedding.model} ready",
            duration_ms=(time.perf_counter() - start) * 1000,
            details={
                "model": config.embedding.model,
                "dimension": embedder.dimension,
            },
        )

    except Exception as e:
        return HealthResult(
            name="Embedding Model",
            status="unhealthy",
            message=f"Model error: {e}",
            duration_ms=(time.perf_counter() - start) * 1000,
        )


def check_dependencies(config: RagdConfig) -> HealthResult:
    """Check required dependencies.

    Args:
        config: Configuration

    Returns:
        HealthResult
    """
    start = time.perf_counter()
    missing = []
    versions: dict[str, str] = {}

    required_packages = [
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence-transformers"),
        ("fitz", "pymupdf"),
        ("nltk", "nltk"),
        ("tiktoken", "tiktoken"),
        ("bs4", "beautifulsoup4"),
    ]

    for import_name, package_name in required_packages:
        try:
            module = __import__(import_name)
            version = getattr(module, "__version__", "unknown")
            versions[package_name] = version
        except ImportError:
            missing.append(package_name)

    if missing:
        return HealthResult(
            name="Dependencies",
            status="unhealthy",
            message=f"Missing packages: {', '.join(missing)}",
            duration_ms=(time.perf_counter() - start) * 1000,
            details={"missing": missing},
        )

    return HealthResult(
        name="Dependencies",
        status="healthy",
        message=f"{len(versions)} packages installed",
        duration_ms=(time.perf_counter() - start) * 1000,
        details={"versions": versions},
    )


def check_nltk_data(config: RagdConfig) -> HealthResult:
    """Check NLTK data availability.

    Args:
        config: Configuration

    Returns:
        HealthResult
    """
    start = time.perf_counter()

    try:
        import nltk

        # Check for punkt tokeniser
        try:
            nltk.data.find("tokenizers/punkt")
            return HealthResult(
                name="NLTK Data",
                status="healthy",
                message="NLTK punkt tokeniser available",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except LookupError:
            # Try to download
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            return HealthResult(
                name="NLTK Data",
                status="healthy",
                message="NLTK data downloaded",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    except Exception as e:
        return HealthResult(
            name="NLTK Data",
            status="degraded",
            message=f"NLTK data issue: {e}",
            duration_ms=(time.perf_counter() - start) * 1000,
        )


# Registry of health checks
HEALTH_CHECKS: list[HealthCheck] = [
    check_config,
    check_storage,
    check_embedding_model,
    check_dependencies,
    check_nltk_data,
]


def run_health_checks(config: RagdConfig | None = None) -> list[HealthResult]:
    """Run all health checks.

    Args:
        config: Configuration (loads default if not provided)

    Returns:
        List of HealthResult objects
    """
    if config is None:
        config = load_config()

    results = []
    for check in HEALTH_CHECKS:
        result = check(config)
        results.append(result)

    return results
