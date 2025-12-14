"""Operations module for ragd.

Provides infrastructure for:
- Error logging and recovery (F-111)
- Operation audit trail (F-112)
- Dry-run mode (F-118)
"""

from ragd.operations.audit import (
    AuditEntry,
    AuditLog,
    audit_operation,
    get_audit_log,
    log_operation,
)
from ragd.operations.dry_run import (
    ActionType,
    OperationPlan,
    OperationType,
    PlannedAction,
    create_delete_plan,
    create_index_plan,
    create_repair_plan,
    display_plan,
)
from ragd.operations.errors import (
    REMEDIATION_HINTS,
    BatchResult,
    DocumentResult,
    IndexingErrorCategory,
    categorise_error,
)
from ragd.operations.quality import (
    QualityFlag,
    QualityScore,
    calculate_quality_score,
    format_quality_badge,
    format_quality_summary,
)
from ragd.operations.inspect import (
    DuplicateGroup,
    InspectResult,
    SkipExplanation,
    explain_skipped,
    find_duplicates_in_index,
    inspect_index,
)

__all__ = [
    # Error logging (F-111)
    "IndexingErrorCategory",
    "DocumentResult",
    "BatchResult",
    "REMEDIATION_HINTS",
    "categorise_error",
    # Dry-run mode (F-118)
    "OperationType",
    "ActionType",
    "PlannedAction",
    "OperationPlan",
    "display_plan",
    "create_index_plan",
    "create_delete_plan",
    "create_repair_plan",
    # Audit trail (F-112)
    "AuditEntry",
    "AuditLog",
    "get_audit_log",
    "audit_operation",
    "log_operation",
    # Quality scoring (F-115)
    "QualityFlag",
    "QualityScore",
    "calculate_quality_score",
    "format_quality_badge",
    "format_quality_summary",
    # Index inspection (v1.0.8)
    "InspectResult",
    "DuplicateGroup",
    "SkipExplanation",
    "inspect_index",
    "find_duplicates_in_index",
    "explain_skipped",
]
