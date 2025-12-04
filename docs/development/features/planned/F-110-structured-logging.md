# F-110: Structured Logging

## Problem Statement

The current `ragd index` command produces noisy, unstructured output that buries important information:

- **Third-party warnings** flood the console (tokenizers, PaddleOCR, transformers)
- **Progress indicators** get lost in warning output
- **Errors and warnings** are not captured for later analysis
- **No log file** is generated for debugging or audit purposes

Users indexing large document collections (1000+ files) cannot easily identify which documents had issues or why.

## Design Approach

### 1. Early Warning Suppression

Suppress third-party library warnings at the earliest possible point - before any imports that trigger them.

**Environment variables to set (at CLI entry point):**
- `TOKENIZERS_PARALLELISM=false`
- `PADDLE_LOGGING_LEVEL=40`
- `TRANSFORMERS_VERBOSITY=error`
- `TF_CPP_MIN_LOG_LEVEL=3`

**Loggers to filter from console output:**
- `paddleocr`, `ppocr`, `paddle*`
- `transformers`, `sentence_transformers`
- `chromadb`, `httpx`, `urllib3`
- `huggingface_hub`, `filelock`

### 2. Console Handler Filter

A `ThirdPartyFilter` class that:
- Allows all `ragd.*` logger output
- Filters third-party logger output from console
- Allows third-party output to reach file handlers

### 3. Structured Log File Format

JSON Lines (JSONL) format for machine-parseable logs:

```json
{"timestamp":"2024-12-04T05:35:48Z","level":"WARNING","logger":"ragd.ocr.pipeline","document_id":"doc123","page":3,"message":"OCR confidence below threshold","confidence":0.45}
{"timestamp":"2024-12-04T05:35:49Z","level":"INFO","logger":"ragd.ingestion.pipeline","document_id":"doc123","message":"Document indexed","chunks":42,"duration_ms":1234}
```

**Log file location:** `~/.ragd/logs/ragd_YYYY-MM-DD_HH-MM-SS.jsonl`

### 4. Log Rotation

Use Python's `RotatingFileHandler` with configurable limits:
- Maximum file size (default: 50MB)
- Maximum number of files (default: 10)

## Implementation Tasks

- [ ] Create `src/ragd/logging.py` module
- [ ] Implement `configure_early_suppression()` function
- [ ] Implement `ThirdPartyFilter` class
- [ ] Implement `JSONLineFormatter` class
- [ ] Implement `configure_logging()` function with rotation
- [ ] Add `LoggingConfig` to `src/ragd/config.py`
- [ ] Call `configure_early_suppression()` at top of `cli.py`
- [ ] Integrate logging configuration in CLI commands

## CLI Options

```
ragd index <path> [OPTIONS]

New options:
  --log-file PATH       Write detailed log to file (default: auto-generated)
  --log-level LEVEL     DEBUG | INFO | WARNING | ERROR (default: INFO)
  --no-log              Disable log file output
  --quiet, -q           Suppress progress, show only final summary
```

## Configuration Schema

```yaml
# ~/.ragd/config.yaml
logging:
  enabled: true
  level: INFO
  file_level: DEBUG
  log_dir: ~/.ragd/logs
  max_files: 10
  max_size_mb: 50
  suppress_third_party: true
```

## Success Criteria

- [ ] No third-party warnings visible during `ragd index` (default mode)
- [ ] All warnings/errors captured in structured log file
- [ ] Log file parseable by standard JSON tools (`jq`, Python `json`)
- [ ] Log rotation prevents unbounded disk usage
- [ ] `--log-level DEBUG` enables verbose file logging without console noise
- [ ] Configuration changes persist across sessions

## Dependencies

- Python `logging` standard library (no new dependencies)
- v0.9.1 (CLI Polish & Documentation II)

---

## Related Documentation

- [F-111 Error Logging & Recovery](./F-111-error-logging-recovery.md)
- [F-114 CLI User Feedback](./F-114-cli-user-feedback.md)
- [v0.9.5 Milestone](../../milestones/v0.9.5.md)

---

**Status**: Planned
