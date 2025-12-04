"""Operations module for ragd.

Provides infrastructure for:
- Error logging and recovery (F-111)
- Operation audit trail (F-112)
- Dry-run mode (F-118)
"""

from ragd.operations.errors import (
    IndexingErrorCategory,
    DocumentResult,
    BatchResult,
    REMEDIATION_HINTS,
    categorise_error,
)
from ragd.operations.dry_run import (
    OperationType,
    ActionType,
    PlannedAction,
    OperationPlan,
    display_plan,
    create_index_plan,
    create_delete_plan,
    create_repair_plan,
)
from ragd.operations.audit import (
    AuditEntry,
    AuditLog,
    get_audit_log,
    audit_operation,
    log_operation,
)
from ragd.operations.quality import (
    QualityFlag,
    QualityScore,
    calculate_quality_score,
    format_quality_badge,
    format_quality_summary,
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
]
