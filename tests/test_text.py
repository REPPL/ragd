"""Tests for text normalisation module."""

import pytest

from ragd.text import (
    NormalisationResult,
    SourceType,
    TextNormaliser,
    normalise_text,
)
from ragd.text.normalise import (
    NormalisationSettings,
    source_type_from_file_type,
)
from ragd.text.pdf_fixes import (
    fix_ocr_spelling,
    fix_spaced_letters,
    fix_spurious_newlines,
    fix_word_boundaries,
)
from ragd.text.html_clean import (
    remove_boilerplate,
    extract_main_content,
    identify_content_blocks,
)
from ragd.text.wordlist import (
    get_common_words,
    is_valid_word,
    COMMON_WORDS,
)


# =============================================================================
# Wordlist Tests
# =============================================================================


def test_common_words_not_empty() -> None:
    """Test common words set is populated."""
    words = get_common_words()
    assert len(words) > 1000  # Should have many words


def test_common_words_contains_basics() -> None:
    """Test common words contains basic words."""
    words = get_common_words()
    assert "the" in words
    assert "and" in words
    assert "is" in words
    assert "computer" in words
    assert "document" in words


def test_is_valid_word_common() -> None:
    """Test is_valid_word with common words."""
    assert is_valid_word("the")
    assert is_valid_word("computer")
    assert is_valid_word("document")
    assert is_valid_word("THE")  # Case insensitive
    assert is_valid_word("Computer")


def test_is_valid_word_invalid() -> None:
    """Test is_valid_word with invalid words."""
    assert not is_valid_word("xyzqwerty")
    assert not is_valid_word("asdfghjkl")


def test_common_words_frozenset() -> None:
    """Test COMMON_WORDS is a frozenset."""
    assert isinstance(COMMON_WORDS, frozenset)


# =============================================================================
# PDF Fixes Tests
# =============================================================================


def test_fix_spaced_letters_basic() -> None:
    """Test fixing spaced letters."""
    text = "y o u r document"
    result = fix_spaced_letters(text)
    assert result == "your document"


def test_fix_spaced_letters_multiple() -> None:
    """Test fixing multiple spaced words."""
    text = "t h e computer and t h e document"
    result = fix_spaced_letters(text)
    assert result == "the computer and the document"


def test_fix_spaced_letters_preserves_valid() -> None:
    """Test spaced letters preserves valid text."""
    text = "This is a normal sentence."
    result = fix_spaced_letters(text)
    assert result == text


def test_fix_spaced_letters_invalid_word() -> None:
    """Test spaced letters doesn't create invalid words."""
    text = "x y z not a word"
    result = fix_spaced_letters(text)
    # Should not change because xyz is not valid
    assert "x y z" in result


def test_fix_word_boundaries_prefix() -> None:
    """Test fixing merged words with prefix."""
    text = "abig problem"
    result = fix_word_boundaries(text)
    assert result == "a big problem"


def test_fix_word_boundaries_suffix() -> None:
    """Test fixing merged words with suffix."""
    text = "problemfor you"
    result = fix_word_boundaries(text)
    assert result == "problem for you"


def test_fix_word_boundaries_preserves_valid() -> None:
    """Test word boundaries preserves valid text."""
    text = "This is a normal sentence."
    result = fix_word_boundaries(text)
    assert result == text


def test_fix_word_boundaries_the() -> None:
    """Test fixing 'the' prefix."""
    text = "thecomputer is working"
    result = fix_word_boundaries(text)
    assert result == "the computer is working"


def test_fix_word_boundaries_preserves_incomplete() -> None:
    """Test that valid words starting with prefixes are preserved.

    Regression test for bug where 'Incomplete' was split to 'In complete'.
    """
    text = "The Incomplete Common Market"
    result = fix_word_boundaries(text)
    assert "Incomplete" in result
    assert "In complete" not in result


def test_fix_word_boundaries_preserves_prefix_words() -> None:
    """Test that words starting with common prefixes are preserved."""
    # Words that legitimately start with prefixes
    test_cases = [
        ("incomplete", "incomplete"),
        ("inaccurate", "in accurate"),  # Not in wordlist, so gets split
        ("information", "information"),
        ("inevitable", "in evitable"),  # Not in wordlist
        ("anarchy", "an archy"),  # Not in wordlist
        ("theorem", "theorem"),
    ]
    for input_text, expected in test_cases:
        result = fix_word_boundaries(input_text)
        # Words in wordlist should be preserved, others may be split
        if is_valid_word(input_text.lower()):
            assert input_text in result, f"'{input_text}' should be preserved"


def test_fix_spurious_newlines_basic() -> None:
    """Test fixing spurious newlines."""
    text = "This is a sentence that continues\non the next line."
    result = fix_spurious_newlines(text)
    assert "continues on" in result


def test_fix_spurious_newlines_preserves_paragraphs() -> None:
    """Test preserving paragraph breaks."""
    text = "First paragraph.\n\nSecond paragraph."
    result = fix_spurious_newlines(text)
    assert "\n\n" in result or "\n" in result  # Should preserve break


def test_fix_spurious_newlines_preserves_lists() -> None:
    """Test preserving list formatting."""
    text = "Items:\n- First item\n- Second item"
    result = fix_spurious_newlines(text)
    assert "- First" in result
    assert "- Second" in result


def test_fix_ocr_spelling_tbe() -> None:
    """Test fixing common OCR error 'tbe' -> 'the'."""
    text = "tbe computer is working"
    result = fix_ocr_spelling(text)
    assert result == "the computer is working"


def test_fix_ocr_spelling_vv() -> None:
    """Test fixing OCR error 'vv' -> 'w'."""
    text = "novv is the time"
    result = fix_ocr_spelling(text)
    assert "now" in result


def test_fix_ocr_spelling_frorn() -> None:
    """Test fixing OCR error 'frorn' -> 'from'."""
    text = "frorn the document"
    result = fix_ocr_spelling(text)
    assert result == "from the document"


def test_fix_ocr_spelling_preserves_valid() -> None:
    """Test OCR spelling preserves valid text."""
    text = "This is a normal sentence."
    result = fix_ocr_spelling(text)
    assert result == text


# =============================================================================
# HTML Boilerplate Tests
# =============================================================================


def test_remove_boilerplate_navigation() -> None:
    """Test removing navigation boilerplate."""
    text = "Home\nAbout\nContact\n\nMain article content here."
    result = remove_boilerplate(text, mode="moderate")
    assert "Main article" in result


def test_remove_boilerplate_footer() -> None:
    """Test removing footer boilerplate."""
    text = "Article content here.\n\n© 2024 Company Name"
    result = remove_boilerplate(text, mode="conservative")
    assert "Article content" in result


def test_remove_boilerplate_cookie_notice() -> None:
    """Test removing cookie notices."""
    text = "Article content.\n\nThis site uses cookies"
    result = remove_boilerplate(text, mode="moderate")
    assert "Article content" in result


def test_remove_boilerplate_preserves_content() -> None:
    """Test boilerplate removal preserves main content."""
    text = """
    This is the main article content with multiple paragraphs.

    The article continues with more detailed information.

    Finally, we conclude with some closing thoughts.
    """
    result = remove_boilerplate(text, mode="aggressive")
    assert "main article" in result
    assert "continues" in result


def test_remove_boilerplate_modes() -> None:
    """Test different boilerplate removal modes."""
    text = "Content\n\nRelated articles\n\nMore content"

    conservative = remove_boilerplate(text, mode="conservative")
    moderate = remove_boilerplate(text, mode="moderate")
    aggressive = remove_boilerplate(text, mode="aggressive")

    # Aggressive should remove more
    assert len(aggressive) <= len(moderate) <= len(conservative)


def test_identify_content_blocks() -> None:
    """Test content block identification."""
    text = "Article title.\n\nMain content paragraph.\n\n© 2024"
    blocks = identify_content_blocks(text)
    assert len(blocks) >= 1
    assert all("type" in b for b in blocks)


def test_extract_main_content() -> None:
    """Test main content extraction."""
    text = """
    Navigation

    This is a long paragraph of main content that should be identified
    as the primary content area. It contains multiple sentences and
    provides valuable information to the reader.

    Another paragraph of content continues here with more details.

    Footer
    """
    result = extract_main_content(text)
    assert "main content" in result.lower()


# =============================================================================
# Normalisation Orchestrator Tests
# =============================================================================


def test_source_type_from_file_type() -> None:
    """Test source type mapping."""
    assert source_type_from_file_type("pdf") == SourceType.PDF
    assert source_type_from_file_type("html") == SourceType.HTML
    assert source_type_from_file_type("htm") == SourceType.HTML
    assert source_type_from_file_type("md") == SourceType.MARKDOWN
    assert source_type_from_file_type("txt") == SourceType.PLAIN_TEXT
    assert source_type_from_file_type("unknown") == SourceType.UNKNOWN


def test_normalisation_settings_defaults() -> None:
    """Test default normalisation settings."""
    settings = NormalisationSettings()
    assert settings.enabled is True
    assert settings.fix_spaced_letters is True
    assert settings.fix_word_boundaries is True
    assert settings.fix_line_breaks is True
    assert settings.fix_ocr_spelling is True
    assert settings.remove_boilerplate is True


def test_normalisation_settings_custom() -> None:
    """Test custom normalisation settings."""
    settings = NormalisationSettings(
        enabled=True,
        fix_spaced_letters=False,
        fix_ocr_spelling=False,
    )
    assert settings.fix_spaced_letters is False
    assert settings.fix_ocr_spelling is False
    assert settings.fix_word_boundaries is True  # Default


def test_normalisation_result_properties() -> None:
    """Test NormalisationResult properties."""
    result = NormalisationResult(
        text="normalised text",
        source_type=SourceType.PDF,
        changes_made=["fixed_spaced_letters", "fixed_ocr"],
        original_length=100,
        normalised_length=90,
    )
    assert result.was_modified is True
    assert result.length_change == -10


def test_normalisation_result_no_changes() -> None:
    """Test NormalisationResult with no changes."""
    result = NormalisationResult(
        text="unchanged text",
        source_type=SourceType.PDF,
        changes_made=[],
        original_length=50,
        normalised_length=50,
    )
    assert result.was_modified is False
    assert result.length_change == 0


def test_text_normaliser_disabled() -> None:
    """Test normaliser when disabled."""
    settings = NormalisationSettings(enabled=False)
    normaliser = TextNormaliser(settings)

    text = "t h e test text"
    result = normaliser.normalise(text, SourceType.PDF)

    assert result.text == text
    assert result.was_modified is False


def test_text_normaliser_pdf() -> None:
    """Test PDF normalisation."""
    normaliser = TextNormaliser()
    text = "t h e document frorn tbe archive"

    result = normaliser.normalise(text, SourceType.PDF)

    assert "the" in result.text
    assert "from" in result.text
    assert result.source_type == SourceType.PDF


def test_text_normaliser_html() -> None:
    """Test HTML normalisation."""
    normaliser = TextNormaliser()
    text = "Main content.\n\nThis site uses cookies"

    result = normaliser.normalise(text, SourceType.HTML)

    assert "Main content" in result.text
    assert result.source_type == SourceType.HTML


def test_normalise_text_function() -> None:
    """Test normalise_text convenience function."""
    text = "t h e document"
    result = normalise_text(text, SourceType.PDF)

    assert isinstance(result, NormalisationResult)
    assert "the" in result.text


def test_universal_fixes_whitespace() -> None:
    """Test universal whitespace normalisation."""
    normaliser = TextNormaliser()
    text = "Multiple   spaces    here"

    result = normaliser.normalise(text, SourceType.PLAIN_TEXT)

    assert "Multiple spaces here" in result.text


def test_universal_fixes_blank_lines() -> None:
    """Test universal blank line collapsing."""
    normaliser = TextNormaliser()
    text = "First paragraph.\n\n\n\n\nSecond paragraph."

    result = normaliser.normalise(text, SourceType.PLAIN_TEXT)

    # Should collapse to at most 2 newlines
    assert "\n\n\n" not in result.text


def test_universal_fixes_zero_width_chars() -> None:
    """Test removal of zero-width Unicode characters.

    Regression test for bug where zero-width spaces appeared in extracted text.
    """
    normaliser = TextNormaliser()
    # Text with zero-width space (U+200B) after hyphen
    text = "Re-\u200bthinking the approach"

    result = normaliser.normalise(text, SourceType.PDF)

    assert "\u200b" not in result.text
    assert "Re-thinking" in result.text
    assert "removed_zero_width_chars" in result.changes_made


def test_universal_fixes_zero_width_disabled() -> None:
    """Test that zero-width removal can be disabled."""
    settings = NormalisationSettings(remove_zero_width_chars=False)
    normaliser = TextNormaliser(settings)
    text = "Re-\u200bthinking"

    result = normaliser.normalise(text, SourceType.PDF)

    # Should preserve zero-width char when disabled
    assert "\u200b" in result.text


def test_normaliser_tracks_changes() -> None:
    """Test that normaliser tracks changes made."""
    normaliser = TextNormaliser()
    text = "t h e document with  multiple spaces"

    result = normaliser.normalise(text, SourceType.PDF)

    assert len(result.changes_made) > 0


def test_normalisation_preserves_meaning() -> None:
    """Test that normalisation preserves semantic meaning."""
    normaliser = TextNormaliser()
    original = """
    This is a well-formatted document with proper spacing.

    It contains multiple paragraphs and should remain largely unchanged.
    """

    result = normaliser.normalise(original, SourceType.PLAIN_TEXT)

    # Key content should be preserved
    assert "well-formatted" in result.text
    assert "multiple paragraphs" in result.text


def test_normaliser_chain_pdf_fixes() -> None:
    """Test PDF fixes are applied in sequence."""
    normaliser = TextNormaliser()
    # Text with multiple issues
    text = "t h e frorn tbe computer"

    result = normaliser.normalise(text, SourceType.PDF)

    # All fixes should be applied
    assert "the" in result.text
    assert "from" in result.text


# =============================================================================
# Edge Cases
# =============================================================================


def test_empty_text() -> None:
    """Test normalisation of empty text."""
    normaliser = TextNormaliser()
    result = normaliser.normalise("", SourceType.PDF)
    assert result.text == ""


def test_whitespace_only() -> None:
    """Test normalisation of whitespace-only text."""
    normaliser = TextNormaliser()
    result = normaliser.normalise("   \n\n   ", SourceType.PDF)
    assert result.text.strip() == ""


def test_unicode_text() -> None:
    """Test normalisation preserves unicode."""
    normaliser = TextNormaliser()
    text = "Document with émojis 🎉 and accénts"

    result = normaliser.normalise(text, SourceType.PLAIN_TEXT)

    assert "émojis" in result.text
    assert "🎉" in result.text


def test_very_long_text() -> None:
    """Test normalisation of long text."""
    normaliser = TextNormaliser()
    text = "This is a sentence. " * 1000

    result = normaliser.normalise(text, SourceType.PLAIN_TEXT)

    assert len(result.text) > 0
    assert "This is a sentence" in result.text


def test_mixed_case_ocr_fixes() -> None:
    """Test OCR fixes work with mixed case."""
    text = "TBE Computer is working"
    result = fix_ocr_spelling(text)
    assert "the" in result.lower()
