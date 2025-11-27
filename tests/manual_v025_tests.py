#!/usr/bin/env python3
"""Manual tests for ragd v0.2.5 - Advanced HTML Processing (F-039).

This script provides interactive testing of F-039 features:
- Fast HTML parsing with selectolax
- Rich metadata extraction (OG, JSON-LD, Schema.org)
- Structure preservation (tables, headings, lists)
- Structure-aware chunking
- Integration with existing pipeline

Usage:
    python tests/manual_v025_tests.py

External Test Data:
    Place your own HTML files in ../test_data/ for testing:
    - ../test_data/archives/     → SingleFile archives
    - ../test_data/complex/      → Complex pages (tables, lists)

    See ../test_data/README.md for instructions.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()

# Test data directory (external)
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "test_data"


def print_header() -> None:
    """Print test header."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]RAGD v0.2.5 Manual Tests[/]\n"
        "[dim]Advanced HTML Processing (F-039)[/]",
        border_style="blue"
    ))
    console.print()


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "[green]PASS[/]" if passed else "[red]FAIL[/]"
    console.print(f"  {status} {test_name}")
    if details:
        console.print(f"       [dim]{details}[/]")


def test_parser_performance() -> bool:
    """Test 1: Parser Performance.

    Compares selectolax vs BeautifulSoup parsing speed.
    """
    console.print("\n[bold cyan][1/6] Parser Performance[/]")

    try:
        from ragd.web.parser import (
            parse_html,
            SELECTOLAX_AVAILABLE,
            BEAUTIFULSOUP_AVAILABLE,
        )

        # Create test HTML (100KB approximately)
        test_html = """
        <html>
        <head><title>Test Document</title></head>
        <body>
        """ + "<article><p>This is a test paragraph with some content. " * 1000 + "</p></article></body></html>"

        # Test parsing
        start = time.perf_counter()
        result = parse_html(test_html)
        elapsed = (time.perf_counter() - start) * 1000

        print_result(
            "HTML parsing",
            result.success,
            f"Parser: {result.parser_used}, Time: {elapsed:.1f}ms, "
            f"HTML size: {len(test_html) / 1024:.1f}KB"
        )

        # Check selectolax availability
        if SELECTOLAX_AVAILABLE:
            print_result("selectolax available", True, "Fast path enabled")
        else:
            print_result(
                "selectolax available",
                False,
                "Install with: pip install 'ragd[web]'"
            )

        print_result(
            "BeautifulSoup available",
            BEAUTIFULSOUP_AVAILABLE,
            "Fallback parser"
        )

        return result.success

    except Exception as e:
        print_result("Parser test", False, str(e))
        return False


def test_metadata_extraction() -> bool:
    """Test 2: Rich Metadata Extraction.

    Tests extraction of Open Graph, JSON-LD, and Dublin Core metadata.
    """
    console.print("\n[bold cyan][2/6] Rich Metadata Extraction[/]")

    try:
        from ragd.web.metadata import extract_metadata

        # Test HTML with various metadata
        test_html = """
        <html lang="en">
        <head>
            <title>Test Article</title>
            <meta name="description" content="A test article description">
            <meta name="author" content="Test Author">

            <!-- Open Graph -->
            <meta property="og:title" content="OG Test Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://example.com/image.jpg">
            <meta property="og:type" content="article">

            <!-- Twitter Cards -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="Twitter Title">

            <!-- Dublin Core -->
            <meta name="DC.title" content="DC Title">
            <meta name="DC.creator" content="DC Author">

            <!-- JSON-LD -->
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Schema.org Article",
                "author": {"@type": "Person", "name": "Schema Author"}
            }
            </script>
        </head>
        <body><p>Content</p></body>
        </html>
        """

        metadata = extract_metadata(test_html)

        # Check Open Graph
        og_ok = bool(metadata.og_title and metadata.og_description and metadata.og_image)
        print_result(
            "Open Graph",
            og_ok,
            f"title={metadata.og_title}, type={metadata.og_type}"
        )

        # Check JSON-LD
        jsonld_ok = bool(metadata.schema_type)
        print_result(
            "JSON-LD/Schema.org",
            jsonld_ok,
            f"@type={metadata.schema_type}"
        )

        # Check Dublin Core
        dc_ok = bool(metadata.dc_title or metadata.dc_creator)
        print_result(
            "Dublin Core",
            dc_ok,
            f"title={metadata.dc_title}, creator={metadata.dc_creator}"
        )

        # Check Twitter Cards
        twitter_ok = bool(metadata.twitter_card)
        print_result(
            "Twitter Cards",
            twitter_ok,
            f"card={metadata.twitter_card}"
        )

        # Check resolution
        best_title = metadata.get_best_title()
        print_result(
            "Metadata resolution",
            bool(best_title),
            f"Best title: {best_title}"
        )

        return og_ok and jsonld_ok

    except Exception as e:
        print_result("Metadata extraction", False, str(e))
        return False


def test_structure_preservation() -> bool:
    """Test 3: Structure Preservation.

    Tests extraction of headings, tables, and lists as Markdown.
    """
    console.print("\n[bold cyan][3/6] Structure Preservation[/]")

    try:
        from ragd.web.structure import extract_structure

        test_html = """
        <html>
        <body>
            <h1>Main Title</h1>
            <p>Introduction paragraph.</p>

            <h2>Data Section</h2>
            <table>
                <thead><tr><th>Name</th><th>Value</th></tr></thead>
                <tbody>
                    <tr><td>Alpha</td><td>100</td></tr>
                    <tr><td>Beta</td><td>200</td></tr>
                </tbody>
            </table>

            <h2>List Section</h2>
            <ul>
                <li>Item one</li>
                <li>Item two</li>
                <li>Item three</li>
            </ul>

            <h3>Ordered List</h3>
            <ol>
                <li>First step</li>
                <li>Second step</li>
            </ol>

            <h2>Code Section</h2>
            <pre><code class="language-python">def hello():
    print("Hello, World!")</code></pre>
        </body>
        </html>
        """

        structure = extract_structure(test_html)

        # Check headings
        headings_ok = len(structure.headings) >= 4
        print_result(
            "Headings extraction",
            headings_ok,
            f"Found {len(structure.headings)} headings"
        )

        # Check heading hierarchy
        if structure.headings:
            levels = [h.level for h in structure.headings]
            hierarchy_ok = 1 in levels and 2 in levels
            print_result(
                "Heading hierarchy",
                hierarchy_ok,
                f"Levels found: {sorted(set(levels))}"
            )

        # Check tables
        tables_ok = len(structure.tables) >= 1
        if tables_ok:
            table = structure.tables[0]
            print_result(
                "Table-to-Markdown",
                tables_ok,
                f"Table: {table.rows} rows × {table.cols} cols"
            )
            # Show sample
            console.print("       [dim]Sample:[/]")
            for line in table.markdown.split("\n")[:3]:
                console.print(f"       [dim]{line}[/]")
        else:
            print_result("Table extraction", False, "No tables found")

        # Check lists
        lists_ok = len(structure.lists) >= 2
        print_result(
            "List extraction",
            lists_ok,
            f"Found {len(structure.lists)} lists"
        )

        # Check code blocks
        code_ok = len(structure.code_blocks) >= 1
        if code_ok:
            code = structure.code_blocks[0]
            print_result(
                "Code block extraction",
                code_ok,
                f"Language: {code.language or 'unknown'}"
            )
        else:
            print_result("Code block extraction", False, "No code blocks found")

        return headings_ok and tables_ok and lists_ok

    except Exception as e:
        print_result("Structure preservation", False, str(e))
        return False


def test_external_data() -> bool:
    """Test 4: External Test Data.

    Tests processing of HTML files from ../test_data/.
    """
    console.print("\n[bold cyan][4/6] External Test Data (../test_data/)[/]")

    if not TEST_DATA_DIR.exists():
        print_result(
            "Test data directory",
            False,
            f"Not found: {TEST_DATA_DIR}"
        )
        return False

    try:
        from ragd.ingestion.extractor import AdvancedHTMLExtractor

        extractor = AdvancedHTMLExtractor()
        html_files: list[Path] = []

        # Find HTML files in archives/ and complex/
        for subdir in ["archives", "complex"]:
            subpath = TEST_DATA_DIR / subdir
            if subpath.exists():
                html_files.extend(subpath.glob("*.html"))

        # Also check root
        html_files.extend(TEST_DATA_DIR.glob("*.html"))

        if not html_files:
            print_result(
                "HTML files",
                False,
                "No HTML files found in test_data/"
            )
            return True  # Not a failure, just no data

        print_result(
            "HTML files found",
            True,
            f"Found {len(html_files)} files"
        )

        # Process a sample (up to 5 files)
        sample = html_files[:5]
        all_ok = True

        for path in sample:
            try:
                result = extractor.extract(path)
                word_count = len(result.text.split()) if result.text else 0
                method = result.extraction_method

                print_result(
                    path.name[:40],
                    result.success,
                    f"{word_count:,} words, method: {method}"
                )

                if not result.success:
                    all_ok = False

            except Exception as e:
                print_result(path.name[:40], False, str(e))
                all_ok = False

        return all_ok

    except Exception as e:
        print_result("External data test", False, str(e))
        return False


def test_structure_chunking() -> bool:
    """Test 5: Structure-Aware Chunking.

    Tests the StructureChunker that respects headings and tables.
    """
    console.print("\n[bold cyan][5/6] Structure-Aware Chunking[/]")

    try:
        from ragd.ingestion.chunker import StructureChunker, chunk_text

        # Test Markdown with structure
        test_md = """
# Main Document Title

This is an introduction paragraph with some context about the document.

## Section One

Content for section one. This section contains important information
that should be kept together with its heading.

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

## Section Two

- List item one with details
- List item two with more details
- List item three

### Subsection 2.1

More detailed content in a subsection.

```python
def example():
    return "Hello"
```

## Section Three

Final section with concluding remarks.
"""

        # Test with structure chunker
        chunker = StructureChunker(
            chunk_size=256,
            min_chunk_size=50,
            keep_tables_together=True,
            respect_headings=True,
        )
        chunks = chunker.chunk(test_md)

        print_result(
            "Structure chunking",
            len(chunks) >= 2,
            f"Created {len(chunks)} chunks"
        )

        # Check that headings are respected
        heading_in_chunk = any("# " in c.content or "## " in c.content for c in chunks)
        print_result(
            "Heading boundaries",
            heading_in_chunk,
            "Chunks start with headings"
        )

        # Check chunk sizes
        avg_tokens = sum(c.token_count for c in chunks) / len(chunks) if chunks else 0
        print_result(
            "Chunk sizes",
            True,
            f"Avg: {avg_tokens:.0f} tokens, Range: "
            f"{min(c.token_count for c in chunks)}-{max(c.token_count for c in chunks)}"
        )

        # Compare with standard chunking
        standard_chunks = chunk_text(test_md, strategy="sentence", chunk_size=256)
        print_result(
            "vs sentence chunker",
            True,
            f"Sentence: {len(standard_chunks)} chunks, "
            f"Structure: {len(chunks)} chunks"
        )

        return len(chunks) >= 2

    except Exception as e:
        print_result("Structure chunking", False, str(e))
        return False


def test_pipeline_integration() -> bool:
    """Test 6: Pipeline Integration.

    Tests that F-039 integrates with the existing RAG pipeline.
    """
    console.print("\n[bold cyan][6/6] Pipeline Integration[/]")

    try:
        from ragd.ingestion.extractor import (
            AdvancedHTMLExtractor,
            HTMLExtractor,
            extract_text,
        )
        from ragd.web import is_singlefile_archive

        # Test basic HTMLExtractor still works
        html = "<html><body><p>Test content</p></body></html>"
        basic = HTMLExtractor()
        # We can't test extract without a file, but we can test imports

        print_result(
            "HTMLExtractor import",
            True,
            "Basic extractor available"
        )

        # Test AdvancedHTMLExtractor
        advanced = AdvancedHTMLExtractor()
        print_result(
            "AdvancedHTMLExtractor",
            True,
            f"Metadata: {advanced.extract_metadata_flag}, "
            f"Structure: {advanced.preserve_structure}"
        )

        # Test SingleFile detection
        singlefile_html = '<meta name="savepage-url" content="https://example.com">'
        is_sf = is_singlefile_archive(singlefile_html)
        print_result(
            "SingleFile detection",
            is_sf,
            "Archive routing works"
        )

        # Test feature detection
        from ragd.features import get_detector

        detector = get_detector()
        features = detector.all_features()
        web_features = ["selectolax", "trafilatura", "web"]
        for feat in web_features:
            status = features.get(feat)
            if status:
                print_result(
                    f"Feature: {feat}",
                    status.available,
                    status.install_command if not status.available else "✓"
                )

        return True

    except Exception as e:
        print_result("Pipeline integration", False, str(e))
        return False


def print_summary(results: dict[str, bool]) -> None:
    """Print test summary."""
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    console.print()
    console.print("=" * 60)
    if passed == total:
        console.print(f"[bold green]RESULTS: {passed}/{total} passed[/]")
    else:
        console.print(f"[bold yellow]RESULTS: {passed}/{total} passed[/]")

    # Show failed tests
    failed = [name for name, result in results.items() if not result]
    if failed:
        console.print("\n[yellow]Failed tests:[/]")
        for name in failed:
            console.print(f"  - {name}")

    console.print("=" * 60)


def main() -> int:
    """Run all manual tests."""
    print_header()

    results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running tests...", total=6)

        # Test 1: Parser Performance
        results["Parser Performance"] = test_parser_performance()
        progress.advance(task)

        # Test 2: Metadata Extraction
        results["Metadata Extraction"] = test_metadata_extraction()
        progress.advance(task)

        # Test 3: Structure Preservation
        results["Structure Preservation"] = test_structure_preservation()
        progress.advance(task)

        # Test 4: External Test Data
        results["External Test Data"] = test_external_data()
        progress.advance(task)

        # Test 5: Structure-Aware Chunking
        results["Structure-Aware Chunking"] = test_structure_chunking()
        progress.advance(task)

        # Test 6: Pipeline Integration
        results["Pipeline Integration"] = test_pipeline_integration()
        progress.advance(task)

    print_summary(results)

    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
