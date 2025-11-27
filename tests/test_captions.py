"""Tests for caption removal module (F-051)."""

from __future__ import annotations

import pytest

from ragd.text.captions import remove_captions, has_caption_content


class TestRemoveCaptions:
    """Tests for caption removal function."""

    def test_removes_figure_captions(self) -> None:
        """Test removal of figure captions."""
        text = """Some content here.

Figure 1: Distribution of responses.

More content after.

Figure 2. Another chart showing data."""

        result = remove_captions(text)

        assert "Figure 1:" not in result
        assert "Figure 2." not in result
        assert "Some content here" in result
        assert "More content after" in result

    def test_removes_table_captions(self) -> None:
        """Test removal of table captions."""
        text = """Paragraph before table.

Table 1: Summary of results.

Paragraph after table."""

        result = remove_captions(text)

        assert "Table 1:" not in result
        assert "Paragraph before table" in result
        assert "Paragraph after table" in result

    def test_removes_photo_credits(self) -> None:
        """Test removal of photo credits."""
        text = """Article content.

Photo credit: Jane Smith

Photo: Getty Images

Credit: Reuters

More article content."""

        result = remove_captions(text)

        assert "Photo credit:" not in result
        assert "Photo: Getty" not in result
        assert "Credit: Reuters" not in result
        assert "Article content" in result
        assert "More article content" in result

    def test_removes_media_attributions(self) -> None:
        """Test removal of agency attributions."""
        text = """News content here.

(Getty Images)

John Smith / Reuters

(AP)

End of article."""

        result = remove_captions(text)

        assert "(Getty Images)" not in result
        assert "/ Reuters" not in result
        assert "(AP)" not in result
        assert "News content here" in result
        assert "End of article" in result

    def test_removes_alt_text_leakage(self) -> None:
        """Test removal of alt text that leaked into content."""
        text = """Real content.

Image description: A photo of a sunset.

[Image: Photo of city skyline]

More real content."""

        result = remove_captions(text)

        assert "Image description:" not in result
        assert "[Image:" not in result
        assert "Real content" in result
        assert "More real content" in result

    def test_preserves_regular_content(self) -> None:
        """Test that regular content is preserved."""
        text = """This is a paragraph about figures in general.

The table in the meeting room was large.

I took a photo of the sunset yesterday.

Here are some credits: good work ethic, dedication."""

        result = remove_captions(text)

        # All lines should be preserved (none match caption patterns)
        assert "This is a paragraph" in result
        assert "The table in the meeting room" in result
        assert "I took a photo" in result
        assert "Here are some credits:" in result

    def test_preserves_empty_lines(self) -> None:
        """Test that paragraph structure is preserved."""
        text = """First paragraph.

Second paragraph.

Third paragraph."""

        result = remove_captions(text)

        # Should have same number of blank lines
        assert result.count("\n\n") >= 1


class TestHasCaptionContent:
    """Tests for caption detection function."""

    def test_detects_figure_caption(self) -> None:
        """Test detection of figure captions."""
        text = "Figure 1: Test data distribution"
        assert has_caption_content(text) is True

    def test_detects_table_caption(self) -> None:
        """Test detection of table captions."""
        text = "Table 2. Results summary"
        assert has_caption_content(text) is True

    def test_detects_photo_credit(self) -> None:
        """Test detection of photo credits."""
        text = "Photo credit: John Smith"
        assert has_caption_content(text) is True

    def test_detects_agency_attribution(self) -> None:
        """Test detection of agency attributions."""
        text = "(Getty Images)"
        assert has_caption_content(text) is True

    def test_no_false_positive_for_regular_text(self) -> None:
        """Test no false positives for regular text."""
        text = "This is a normal paragraph without any captions."
        assert has_caption_content(text) is False

    def test_empty_text(self) -> None:
        """Test empty text returns False."""
        assert has_caption_content("") is False
