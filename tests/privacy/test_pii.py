"""Tests for ragd.privacy.pii module."""

import pytest

from ragd.privacy.pii import (
    PIIDetector,
    PIIEngine,
    PIIEntity,
    PIIEntityType,
    PIIReport,
    PIIResult,
    RegexDetector,
    is_presidio_available,
    is_spacy_available,
    redact_pii,
)


class TestRegexDetector:
    """Tests for RegexDetector class."""

    def test_detect_email(self) -> None:
        """Detects email addresses."""
        detector = RegexDetector()
        text = "Contact me at john.doe@company.org"

        entities = detector.detect(text)

        assert len(entities) == 1
        assert entities[0].entity_type == PIIEntityType.EMAIL_ADDRESS
        assert entities[0].value == "john.doe@company.org"
        assert entities[0].confidence == 0.9

    def test_detect_multiple_emails(self) -> None:
        """Detects multiple email addresses."""
        detector = RegexDetector()
        text = "Send to alice@test.org and bob@company.co.uk"

        entities = detector.detect(text)

        assert len(entities) == 2

    def test_detect_phone_uk(self) -> None:
        """Detects UK phone numbers."""
        detector = RegexDetector()
        text = "Call us on +44 7700900123"

        entities = detector.detect(text)

        phone_entities = [e for e in entities if e.entity_type == PIIEntityType.PHONE_NUMBER]
        assert len(phone_entities) >= 1

    def test_detect_phone_us_allowlisted(self) -> None:
        """555 phone numbers are allowlisted."""
        detector = RegexDetector()
        text = "Phone: (555) 123-4567"

        entities = detector.detect(text)

        # 555 numbers should be filtered out by allowlist
        phone_entities = [e for e in entities if e.entity_type == PIIEntityType.PHONE_NUMBER]
        assert len(phone_entities) == 0

    def test_detect_real_phone(self) -> None:
        """Detects non-555 phone numbers."""
        detector = RegexDetector()
        text = "Phone: (212) 123-4567"

        entities = detector.detect(text)

        phone_entities = [e for e in entities if e.entity_type == PIIEntityType.PHONE_NUMBER]
        assert len(phone_entities) == 1

    def test_detect_credit_card(self) -> None:
        """Detects credit card numbers."""
        detector = RegexDetector()
        text = "Card: 4532-1234-5678-9012"

        entities = detector.detect(text)

        cc_entities = [e for e in entities if e.entity_type == PIIEntityType.CREDIT_CARD]
        assert len(cc_entities) == 1

    def test_detect_ssn(self) -> None:
        """Detects US Social Security Numbers."""
        detector = RegexDetector()
        text = "SSN: 123-45-6789"

        entities = detector.detect(text)

        ssn_entities = [e for e in entities if e.entity_type == PIIEntityType.US_SSN]
        assert len(ssn_entities) == 1

    def test_detect_uk_nino(self) -> None:
        """Detects UK National Insurance Numbers."""
        detector = RegexDetector()
        text = "NI Number: AB 12 34 56 C"

        entities = detector.detect(text)

        nino_entities = [e for e in entities if e.entity_type == PIIEntityType.UK_NINO]
        assert len(nino_entities) == 1

    def test_detect_ip_address(self) -> None:
        """Detects IP addresses."""
        detector = RegexDetector()
        text = "Server at 192.168.1.100"

        entities = detector.detect(text)

        ip_entities = [e for e in entities if e.entity_type == PIIEntityType.IP_ADDRESS]
        assert len(ip_entities) == 1

    def test_allowlist_example_domain(self) -> None:
        """Example domains are allowlisted."""
        detector = RegexDetector()
        text = "Send to test@example.com"

        entities = detector.detect(text)

        # example.com should be allowlisted
        email_entities = [e for e in entities if e.entity_type == PIIEntityType.EMAIL_ADDRESS]
        assert len(email_entities) == 0

    def test_enabled_types_filter(self) -> None:
        """Can filter by enabled entity types."""
        detector = RegexDetector(
            enabled_types=[PIIEntityType.EMAIL_ADDRESS]
        )
        text = "Email: john@test.org, Phone: (212) 555-1234"

        entities = detector.detect(text)

        # Should only detect emails
        assert all(e.entity_type == PIIEntityType.EMAIL_ADDRESS for e in entities)


class TestPIIResult:
    """Tests for PIIResult class."""

    def test_has_pii(self) -> None:
        """has_pii property works correctly."""
        result_with_pii = PIIResult(
            entities=[
                PIIEntity(
                    entity_type=PIIEntityType.EMAIL_ADDRESS,
                    value="test@test.com",
                    start=0,
                    end=13,
                    confidence=0.9,
                    engine=PIIEngine.REGEX,
                )
            ]
        )
        result_without_pii = PIIResult()

        assert result_with_pii.has_pii is True
        assert result_without_pii.has_pii is False

    def test_by_type(self) -> None:
        """by_type counts entities correctly."""
        result = PIIResult(
            entities=[
                PIIEntity(PIIEntityType.EMAIL_ADDRESS, "a@b.com", 0, 7, 0.9, PIIEngine.REGEX),
                PIIEntity(PIIEntityType.EMAIL_ADDRESS, "c@d.com", 10, 17, 0.9, PIIEngine.REGEX),
                PIIEntity(PIIEntityType.PHONE_NUMBER, "123", 20, 23, 0.8, PIIEngine.REGEX),
            ]
        )

        by_type = result.by_type()
        assert by_type["EMAIL_ADDRESS"] == 2
        assert by_type["PHONE_NUMBER"] == 1

    def test_high_low_confidence(self) -> None:
        """Filters by confidence threshold."""
        result = PIIResult(
            entities=[
                PIIEntity(PIIEntityType.EMAIL_ADDRESS, "a@b.com", 0, 7, 0.95, PIIEngine.REGEX),
                PIIEntity(PIIEntityType.EMAIL_ADDRESS, "c@d.com", 10, 17, 0.7, PIIEngine.REGEX),
            ]
        )

        assert len(result.high_confidence(0.85)) == 1
        assert len(result.low_confidence(0.85)) == 1


class TestPIIReport:
    """Tests for PIIReport class."""

    def test_from_results(self) -> None:
        """Creates report from results."""
        results = [
            PIIResult(
                entities=[
                    PIIEntity(PIIEntityType.EMAIL_ADDRESS, "a@b.com", 0, 7, 0.9, PIIEngine.REGEX),
                ]
            ),
            PIIResult(
                entities=[
                    PIIEntity(PIIEntityType.PERSON, "John", 0, 4, 0.8, PIIEngine.SPACY),
                ]
            ),
        ]

        report = PIIReport.from_results("test.txt", results)

        assert report.document_path == "test.txt"
        assert report.total_pii_found == 2
        assert report.by_type["EMAIL_ADDRESS"] == 1
        assert report.by_type["PERSON"] == 1

    def test_empty_results(self) -> None:
        """Handles empty results."""
        report = PIIReport.from_results("test.txt", [])

        assert report.total_pii_found == 0
        assert report.summary == "No PII detected"


class TestPIIDetector:
    """Tests for PIIDetector class."""

    def test_regex_engine(self) -> None:
        """Regex engine works."""
        detector = PIIDetector(engine=PIIEngine.REGEX)
        result = detector.detect("Contact john@test.org")

        assert result.has_pii
        assert result.engine_used == PIIEngine.REGEX

    def test_hybrid_engine_fallback(self) -> None:
        """Hybrid falls back to regex when others unavailable."""
        detector = PIIDetector(engine=PIIEngine.HYBRID)

        # Should have at least regex available
        assert PIIEngine.REGEX in detector.available_engines

    def test_available_engines(self) -> None:
        """Lists available engines."""
        detector = PIIDetector(engine=PIIEngine.HYBRID)

        engines = detector.available_engines
        assert PIIEngine.REGEX in engines

    def test_deduplication(self) -> None:
        """Removes overlapping entities."""
        detector = PIIDetector(engine=PIIEngine.REGEX)
        # This text should only produce one entity per pattern match
        result = detector.detect("Email: valid@domain.org")

        # Count by position - shouldn't have overlapping
        positions = set()
        for e in result.entities:
            position_key = (e.start, e.end)
            assert position_key not in positions
            positions.add(position_key)

    def test_generate_report(self) -> None:
        """Generates report from multiple texts."""
        detector = PIIDetector(engine=PIIEngine.REGEX)
        texts = [
            "Email: alice@company.org",
            "Card: 4532-1234-5678-9012",
        ]

        report = detector.generate_report("test.pdf", texts)

        assert report.document_path == "test.pdf"
        assert report.total_pii_found >= 2


class TestRedactPII:
    """Tests for redact_pii function."""

    def test_basic_redaction(self) -> None:
        """Basic redaction works."""
        text = "My email is john@test.org"
        entities = [
            PIIEntity(
                entity_type=PIIEntityType.EMAIL_ADDRESS,
                value="john@test.org",
                start=12,
                end=25,
                confidence=0.9,
                engine=PIIEngine.REGEX,
            )
        ]

        redacted = redact_pii(text, entities)

        assert "john@test.org" not in redacted
        assert "█" in redacted
        assert redacted == "My email is █████████████"

    def test_multiple_redactions(self) -> None:
        """Multiple entities redacted correctly."""
        text = "Name: John, Email: john@test.org"
        entities = [
            PIIEntity(PIIEntityType.PERSON, "John", 6, 10, 0.9, PIIEngine.SPACY),
            PIIEntity(PIIEntityType.EMAIL_ADDRESS, "john@test.org", 19, 32, 0.9, PIIEngine.REGEX),
        ]

        redacted = redact_pii(text, entities)

        assert "John" not in redacted
        assert "john@test.org" not in redacted

    def test_custom_redaction_char(self) -> None:
        """Custom redaction character works."""
        text = "SSN: 123-45-6789"
        entities = [
            PIIEntity(PIIEntityType.US_SSN, "123-45-6789", 5, 16, 0.9, PIIEngine.REGEX),
        ]

        redacted = redact_pii(text, entities, redaction_char="X")

        assert redacted == "SSN: XXXXXXXXXXX"

    def test_empty_entities(self) -> None:
        """No redaction when no entities."""
        text = "No PII here"

        redacted = redact_pii(text, [])

        assert redacted == text


class TestAvailabilityChecks:
    """Tests for dependency availability checks."""

    def test_presidio_check_returns_boolean(self) -> None:
        """is_presidio_available returns boolean."""
        result = is_presidio_available()
        assert isinstance(result, bool)

    def test_spacy_check_returns_boolean(self) -> None:
        """is_spacy_available returns boolean."""
        result = is_spacy_available()
        assert isinstance(result, bool)


@pytest.mark.skipif(
    not is_presidio_available(),
    reason="Presidio not available"
)
class TestPresidioDetector:
    """Tests for PresidioDetector (requires Presidio)."""

    def test_detect_email(self) -> None:
        """Presidio detects emails."""
        from ragd.privacy.pii import PresidioDetector

        detector = PresidioDetector()
        entities = detector.detect("Contact john.doe@example.com")

        email_entities = [
            e for e in entities
            if e.entity_type == PIIEntityType.EMAIL_ADDRESS
            or e.entity_type == "EMAIL_ADDRESS"
        ]
        assert len(email_entities) >= 1

    def test_detect_person(self) -> None:
        """Presidio detects person names."""
        from ragd.privacy.pii import PresidioDetector

        detector = PresidioDetector()
        entities = detector.detect("Meeting with John Smith tomorrow")

        person_entities = [
            e for e in entities
            if e.entity_type == PIIEntityType.PERSON
            or e.entity_type == "PERSON"
        ]
        assert len(person_entities) >= 1


@pytest.mark.skipif(
    not is_spacy_available(),
    reason="spaCy not available"
)
class TestSpacyDetector:
    """Tests for SpacyDetector (requires spaCy)."""

    def test_detect_person(self) -> None:
        """spaCy detects person names."""
        from ragd.privacy.pii import SpacyDetector

        detector = SpacyDetector()
        entities = detector.detect("Barack Obama was the president")

        person_entities = [
            e for e in entities
            if e.entity_type == PIIEntityType.PERSON
        ]
        assert len(person_entities) >= 1

    def test_detect_location(self) -> None:
        """spaCy detects locations."""
        from ragd.privacy.pii import SpacyDetector

        detector = SpacyDetector()
        entities = detector.detect("I live in London, United Kingdom")

        location_entities = [
            e for e in entities
            if e.entity_type == PIIEntityType.LOCATION
        ]
        assert len(location_entities) >= 1
