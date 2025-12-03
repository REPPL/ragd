"""Tests for Auto-Tag Suggestions (F-061)."""

import pytest
from datetime import datetime
from pathlib import Path

from ragd.metadata.suggestions import (
    SuggestionConfig,
    SuggestionEngine,
    TagSuggestion,
)
from ragd.metadata.store import MetadataStore
from ragd.metadata.schema import DocumentMetadata
from ragd.metadata.tags import TagManager


class TestTagSuggestion:
    """Tests for TagSuggestion class."""

    def test_create_basic(self):
        """Create basic suggestion."""
        suggestion = TagSuggestion(
            tag_name="finance",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )

        assert suggestion.tag_name == "finance"
        assert suggestion.source == "keybert"
        assert suggestion.confidence == 0.85
        assert suggestion.status == "pending"

    def test_from_keybert(self):
        """Create suggestion from KeyBERT extraction."""
        suggestion = TagSuggestion.from_keybert(
            doc_id="doc-123",
            keyword="Machine Learning",
            score=0.89,
            source_text="This is about machine learning",
        )

        assert suggestion.tag_name == "machine-learning"  # Normalised
        assert suggestion.source == "keybert"
        assert suggestion.confidence == 0.89
        assert suggestion.source_model == "all-MiniLM-L6-v2"

    def test_from_llm(self):
        """Create suggestion from LLM classification."""
        suggestion = TagSuggestion.from_llm(
            doc_id="doc-123",
            category="Financial Report",
            confidence=0.95,
            model="llama3.2:3b",
        )

        assert suggestion.tag_name == "financial-report"
        assert suggestion.source == "llm"
        assert suggestion.confidence == 0.95

    def test_from_ner(self):
        """Create suggestion from NER extraction."""
        suggestion = TagSuggestion.from_ner(
            doc_id="doc-123",
            entity="OpenAI",
            entity_type="ORG",
            confidence=0.92,
        )

        assert suggestion.tag_name == "org/openai"  # Namespaced
        assert suggestion.source == "ner"
        assert suggestion.confidence == 0.92

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        suggestion = TagSuggestion(
            tag_name="test",
            source="keybert",
            confidence=0.8,
            doc_id="doc-123",
            status="pending",
            source_text="sample text",
            source_model="model-v1",
        )

        data = suggestion.to_dict()
        restored = TagSuggestion.from_dict(data)

        assert restored.tag_name == suggestion.tag_name
        assert restored.source == suggestion.source
        assert restored.confidence == suggestion.confidence
        assert restored.status == suggestion.status


class TestSuggestionConfig:
    """Tests for SuggestionConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = SuggestionConfig()

        assert config.enabled is True
        assert config.min_confidence == 0.7
        assert config.max_suggestions_per_doc == 10


class TestSuggestionEngine:
    """Tests for SuggestionEngine class."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create SuggestionEngine with temporary database."""
        db_path = tmp_path / "test.db"
        store = MetadataStore(db_path)
        tag_manager = TagManager(store)

        # Add test document
        metadata = DocumentMetadata(dc_title="Test Document")
        store.set("doc-123", metadata)

        return SuggestionEngine(db_path, tag_manager)

    def test_add_suggestion(self, engine):
        """Add a suggestion."""
        suggestion = TagSuggestion(
            tag_name="finance",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )

        assert engine.add(suggestion) is True

    def test_add_below_threshold_skipped(self, engine):
        """Suggestions below confidence threshold are skipped."""
        engine.configure(SuggestionConfig(min_confidence=0.8))

        suggestion = TagSuggestion(
            tag_name="low-confidence",
            source="keybert",
            confidence=0.5,  # Below 0.8 threshold
            doc_id="doc-123",
        )

        assert engine.add(suggestion) is False

    def test_add_duplicate_skipped(self, engine):
        """Duplicate suggestions are skipped."""
        suggestion = TagSuggestion(
            tag_name="finance",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )

        assert engine.add(suggestion) is True
        assert engine.add(suggestion) is False  # Duplicate

    def test_add_batch(self, engine):
        """Add multiple suggestions."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="keybert", confidence=0.85, doc_id="doc-123"),
            TagSuggestion(tag_name="c", source="keybert", confidence=0.9, doc_id="doc-123"),
        ]

        added = engine.add_batch(suggestions)
        assert added == 3

    def test_get_for_doc(self, engine):
        """Get suggestions for a document."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="llm", confidence=0.9, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        results = engine.get_for_doc("doc-123")
        assert len(results) == 2
        # Sorted by confidence descending
        assert results[0].tag_name == "b"
        assert results[1].tag_name == "a"

    def test_get_for_doc_filter_status(self, engine):
        """Filter suggestions by status."""
        suggestion = TagSuggestion(
            tag_name="test",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )
        engine.add(suggestion)

        # Get pending
        pending = engine.get_for_doc("doc-123", status="pending")
        assert len(pending) == 1

        # Confirm it
        engine.confirm("doc-123", ["test"])

        # No longer pending
        pending = engine.get_for_doc("doc-123", status="pending")
        assert len(pending) == 0

    def test_get_pending_docs(self, engine):
        """Get documents with pending suggestions."""
        # Initially none
        assert engine.get_pending_docs() == []

        # Add suggestion
        suggestion = TagSuggestion(
            tag_name="test",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )
        engine.add(suggestion)

        docs = engine.get_pending_docs()
        assert "doc-123" in docs

    def test_confirm_suggestions(self, engine):
        """Confirm suggestions and apply as tags."""
        suggestions = [
            TagSuggestion(tag_name="finance", source="keybert", confidence=0.85, doc_id="doc-123"),
            TagSuggestion(tag_name="report", source="llm", confidence=0.9, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        confirmed = engine.confirm("doc-123", ["finance"])
        assert confirmed == 1

        # Check tag was added
        tags = engine._tag_manager.get_names("doc-123")
        assert "finance" in tags

        # Check suggestion status
        remaining = engine.get_for_doc("doc-123", status="pending")
        assert len(remaining) == 1
        assert remaining[0].tag_name == "report"

    def test_confirm_all_above_confidence(self, engine):
        """Confirm all suggestions above confidence threshold."""
        suggestions = [
            TagSuggestion(tag_name="high", source="keybert", confidence=0.9, doc_id="doc-123"),
            TagSuggestion(tag_name="medium", source="keybert", confidence=0.75, doc_id="doc-123"),
            TagSuggestion(tag_name="low", source="keybert", confidence=0.71, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        confirmed = engine.confirm("doc-123", min_confidence=0.8)
        assert confirmed == 1

        tags = engine._tag_manager.get_names("doc-123")
        assert "high" in tags
        assert "medium" not in tags

    def test_reject_suggestions(self, engine):
        """Reject suggestions."""
        suggestion = TagSuggestion(
            tag_name="irrelevant",
            source="keybert",
            confidence=0.85,
            doc_id="doc-123",
        )
        engine.add(suggestion)

        rejected = engine.reject("doc-123", ["irrelevant"])
        assert rejected == 1

        # Should not appear in pending
        pending = engine.get_for_doc("doc-123", status="pending")
        assert len(pending) == 0

        # Should appear in rejected
        all_suggestions = engine.get_for_doc("doc-123")
        assert all_suggestions[0].status == "rejected"

    def test_reject_all_pending(self, engine):
        """Reject all pending suggestions for a document."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="keybert", confidence=0.85, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        rejected = engine.reject("doc-123")  # No specific tags = reject all
        assert rejected == 2

    def test_clear_for_doc(self, engine):
        """Clear all suggestions for a document."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="keybert", confidence=0.85, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        cleared = engine.clear_for_doc("doc-123")
        assert cleared == 2

        remaining = engine.get_for_doc("doc-123")
        assert len(remaining) == 0

    def test_count_pending(self, engine):
        """Count pending suggestions."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="keybert", confidence=0.85, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)

        assert engine.count_pending("doc-123") == 2
        assert engine.count_pending() == 2  # Total

    def test_stats(self, engine):
        """Get suggestion statistics."""
        suggestions = [
            TagSuggestion(tag_name="a", source="keybert", confidence=0.8, doc_id="doc-123"),
            TagSuggestion(tag_name="b", source="llm", confidence=0.85, doc_id="doc-123"),
        ]
        engine.add_batch(suggestions)
        engine.confirm("doc-123", ["a"])

        stats = engine.stats()

        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["confirmed"] == 1
        assert stats["by_source"]["keybert"] == 1
        assert stats["by_source"]["llm"] == 1
        assert stats["docs_with_pending"] == 1
        assert stats["total"] == 2
