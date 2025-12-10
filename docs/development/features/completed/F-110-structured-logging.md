# F-110: Structured Logging

**Status:** Completed
**Milestone:** v0.9.5

## Problem Statement

Third-party library warnings pollute CLI output. Need structured logging with file output and suppression.

## Design Approach

JSON-formatted logging with configurable levels and third-party suppression.

## Implementation

### Files Created
- `src/ragd/logging/__init__.py` - Logging package
- `src/ragd/logging/structured.py` - Structured logging implementation

### Key Components

**LogLevel** (enum):
- DEBUG, INFO, WARNING, ERROR, CRITICAL

**LogEntry** (dataclass):
- `timestamp` - ISO format timestamp
- `level` - Log level
- `message` - Log message
- `operation` - Operation name (optional)
- `file` - Related file (optional)
- `duration_ms` - Duration in ms (optional)
- `to_json()` - Serialise to JSON

**StructuredLogger** (class):
- Configurable console and file levels
- JSON or human-readable console output
- File output with JSON Lines format
- Level filtering for both outputs

**Functions**:
- `get_logger()` - Get global logger
- `configure_logging()` - Configure global logger
- `suppress_third_party_logs()` - Suppress noisy loggers

### Suppressed Loggers
- transformers
- tokenizers
- sentence_transformers
- paddleocr, paddle, ppocr
- httpx, httpcore, urllib3
- chromadb
- onnxruntime

## Implementation Tasks

- [x] Create LogEntry dataclass
- [x] Implement StructuredLogger
- [x] JSON serialisation
- [x] Level filtering
- [x] Third-party log suppression
- [x] Global logger configuration

## Success Criteria

- [x] JSON logging to file
- [x] Configurable log levels
- [x] Third-party logs suppressed
- [x] Human-readable console output

## Testing

- 10 tests in `tests/test_stability.py`
- All tests passing

## Related Documentation

- [F-111: Error Logging & Recovery](./F-111-error-logging-recovery.md)
- [v0.9.5 Implementation](../../implementation/v0.9.5.md)

---

**Status**: Completed
