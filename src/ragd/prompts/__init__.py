"""Prompt template management for ragd.

This package provides infrastructure for loading, customising, and managing
prompt templates used throughout ragd.

v1.0.5: Configuration Exposure
"""

from ragd.prompts.loader import (
    DEFAULT_PROMPTS_DIR,
    ensure_prompts_dir,
    export_default_prompts,
    get_prompt,
    list_prompt_categories,
    list_prompts,
)

__all__ = [
    "DEFAULT_PROMPTS_DIR",
    "ensure_prompts_dir",
    "export_default_prompts",
    "get_prompt",
    "list_prompt_categories",
    "list_prompts",
]
