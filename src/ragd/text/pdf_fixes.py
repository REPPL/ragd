"""PDF-specific text fixes.

Addresses common issues from PDF text extraction:
- Spaced letters from justified text
- Merged words from missing spaces
- Spurious line breaks
- OCR errors
"""

from __future__ import annotations

import re
from functools import lru_cache

from ragd.text.wordlist import get_common_words, is_valid_word


def fix_spaced_letters(text: str) -> str:
    """Fix spaced-out letters like 'y o u r' → 'your'.

    This pattern commonly occurs in justified PDF text where characters
    are spaced apart.

    Args:
        text: Text with potential spaced letters

    Returns:
        Text with spaced letters collapsed
    """
    # Pattern: single letters separated by spaces (minimum 3 letters)
    # e.g., "y o u r" or "c o m p u t e r"
    pattern = r"\b([a-zA-Z])((?:\s+[a-zA-Z]){2,})\b"

    def replace_spaced(match: re.Match[str]) -> str:
        # Get all characters
        full_match = match.group(0)
        letters = re.findall(r"[a-zA-Z]", full_match)
        collapsed = "".join(letters)

        # Verify it forms a valid word
        if is_valid_word(collapsed.lower()):
            return collapsed

        # Not a valid word, return original
        return full_match

    return re.sub(pattern, replace_spaced, text)


def fix_word_boundaries(text: str) -> str:
    """Fix merged words like 'abig' → 'a big'.

    This commonly occurs when PDF extraction misses space characters.

    Args:
        text: Text with potential merged words

    Returns:
        Text with word boundaries fixed
    """
    common_prefixes = {
        "a",
        "an",
        "the",
        "is",
        "it",
        "to",
        "in",
        "on",
        "of",
        "or",
        "as",
        "at",
        "by",
        "we",
        "be",
        "if",
        "so",
        "no",
        "do",
        "my",
        "up",
        "he",
        "me",
    }

    common_suffixes = {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "had",
        "her",
        "was",
        "one",
        "our",
        "out",
        "has",
        "his",
        "how",
        "man",
        "new",
        "now",
        "old",
        "see",
        "way",
        "who",
        "its",
        "say",
        "she",
        "two",
        "may",
        "day",
    }

    result = text

    # Try to split merged words using common prefix patterns
    for prefix in common_prefixes:
        # Pattern: prefix directly followed by another word
        pattern = rf"\b({prefix})([a-z]{{3,}})\b"

        def split_prefix(match: re.Match[str]) -> str:
            prefix_word = match.group(1)
            rest = match.group(2)
            # Check if the rest is a valid word
            if is_valid_word(rest.lower()):
                return f"{prefix_word} {rest}"
            return match.group(0)

        result = re.sub(pattern, split_prefix, result, flags=re.IGNORECASE)

    # Try common suffix patterns (word ending with common word)
    for suffix in common_suffixes:
        # Pattern: word ending with a common word suffix
        pattern = rf"\b([a-z]{{2,}})({suffix})\b"

        def split_suffix(match: re.Match[str]) -> str:
            first = match.group(1)
            suffix_word = match.group(2)
            # Check if the first part is a valid word
            if is_valid_word(first.lower()):
                return f"{first} {suffix_word}"
            return match.group(0)

        result = re.sub(pattern, split_suffix, result, flags=re.IGNORECASE)

    return result


def fix_spurious_newlines(text: str) -> str:
    """Fix newlines that break sentences inappropriately.

    Preserves paragraph breaks (double newlines) but removes single
    newlines that occur mid-sentence.

    Args:
        text: Text with potential spurious newlines

    Returns:
        Text with sentence-breaking newlines fixed
    """
    # First, normalise to Unix line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Protect paragraph breaks (convert to placeholder)
    text = re.sub(r"\n\n+", "\n\n<PARA_BREAK>\n\n", text)

    # Pattern for newlines that break sentences
    # - Don't merge if line ends with sentence-ending punctuation
    # - Don't merge if next line starts with bullet/number
    # - Don't merge if line appears to be a heading (short, no punctuation)

    lines = text.split("\n")
    merged_lines: list[str] = []

    for i, line in enumerate(lines):
        line = line.strip()

        if not line:
            merged_lines.append("")
            continue

        # Check if this is a paragraph break placeholder
        if line == "<PARA_BREAK>":
            merged_lines.append("")
            continue

        # Check if we should merge with previous line
        if merged_lines and merged_lines[-1]:
            prev_line = merged_lines[-1]

            should_merge = (
                # Previous line doesn't end with sentence terminator
                not re.search(r"[.!?:;]$", prev_line)
                # Current line doesn't start with bullet/number
                and not re.match(r"^[\d•\-\*\[\(]", line)
                # Current line doesn't look like a heading (all caps, short)
                and not (line.isupper() and len(line) < 50)
                # Previous line isn't very short (likely heading)
                and len(prev_line) > 30
                # Current line starts with lowercase (continuation)
                and (line[0].islower() if line else False)
            )

            if should_merge:
                merged_lines[-1] = f"{prev_line} {line}"
                continue

        merged_lines.append(line)

    # Restore paragraph breaks
    result = "\n".join(merged_lines)
    result = result.replace("<PARA_BREAK>", "")
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def fix_ocr_spelling(text: str) -> str:
    """Fix common OCR errors.

    Common OCR confusions:
    - rn → m
    - vv → w
    - cl → d
    - li → h
    - 0 → O (and vice versa)
    - 1 → l (and vice versa)

    Args:
        text: Text with potential OCR errors

    Returns:
        Text with OCR errors fixed
    """
    # Common OCR confusion patterns
    ocr_patterns = [
        # rn → m (very common)
        (r"\brn(?=[aeiou])", "m"),  # rn before vowel → m
        # vv → w
        (r"vv", "w"),
        # cl → d (in specific contexts)
        (r"\bcl(?=ose|ear|ean|aim|ass)", "d"),
        # Common misspellings from OCR
        (r"\btbe\b", "the"),
        (r"\btlie\b", "the"),
        (r"\bwbich\b", "which"),
        (r"\bwbat\b", "what"),
        (r"\btbat\b", "that"),
        (r"\btbis\b", "this"),
        (r"\bwitb\b", "with"),
        (r"\bfrorn\b", "from"),
        (r"\bsorne\b", "some"),
        (r"\btirne\b", "time"),
        (r"\brnore\b", "more"),
        (r"\bbecorne\b", "become"),
        (r"\bnarne\b", "name"),
        (r"\bsarne\b", "same"),
        (r"\bcarne\b", "came"),
        (r"\bgarne\b", "game"),
        (r"\bfrarne\b", "frame"),
    ]

    result = text
    for pattern, replacement in ocr_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # More aggressive: try to fix unrecognised words
    result = _fix_unrecognised_words(result)

    return result


def _fix_unrecognised_words(text: str) -> str:
    """Try to fix unrecognised words using OCR substitutions.

    Args:
        text: Text with potential OCR errors

    Returns:
        Text with some errors fixed
    """
    # OCR character substitutions
    substitutions = {
        "rn": "m",
        "vv": "w",
        "cl": "d",
        "ii": "u",
        "nn": "m",
    }

    words = text.split()
    fixed_words = []

    for word in words:
        # Skip short words and words with non-alpha characters
        if len(word) < 4 or not word.isalpha():
            fixed_words.append(word)
            continue

        # Skip if already a valid word
        if is_valid_word(word.lower()):
            fixed_words.append(word)
            continue

        # Try substitutions
        fixed = word
        for wrong, right in substitutions.items():
            if wrong in word.lower():
                candidate = re.sub(wrong, right, word, flags=re.IGNORECASE)
                if is_valid_word(candidate.lower()):
                    fixed = candidate
                    break

        fixed_words.append(fixed)

    return " ".join(fixed_words)


@lru_cache(maxsize=1)
def _get_word_set() -> set[str]:
    """Get cached set of common words for validation."""
    return get_common_words()
