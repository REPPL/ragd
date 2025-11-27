"""HTML boilerplate removal.

Removes common non-content elements from HTML-extracted text:
- Navigation menus
- Headers and footers
- Sidebars and advertising
- Cookie notices
- Social media widgets
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class BoilerplatePatterns:
    """Patterns for identifying boilerplate content.

    Different modes use different pattern sets:
    - conservative: Only very obvious boilerplate
    - moderate: Balance between removal and retention
    - aggressive: Remove anything that looks like boilerplate
    """

    # Navigation patterns
    nav_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^(home|about|contact|privacy|terms|sitemap|search|menu|navigation)\s*$",
        r"(?i)^\s*[|>»›→]\s*(home|about|contact|privacy|terms)\s*$",
        r"(?i)^(skip to|jump to|go to)\s+(main|content|navigation)",
        r"(?i)^(previous|next|back|forward)\s*(page|article)?$",
        r"(?i)^page\s+\d+\s*(of\s+\d+)?$",
        r"(?i)^(first|last|prev|next)\s*$",
    ])

    # Footer patterns
    footer_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^©\s*\d{4}",
        r"(?i)^copyright\s*©?\s*\d{4}",
        r"(?i)^all rights reserved\.?$",
        r"(?i)^(privacy policy|terms of (service|use)|cookie policy)$",
        r"(?i)^(contact us|about us|careers|press|investors)$",
        r"(?i)^(follow us|connect with us|stay connected)$",
        r"(?i)^(subscribe|newsletter|sign up|register)$",
        r"(?i)^powered by\s+\w+",
        r"(?i)^(facebook|twitter|linkedin|instagram|youtube)\s*$",
    ])

    # Cookie/consent patterns
    cookie_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)this (site|website) uses cookies",
        r"(?i)we use cookies",
        r"(?i)cookie (policy|notice|preferences|settings)",
        r"(?i)accept (all )?cookies",
        r"(?i)reject (all )?cookies",
        r"(?i)manage (cookie )?preferences",
        r"(?i)by (continuing|using|browsing)",
        r"(?i)gdpr|ccpa|privacy",
    ])

    # Advertising patterns
    ad_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^advertisement$",
        r"(?i)^sponsored\s*(content|post|link)?$",
        r"(?i)^promoted\s*(content|post)?$",
        r"(?i)^(click here|learn more|read more|see more)$",
        r"(?i)^(buy now|shop now|order now|subscribe now)$",
        r"(?i)^(free (trial|shipping|download))$",
        r"(?i)^(limited time|special offer|sale|discount)$",
    ])

    # Social sharing patterns
    social_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^(share|tweet|pin|post)\s*(this|on)?$",
        r"(?i)^(share on|share via)\s+(facebook|twitter|linkedin)",
        r"(?i)^(like|follow|subscribe)\s*(us)?$",
        r"(?i)^(\d+)\s*(likes?|shares?|comments?|views?)$",
        r"(?i)^(print|email|save)\s*(this)?\s*(article|page)?$",
    ])

    # Comment section patterns
    comment_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^(leave|post|add|write)\s+a?\s*comment",
        r"(?i)^(\d+)\s*comments?$",
        r"(?i)^(reply|respond)\s*(to\s+this)?$",
        r"(?i)^(log ?in|sign ?in)\s+to\s+(comment|reply)",
        r"(?i)^comments?\s+(are\s+)?(closed|disabled)",
    ])

    # Related content patterns
    related_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)^(related|similar|recommended)\s*(articles?|posts?|content)?$",
        r"(?i)^(you (may|might) also like|also read|see also)$",
        r"(?i)^(popular|trending|featured)\s*(articles?|posts?)?$",
        r"(?i)^(more from|other articles by)$",
        r"(?i)^(in this (section|category))$",
    ])


def remove_boilerplate(
    text: str,
    mode: str = "moderate",
    custom_patterns: list[str] | None = None,
) -> str:
    """Remove boilerplate content from HTML-extracted text.

    Args:
        text: Text extracted from HTML
        mode: Removal mode - conservative, moderate, or aggressive
        custom_patterns: Additional regex patterns to match boilerplate

    Returns:
        Text with boilerplate removed
    """
    patterns = BoilerplatePatterns()

    # Build pattern list based on mode
    all_patterns: list[str] = []

    if mode in ("conservative", "moderate", "aggressive"):
        # All modes include navigation and footer
        all_patterns.extend(patterns.nav_patterns)
        all_patterns.extend(patterns.footer_patterns)
        all_patterns.extend(patterns.cookie_patterns)

    if mode in ("moderate", "aggressive"):
        # Moderate adds social and ads
        all_patterns.extend(patterns.social_patterns)
        all_patterns.extend(patterns.ad_patterns)

    if mode == "aggressive":
        # Aggressive adds comments and related
        all_patterns.extend(patterns.comment_patterns)
        all_patterns.extend(patterns.related_patterns)

    # Add custom patterns
    if custom_patterns:
        all_patterns.extend(custom_patterns)

    # Process line by line
    lines = text.split("\n")
    filtered_lines: list[str] = []
    skip_block = False
    block_depth = 0

    for line in lines:
        stripped = line.strip()

        # Skip empty lines (will be normalised later)
        if not stripped:
            filtered_lines.append(line)
            continue

        # Check for block-level boilerplate markers
        if _is_block_start(stripped, mode):
            skip_block = True
            block_depth = 1
            continue

        if skip_block:
            if _is_block_end(stripped):
                block_depth -= 1
                if block_depth <= 0:
                    skip_block = False
            continue

        # Check individual line patterns
        is_boilerplate = False
        for pattern in all_patterns:
            if re.match(pattern, stripped):
                is_boilerplate = True
                break

        if not is_boilerplate:
            # Additional heuristic checks
            is_boilerplate = _is_heuristic_boilerplate(stripped, mode)

        if not is_boilerplate:
            filtered_lines.append(line)

    return "\n".join(filtered_lines)


def _is_block_start(line: str, mode: str) -> bool:
    """Check if line indicates start of boilerplate block.

    Args:
        line: Line to check
        mode: Removal mode

    Returns:
        True if this starts a boilerplate block
    """
    block_starts = [
        r"(?i)^-{3,}\s*(footer|header|sidebar|nav(igation)?)\s*-{3,}$",
        r"(?i)^={3,}\s*(footer|header|sidebar|nav(igation)?)\s*={3,}$",
        r"(?i)^#{3,}\s*(footer|header|sidebar|nav(igation)?)\s*#{3,}$",
        r"(?i)^\[start\s+(footer|header|sidebar|nav(igation)?)\]$",
        r"(?i)^(begin|start)\s+(footer|header|sidebar|nav(igation)?)$",
    ]

    if mode == "aggressive":
        block_starts.extend([
            r"(?i)^-{3,}\s*(comments?|related|social)\s*-{3,}$",
            r"(?i)^\[start\s+(comments?|related|social)\]$",
        ])

    for pattern in block_starts:
        if re.match(pattern, line):
            return True

    return False


def _is_block_end(line: str) -> bool:
    """Check if line indicates end of boilerplate block.

    Args:
        line: Line to check

    Returns:
        True if this ends a boilerplate block
    """
    block_ends = [
        r"(?i)^-{3,}\s*end\s*-{3,}$",
        r"(?i)^={3,}\s*end\s*={3,}$",
        r"(?i)^\[end\s*\w*\]$",
        r"(?i)^end\s+(footer|header|sidebar|nav(igation)?)$",
        r"(?i)^-{3,}\s*(content|main|article)\s*-{3,}$",
    ]

    for pattern in block_ends:
        if re.match(pattern, line):
            return True

    return False


def _is_heuristic_boilerplate(line: str, mode: str) -> bool:
    """Apply heuristic checks for boilerplate content.

    Args:
        line: Line to check
        mode: Removal mode

    Returns:
        True if line appears to be boilerplate
    """
    # Very short lines with only symbols/numbers
    if len(line) < 5 and not any(c.isalpha() for c in line):
        return True

    # Lines that are just punctuation
    if re.match(r"^[\s\-_=|•·→›»<>]+$", line):
        return True

    # In aggressive mode, apply additional checks
    if mode == "aggressive":
        # Lines with excessive capitalisation (likely headers/buttons)
        words = line.split()
        if len(words) <= 4 and all(w[0].isupper() for w in words if w):
            upper_ratio = sum(1 for c in line if c.isupper()) / max(len(line), 1)
            if upper_ratio > 0.5:
                return True

        # Lines that are just URLs
        if re.match(r"^https?://\S+$", line):
            return True

        # Lines with email addresses only
        if re.match(r"^\S+@\S+\.\S+$", line):
            return True

    return False


def extract_main_content(
    text: str,
    min_paragraph_length: int = 50,
    min_paragraphs: int = 2,
) -> str:
    """Extract main content by identifying the densest text region.

    Uses text density heuristics to find the main content area:
    - Longer paragraphs are more likely to be content
    - Consecutive long paragraphs indicate main content

    Args:
        text: Text to process
        min_paragraph_length: Minimum chars for a paragraph
        min_paragraphs: Minimum consecutive paragraphs to identify content

    Returns:
        Extracted main content
    """
    # Split into paragraphs (separated by blank lines)
    paragraphs = re.split(r"\n\s*\n", text)

    # Score each paragraph by length and content indicators
    scored_paragraphs: list[tuple[int, str, float]] = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue

        # Base score is length
        score = len(para)

        # Boost for sentence-ending punctuation (indicates prose)
        sentence_ends = len(re.findall(r"[.!?]", para))
        score += sentence_ends * 20

        # Penalise for list markers (might be navigation)
        list_markers = len(re.findall(r"^\s*[-•*]\s", para, re.MULTILINE))
        score -= list_markers * 10

        # Penalise for all-caps words (headers/buttons)
        caps_words = len(re.findall(r"\b[A-Z]{2,}\b", para))
        score -= caps_words * 5

        scored_paragraphs.append((i, para, score))

    if not scored_paragraphs:
        return text

    # Find the highest-scoring contiguous region
    best_start = 0
    best_end = len(scored_paragraphs)
    best_score = 0

    for start in range(len(scored_paragraphs)):
        cumulative_score = 0
        for end in range(start + min_paragraphs, len(scored_paragraphs) + 1):
            cumulative_score = sum(
                s[2] for s in scored_paragraphs[start:end]
                if s[2] > min_paragraph_length
            )
            if cumulative_score > best_score:
                best_score = cumulative_score
                best_start = start
                best_end = end

    # Extract the best region
    content_paragraphs = [
        scored_paragraphs[i][1]
        for i in range(best_start, best_end)
        if scored_paragraphs[i][2] > 0
    ]

    return "\n\n".join(content_paragraphs)


def identify_content_blocks(text: str) -> list[dict[str, str | int]]:
    """Identify and label content blocks in text.

    Useful for debugging and understanding document structure.

    Args:
        text: Text to analyse

    Returns:
        List of dicts with block info: type, content, start, end
    """
    blocks: list[dict[str, str | int]] = []
    paragraphs = re.split(r"\n\s*\n", text)

    position = 0
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            position += len(para) + 2  # Account for split
            continue

        block_type = _classify_block(para_stripped)
        blocks.append({
            "type": block_type,
            "content": para_stripped[:100] + "..." if len(para_stripped) > 100 else para_stripped,
            "start": position,
            "end": position + len(para),
            "length": len(para_stripped),
        })
        position += len(para) + 2

    return blocks


def _classify_block(text: str) -> str:
    """Classify a text block by type.

    Args:
        text: Text block to classify

    Returns:
        Classification: 'content', 'navigation', 'footer', 'header', 'boilerplate'
    """
    patterns = BoilerplatePatterns()

    # Check navigation
    for pattern in patterns.nav_patterns:
        if re.search(pattern, text):
            return "navigation"

    # Check footer
    for pattern in patterns.footer_patterns:
        if re.search(pattern, text):
            return "footer"

    # Check cookies
    for pattern in patterns.cookie_patterns:
        if re.search(pattern, text):
            return "cookie_notice"

    # Check ads
    for pattern in patterns.ad_patterns:
        if re.search(pattern, text):
            return "advertisement"

    # Check social
    for pattern in patterns.social_patterns:
        if re.search(pattern, text):
            return "social"

    # Check comments
    for pattern in patterns.comment_patterns:
        if re.search(pattern, text):
            return "comments"

    # Check related
    for pattern in patterns.related_patterns:
        if re.search(pattern, text):
            return "related_content"

    # Heuristic classification
    if len(text) < 20:
        return "short_text"

    # Check if it looks like prose
    sentence_count = len(re.findall(r"[.!?]", text))
    word_count = len(text.split())

    if sentence_count >= 2 and word_count >= 20:
        return "content"

    if word_count < 10:
        return "header" if text[0].isupper() else "boilerplate"

    return "uncertain"
