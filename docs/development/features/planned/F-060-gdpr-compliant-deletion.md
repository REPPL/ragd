# F-060: GDPR-Compliant Deletion

## Overview

**Research**: [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md)
**ADR**: [ADR-0028: PII Handling Architecture](../../decisions/adrs/0028-pii-handling-architecture.md)
**Milestone**: v0.8
**Priority**: P1

## Problem Statement

GDPR Article 17 ("Right to Erasure") requires complete deletion of personal data upon request. RAG systems present unique challenges:

1. **Distributed storage**: Data exists in multiple locations (source, metadata, embeddings)
2. **Embedded PII**: PII may be encoded in vector embeddings
3. **Cascade requirements**: Deleting a document must remove all derived data
4. **Audit requirements**: Organisations must demonstrate compliance
5. **Backup handling**: PII persists in backups unless explicitly purged

For ragd to be usable in regulated environments (healthcare, finance, legal), it must support verifiable, complete data deletion.

## Design Approach

### Cascade Deletion Architecture

```
Delete Request
    ↓
┌─────────────────────────────────────────┐
│ GDPR Deletion Pipeline                  │
├─────────────────────────────────────────┤
│ 1. Validate document exists             │
│ 2. Begin transaction                    │
│ 3. Remove from ChromaDB (embeddings)    │
│ 4. Remove from metadata SQLite          │
│ 5. Remove from search history           │
│ 6. Create audit record                  │
│ 7. Commit transaction                   │
│ 8. Return deletion certificate          │
└─────────────────────────────────────────┘
    ↓
Audit Log Entry
```

### Deletion Scope

| Data Type | Location | Deletion Method |
|-----------|----------|-----------------|
| Document reference | metadata.db | SQL DELETE |
| Chunk text | metadata.db | SQL DELETE |
| Chunk embeddings | ChromaDB | Collection.delete() |
| Search history | history.db | SQL DELETE (if contains doc) |
| Session context | session.db | SQL DELETE |
| Audit trail | audit.db | RETAINED (required for compliance) |

### Audit Trail Requirements

Every deletion must record:

```json
{
  "id": "del-2024-001234",
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "gdpr_deletion",
  "reason": "User request - GDPR Article 17",
  "reference": "GDPR-REQ-2024-0042",
  "document": {
    "id": "doc-abc123",
    "filename": "contract-2024.pdf",
    "hash": "sha256:abc123...",
    "indexed_at": "2024-01-01T00:00:00Z"
  },
  "deleted_data": {
    "chunks": 15,
    "embeddings": 15,
    "metadata_records": 1,
    "history_entries": 3
  },
  "verification": {
    "embeddings_removed": true,
    "metadata_removed": true,
    "history_cleaned": true
  },
  "completed_at": "2024-01-15T10:30:05Z"
}
```

## Implementation Tasks

- [ ] Implement cascade deletion across all storage layers
- [ ] Create transaction wrapper for atomic deletion
- [ ] Implement audit logging for deletions
- [ ] Add `ragd purge` command with GDPR flags
- [ ] Add deletion verification (confirm data removed)
- [ ] Implement batch deletion for multiple documents
- [ ] Add deletion certificate generation
- [ ] Create deletion report for compliance officers
- [ ] Add rollback capability (within grace period)
- [ ] Implement search history cleaning
- [ ] Write unit tests for each deletion scope
- [ ] Write integration tests for cascade deletion
- [ ] Document compliance workflow

## Success Criteria

- [ ] Single command deletes all document data
- [ ] Deletion is atomic (all-or-nothing)
- [ ] Audit trail created for every deletion
- [ ] Verification confirms complete removal
- [ ] Batch deletion supported
- [ ] Deletion certificate exportable
- [ ] Clear documentation for compliance teams
- [ ] <5 second deletion for typical documents

## Dependencies

- F-017: Secure Deletion (base deletion capability)
- F-029: Metadata Storage (cascade target)
- SQLite/ChromaDB storage (implementation detail)

## Technical Notes

### CLI Commands

```bash
# GDPR-compliant deletion with audit trail
ragd purge document.pdf --gdpr --reason "User request #12345"
# Output:
# GDPR Deletion Request
# Document: document.pdf (doc-abc123)
# Reason: User request #12345
#
# This will permanently delete:
#   - 1 document reference
#   - 15 text chunks
#   - 15 embeddings
#   - 3 search history entries
#
# Continue? [y/N] y
#   ├─ Removing embeddings... done
#   ├─ Removing chunks... done
#   ├─ Removing metadata... done
#   ├─ Cleaning search history... done
#   └─ Creating audit record... done
#
# ✓ Deletion complete
# Certificate: ~/.ragd/audit/certificates/del-2024-001234.json

# Batch deletion
ragd purge --source ~/contracts/ --gdpr --reason "GDPR-REQ-2024-0042"
# Deletes all indexed documents from specified source

# View deletion audit log
ragd audit --type deletion --since "2024-01-01"
# Lists all deletions with details

# Export deletion certificate
ragd audit --certificate del-2024-001234 --export compliance-report.pdf
# Generates PDF certificate for compliance

# Verify deletion (spot-check)
ragd verify --deleted doc-abc123
# Confirms no traces remain in any storage layer
```

### Configuration

```yaml
compliance:
  gdpr:
    enabled: true
    require_reason: true
    audit_retention_days: 2555  # 7 years
    certificate_format: json  # json | pdf

  deletion:
    require_confirmation: true
    grace_period_hours: 0  # 0 = immediate, >0 = soft delete first
    verify_after_delete: true
    clean_search_history: true

  audit:
    path: ~/.ragd/audit/
    encrypt: true
    backup: true
```

### Deletion Certificate Schema

```python
@dataclass
class DeletionCertificate:
    """GDPR-compliant deletion certificate."""

    certificate_id: str
    timestamp: datetime
    reason: str
    reference: Optional[str]  # External ticket/request ID

    document: DocumentInfo
    deleted_data: DeletedDataSummary
    verification: VerificationResult

    ragd_version: str
    signed_hash: str  # SHA-256 of certificate content

    def to_json(self) -> str:
        """Export as JSON."""
        ...

    def to_pdf(self) -> bytes:
        """Generate PDF certificate."""
        ...
```

### Verification Process

```python
def verify_deletion(document_id: str) -> VerificationResult:
    """Verify document completely deleted from all storage."""
    results = {
        "chromadb": not chromadb_contains(document_id),
        "metadata": not metadata_contains(document_id),
        "history": not history_contains(document_id),
        "sessions": not sessions_contain(document_id)
    }

    return VerificationResult(
        complete=all(results.values()),
        details=results
    )
```

### Transaction Safety

```python
def gdpr_delete(document_id: str, reason: str) -> DeletionCertificate:
    """GDPR-compliant deletion with rollback on failure."""
    with transaction_context() as txn:
        # Gather pre-deletion data for audit
        doc_info = get_document_info(document_id)
        chunk_count = count_chunks(document_id)

        # Delete from all locations
        delete_embeddings(document_id, txn)
        delete_chunks(document_id, txn)
        delete_metadata(document_id, txn)
        clean_history(document_id, txn)

        # Create audit record (inside transaction)
        audit_id = create_audit_record(
            action="gdpr_deletion",
            document=doc_info,
            reason=reason,
            txn=txn
        )

        # Commit everything atomically
        txn.commit()

    # Verify outside transaction
    verification = verify_deletion(document_id)

    # Generate certificate
    return generate_certificate(
        audit_id=audit_id,
        document=doc_info,
        verification=verification,
        reason=reason
    )
```

## Related Documentation

- [State-of-the-Art PII Removal](../../research/state-of-the-art-pii-removal.md) - GDPR research
- [ADR-0028: PII Handling Architecture](../../decisions/adrs/0028-pii-handling-architecture.md)
- [F-017: Secure Deletion](./F-017-secure-deletion.md) - Base deletion capability
- [F-023: PII Detection](./F-023-pii-detection.md) - PII scanning
- [GDPR Article 17](https://gdpr-info.eu/art-17-gdpr/) - Legal requirement

---
