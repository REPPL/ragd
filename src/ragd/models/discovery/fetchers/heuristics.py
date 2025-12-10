"""Heuristic model metadata inference from naming conventions.

Provides offline metadata inference based on common model naming patterns.
This is the fallback when no other sources are available.
"""

from __future__ import annotations

import re

from ragd.models.discovery.fetchers.base import FetchedMetadata


class HeuristicInferrer:
    """Infer model metadata from naming conventions.

    Works completely offline by analysing model name patterns.
    """

    # Patterns for model type detection
    EMBEDDING_PATTERNS = [
        "embed",
        "minilm",
        "bge",
        "e5-",
        "nomic",
        "jina",
        "gte",
        "instructor",
    ]
    RERANKER_PATTERNS = ["rerank", "cross-encoder"]
    VISION_PATTERNS = ["llava", "vision", "moondream", "bakllava", "colpali"]

    # Known model families and their context lengths
    CONTEXT_HEURISTICS: dict[str, int] = {
        "llama3.2": 8192,
        "llama3.1": 131072,
        "llama3": 8192,
        "llama2": 4096,
        "qwen2.5": 32768,
        "qwen2": 32768,
        "qwen": 8192,
        "mistral": 8192,
        "mixtral": 32768,
        "phi3": 4096,
        "phi": 2048,
        "gemma2": 8192,
        "gemma": 8192,
        "codellama": 16384,
        "deepseek": 32768,
        "command-r": 128000,
        "solar": 4096,
        "falcon": 2048,
        "vicuna": 4096,
    }

    # Known model families
    FAMILY_PATTERNS: dict[str, str] = {
        "llama": "llama",
        "qwen": "qwen",
        "mistral": "mistral",
        "mixtral": "mixtral",
        "phi": "phi",
        "gemma": "gemma",
        "codellama": "codellama",
        "deepseek": "deepseek",
        "command": "command",
        "solar": "solar",
        "falcon": "falcon",
        "vicuna": "vicuna",
        "nomic": "nomic",
        "minilm": "minilm",
        "bge": "bge",
        "jina": "jina",
    }

    # Capability inference based on model family
    CAPABILITY_PATTERNS: dict[str, list[str]] = {
        "llama": ["chat", "summarisation", "extraction", "rag_generation"],
        "qwen": ["chat", "reasoning", "coding", "summarisation", "rag_generation"],
        "mistral": ["chat", "reasoning", "summarisation", "rag_generation"],
        "codellama": ["coding", "chat"],
        "deepseek": ["coding", "reasoning", "chat"],
        "phi": ["chat", "summarisation"],
        "gemma": ["chat", "summarisation"],
    }

    def fetch(self, model_id: str) -> FetchedMetadata:
        """Infer metadata from model name patterns.

        Args:
            model_id: Model identifier (e.g., 'llama3.2:3b')

        Returns:
            FetchedMetadata with inferred values
        """
        name_lower = model_id.lower()

        # Infer model type
        model_type = self._infer_model_type(name_lower)

        # Infer family
        family = self._infer_family(name_lower)

        # Infer parameters
        parameters = self._infer_parameters(model_id)

        # Infer context length
        context_length = self._infer_context_length(name_lower)

        # Infer capabilities
        capabilities = self._infer_capabilities(family, model_type)

        # Generate human-readable name
        name = self._generate_name(model_id, parameters)

        # Estimate hardware requirements from parameters
        hardware_min_ram = self._estimate_ram(parameters)

        return FetchedMetadata(
            source="heuristic",
            model_id=model_id,
            name=name,
            model_type=model_type,
            family=family,
            parameters=parameters,
            context_length=context_length,
            capabilities=capabilities,
            hardware_min_ram_gb=hardware_min_ram,
        )

    def is_available(self) -> bool:
        """Heuristic inference is always available (offline).

        Returns:
            Always True
        """
        return True

    def _infer_model_type(self, name_lower: str) -> str:
        """Infer model type from name patterns.

        Args:
            name_lower: Lowercase model name

        Returns:
            Model type string
        """
        if any(p in name_lower for p in self.EMBEDDING_PATTERNS):
            return "embedding"
        if any(p in name_lower for p in self.RERANKER_PATTERNS):
            return "reranker"
        if any(p in name_lower for p in self.VISION_PATTERNS):
            return "vision"
        return "llm"

    def _infer_family(self, name_lower: str) -> str | None:
        """Infer model family from name.

        Args:
            name_lower: Lowercase model name

        Returns:
            Family name or None
        """
        for pattern, family in self.FAMILY_PATTERNS.items():
            if pattern in name_lower:
                return family
        return None

    def _infer_parameters(self, model_id: str) -> float | None:
        """Extract parameter count from model name.

        Args:
            model_id: Model identifier

        Returns:
            Parameters in billions or None
        """
        # Common patterns: "7b", ":3b", "-7b", "70b"
        patterns = [
            r"[:\-_](\d+\.?\d*)b\b",  # :3b, -7b, _70b
            r"\b(\d+\.?\d*)b\b",  # 7b, 70b
            r"(\d+\.?\d*)B\b",  # 7B, 70B
        ]

        for pattern in patterns:
            match = re.search(pattern, model_id, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def _infer_context_length(self, name_lower: str) -> int | None:
        """Infer context length from model family.

        Args:
            name_lower: Lowercase model name

        Returns:
            Context length in tokens or None
        """
        for family_pattern, context_length in self.CONTEXT_HEURISTICS.items():
            if family_pattern in name_lower:
                return context_length
        return None

    def _infer_capabilities(
        self, family: str | None, model_type: str
    ) -> list[str]:
        """Infer capabilities from family and type.

        Args:
            family: Model family
            model_type: Model type

        Returns:
            List of capability strings
        """
        if model_type == "embedding":
            return ["semantic_search", "clustering", "classification"]
        if model_type == "reranker":
            return ["semantic_search"]
        if model_type == "vision":
            return ["vision", "chat"]

        # LLM capabilities
        if family and family in self.CAPABILITY_PATTERNS:
            return self.CAPABILITY_PATTERNS[family].copy()

        # Default LLM capabilities
        return ["chat", "summarisation"]

    def _generate_name(self, model_id: str, parameters: float | None) -> str:
        """Generate human-readable name.

        Args:
            model_id: Model identifier
            parameters: Parameter count

        Returns:
            Human-readable name
        """
        # Remove provider prefix if present
        name = model_id.split("/")[-1]

        # Capitalise appropriately
        parts = name.replace(":", " ").replace("-", " ").split()
        capitalised = []
        for part in parts:
            if part.lower().endswith("b") and part[:-1].replace(".", "").isdigit():
                # Parameter count like "3b" -> "3B"
                capitalised.append(part.upper())
            else:
                capitalised.append(part.capitalize())

        return " ".join(capitalised)

    def _estimate_ram(self, parameters: float | None) -> float | None:
        """Estimate minimum RAM from parameter count.

        Assumes Q4 quantisation (~0.5 bytes per parameter).

        Args:
            parameters: Parameter count in billions

        Returns:
            Estimated minimum RAM in GB
        """
        if parameters is None:
            return None

        # Q4 quantisation: ~0.5 bytes per parameter
        # Add ~20% overhead for KV cache and system
        estimated_gb = parameters * 0.5 * 1.2

        # Round up to nearest 0.5 GB
        return round(estimated_gb * 2) / 2
