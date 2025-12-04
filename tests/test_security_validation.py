"""Tests for security validation module (F-082)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ragd.security.validation import (
    MAX_DOCUMENT_ID_LENGTH,
    MAX_PATH_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
    MAX_TAG_NAME_LENGTH,
    ValidationError,
    sanitise_search_query,
    validate_document_id,
    validate_file_size,
    validate_limit,
    validate_path,
    validate_tag_name,
)


class TestValidatePath:
    """Tests for path validation."""

    def test_valid_path(self, tmp_path: Path) -> None:
        """Test validation of a valid path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = validate_path(test_file, must_exist=True)
        assert result == test_file.resolve()

    def test_path_as_string(self, tmp_path: Path) -> None:
        """Test validation accepts string paths."""
        result = validate_path(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Test that path traversal is blocked."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Attempt to escape safe_dir
        malicious_path = safe_dir / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_path(malicious_path, base_dir=safe_dir)

        assert "outside allowed directory" in str(exc_info.value)
        assert exc_info.value.field == "path"

    def test_null_byte_rejected(self) -> None:
        """Test that null bytes in paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_path("/etc/passwd\x00.txt")

        assert "null bytes" in str(exc_info.value)

    def test_path_too_long(self) -> None:
        """Test that excessively long paths are rejected."""
        long_path = "a" * (MAX_PATH_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validate_path(long_path)

        assert "maximum length" in str(exc_info.value)

    def test_must_exist_fails_for_missing(self, tmp_path: Path) -> None:
        """Test that must_exist=True fails for missing files."""
        missing = tmp_path / "does_not_exist.txt"

        with pytest.raises(ValidationError) as exc_info:
            validate_path(missing, must_exist=True)

        assert "does not exist" in str(exc_info.value)

    def test_symlink_allowed_by_default(self, tmp_path: Path) -> None:
        """Test that symlinks are allowed by default."""
        target = tmp_path / "target.txt"
        target.write_text("target")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        result = validate_path(link)
        assert result.exists()

    def test_symlink_rejected_when_disabled(self, tmp_path: Path) -> None:
        """Test that symlinks are rejected when allow_symlinks=False."""
        target = tmp_path / "target.txt"
        target.write_text("target")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        with pytest.raises(ValidationError) as exc_info:
            validate_path(link, allow_symlinks=False)

        assert "Symbolic links" in str(exc_info.value)


class TestValidateDocumentId:
    """Tests for document ID validation."""

    def test_valid_document_id(self) -> None:
        """Test validation of valid document IDs."""
        assert validate_document_id("doc-123") == "doc-123"
        assert validate_document_id("DOC_456") == "DOC_456"
        assert validate_document_id("a1b2c3") == "a1b2c3"
        assert validate_document_id("X") == "X"

    def test_empty_document_id_rejected(self) -> None:
        """Test that empty document IDs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_document_id("")

        assert "cannot be empty" in str(exc_info.value)

    def test_document_id_too_long(self) -> None:
        """Test that overly long document IDs are rejected."""
        long_id = "a" * (MAX_DOCUMENT_ID_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validate_document_id(long_id)

        assert "maximum length" in str(exc_info.value)

    def test_special_characters_rejected(self) -> None:
        """Test that special characters are rejected."""
        invalid_ids = [
            "../passwd",
            "doc;rm -rf",
            "doc<script>",
            "doc\x00null",
            " leadingspace",
            "doc with spaces",
            "doc/slash",
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError):
                validate_document_id(invalid_id)

    def test_must_start_with_alphanumeric(self) -> None:
        """Test that document IDs must start with alphanumeric."""
        invalid_ids = ["_underscore", "-hyphen", "123numeric"]

        # Numeric start is actually valid
        assert validate_document_id("123numeric") == "123numeric"

        # But underscore and hyphen start are not
        with pytest.raises(ValidationError):
            validate_document_id("_underscore")

        with pytest.raises(ValidationError):
            validate_document_id("-hyphen")


class TestValidateTagName:
    """Tests for tag name validation."""

    def test_valid_tag_names(self) -> None:
        """Test validation of valid tag names."""
        assert validate_tag_name("important") == "important"
        assert validate_tag_name("project:alpha") == "project:alpha"
        assert validate_tag_name("topic/ml/transformers") == "topic/ml/transformers"
        assert validate_tag_name("status-draft") == "status-draft"
        assert validate_tag_name("A1_test") == "A1_test"

    def test_empty_tag_rejected(self) -> None:
        """Test that empty tags are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_tag_name("")

        assert "cannot be empty" in str(exc_info.value)

    def test_tag_too_long(self) -> None:
        """Test that overly long tags are rejected."""
        long_tag = "a" * (MAX_TAG_NAME_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validate_tag_name(long_tag)

        assert "maximum length" in str(exc_info.value)

    def test_special_characters_rejected(self) -> None:
        """Test that dangerous special characters are rejected."""
        invalid_tags = [
            "tag<script>",
            "tag;command",
            "tag\x00null",
            " leading",
            "with spaces",
        ]

        for invalid_tag in invalid_tags:
            with pytest.raises(ValidationError):
                validate_tag_name(invalid_tag)


class TestSanitiseSearchQuery:
    """Tests for search query sanitisation."""

    def test_simple_query_unchanged(self) -> None:
        """Test that simple queries pass through."""
        assert sanitise_search_query("hello world") == "hello world"

    def test_empty_query_rejected(self) -> None:
        """Test that empty queries are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            sanitise_search_query("")

        assert "cannot be empty" in str(exc_info.value)

    def test_query_too_long(self) -> None:
        """Test that overly long queries are rejected."""
        long_query = "a" * (MAX_SEARCH_QUERY_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            sanitise_search_query(long_query)

        assert "maximum length" in str(exc_info.value)

    def test_null_byte_rejected(self) -> None:
        """Test that null bytes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            sanitise_search_query("query\x00injection")

        assert "null bytes" in str(exc_info.value)

    def test_regex_characters_escaped(self) -> None:
        """Test that regex special characters are escaped."""
        result = sanitise_search_query("hello.*world")
        assert r"\." in result
        assert r"\*" in result

    def test_brackets_escaped(self) -> None:
        """Test that brackets are escaped."""
        result = sanitise_search_query("array[0]")
        assert r"\[" in result
        assert r"\]" in result


class TestValidateLimit:
    """Tests for limit validation."""

    def test_valid_limit(self) -> None:
        """Test validation of valid limits."""
        assert validate_limit(10) == 10
        assert validate_limit(1) == 1
        assert validate_limit(1000) == 1000

    def test_limit_below_minimum(self) -> None:
        """Test that limits below minimum are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_limit(0)

        assert "at least" in str(exc_info.value)

    def test_limit_above_maximum(self) -> None:
        """Test that limits above maximum are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_limit(10000, max_limit=1000)

        assert "cannot exceed" in str(exc_info.value)

    def test_custom_limits(self) -> None:
        """Test custom min/max limits."""
        assert validate_limit(5, min_limit=5, max_limit=10) == 5
        assert validate_limit(10, min_limit=5, max_limit=10) == 10

        with pytest.raises(ValidationError):
            validate_limit(4, min_limit=5, max_limit=10)

        with pytest.raises(ValidationError):
            validate_limit(11, min_limit=5, max_limit=10)


class TestValidateFileSize:
    """Tests for file size validation."""

    def test_valid_file_size(self, tmp_path: Path) -> None:
        """Test validation of files within size limit."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("small content")

        result = validate_file_size(test_file, max_size_mb=1.0)
        assert result == test_file

    def test_file_too_large(self, tmp_path: Path) -> None:
        """Test that large files are rejected."""
        test_file = tmp_path / "large.txt"
        # Write 2MB of data
        test_file.write_bytes(b"x" * (2 * 1024 * 1024))

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(test_file, max_size_mb=1.0)

        assert "exceeds limit" in str(exc_info.value)

    def test_missing_file(self, tmp_path: Path) -> None:
        """Test that missing files are rejected."""
        missing = tmp_path / "missing.txt"

        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(missing)

        assert "does not exist" in str(exc_info.value)
