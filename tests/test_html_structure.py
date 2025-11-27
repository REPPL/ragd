"""Tests for HTML structure extraction module (F-039).

Tests the structure preservation functionality including heading hierarchy,
table-to-Markdown conversion, list extraction, and code block handling.
"""

import pytest

from ragd.web.structure import (
    CodeBlockInfo,
    HeadingInfo,
    HTMLStructure,
    ListInfo,
    TableInfo,
    extract_structure,
    get_text_with_structure,
)


class TestHeadingExtraction:
    """Tests for heading hierarchy extraction."""

    def test_extract_single_heading(self) -> None:
        """Extract a single heading."""
        html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <p>Content</p>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.headings) == 1
        assert structure.headings[0].level == 1
        assert structure.headings[0].text == "Main Title"

    def test_extract_heading_hierarchy(self) -> None:
        """Extract multiple heading levels."""
        html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <h2>Section 1</h2>
            <p>Content</p>
            <h2>Section 2</h2>
            <h3>Subsection 2.1</h3>
            <p>More content</p>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.headings) >= 4
        levels = [h.level for h in structure.headings]
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels

    def test_heading_with_id(self) -> None:
        """Extract heading with id attribute."""
        html = """
        <html>
        <body>
            <h2 id="section-one">Section One</h2>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.headings) == 1
        assert structure.headings[0].id == "section-one"

    def test_empty_heading_ignored(self) -> None:
        """Empty headings are ignored."""
        html = """
        <html>
        <body>
            <h1></h1>
            <h2>Valid Heading</h2>
        </body>
        </html>
        """
        structure = extract_structure(html)

        # Only non-empty headings should be extracted
        assert all(h.text for h in structure.headings)

    def test_heading_outline(self) -> None:
        """Get document outline from headings."""
        html = """
        <html>
        <body>
            <h1>Title</h1>
            <h2>Section A</h2>
            <h3>Subsection A1</h3>
            <h2>Section B</h2>
        </body>
        </html>
        """
        structure = extract_structure(html)
        outline = structure.get_heading_outline()

        assert "Title" in outline
        assert "Section A" in outline
        assert "Subsection A1" in outline


class TestTableExtraction:
    """Tests for table-to-Markdown extraction."""

    def test_extract_simple_table(self) -> None:
        """Extract a simple table."""
        html = """
        <html>
        <body>
            <table>
                <thead>
                    <tr><th>Name</th><th>Age</th></tr>
                </thead>
                <tbody>
                    <tr><td>Alice</td><td>30</td></tr>
                    <tr><td>Bob</td><td>25</td></tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.tables) == 1
        table = structure.tables[0]
        assert table.rows == 3  # Header + 2 data rows
        assert table.cols == 2
        assert "| Name | Age |" in table.markdown
        assert "| Alice | 30 |" in table.markdown

    def test_table_without_thead(self) -> None:
        """Extract table without explicit thead."""
        html = """
        <html>
        <body>
            <table>
                <tr><td>Cell 1</td><td>Cell 2</td></tr>
                <tr><td>Cell 3</td><td>Cell 4</td></tr>
            </table>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.tables) == 1
        # Should still generate valid Markdown table
        assert "|" in structure.tables[0].markdown

    def test_table_with_special_characters(self) -> None:
        """Handle special characters in table cells."""
        html = """
        <html>
        <body>
            <table>
                <tr><td>Pipe | char</td><td>Normal</td></tr>
            </table>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.tables) == 1
        # Pipe should be escaped
        assert "\\|" in structure.tables[0].markdown or "Pipe" in structure.tables[0].markdown

    def test_multiple_tables(self) -> None:
        """Extract multiple tables."""
        html = """
        <html>
        <body>
            <table><tr><td>Table 1</td></tr></table>
            <p>Some text</p>
            <table><tr><td>Table 2</td></tr></table>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.tables) == 2

    def test_get_all_tables_markdown(self) -> None:
        """Get all tables as combined Markdown."""
        html = """
        <html>
        <body>
            <table><tr><td>A</td></tr></table>
            <table><tr><td>B</td></tr></table>
        </body>
        </html>
        """
        structure = extract_structure(html)
        all_md = structure.get_all_tables_markdown()

        assert "A" in all_md
        assert "B" in all_md


class TestListExtraction:
    """Tests for list structure extraction."""

    def test_extract_unordered_list(self) -> None:
        """Extract unordered list."""
        html = """
        <html>
        <body>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.lists) == 1
        lst = structure.lists[0]
        assert lst.list_type == "unordered"
        assert lst.items == 3
        assert "- Item 1" in lst.markdown
        assert "- Item 2" in lst.markdown

    def test_extract_ordered_list(self) -> None:
        """Extract ordered list."""
        html = """
        <html>
        <body>
            <ol>
                <li>First</li>
                <li>Second</li>
                <li>Third</li>
            </ol>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.lists) == 1
        lst = structure.lists[0]
        assert lst.list_type == "ordered"
        assert lst.items == 3
        assert "1. First" in lst.markdown
        assert "2. Second" in lst.markdown

    def test_multiple_lists(self) -> None:
        """Extract multiple lists of different types."""
        html = """
        <html>
        <body>
            <ul><li>Bullet</li></ul>
            <ol><li>Number</li></ol>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.lists) == 2
        types = {lst.list_type for lst in structure.lists}
        assert "ordered" in types
        assert "unordered" in types


class TestCodeBlockExtraction:
    """Tests for code block extraction."""

    def test_extract_code_block(self) -> None:
        """Extract code block."""
        html = """
        <html>
        <body>
            <pre><code>def hello():
    print("Hello")</code></pre>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.code_blocks) == 1
        code = structure.code_blocks[0]
        assert "def hello" in code.code
        assert "print" in code.code

    def test_extract_code_with_language(self) -> None:
        """Extract code block with language class."""
        html = """
        <html>
        <body>
            <pre><code class="language-python">print("Hello")</code></pre>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.code_blocks) == 1
        code = structure.code_blocks[0]
        assert code.language == "python"

    def test_extract_pre_without_code(self) -> None:
        """Extract pre without nested code tag."""
        html = """
        <html>
        <body>
            <pre>Plain preformatted text</pre>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.code_blocks) == 1
        assert "Plain preformatted" in structure.code_blocks[0].code


class TestGetTextWithStructure:
    """Tests for combined text extraction with structure."""

    def test_includes_headings_outline(self) -> None:
        """Text includes heading outline."""
        html = """
        <html>
        <body>
            <h1>Title</h1>
            <h2>Section</h2>
            <p>Content</p>
        </body>
        </html>
        """
        text = get_text_with_structure(html)

        assert "Title" in text
        assert "Section" in text

    def test_includes_tables(self) -> None:
        """Text includes tables."""
        html = """
        <html>
        <body>
            <p>Intro</p>
            <table><tr><td>Data</td></tr></table>
        </body>
        </html>
        """
        text = get_text_with_structure(html)

        assert "Data" in text

    def test_removes_scripts(self) -> None:
        """Scripts are removed from text."""
        html = """
        <html>
        <body>
            <script>alert('evil');</script>
            <p>Good content</p>
        </body>
        </html>
        """
        text = get_text_with_structure(html)

        assert "alert" not in text
        assert "Good content" in text


class TestStructureToDict:
    """Tests for structure serialisation."""

    def test_to_dict(self) -> None:
        """Structure can be converted to dictionary."""
        html = """
        <html>
        <body>
            <h1>Title</h1>
            <table><tr><td>A</td></tr></table>
            <ul><li>Item</li></ul>
            <pre><code>code</code></pre>
        </body>
        </html>
        """
        structure = extract_structure(html)
        data = structure.to_dict()

        assert "headings" in data
        assert "tables_count" in data
        assert "lists_count" in data
        assert "code_blocks_count" in data

        assert data["tables_count"] == 1
        assert data["lists_count"] == 1
        assert data["code_blocks_count"] == 1


class TestEmptyContent:
    """Tests for handling empty/minimal HTML."""

    def test_empty_html(self) -> None:
        """Handle empty HTML."""
        html = ""
        structure = extract_structure(html)

        assert structure.headings == []
        assert structure.tables == []
        assert structure.lists == []

    def test_html_without_structure(self) -> None:
        """Handle HTML without structural elements."""
        html = "<html><body><p>Just text</p></body></html>"
        structure = extract_structure(html)

        assert structure.headings == []
        assert structure.tables == []
        assert structure.lists == []
        assert structure.code_blocks == []


class TestComplexStructures:
    """Tests for complex HTML structures."""

    def test_nested_tables_handled(self) -> None:
        """Handle nested tables (extract both)."""
        html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>
                        <table><tr><td>Nested</td></tr></table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        structure = extract_structure(html)

        # Should extract both tables (or at least not crash)
        assert len(structure.tables) >= 1

    def test_mixed_content(self) -> None:
        """Handle page with mixed content types."""
        html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <p>Introduction paragraph.</p>
            <h2>Data Section</h2>
            <table>
                <tr><th>Col A</th><th>Col B</th></tr>
                <tr><td>1</td><td>2</td></tr>
            </table>
            <h2>List Section</h2>
            <ul>
                <li>Item one</li>
                <li>Item two</li>
            </ul>
            <h2>Code Section</h2>
            <pre><code class="language-python">print("test")</code></pre>
        </body>
        </html>
        """
        structure = extract_structure(html)

        assert len(structure.headings) >= 3
        assert len(structure.tables) == 1
        assert len(structure.lists) == 1
        assert len(structure.code_blocks) == 1
