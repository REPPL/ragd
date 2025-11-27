"""Text normalisation orchestrator.

Coordinates source-specific normalisation based on document type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragd.config import RagdConfig


class SourceType(Enum):
    """Document source type for normalisation routing."""

    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


@dataclass
class NormalisationResult:
    """Result of text normalisation."""

    text: str
    source_type: SourceType
    changes_made: list[str] = field(default_factory=list)
    original_length: int = 0
    normalised_length: int = 0

    @property
    def was_modified(self) -> bool:
        """Check if any changes were made."""
        return len(self.changes_made) > 0

    @property
    def length_change(self) -> int:
        """Get change in text length."""
        return self.normalised_length - self.original_length


@dataclass
class NormalisationSettings:
    """Settings for text normalisation."""

    enabled: bool = True
    fix_spaced_letters: bool = True
    fix_word_boundaries: bool = True
    fix_line_breaks: bool = True
    fix_ocr_spelling: bool = True
    remove_boilerplate: bool = True
    boilerplate_mode: str = "aggressive"  # conservative | moderate | aggressive

    @classmethod
    def from_config(cls, config: RagdConfig | None) -> NormalisationSettings:
        """Create settings from ragd config.

        Args:
            config: RagdConfig instance or None for defaults

        Returns:
            NormalisationSettings instance
        """
        if config is None:
            return cls()

        # Check if config has normalisation attribute
        if hasattr(config, "normalisation"):
            norm_config = config.normalisation
            return cls(
                enabled=getattr(norm_config, "enabled", True),
                fix_spaced_letters=getattr(norm_config, "fix_spaced_letters", True),
                fix_word_boundaries=getattr(norm_config, "fix_word_boundaries", True),
                fix_line_breaks=getattr(norm_config, "fix_line_breaks", True),
                fix_ocr_spelling=getattr(norm_config, "fix_ocr_spelling", True),
                remove_boilerplate=getattr(norm_config, "remove_boilerplate", True),
                boilerplate_mode=getattr(norm_config, "boilerplate_mode", "aggressive"),
            )

        return cls()


class TextNormaliser:
    """Orchestrates text normalisation based on source type."""

    def __init__(self, settings: NormalisationSettings | None = None) -> None:
        """Initialise normaliser.

        Args:
            settings: Normalisation settings (uses defaults if None)
        """
        self.settings = settings or NormalisationSettings()

    def normalise(
        self,
        text: str,
        source_type: SourceType,
    ) -> NormalisationResult:
        """Normalise text based on source type.

        Args:
            text: Text to normalise
            source_type: Type of source document

        Returns:
            NormalisationResult with normalised text and metadata
        """
        if not self.settings.enabled:
            return NormalisationResult(
                text=text,
                source_type=source_type,
                original_length=len(text),
                normalised_length=len(text),
            )

        original_length = len(text)
        changes: list[str] = []
        normalised = text

        # Apply source-specific fixes
        if source_type == SourceType.PDF:
            normalised, pdf_changes = self._normalise_pdf(normalised)
            changes.extend(pdf_changes)
        elif source_type == SourceType.HTML:
            normalised, html_changes = self._normalise_html(normalised)
            changes.extend(html_changes)

        # Apply universal fixes
        normalised, universal_changes = self._apply_universal_fixes(normalised)
        changes.extend(universal_changes)

        return NormalisationResult(
            text=normalised,
            source_type=source_type,
            changes_made=changes,
            original_length=original_length,
            normalised_length=len(normalised),
        )

    def _normalise_pdf(self, text: str) -> tuple[str, list[str]]:
        """Apply PDF-specific normalisation.

        Args:
            text: Text to normalise

        Returns:
            Tuple of (normalised_text, list_of_changes)
        """
        from ragd.text.pdf_fixes import (
            fix_ocr_spelling,
            fix_spaced_letters,
            fix_spurious_newlines,
            fix_word_boundaries,
        )

        changes: list[str] = []
        normalised = text

        if self.settings.fix_spaced_letters:
            new_text = fix_spaced_letters(normalised)
            if new_text != normalised:
                changes.append("fixed_spaced_letters")
                normalised = new_text

        if self.settings.fix_word_boundaries:
            new_text = fix_word_boundaries(normalised)
            if new_text != normalised:
                changes.append("fixed_word_boundaries")
                normalised = new_text

        if self.settings.fix_line_breaks:
            new_text = fix_spurious_newlines(normalised)
            if new_text != normalised:
                changes.append("fixed_spurious_newlines")
                normalised = new_text

        if self.settings.fix_ocr_spelling:
            new_text = fix_ocr_spelling(normalised)
            if new_text != normalised:
                changes.append("fixed_ocr_spelling")
                normalised = new_text

        return normalised, changes

    def _normalise_html(self, text: str) -> tuple[str, list[str]]:
        """Apply HTML-specific normalisation.

        Args:
            text: Text to normalise

        Returns:
            Tuple of (normalised_text, list_of_changes)
        """
        from ragd.text.html_clean import remove_boilerplate

        changes: list[str] = []
        normalised = text

        if self.settings.remove_boilerplate:
            new_text = remove_boilerplate(normalised, mode=self.settings.boilerplate_mode)
            if new_text != normalised:
                changes.append(f"removed_boilerplate_{self.settings.boilerplate_mode}")
                normalised = new_text

        return normalised, changes

    def _apply_universal_fixes(self, text: str) -> tuple[str, list[str]]:
        """Apply fixes that work for all source types.

        Args:
            text: Text to normalise

        Returns:
            Tuple of (normalised_text, list_of_changes)
        """
        changes: list[str] = []
        normalised = text

        # Normalise multiple spaces to single space (but preserve newlines)
        import re

        new_text = re.sub(r"[^\S\n]+", " ", normalised)
        if new_text != normalised:
            changes.append("normalised_whitespace")
            normalised = new_text

        # Strip leading/trailing whitespace from lines
        lines = normalised.split("\n")
        stripped_lines = [line.strip() for line in lines]
        new_text = "\n".join(stripped_lines)
        if new_text != normalised:
            changes.append("stripped_line_whitespace")
            normalised = new_text

        # Collapse multiple blank lines to single blank line
        new_text = re.sub(r"\n{3,}", "\n\n", normalised)
        if new_text != normalised:
            changes.append("collapsed_blank_lines")
            normalised = new_text

        return normalised, changes


def normalise_text(
    text: str,
    source_type: SourceType,
    settings: NormalisationSettings | None = None,
) -> NormalisationResult:
    """Convenience function to normalise text.

    Args:
        text: Text to normalise
        source_type: Type of source document
        settings: Normalisation settings (uses defaults if None)

    Returns:
        NormalisationResult with normalised text
    """
    normaliser = TextNormaliser(settings)
    return normaliser.normalise(text, source_type)


def source_type_from_file_type(file_type: str) -> SourceType:
    """Map file type string to SourceType.

    Args:
        file_type: File type string (e.g., "pdf", "html")

    Returns:
        Corresponding SourceType
    """
    mapping = {
        "pdf": SourceType.PDF,
        "html": SourceType.HTML,
        "htm": SourceType.HTML,
        "md": SourceType.MARKDOWN,
        "markdown": SourceType.MARKDOWN,
        "txt": SourceType.PLAIN_TEXT,
        "text": SourceType.PLAIN_TEXT,
    }
    return mapping.get(file_type.lower(), SourceType.UNKNOWN)
