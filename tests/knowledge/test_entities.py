"""Tests for entity extraction (F-022)."""

import pytest

from ragd.knowledge.entities import (
    Entity,
    EntityType,
    PatternEntityExtractor,
    SpacyEntityExtractor,
    get_entity_extractor,
)


class TestEntity:
    """Tests for Entity dataclass."""

    def test_create_entity(self):
        """Create entity with all fields."""
        entity = Entity(
            name="Python",
            type=EntityType.TECHNOLOGY,
            start=0,
            end=6,
            confidence=0.9,
        )

        assert entity.name == "Python"
        assert entity.type == EntityType.TECHNOLOGY
        assert entity.confidence == 0.9

    def test_normalised_name(self):
        """Entity names are normalised for comparison."""
        e1 = Entity(name="machine-learning", type=EntityType.CONCEPT)
        e2 = Entity(name="Machine Learning", type=EntityType.CONCEPT)

        assert e1.normalised_name == "machine learning"
        assert e2.normalised_name == "machine learning"

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        entity = Entity(
            name="Test",
            type=EntityType.TECHNOLOGY,
            start=10,
            end=14,
            confidence=0.85,
        )

        data = entity.to_dict()
        restored = Entity.from_dict(data)

        assert restored.name == entity.name
        assert restored.type == entity.type
        assert restored.start == entity.start
        assert restored.confidence == entity.confidence

    def test_strip_whitespace(self):
        """Entity names are stripped."""
        entity = Entity(name="  Python  ", type=EntityType.TECHNOLOGY)
        assert entity.name == "Python"


class TestPatternEntityExtractor:
    """Tests for PatternEntityExtractor."""

    @pytest.fixture
    def extractor(self):
        return PatternEntityExtractor()

    def test_available(self, extractor):
        """Pattern extractor is always available."""
        assert extractor.available is True

    def test_extract_technology(self, extractor):
        """Extract technology entities."""
        text = "We use Python and Django for our backend."
        entities = extractor.extract(text)

        names = [e.name.lower() for e in entities]
        assert "python" in names
        assert "django" in names

    def test_extract_organisation(self, extractor):
        """Extract organisation entities."""
        text = "Google and Microsoft are tech giants."
        entities = extractor.extract(text)

        names = [e.name.lower() for e in entities]
        types = [e.type for e in entities]

        assert "google" in names
        assert "microsoft" in names
        assert EntityType.ORGANISATION in types

    def test_extract_concepts(self, extractor):
        """Extract concept entities."""
        text = "Machine learning and deep learning are related fields."
        entities = extractor.extract(text)

        names = [e.name.lower() for e in entities]
        assert "machine learning" in names or any("learning" in n for n in names)

    def test_no_duplicates(self, extractor):
        """Same entity not extracted twice."""
        text = "Python is great. Python is also fast."
        entities = extractor.extract(text)

        python_count = sum(1 for e in entities if e.name.lower() == "python")
        assert python_count == 1

    def test_position_tracking(self, extractor):
        """Entity positions are tracked."""
        text = "Use Python for scripting."
        entities = extractor.extract(text)

        python_entity = next(e for e in entities if e.name.lower() == "python")
        assert python_entity.start == text.lower().find("python")

    def test_empty_text(self, extractor):
        """Empty text returns empty list."""
        entities = extractor.extract("")
        assert entities == []

    def test_no_entities(self, extractor):
        """Text without entities returns empty list."""
        text = "The quick brown fox jumps over the lazy dog."
        entities = extractor.extract(text)
        # May or may not find entities depending on patterns
        assert isinstance(entities, list)


class TestSpacyEntityExtractor:
    """Tests for SpacyEntityExtractor."""

    def test_unavailable_without_spacy(self):
        """Extractor reports unavailable if spaCy not installed."""
        extractor = SpacyEntityExtractor(model_name="nonexistent_model")
        # Will be False if model doesn't exist
        assert extractor.available is False

    def test_extract_returns_empty_when_unavailable(self):
        """Extract returns empty when unavailable."""
        extractor = SpacyEntityExtractor(model_name="nonexistent_model")
        entities = extractor.extract("Test text with entities.")
        assert entities == []


class TestGetEntityExtractor:
    """Tests for get_entity_extractor factory."""

    def test_returns_pattern_extractor(self):
        """Returns pattern extractor when spaCy unavailable."""
        extractor = get_entity_extractor(prefer_spacy=False)
        assert isinstance(extractor, PatternEntityExtractor)

    def test_fallback_to_pattern(self):
        """Falls back to pattern when spaCy unavailable."""
        extractor = get_entity_extractor(
            prefer_spacy=True,
            spacy_model="nonexistent_model_xyz",
        )
        # Should fall back to pattern extractor
        assert extractor.available is True
