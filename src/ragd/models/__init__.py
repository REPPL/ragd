"""Model management for ragd.

This package provides model cards, recommendations, and fallback chain management
for LLM and embedding models used by ragd.
"""

from __future__ import annotations

from ragd.models.cards import (
    HardwareRequirements,
    ModelCapability,
    ModelCard,
    ModelType,
    get_installed_models,
    list_model_cards,
    load_model_card,
)
from ragd.models.recommender import (
    ModelRecommendation,
    ModelRecommender,
    UseCase,
    recommend_model,
)

__all__ = [
    # Model cards
    "ModelCard",
    "ModelCapability",
    "ModelType",
    "HardwareRequirements",
    "load_model_card",
    "list_model_cards",
    "get_installed_models",
    # Recommender
    "ModelRecommender",
    "ModelRecommendation",
    "UseCase",
    "recommend_model",
]
