"""Prompt template loading and management for ragd.

This module provides utilities for:
- Loading prompts from config (file or inline) with fallback to defaults
- Exporting default prompts to files for customisation
- Managing prompt template directories

v1.0.5: Configuration Exposure
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragd.config import PromptFileReference, RagdConfig

logger = logging.getLogger(__name__)

# Default prompts directory
DEFAULT_PROMPTS_DIR = Path.home() / ".ragd" / "prompts"

# Prompt categories and their templates
PROMPT_CATEGORIES = {
    "rag": ["answer", "summarise", "compare", "chat", "refine"],
    "agentic": ["relevance_eval", "query_rewrite", "faithfulness_eval", "refine_response"],
    "metadata": ["summary", "classification", "context_generation"],
    "evaluation": ["faithfulness", "answer_relevancy"],
}

# README content for prompts directory
PROMPTS_README = """# ragd Custom Prompts

This directory contains custom prompt templates for ragd.

## Directory Structure

```
prompts/
├── rag/                    # RAG response prompts
│   ├── answer.txt          # Main answer generation
│   ├── summarise.txt       # Multi-source summarisation
│   ├── compare.txt         # Source comparison
│   ├── chat.txt            # Multi-turn chat
│   └── refine.txt          # Response refinement
├── agentic/                # Agentic RAG prompts
│   ├── relevance_eval.txt  # Context relevance evaluation
│   ├── query_rewrite.txt   # Query rewriting for better retrieval
│   ├── faithfulness_eval.txt # Response faithfulness check
│   └── refine_response.txt # Response refinement
├── metadata/               # Metadata extraction prompts
│   ├── summary.txt         # Document summarisation
│   ├── classification.txt  # Document classification
│   └── context_generation.txt # Contextual retrieval
└── evaluation/             # Evaluation prompts
    ├── faithfulness.txt    # Faithfulness metric
    └── answer_relevancy.txt # Relevancy metric
```

## Template Variables

Prompts can include template variables using `{variable}` syntax:

- `{context}` - Retrieved context chunks
- `{question}` - User question/query
- `{query}` - Search query
- `{text}` - Document text
- `{history}` - Conversation history
- `{title}` - Document title
- `{file_type}` - Document type
- `{answer}` - Generated answer (for evaluation)
- `{response}` - Model response (for evaluation)

## Customisation

1. Copy a default prompt: `ragd config prompts --export`
2. Edit the file in your preferred text editor
3. ragd will automatically use your custom prompts

## Resetting to Defaults

To reset a prompt to default, simply delete the file.
ragd will fall back to built-in defaults automatically.
"""


def ensure_prompts_dir() -> Path:
    """Create prompts directory with README if it doesn't exist.

    Returns:
        Path to the prompts directory
    """
    if not DEFAULT_PROMPTS_DIR.exists():
        DEFAULT_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        readme_path = DEFAULT_PROMPTS_DIR / "README.md"
        readme_path.write_text(PROMPTS_README, encoding="utf-8")
        logger.info("Created prompts directory: %s", DEFAULT_PROMPTS_DIR)
    return DEFAULT_PROMPTS_DIR


def get_prompt(
    ref: PromptFileReference | None,
    default: str,
    category: str = "",
    name: str = "",
) -> str:
    """Load prompt from reference, falling back to default.

    Resolution order:
    1. PromptFileReference.file (if exists)
    2. PromptFileReference.inline (if provided)
    3. Conventional location (~/.ragd/prompts/{category}/{name}.txt)
    4. Default string

    Args:
        ref: Optional prompt file reference from config
        default: Default prompt string
        category: Prompt category (e.g., 'rag', 'agentic')
        name: Prompt name (e.g., 'answer', 'relevance_eval')

    Returns:
        Resolved prompt string
    """
    # Try config reference first
    if ref is not None:
        resolved = ref.resolve(default)
        if resolved != default:
            logger.debug("Using custom prompt from config: %s/%s", category, name)
            return resolved

    # Try conventional file location
    if category and name:
        conventional_path = DEFAULT_PROMPTS_DIR / category / f"{name}.txt"
        if conventional_path.exists():
            try:
                content = conventional_path.read_text(encoding="utf-8")
                logger.debug("Using custom prompt from file: %s", conventional_path)
                return content
            except OSError as e:
                logger.warning("Failed to read prompt file %s: %s", conventional_path, e)

    # Fall back to default
    return default


def list_prompt_categories() -> list[str]:
    """List available prompt categories.

    Returns:
        List of category names
    """
    return list(PROMPT_CATEGORIES.keys())


def list_prompts(category: str | None = None) -> dict[str, list[str]]:
    """List available prompts, optionally filtered by category.

    Args:
        category: Optional category to filter by

    Returns:
        Dictionary of category -> prompt names
    """
    if category:
        if category in PROMPT_CATEGORIES:
            return {category: PROMPT_CATEGORIES[category]}
        return {}
    return dict(PROMPT_CATEGORIES)


def export_default_prompts(
    output_dir: Path | None = None,
    category: str | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """Export default prompts to files for customisation.

    Args:
        output_dir: Directory to export to (default: ~/.ragd/prompts)
        category: Optional category to export (default: all)
        overwrite: Whether to overwrite existing files

    Returns:
        List of paths to exported files
    """
    from ragd.prompts.defaults import DEFAULT_PROMPTS

    output_dir = output_dir or DEFAULT_PROMPTS_DIR
    exported: list[Path] = []

    categories_to_export = [category] if category else list(DEFAULT_PROMPTS.keys())

    for cat in categories_to_export:
        if cat not in DEFAULT_PROMPTS:
            logger.warning("Unknown category: %s", cat)
            continue

        cat_dir = output_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        for name, content in DEFAULT_PROMPTS[cat].items():
            file_path = cat_dir / f"{name}.txt"

            if file_path.exists() and not overwrite:
                logger.debug("Skipping existing file: %s", file_path)
                continue

            try:
                file_path.write_text(content, encoding="utf-8")
                exported.append(file_path)
                logger.info("Exported: %s", file_path)
            except OSError as e:
                logger.error("Failed to export %s: %s", file_path, e)

    # Create README if needed
    readme_path = output_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(PROMPTS_README, encoding="utf-8")
        exported.append(readme_path)

    return exported


def get_custom_prompt_status(config: RagdConfig | None = None) -> dict[str, dict[str, str]]:
    """Check which prompts have custom overrides.

    Args:
        config: Optional config to check for config-based overrides

    Returns:
        Dictionary of category -> {name -> status}
        Status is one of: 'default', 'config_file', 'config_inline', 'custom_file'
    """
    status: dict[str, dict[str, str]] = {}

    for category, names in PROMPT_CATEGORIES.items():
        status[category] = {}
        for name in names:
            # Check conventional file location
            file_path = DEFAULT_PROMPTS_DIR / category / f"{name}.txt"
            if file_path.exists():
                status[category][name] = "custom_file"
            else:
                status[category][name] = "default"

    # Check config-based overrides
    if config:
        # Agentic prompts
        if config.agentic_prompts.relevance_eval:
            status["agentic"]["relevance_eval"] = (
                "config_file" if config.agentic_prompts.relevance_eval.file
                else "config_inline"
            )
        if config.agentic_prompts.query_rewrite:
            status["agentic"]["query_rewrite"] = (
                "config_file" if config.agentic_prompts.query_rewrite.file
                else "config_inline"
            )
        if config.agentic_prompts.faithfulness_eval:
            status["agentic"]["faithfulness_eval"] = (
                "config_file" if config.agentic_prompts.faithfulness_eval.file
                else "config_inline"
            )

        # Metadata prompts
        if config.metadata_prompts.summary:
            status["metadata"]["summary"] = (
                "config_file" if config.metadata_prompts.summary.file
                else "config_inline"
            )
        if config.metadata_prompts.classification:
            status["metadata"]["classification"] = (
                "config_file" if config.metadata_prompts.classification.file
                else "config_inline"
            )

        # Evaluation prompts
        if config.evaluation_prompts.faithfulness:
            status["evaluation"]["faithfulness"] = (
                "config_file" if config.evaluation_prompts.faithfulness.file
                else "config_inline"
            )
        if config.evaluation_prompts.answer_relevancy:
            status["evaluation"]["answer_relevancy"] = (
                "config_file" if config.evaluation_prompts.answer_relevancy.file
                else "config_inline"
            )

    return status
