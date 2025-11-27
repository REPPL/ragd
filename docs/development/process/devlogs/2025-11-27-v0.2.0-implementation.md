# Devlog: v0.2.0 Implementation

## Context

v0.2.0 represents a significant expansion of ragd's capabilities, adding advanced PDF processing, metadata management, archive export/import, and web archive support. This implementation covered 12 features across 4 minor releases.

## Approach

### Architecture Decisions

**Protocol-based design:** All new modules use Python Protocols for extensibility:

```python
class PDFProcessor(Protocol):
    def extract(self, path: Path) -> ExtractedContent: ...

class OCREngine(Protocol):
    def process(self, image: Image) -> OCRResult: ...
```

**Lazy loading:** Heavy dependencies (Docling, PaddleOCR, KeyBERT) load only when needed:

```python
class DoclingProcessor:
    _converter: DocumentConverter | None = None

    def _ensure_converter(self) -> None:
        if self._converter is None:
            from docling import DocumentConverter
            self._converter = DocumentConverter()
```

**Feature flags:** Graceful degradation when optional deps missing:

```python
try:
    from docling import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
```

### Implementation Order

1. **v0.2.0** - Foundation: PDF quality detection + metadata storage
2. **v0.2.1** - Processing: OCR pipeline + table extraction + tags
3. **v0.2.2** - Portability: Export/import with archive format
4. **v0.2.3** - Automation: Folder watching + web archives

## Challenges

### 1. ChromaDB Metadata Constraints

**Problem:** ChromaDB doesn't accept list values in metadata.

**Solution:** Convert lists to JSON strings:

```python
if isinstance(v, list):
    chunk_meta[k] = json.dumps(v)
```

### 2. Numpy Array Truth Value

**Problem:** `if embeddings:` fails with numpy arrays.

**Solution:** Explicit length check:

```python
if embeddings is not None and len(embeddings) > 0:
```

### 3. Tarfile Path Traversal (CVE-2007-4559)

**Problem:** `tar.extractall()` vulnerable to malicious paths.

**Solution:** Member-by-member validation:

```python
def _safe_extract(tar: tarfile.TarFile, path: Path) -> None:
    for member in tar.getmembers():
        if member.name.startswith("/"):
            raise ValueError("Absolute path")
        if ".." in member.name.split("/"):
            raise ValueError("Path traversal")
        # ... validate and extract
```

### 4. Document Record Import

**Problem:** Roundtrip test failed - documents weren't being added to ChromaDB metadata collection.

**Solution:** Added document record insertion during chunk import:

```python
self._chroma._metadata.add(
    ids=[doc_id],
    documents=[source_path],
    metadatas=[{...}],
)
```

## Key Files Created

```
src/ragd/
├── pdf/
│   ├── quality.py      # PDFQualityDetector
│   ├── processor.py    # PyMuPDFProcessor
│   └── docling.py      # DoclingProcessor
├── metadata/
│   ├── schema.py       # DocumentMetadata
│   ├── store.py        # MetadataStore (SQLite)
│   ├── extractor.py    # MetadataExtractor
│   └── tags.py         # TagManager
├── ocr/
│   └── engine.py       # OCREngine Protocol + implementations
├── archive/
│   ├── format.py       # Archive format v1.0
│   ├── export.py       # ExportEngine
│   └── import_.py      # ImportEngine
└── web/
    ├── archive.py      # WebArchiveProcessor
    └── watcher.py      # FolderWatcher
```

## Test Coverage

- 315 tests passing (21 skipped for optional deps)
- Security tests for path traversal prevention
- Manual UAT script: `tests/manual_v02_tests.py`

## Outcome

All 12 features implemented successfully. Key achievements:

1. **Flexible PDF processing** - Auto-routes based on quality detection
2. **Rich metadata** - Dublin Core + RAG extensions + custom tags
3. **Portable archives** - Full export/import with checksums
4. **Automation ready** - Watch folders for auto-indexing
5. **Web archive support** - SingleFile HTML parsing

The protocol-based architecture proved valuable - adding new PDF processors or OCR engines requires only implementing the relevant Protocol.

---

**Session:** 26-27 November 2025
