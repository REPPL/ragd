"""Document metadata schema with Dublin Core and RAG extensions.

This module defines the DocumentMetadata dataclass which combines:
- Dublin Core standard metadata elements
- RAG-specific extensions for knowledge management
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DocumentMetadata:
    """Dublin Core-based metadata with RAG extensions.

    This dataclass follows the Dublin Core Metadata Initiative (DCMI) terms
    with additional fields specific to RAG knowledge base management.

    Schema version is tracked for forward/backward compatibility during
    upgrades. See ADR-0023 for migration strategy.
    """

    # Schema version for migration handling
    ragd_schema_version: str = "2.0"

    # Dublin Core Core Elements
    dc_title: str = ""
    dc_creator: list[str] = field(default_factory=list)
    dc_subject: list[str] = field(default_factory=list)
    dc_description: str = ""
    dc_date: datetime | None = None
    dc_type: str = ""  # "Research Paper", "Report", etc.
    dc_format: str = ""  # MIME type
    dc_identifier: str = ""  # DOI, ISBN, etc.
    dc_language: str = "en"

    # RAG Extensions
    ragd_source_path: str = ""
    ragd_source_hash: str = ""
    ragd_chunk_count: int = 0
    ragd_ingestion_date: datetime | None = None
    ragd_quality_score: float = 0.0
    ragd_tags: list[str] = field(default_factory=list)
    ragd_project: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage.

        Handles datetime serialisation to ISO format strings.
        """
        data = {
            "ragd_schema_version": self.ragd_schema_version,
            "dc_title": self.dc_title,
            "dc_creator": self.dc_creator,
            "dc_subject": self.dc_subject,
            "dc_description": self.dc_description,
            "dc_date": self.dc_date.isoformat() if self.dc_date else None,
            "dc_type": self.dc_type,
            "dc_format": self.dc_format,
            "dc_identifier": self.dc_identifier,
            "dc_language": self.dc_language,
            "ragd_source_path": self.ragd_source_path,
            "ragd_source_hash": self.ragd_source_hash,
            "ragd_chunk_count": self.ragd_chunk_count,
            "ragd_ingestion_date": (
                self.ragd_ingestion_date.isoformat()
                if self.ragd_ingestion_date
                else None
            ),
            "ragd_quality_score": self.ragd_quality_score,
            "ragd_tags": self.ragd_tags,
            "ragd_project": self.ragd_project,
        }
        return data

    def to_json(self) -> str:
        """Serialise to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentMetadata:
        """Create from stored dictionary.

        Handles datetime deserialisation from ISO format strings.
        """
        # Parse datetime fields
        dc_date = None
        if data.get("dc_date"):
            dc_date = datetime.fromisoformat(data["dc_date"])

        ingestion_date = None
        if data.get("ragd_ingestion_date"):
            ingestion_date = datetime.fromisoformat(data["ragd_ingestion_date"])

        return cls(
            ragd_schema_version=data.get("ragd_schema_version", "2.0"),
            dc_title=data.get("dc_title", ""),
            dc_creator=data.get("dc_creator", []),
            dc_subject=data.get("dc_subject", []),
            dc_description=data.get("dc_description", ""),
            dc_date=dc_date,
            dc_type=data.get("dc_type", ""),
            dc_format=data.get("dc_format", ""),
            dc_identifier=data.get("dc_identifier", ""),
            dc_language=data.get("dc_language", "en"),
            ragd_source_path=data.get("ragd_source_path", ""),
            ragd_source_hash=data.get("ragd_source_hash", ""),
            ragd_chunk_count=data.get("ragd_chunk_count", 0),
            ragd_ingestion_date=ingestion_date,
            ragd_quality_score=data.get("ragd_quality_score", 0.0),
            ragd_tags=data.get("ragd_tags", []),
            ragd_project=data.get("ragd_project", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DocumentMetadata:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        """Human-readable summary."""
        parts = []
        if self.dc_title:
            parts.append(f"Title: {self.dc_title}")
        if self.dc_creator:
            parts.append(f"Creator: {', '.join(self.dc_creator)}")
        if self.ragd_tags:
            parts.append(f"Tags: {', '.join(self.ragd_tags)}")
        if self.ragd_source_path:
            parts.append(f"Source: {self.ragd_source_path}")

        return " | ".join(parts) if parts else "(No metadata)"
