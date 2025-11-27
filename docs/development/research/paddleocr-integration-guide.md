# PaddleOCR Integration Guide

Implementation-specific guidance for integrating PaddleOCR (with EasyOCR fallback) into ragd v0.2.

---

## Overview

This guide documents OCR integration for F-027 (OCR Pipeline), complementing [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md).

**Primary Engine:** PaddleOCR (93% accuracy, best for complex layouts)
**Fallback Engine:** EasyOCR (easier setup, good for scene text)
**Decision:** Per [ADR-0019](../decisions/adrs/0019-pdf-processing.md), PaddleOCR is primary with EasyOCR fallback.

---

## PaddleOCR Installation

### macOS ARM64 (Apple Silicon)

PaddlePaddle 3.x supports native ARM64 on Apple Silicon (CPU-only):

```bash
# Verify architecture
python3 -c "import platform; print(platform.machine())"  # Should show arm64

# Install PaddlePaddle (CPU for macOS ARM64)
pip install paddlepaddle==3.2.2

# Install PaddleOCR
pip install paddleocr
```

### Linux/Windows (with GPU)

```bash
# For CUDA 11.8
pip install paddlepaddle-gpu==3.2.2 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# Install PaddleOCR
pip install paddleocr
```

### ragd Optional Dependency Group

```toml
# pyproject.toml
[project.optional-dependencies]
ocr = [
    "paddlepaddle>=3.2.0",
    "paddleocr>=2.9.0",
    "easyocr>=1.7.0",
]
```

---

## PaddleOCR API Usage

### Basic Initialisation

```python
from paddleocr import PaddleOCR

# Create OCR instance (downloads models on first use, ~150MB)
ocr = PaddleOCR(
    use_angle_cls=True,  # Enable text orientation classification
    lang='en',           # Language: 'en', 'ch', 'ja', etc.
    show_log=False,      # Suppress logs
)
```

### Performing OCR

```python
# OCR on image file
result = ocr.ocr('document.png', cls=True)

# OCR on numpy array
import cv2
image = cv2.imread('document.png')
result = ocr.ocr(image, cls=True)
```

### Understanding Results

```python
# Result structure: list of pages, each page is list of text lines
# Each line: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)

for page_result in result:
    if page_result is None:
        continue
    for line in page_result:
        bbox = line[0]           # Bounding box coordinates
        text = line[1][0]        # Recognised text
        confidence = line[1][1]  # Confidence score (0.0 - 1.0)
        print(f"{text} ({confidence:.2f})")
```

### Extracting Components

```python
def extract_text_with_confidence(result) -> list[tuple[str, float]]:
    """Extract text and confidence from PaddleOCR result."""
    extracted = []
    for page_result in result:
        if page_result is None:
            continue
        for line in page_result:
            text = line[1][0]
            confidence = line[1][1]
            extracted.append((text, confidence))
    return extracted
```

---

## Configuration Options

### Language Support

PaddleOCR supports 109+ languages. Common codes:

| Code | Language |
|------|----------|
| `en` | English |
| `ch` | Chinese (Simplified) |
| `japan` | Japanese |
| `korean` | Korean |
| `fr` | French |
| `german` | German |
| `arabic` | Arabic |

```python
# Multi-language document
ocr = PaddleOCR(lang='ch')  # Chinese includes English
```

### Detection vs Recognition

```python
# Full pipeline (detect + recognise)
result = ocr.ocr(image, det=True, rec=True, cls=True)

# Detection only (get bounding boxes)
result = ocr.ocr(image, det=True, rec=False)

# Recognition only (on cropped text regions)
result = ocr.ocr(cropped_image, det=False, rec=True)
```

### Custom Model Paths

```python
ocr = PaddleOCR(
    det_model_dir='/path/to/detection/model',
    rec_model_dir='/path/to/recognition/model',
    cls_model_dir='/path/to/classification/model',
)
```

### Batch Processing

```python
# Process multiple images
image_paths = ['page1.png', 'page2.png', 'page3.png']
results = ocr.ocr(image_paths, batch_size=4)
```

---

## EasyOCR Fallback

### Installation

```bash
pip install easyocr
```

### Basic Usage

```python
import easyocr

# Create reader (downloads models on first use, ~100MB per language)
reader = easyocr.Reader(['en'], gpu=False)  # CPU mode for macOS

# Perform OCR
result = reader.readtext('document.png')

# Result: [(bbox, text, confidence), ...]
for bbox, text, confidence in result:
    print(f"{text} ({confidence:.2f})")
```

### GPU Configuration

```python
# CPU mode (recommended for macOS/low memory)
reader = easyocr.Reader(['en'], gpu=False)

# GPU mode (NVIDIA required)
reader = easyocr.Reader(['en'], gpu=True)

# Specific GPU
reader = easyocr.Reader(['en'], gpu='cuda:0')
```

### Custom Model Directory

```python
reader = easyocr.Reader(
    ['en'],
    model_storage_directory='/path/to/models',
    gpu=False
)
```

---

## ragd OCR Pipeline Implementation

### Unified OCR Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    bboxes: list[list[tuple[float, float]]] | None = None
    page_number: int = 1
    engine: str = "unknown"

class OCREngine(Protocol):
    """Protocol for OCR engines."""

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Perform OCR on an image file."""
        ...

    def ocr_pdf_page(self, pdf_path: Path, page: int) -> list[OCRResult]:
        """Perform OCR on a specific PDF page."""
        ...

    @property
    def name(self) -> str:
        """Engine name for logging."""
        ...
```

### PaddleOCR Engine Implementation

```python
class PaddleOCREngine:
    """PaddleOCR-based OCR engine."""

    def __init__(self, lang: str = 'en', use_gpu: bool = False):
        self._ocr: PaddleOCR | None = None
        self._lang = lang
        self._use_gpu = use_gpu

    def _ensure_ocr(self) -> PaddleOCR:
        """Lazy load PaddleOCR."""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self._lang,
                show_log=False,
                use_gpu=self._use_gpu,
            )
        return self._ocr

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Perform OCR on an image."""
        ocr = self._ensure_ocr()
        result = ocr.ocr(str(image_path), cls=True)

        ocr_results = []
        for page_result in result:
            if page_result is None:
                continue
            for line in page_result:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]
                ocr_results.append(OCRResult(
                    text=text,
                    confidence=confidence,
                    bboxes=[bbox],
                    engine="paddleocr",
                ))
        return ocr_results

    @property
    def name(self) -> str:
        return "PaddleOCR"
```

### EasyOCR Fallback Engine

```python
class EasyOCREngine:
    """EasyOCR-based OCR engine (fallback)."""

    def __init__(self, lang: list[str] = ['en'], use_gpu: bool = False):
        self._reader: easyocr.Reader | None = None
        self._lang = lang
        self._use_gpu = use_gpu

    def _ensure_reader(self):
        """Lazy load EasyOCR reader."""
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(
                self._lang,
                gpu=self._use_gpu,
            )
        return self._reader

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Perform OCR on an image."""
        reader = self._ensure_reader()
        result = reader.readtext(str(image_path))

        return [
            OCRResult(
                text=text,
                confidence=confidence,
                bboxes=[bbox],
                engine="easyocr",
            )
            for bbox, text, confidence in result
        ]

    @property
    def name(self) -> str:
        return "EasyOCR"
```

### OCR Pipeline with Fallback

```python
class OCRPipeline:
    """OCR pipeline with automatic fallback."""

    def __init__(self, config: OCRConfig):
        self._primary: OCREngine | None = None
        self._fallback: OCREngine | None = None
        self._config = config

    def _get_primary(self) -> OCREngine:
        """Get primary OCR engine (PaddleOCR)."""
        if self._primary is None:
            self._primary = PaddleOCREngine(
                lang=self._config.language,
                use_gpu=self._config.use_gpu,
            )
        return self._primary

    def _get_fallback(self) -> OCREngine:
        """Get fallback OCR engine (EasyOCR)."""
        if self._fallback is None:
            self._fallback = EasyOCREngine(
                lang=[self._config.language],
                use_gpu=self._config.use_gpu,
            )
        return self._fallback

    def ocr(self, image_path: Path, min_confidence: float = 0.3) -> list[OCRResult]:
        """Perform OCR with automatic fallback on failure."""
        try:
            results = self._get_primary().ocr_image(image_path)
            if results and self._average_confidence(results) >= min_confidence:
                return results
        except Exception as e:
            logger.warning(f"PaddleOCR failed: {e}, trying EasyOCR")

        # Fallback to EasyOCR
        try:
            return self._get_fallback().ocr_image(image_path)
        except Exception as e:
            logger.error(f"All OCR engines failed: {e}")
            return []

    def _average_confidence(self, results: list[OCRResult]) -> float:
        """Calculate average confidence score."""
        if not results:
            return 0.0
        return sum(r.confidence for r in results) / len(results)
```

---

## PDF Page to Image Conversion

OCR requires images. Convert PDF pages using PyMuPDF:

```python
import fitz  # PyMuPDF

def pdf_page_to_image(pdf_path: Path, page_number: int, dpi: int = 300) -> Path:
    """Convert a PDF page to a PNG image for OCR."""
    doc = fitz.open(pdf_path)
    page = doc[page_number]

    # Render at high DPI for better OCR
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Save to temporary file
    temp_path = Path(f"/tmp/ocr_page_{page_number}.png")
    pix.save(temp_path)

    return temp_path
```

---

## Confidence Score Handling

### Filtering Low-Confidence Results

```python
def filter_by_confidence(
    results: list[OCRResult],
    min_confidence: float = 0.5
) -> list[OCRResult]:
    """Filter OCR results by confidence threshold."""
    return [r for r in results if r.confidence >= min_confidence]
```

### Aggregating Page-Level Confidence

```python
def calculate_page_confidence(results: list[OCRResult]) -> float:
    """Calculate weighted confidence for a page."""
    if not results:
        return 0.0

    # Weight by text length (longer text = more reliable)
    total_weight = sum(len(r.text) for r in results)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(r.confidence * len(r.text) for r in results)
    return weighted_sum / total_weight
```

### User Warning for Low Confidence

```python
def assess_ocr_quality(confidence: float) -> str:
    """Assess OCR quality and return user message."""
    if confidence >= 0.9:
        return "excellent"
    elif confidence >= 0.7:
        return "good"
    elif confidence >= 0.5:
        return "fair - some text may be incorrect"
    else:
        return "poor - results may be unreliable"
```

---

## Testing Strategy

### Mocking for Unit Tests

```python
@pytest.fixture
def mock_paddleocr():
    """Mock PaddleOCR for fast unit tests."""
    with patch("paddleocr.PaddleOCR") as mock:
        instance = Mock()
        instance.ocr.return_value = [[
            [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Test text", 0.95)],
            [[[0, 30], [100, 30], [100, 50], [0, 50]], ("More text", 0.87)],
        ]]
        mock.return_value = instance
        yield mock
```

### Integration Tests (Slow)

```python
@pytest.mark.slow
@pytest.mark.ocr
def test_paddleocr_real_image(sample_scanned_image):
    """Integration test with real PaddleOCR."""
    engine = PaddleOCREngine(lang='en')
    results = engine.ocr_image(sample_scanned_image)

    assert len(results) > 0
    assert all(r.confidence > 0 for r in results)
    assert any("expected" in r.text.lower() for r in results)
```

---

## Memory and Performance

### Model Sizes

| Engine | Model Size | First Load Time |
|--------|------------|-----------------|
| PaddleOCR (en) | ~150MB | 5-10s |
| PaddleOCR (ch) | ~200MB | 5-10s |
| EasyOCR (en) | ~100MB | 5-15s |

### Memory Usage

| Operation | Estimated Memory |
|-----------|------------------|
| Model loading | ~500MB-1GB |
| Per-image OCR | ~200-500MB |
| Batch (4 images) | ~1-2GB |

### Lazy Loading Recommendation

Always use lazy loading to avoid impacting CLI startup time:

```python
# DON'T do this at module level
# from paddleocr import PaddleOCR
# ocr = PaddleOCR()  # Blocks for 5-10s

# DO use lazy loading
class OCREngine:
    def __init__(self):
        self._ocr = None

    def ocr(self, image):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(...)
        return self._ocr.ocr(image)
```

---

## Known Issues

### macOS ARM64

- **CPU-only:** No GPU support on Apple Silicon
- **Stuck initialisation:** Some M3 users report hanging ([Issue #11588](https://github.com/PaddlePaddle/PaddleOCR/issues/11588))
- **Workaround:** If PaddleOCR hangs, fall back to EasyOCR

### Memory on Low-RAM Systems

- Use `det_limit_side_len=960` to reduce memory (default: 1920)
- Process pages sequentially, not in batch
- Clear model between documents if memory-constrained

---

## Related Documentation

- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Research context
- [Docling Integration Guide](./docling-integration-guide.md) - Primary PDF processor
- [ADR-0019: PDF Processing](../decisions/adrs/0019-pdf-processing.md) - Library selection
- [F-027: OCR Pipeline](../features/completed/F-027-ocr-pipeline.md) - Feature spec

---

## Sources

- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [PaddlePaddle macOS Installation](https://www.paddlepaddle.org.cn/documentation/docs/en/install/pip/macos-pip_en.html)
- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [EasyOCR Installation Guide](https://www.jaided.ai/easyocr/install/)
- [PaddleOCR PyPI](https://pypi.org/project/paddleocr/)

---

**Status**: Research complete
