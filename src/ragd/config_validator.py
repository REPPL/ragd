"""Configuration validation for ragd.

This module provides validation checks for ragd configuration to detect
issues BEFORE they cause runtime errors (like missing Ollama models).
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragd.config import RagdConfig


class ValidationSeverity(Enum):
    """Severity level for validation results."""

    ERROR = "error"  # Will cause failures
    WARNING = "warning"  # May cause issues
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    severity: ValidationSeverity
    suggestion: str | None = None


@dataclass
class ValidationReport:
    """Complete validation report."""

    results: list[ValidationResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return any(
            not r.passed and r.severity == ValidationSeverity.ERROR for r in self.results
        )

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return any(
            not r.passed and r.severity == ValidationSeverity.WARNING
            for r in self.results
        )

    @property
    def error_count(self) -> int:
        """Count of failed error checks."""
        return sum(
            1
            for r in self.results
            if not r.passed and r.severity == ValidationSeverity.ERROR
        )

    @property
    def warning_count(self) -> int:
        """Count of failed warning checks."""
        return sum(
            1
            for r in self.results
            if not r.passed and r.severity == ValidationSeverity.WARNING
        )

    @property
    def info_count(self) -> int:
        """Count of info-level notices."""
        return sum(
            1
            for r in self.results
            if not r.passed and r.severity == ValidationSeverity.INFO
        )


class ConfigValidator:
    """Validates ragd configuration.

    Usage:
        validator = ConfigValidator(config)
        report = validator.validate()
        if report.has_errors:
            for r in report.results:
                print(f"{r.name}: {r.message}")
    """

    def __init__(self, config: RagdConfig, config_path: Path | None = None):
        """Initialise validator.

        Args:
            config: Configuration to validate
            config_path: Path to config file (for permission checks)
        """
        self.config = config
        self.config_path = config_path

    def validate(self) -> ValidationReport:
        """Run all validation checks.

        Returns:
            ValidationReport with all check results
        """
        report = ValidationReport()

        # Path checks
        report.results.append(self._check_data_dir())
        report.results.append(self._check_chroma_path())

        # Model checks
        report.results.append(self._check_llm_model())
        report.results.append(self._check_embedding_model())

        # Feature checks
        report.results.append(self._check_contextual_ollama())

        # Search checks
        report.results.append(self._check_search_weights())

        # Security checks
        if self.config_path:
            report.results.append(self._check_config_permissions())

        return report

    def _check_data_dir(self) -> ValidationResult:
        """Check that data_dir exists and is writable."""
        data_dir = self.config.storage.data_dir

        if not data_dir.exists():
            return ValidationResult(
                name="data_dir",
                passed=False,
                message=f"Data directory does not exist: {data_dir}",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Run 'ragd init' or create directory: mkdir -p {data_dir}",
            )

        if not os.access(data_dir, os.W_OK):
            return ValidationResult(
                name="data_dir",
                passed=False,
                message=f"Data directory is not writable: {data_dir}",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Fix permissions: chmod u+w {data_dir}",
            )

        return ValidationResult(
            name="data_dir",
            passed=True,
            message="Data directory exists and is writable",
            severity=ValidationSeverity.ERROR,
        )

    def _check_chroma_path(self) -> ValidationResult:
        """Check that chroma_path parent exists."""
        chroma_path = self.config.chroma_path
        parent = chroma_path.parent

        if not parent.exists():
            return ValidationResult(
                name="chroma_path",
                passed=False,
                message=f"ChromaDB parent directory does not exist: {parent}",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Run 'ragd init' or create directory: mkdir -p {parent}",
            )

        return ValidationResult(
            name="chroma_path",
            passed=True,
            message="ChromaDB path parent exists",
            severity=ValidationSeverity.ERROR,
        )

    def _check_llm_model(self) -> ValidationResult:
        """Check that LLM model exists in Ollama."""
        model = self.config.llm.model
        base_url = self.config.llm.base_url

        # Try to check Ollama models
        available_models = self._get_ollama_models(base_url)

        if available_models is None:
            return ValidationResult(
                name="llm.model",
                passed=False,
                message=f"Cannot connect to Ollama at {base_url}",
                severity=ValidationSeverity.WARNING,
                suggestion="Ensure Ollama is running: ollama serve",
            )

        # Check for exact model match first
        if model in available_models:
            return ValidationResult(
                name="llm.model",
                passed=True,
                message=f"LLM model '{model}' is available",
                severity=ValidationSeverity.ERROR,
            )

        # Check if model base exists with different version
        model_base = model.split(":")[0] if ":" in model else model
        matching_models = [m for m in available_models if m.startswith(model_base)]

        if matching_models:
            # Model base exists but exact version not found - ERROR
            # This is the case where llama3.1:70b requested but only llama3.1:8b exists
            return ValidationResult(
                name="llm.model",
                passed=False,
                message=f"LLM model '{model}' not found (similar: {matching_models[0]})",
                severity=ValidationSeverity.ERROR,
                suggestion=f"Update config: ragd config set llm.model {matching_models[0]}",
            )

        # Model not found at all
        suggestions = [m for m in available_models if "llama" in m.lower()][:3]
        suggestion_text = (
            f"Available: {', '.join(suggestions)}"
            if suggestions
            else f"Run 'ollama pull {model}' to download"
        )

        return ValidationResult(
            name="llm.model",
            passed=False,
            message=f"LLM model '{model}' not found in Ollama",
            severity=ValidationSeverity.ERROR,
            suggestion=suggestion_text,
        )

    def _check_embedding_model(self) -> ValidationResult:
        """Check that embedding model name is valid format."""
        model = self.config.embedding.model

        # Basic format validation - should be a reasonable model name
        if not model or len(model) < 3:
            return ValidationResult(
                name="embedding.model",
                passed=False,
                message=f"Invalid embedding model name: '{model}'",
                severity=ValidationSeverity.WARNING,
                suggestion="Use a valid model like 'all-MiniLM-L6-v2'",
            )

        # Check for common valid patterns
        valid_patterns = [
            "all-",  # all-MiniLM-*, all-mpnet-*
            "sentence-",  # sentence-transformers models
            "paraphrase-",  # paraphrase models
            "jinaai/",  # Jina models
            "BAAI/",  # BGE models
        ]

        is_valid_pattern = any(model.startswith(p) for p in valid_patterns)
        if not is_valid_pattern:
            return ValidationResult(
                name="embedding.model",
                passed=True,  # Pass with info - might be custom model
                message=f"Embedding model '{model}' (custom format)",
                severity=ValidationSeverity.WARNING,
            )

        return ValidationResult(
            name="embedding.model",
            passed=True,
            message=f"Embedding model '{model}' is valid",
            severity=ValidationSeverity.WARNING,
        )

    def _check_contextual_ollama(self) -> ValidationResult:
        """Check that contextual retrieval has running Ollama if enabled."""
        contextual = self.config.retrieval.contextual

        if not contextual.enabled:
            return ValidationResult(
                name="contextual",
                passed=True,
                message="Contextual retrieval is disabled",
                severity=ValidationSeverity.WARNING,
            )

        # Check Ollama connectivity
        available_models = self._get_ollama_models(contextual.base_url)

        if available_models is None:
            return ValidationResult(
                name="contextual",
                passed=False,
                message=f"Contextual enabled but Ollama not reachable at {contextual.base_url}",
                severity=ValidationSeverity.WARNING,
                suggestion="Start Ollama or disable contextual: ragd config set retrieval.contextual.enabled false",
            )

        # Check if model is available
        if contextual.model not in available_models:
            return ValidationResult(
                name="contextual",
                passed=False,
                message=f"Contextual model '{contextual.model}' not found",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Pull model: ollama pull {contextual.model}",
            )

        return ValidationResult(
            name="contextual",
            passed=True,
            message=f"Contextual retrieval configured correctly",
            severity=ValidationSeverity.WARNING,
        )

    def _check_search_weights(self) -> ValidationResult:
        """Check that search weights sum to 1.0."""
        semantic = self.config.search.semantic_weight
        keyword = self.config.search.keyword_weight
        total = semantic + keyword

        if abs(total - 1.0) > 0.001:
            return ValidationResult(
                name="search_weights",
                passed=False,
                message=f"Search weights sum to {total:.2f}, not 1.0",
                severity=ValidationSeverity.WARNING,
                suggestion=f"Adjust weights: semantic={semantic} + keyword={keyword} should equal 1.0",
            )

        return ValidationResult(
            name="search_weights",
            passed=True,
            message=f"Search weights valid (semantic={semantic}, keyword={keyword})",
            severity=ValidationSeverity.WARNING,
        )

    def _check_config_permissions(self) -> ValidationResult:
        """Check config file permissions."""
        if not self.config_path or not self.config_path.exists():
            return ValidationResult(
                name="permissions",
                passed=True,
                message="Config file not found (using defaults)",
                severity=ValidationSeverity.INFO,
            )

        try:
            mode = os.stat(self.config_path).st_mode
            perms = mode & 0o777

            # Ideal is 600 (owner read/write only)
            if perms & (stat.S_IRWXG | stat.S_IRWXO):
                return ValidationResult(
                    name="permissions",
                    passed=False,
                    message=f"Config file permissions are {oct(perms)} (group/other access)",
                    severity=ValidationSeverity.INFO,
                    suggestion=f"Recommended: chmod 600 {self.config_path}",
                )

            return ValidationResult(
                name="permissions",
                passed=True,
                message=f"Config file permissions are secure ({oct(perms)})",
                severity=ValidationSeverity.INFO,
            )

        except OSError as e:
            return ValidationResult(
                name="permissions",
                passed=False,
                message=f"Cannot check permissions: {e}",
                severity=ValidationSeverity.INFO,
            )

    def _get_ollama_models(self, base_url: str) -> list[str] | None:
        """Get list of available Ollama models.

        Args:
            base_url: Ollama API base URL

        Returns:
            List of model names, or None if Ollama not reachable
        """
        import urllib.request
        import json

        try:
            url = f"{base_url}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return None


def validate_config(
    config: RagdConfig, config_path: Path | None = None
) -> ValidationReport:
    """Convenience function to validate configuration.

    Args:
        config: Configuration to validate
        config_path: Optional path to config file

    Returns:
        ValidationReport with all check results
    """
    validator = ConfigValidator(config, config_path)
    return validator.validate()
