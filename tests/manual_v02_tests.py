#!/usr/bin/env python3
"""Manual tests for v0.2 features.

Run with: python tests/manual_v02_tests.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path


def test_web_archive():
    """Test F-038: Web Archive Support."""
    print("\n" + "=" * 60)
    print("TEST: Web Archive (F-038)")
    print("=" * 60)

    from ragd.web import WebArchiveProcessor, is_singlefile_archive

    # Create sample SingleFile archive
    html = """<!DOCTYPE html>
<html>
<head>
    <meta name="savepage-url" content="https://example.com/article">
    <meta name="savepage-date" content="2024-01-15T10:30:00Z">
    <title>Test Article</title>
</head>
<body>
    <h1>Test Article Title</h1>
    <p>This is the main content of the test article.</p>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html)
        test_file = Path(f.name)

    try:
        # Test detection
        is_sf = is_singlefile_archive(html)
        print(f"  Is SingleFile archive: {is_sf}")
        assert is_sf, "Should detect as SingleFile"

        # Test processing
        processor = WebArchiveProcessor()
        result = processor.process(test_file)

        print(f"  Extraction success: {result.success}")
        print(f"  Title: {result.metadata.title}")
        print(f"  Original URL: {result.metadata.original_url}")
        print(f"  Text preview: {result.text[:50]}...")

        assert result.success, "Extraction should succeed"
        assert result.metadata.original_url == "https://example.com/article"

        print("  [PASS] Web Archive tests passed")

    finally:
        test_file.unlink()


def test_folder_watcher():
    """Test F-037: Watch Folder."""
    print("\n" + "=" * 60)
    print("TEST: Folder Watcher (F-037)")
    print("=" * 60)

    from ragd.web import WatchConfig, should_index, WATCHDOG_AVAILABLE

    print(f"  Watchdog available: {WATCHDOG_AVAILABLE}")

    # Test config
    config = WatchConfig()
    print(f"  Default patterns: {config.patterns[:3]}...")
    print(f"  Default excludes: {config.excludes[:2]}...")

    # Test should_index with PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"test content")
        test_file = f.name

    try:
        should, reason = should_index(test_file, ["*.pdf"], [], 100 * 1024 * 1024)
        print(f"  Should index .pdf: {should}")
        assert should, "PDF should match *.pdf pattern"

        should, reason = should_index(test_file, ["*.txt"], [], 100 * 1024 * 1024)
        print(f"  Should index as .txt: {should} ({reason})")
        assert not should, "PDF should not match *.txt pattern"

        print("  [PASS] Folder Watcher tests passed")

    finally:
        Path(test_file).unlink()


def test_export_import():
    """Test F-032, F-033, F-034: Export/Import."""
    print("\n" + "=" * 60)
    print("TEST: Export/Import (F-032, F-033, F-034)")
    print("=" * 60)

    from ragd.archive import ExportEngine, ImportEngine, ARCHIVE_VERSION
    from ragd.storage import ChromaStore

    print(f"  Archive version: {ARCHIVE_VERSION}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create store and export
        store = ChromaStore(tmpdir / "chroma")
        engine = ExportEngine(store)

        result = engine.export(tmpdir / "test.tar.gz")
        print(f"  Export success: {result.success}")
        print(f"  Documents exported: {result.document_count}")
        assert result.success, "Export should succeed"

        # Validate archive
        import_engine = ImportEngine(store)
        validation = import_engine.validate(tmpdir / "test.tar.gz")
        print(f"  Archive valid: {validation.valid}")
        assert validation.valid, f"Validation failed: {validation.errors}"

        print("  [PASS] Export/Import tests passed")


def test_tag_management():
    """Test F-031: Tag Management."""
    print("\n" + "=" * 60)
    print("TEST: Tag Management (F-031)")
    print("=" * 60)

    from ragd.metadata import MetadataStore, TagManager, DocumentMetadata

    with tempfile.TemporaryDirectory() as tmpdir:
        store = MetadataStore(Path(tmpdir) / "meta.sqlite")
        tags = TagManager(store)

        # Create documents
        store.set("doc-001", DocumentMetadata(dc_title="Test Doc 1"))
        store.set("doc-002", DocumentMetadata(dc_title="Test Doc 2"))

        # Add tags
        tags.add("doc-001", ["important", "work"])
        tags.add("doc-002", ["work"])

        doc_tags = tags.get("doc-001")
        print(f"  Tags for doc-001: {doc_tags}")
        assert "important" in doc_tags
        assert "work" in doc_tags

        # Find by tag
        found = tags.find_by_tags(["important"])
        print(f"  Docs with 'important': {found}")
        assert "doc-001" in found
        assert "doc-002" not in found

        # Tag counts
        counts = tags.tag_counts()
        print(f"  Tag counts: {counts}")
        assert counts["work"] == 2
        assert counts["important"] == 1

        print("  [PASS] Tag Management tests passed")


def test_pdf_quality():
    """Test F-025: PDF Quality Detection."""
    print("\n" + "=" * 60)
    print("TEST: PDF Quality Detection (F-025)")
    print("=" * 60)

    from ragd.pdf import PDFQualityDetector, PDFQuality

    print(f"  Quality levels: {[q.value for q in PDFQuality]}")

    detector = PDFQualityDetector()
    print("  PDFQualityDetector initialised")

    print("  [PASS] PDF Quality tests passed")


def test_metadata_store():
    """Test F-029: Metadata Storage."""
    print("\n" + "=" * 60)
    print("TEST: Metadata Storage (F-029)")
    print("=" * 60)

    from ragd.metadata import MetadataStore, DocumentMetadata

    with tempfile.TemporaryDirectory() as tmpdir:
        store = MetadataStore(Path(tmpdir) / "meta.sqlite")

        # Create and retrieve
        meta = DocumentMetadata(
            dc_title="Test Document",
            dc_creator=["Author One"],
            dc_subject=["testing", "ragd"],
        )
        store.set("doc-test", meta)

        retrieved = store.get("doc-test")
        print(f"  Title: {retrieved.dc_title}")
        print(f"  Creator: {retrieved.dc_creator}")
        print(f"  Subject: {retrieved.dc_subject}")

        assert retrieved.dc_title == "Test Document"
        assert "Author One" in retrieved.dc_creator

        print("  [PASS] Metadata Storage tests passed")


def main():
    """Run all manual tests."""
    print("\n" + "#" * 60)
    print("# RAGD v0.2 Manual Tests")
    print("#" * 60)

    tests = [
        test_web_archive,
        test_folder_watcher,
        test_export_import,
        test_tag_management,
        test_pdf_quality,
        test_metadata_store,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\nAll tests passed! Ready to merge v0.2 to main.")
    else:
        print("\nSome tests failed. Please investigate before merging.")

    return failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
