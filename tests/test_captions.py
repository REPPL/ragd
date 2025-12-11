"""Tests for caption removal module (F-051)."""

from __future__ import annotations

import pytest

from ragd.text.captions import remove_captions, has_caption_content


class TestRemoveCaptions:
    """Tests for caption removal function.

    Note: Tests use substantial content to avoid triggering the safety check
    that prevents removing >50% of content.
    """

    def test_removes_figure_captions(self) -> None:
        """Test removal of figure captions."""
        # Use substantial content so caption removal is < 50% of document
        text = """This is the introduction to our research paper. We conducted
an extensive study on user behaviour patterns over the course of several
months. The data collection involved multiple surveys and interviews with
participants from diverse backgrounds. Our methodology was carefully designed
to ensure statistical significance.

Figure 1: Distribution of responses.

The results show several interesting trends that warrant further investigation.
We found that most participants exhibited similar patterns in their daily
routines. The variations were primarily attributable to demographic factors
such as age and location.

Figure 2. Another chart showing data.

In conclusion, our findings suggest that there are significant opportunities
for improving user engagement through targeted interventions."""

        result = remove_captions(text)

        assert "Figure 1:" not in result
        assert "Figure 2." not in result
        assert "introduction to our research paper" in result
        assert "results show several interesting trends" in result

    def test_removes_table_captions(self) -> None:
        """Test removal of table captions."""
        text = """This section presents our quantitative findings from the survey.
We collected data from over 500 participants across multiple demographics.
The response rate was approximately 75%, which exceeded our expectations.

Table 1: Summary of results.

The data was analysed using standard statistical methods including regression
analysis and correlation matrices. All results were verified for significance."""

        result = remove_captions(text)

        assert "Table 1:" not in result
        assert "quantitative findings" in result
        assert "data was analysed" in result

    def test_removes_photo_credits(self) -> None:
        """Test removal of photo credits."""
        text = """The event attracted thousands of visitors from across the region.
Local businesses reported increased sales during the festival period. Community
leaders praised the organisation and called for the event to become an annual
tradition. Many families brought children to enjoy the various activities.

Photo credit: Jane Smith

The weather was particularly favourable this year, with sunny skies throughout
the weekend. Organisers had prepared contingency plans for rain but these were
not needed. Several food vendors sold out of their supplies by Saturday evening.

Photo: Getty Images

Security personnel reported no major incidents during the three-day event.
Traffic management was handled efficiently by local police working with
volunteer marshals. Parking was available at multiple designated locations.

Credit: Reuters

Overall, the event was deemed a significant success by all stakeholders involved."""

        result = remove_captions(text)

        assert "Photo credit:" not in result
        assert "Photo: Getty" not in result
        assert "Credit: Reuters" not in result
        assert "event attracted thousands" in result
        assert "event was deemed a significant success" in result

    def test_preserves_media_attributions(self) -> None:
        """Test that agency attributions are preserved (no longer removed).

        In v1.0.0a4, media attribution patterns (Getty, Reuters, AP, etc.) were
        removed due to high false positive risk - "AP" matches words like "Chapter".
        """
        text = """Breaking news from the international summit today as world leaders
gathered to discuss pressing economic concerns. The meeting lasted several
hours with multiple sessions covering trade agreements and climate policy.
Delegates from over 40 countries participated in the discussions.

(Getty Images)

Representatives spoke about the importance of multilateral cooperation in
addressing global challenges. Several bilateral meetings were also held on
the sidelines of the main conference. The host nation provided excellent
facilities and hospitality for all participants throughout the event.

John Smith / Reuters

Press conferences were held throughout the day with regular updates on
progress. Journalists from around the world covered the proceedings.

(AP)

The summit concluded with a joint statement outlining key areas of agreement
and a commitment to future collaboration between participating nations."""

        result = remove_captions(text)

        # Media attributions are now PRESERVED (no longer removed)
        assert "(Getty Images)" in result
        assert "/ Reuters" in result
        assert "(AP)" in result
        assert "Breaking news from the international summit" in result
        assert "summit concluded with a joint statement" in result

    def test_removes_alt_text_leakage(self) -> None:
        """Test removal of alt text that leaked into content."""
        text = """Our new product line has been designed with sustainability in mind.
Every component has been carefully selected to minimise environmental impact
while maintaining the highest quality standards. The manufacturing process
uses renewable energy sources and produces minimal waste.

Image description: A photo of a sunset.

Customer feedback has been overwhelmingly positive since the launch last month.
Sales figures have exceeded initial projections by a significant margin. The
marketing campaign emphasised our commitment to environmental responsibility.

[Image: Photo of city skyline]

We are now expanding distribution to international markets with strong demand
from European and Asian retailers. Our supply chain has been optimised to
handle the increased volume while maintaining delivery timelines."""

        result = remove_captions(text)

        assert "Image description:" not in result
        assert "[Image:" not in result
        assert "product line has been designed" in result
        assert "expanding distribution" in result

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

    def test_detects_image_marker(self) -> None:
        """Test detection of image markers."""
        text = "(Image)"
        assert has_caption_content(text) is True

    def test_no_false_positive_for_regular_text(self) -> None:
        """Test no false positives for regular text."""
        text = "This is a normal paragraph without any captions."
        assert has_caption_content(text) is False

    def test_empty_text(self) -> None:
        """Test empty text returns False."""
        assert has_caption_content("") is False


class TestRemoveCaptionsSafetyCheck:
    """Tests for the safety check that prevents over-aggressive removal."""

    def test_safety_check_prevents_over_removal(self) -> None:
        """Test that safety check prevents removing >50% of content."""
        # Short text where captions make up >50%
        text = """Short intro.

Figure 1: Caption line.
Figure 2: Another caption.
Figure 3: Third caption."""

        result = remove_captions(text)

        # Should NOT remove captions because it would delete >50% of content
        assert "Figure 1:" in result
        assert "Short intro" in result

    def test_safety_check_allows_reasonable_removal(self) -> None:
        """Test that removal works when captions are < 50% of content."""
        # Longer text where captions are small portion
        text = """This is a substantial introduction paragraph with many words.
It continues on for multiple lines with detailed content about the topic.
The paragraph provides context and background information.

Figure 1: Simple caption.

This is another substantial paragraph following the figure caption.
It also contains multiple sentences with meaningful content.
The document continues with more important information."""

        result = remove_captions(text)

        # Should remove caption because remaining content is >50%
        assert "Figure 1:" not in result
        assert "substantial introduction" in result
        assert "substantial paragraph" in result
