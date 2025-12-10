"""Model card builder from fetched metadata.

Merges metadata from multiple sources into a complete ModelCard,
using priority-based merging where higher-priority sources override
lower-priority ones.
"""

from __future__ import annotations

import logging
from typing import Any

from ragd.models.cards import (
    HardwareRequirements,
    ModelCapability,
    ModelCard,
    ModelType,
)
from ragd.models.discovery.fetchers.base import FetchedMetadata

logger = logging.getLogger(__name__)


class CardBuilder:
    """Build ModelCard by merging metadata from multiple sources.

    Sources are merged in priority order, with higher-priority sources
    overriding lower-priority ones for non-null values.
    """

    # Priority order (higher index = higher priority)
    SOURCE_PRIORITY = ["heuristic", "huggingface", "ollama"]

    def build(self, metadata_list: list[FetchedMetadata]) -> ModelCard:
        """Build a ModelCard from multiple metadata sources.

        Args:
            metadata_list: List of FetchedMetadata from different sources

        Returns:
            Merged ModelCard instance
        """
        if not metadata_list:
            raise ValueError("At least one metadata source required")

        # Sort by priority (lower priority first, so higher priority overwrites)
        sorted_metadata = sorted(
            metadata_list,
            key=lambda m: self.SOURCE_PRIORITY.index(m.source)
            if m.source in self.SOURCE_PRIORITY
            else -1,
        )

        # Merge all metadata
        merged = self._merge_metadata(sorted_metadata)

        # Build ModelCard from merged data
        return self._build_card(merged)

    def _merge_metadata(
        self, metadata_list: list[FetchedMetadata]
    ) -> dict[str, Any]:
        """Merge metadata from multiple sources.

        Later sources override earlier ones for non-null values.

        Args:
            metadata_list: Sorted list of metadata (low to high priority)

        Returns:
            Merged metadata dictionary
        """
        merged: dict[str, Any] = {
            "model_id": None,
            "name": None,
            "model_type": None,
            "family": None,
            "parameters": None,
            "context_length": None,
            "quantisation": None,
            "description": None,
            "capabilities": [],
            "licence": None,
            "hardware_min_ram_gb": None,
            "sources": [],
        }

        for meta in metadata_list:
            merged["sources"].append(meta.source)

            if meta.model_id:
                merged["model_id"] = meta.model_id
            if meta.name:
                merged["name"] = meta.name
            if meta.model_type:
                merged["model_type"] = meta.model_type
            if meta.family:
                merged["family"] = meta.family
            if meta.parameters is not None:
                merged["parameters"] = meta.parameters
            if meta.context_length is not None:
                merged["context_length"] = meta.context_length
            if meta.quantisation:
                merged["quantisation"] = meta.quantisation
            if meta.description:
                merged["description"] = meta.description
            if meta.capabilities:
                merged["capabilities"] = meta.capabilities
            if meta.licence:
                merged["licence"] = meta.licence
            if meta.hardware_min_ram_gb is not None:
                merged["hardware_min_ram_gb"] = meta.hardware_min_ram_gb

        return merged

    def _build_card(self, merged: dict[str, Any]) -> ModelCard:
        """Build ModelCard from merged metadata.

        Args:
            merged: Merged metadata dictionary

        Returns:
            ModelCard instance
        """
        model_id = merged["model_id"] or "unknown"

        # Parse model type
        model_type_str = merged["model_type"] or "llm"
        try:
            model_type = ModelType(model_type_str)
        except ValueError:
            model_type = ModelType.LLM

        # Parse capabilities
        capabilities = []
        for cap_str in merged.get("capabilities", []):
            try:
                capabilities.append(ModelCapability(cap_str))
            except ValueError:
                logger.debug("Unknown capability: %s", cap_str)

        # Build hardware requirements
        hardware = None
        if merged.get("hardware_min_ram_gb"):
            min_ram = merged["hardware_min_ram_gb"]
            hardware = HardwareRequirements(
                min_ram_gb=min_ram,
                recommended_ram_gb=min_ram * 1.5,
                min_vram_gb=min_ram * 0.8 if merged.get("parameters", 0) >= 7 else None,
            )

        # Build description
        description = merged.get("description") or self._generate_description(merged)

        # Build metadata dict with extra info
        metadata: dict[str, Any] = {}
        if merged.get("quantisation"):
            metadata["quantisation"] = merged["quantisation"]
        if merged.get("family"):
            metadata["family"] = merged["family"]
        metadata["auto_discovered"] = True
        metadata["sources"] = merged.get("sources", [])

        return ModelCard(
            id=model_id,
            name=merged.get("name") or model_id,
            model_type=model_type,
            provider="ollama",  # Default provider
            description=description,
            capabilities=capabilities,
            hardware=hardware,
            context_length=merged.get("context_length"),
            parameters=merged.get("parameters"),
            licence=merged.get("licence"),
            metadata=metadata,
        )

    def _generate_description(self, merged: dict[str, Any]) -> str:
        """Generate a description from metadata.

        Args:
            merged: Merged metadata dictionary

        Returns:
            Generated description string
        """
        parts = []

        model_type = merged.get("model_type", "llm").upper()
        if model_type == "LLM":
            model_type = "language model"
        elif model_type == "EMBEDDING":
            model_type = "embedding model"

        if merged.get("parameters"):
            parts.append(f"{merged['parameters']:.1f}B parameter {model_type}")
        else:
            parts.append(f"A {model_type}")

        if merged.get("family"):
            parts[0] = f"{merged['family'].capitalize()} {parts[0]}"

        if merged.get("context_length"):
            ctx = merged["context_length"]
            if ctx >= 1000:
                parts.append(f"with {ctx // 1000}K context window")
            else:
                parts.append(f"with {ctx} token context")

        return " ".join(parts) + "."
