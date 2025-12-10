"""CLI interface components."""

from ragd.ui.cli.commands import (
    get_console,
    init_command,
    index_command,
    search_command,
    info_command,
    status_command,
    stats_command,
    doctor_command,
    config_command,
    reindex_command,
    meta_show_command,
    meta_edit_command,
    tag_add_command,
    tag_remove_command,
    tag_list_command,
    list_documents_command,
    export_command,
    import_command,
    watch_start_command,
    watch_stop_command,
    watch_status_command,
    ask_command,
    chat_command,
    models_list_command,
    models_recommend_command,
    models_show_command,
    models_set_command,
    models_discover_command,
    models_cards_command,
    models_card_edit_command,
    evaluate_command,
    quality_command,
)

from ragd.ui.cli.backend import (
    backend_show_command,
    backend_list_command,
    backend_health_command,
    backend_set_command,
    backend_benchmark_command,
)

from ragd.ui.cli.security import (
    unlock_command,
    lock_command,
    password_change_command,
    password_reset_command,
    session_status_command,
)

from ragd.ui.cli.deletion import (
    delete_command,
    delete_audit_command,
)

from ragd.ui.cli.tiers import (
    tier_set_command,
    tier_show_command,
    tier_list_command,
    tier_summary_command,
    tier_promote_command,
    tier_demote_command,
)

from ragd.ui.cli.collections import (
    collection_create_command,
    collection_list_command,
    collection_show_command,
    collection_update_command,
    collection_delete_command,
    collection_export_command,
)

from ragd.ui.cli.suggestions import (
    suggestions_show_command,
    suggestions_pending_command,
    suggestions_confirm_command,
    suggestions_reject_command,
    suggestions_stats_command,
)

from ragd.ui.cli.library import (
    library_show_command,
    library_create_command,
    library_add_command,
    library_remove_command,
    library_rename_command,
    library_delete_command,
    library_hide_command,
    library_validate_command,
    library_promote_command,
    library_pending_command,
    library_stats_command,
)

from ragd.ui.cli.errors import (
    handle_dependency_errors,
    format_error_for_cli,
)

from ragd.ui.cli.config_wizard import run_config_wizard
from ragd.ui.cli.config_debug import (
    show_effective_config,
    show_config_diff,
    show_config_source,
    validate_config,
)
from ragd.ui.cli.config_migration import (
    migrate_config,
    rollback_config,
    needs_migration,
)
from ragd.ui.cli.help_system import (
    show_extended_help,
    show_examples,
    list_help_topics,
)
from ragd.ui.cli.statistics import (
    IndexStatistics,
    get_index_statistics,
    format_statistics_table,
    format_statistics_json,
    format_statistics_plain,
)
from ragd.ui.cli.audit import (
    audit_list_command,
    audit_show_command,
    audit_clear_command,
    audit_stats_command,
)

__all__ = [
    "get_console",
    "init_command",
    "index_command",
    "search_command",
    "info_command",
    "status_command",
    "stats_command",
    "doctor_command",
    "config_command",
    "reindex_command",
    "meta_show_command",
    "meta_edit_command",
    "tag_add_command",
    "tag_remove_command",
    "tag_list_command",
    "list_documents_command",
    "export_command",
    "import_command",
    "watch_start_command",
    "watch_stop_command",
    "watch_status_command",
    "ask_command",
    "chat_command",
    "models_list_command",
    "models_recommend_command",
    "models_show_command",
    "models_set_command",
    "models_discover_command",
    "models_cards_command",
    "models_card_edit_command",
    "evaluate_command",
    "quality_command",
    # Backend commands
    "backend_show_command",
    "backend_list_command",
    "backend_health_command",
    "backend_set_command",
    "backend_benchmark_command",
    # Security commands
    "unlock_command",
    "lock_command",
    "password_change_command",
    "password_reset_command",
    "session_status_command",
    # Deletion commands
    "delete_command",
    "delete_audit_command",
    # Tier commands
    "tier_set_command",
    "tier_show_command",
    "tier_list_command",
    "tier_summary_command",
    "tier_promote_command",
    "tier_demote_command",
    # Collection commands (F-063)
    "collection_create_command",
    "collection_list_command",
    "collection_show_command",
    "collection_update_command",
    "collection_delete_command",
    "collection_export_command",
    # Suggestion commands (F-061)
    "suggestions_show_command",
    "suggestions_pending_command",
    "suggestions_confirm_command",
    "suggestions_reject_command",
    "suggestions_stats_command",
    # Library commands (F-062)
    "library_show_command",
    "library_create_command",
    "library_add_command",
    "library_remove_command",
    "library_rename_command",
    "library_delete_command",
    "library_hide_command",
    "library_validate_command",
    "library_promote_command",
    "library_pending_command",
    "library_stats_command",
    # Error handling
    "handle_dependency_errors",
    "format_error_for_cli",
    # Config wizard (F-088)
    "run_config_wizard",
    # Config debugging (F-097)
    "show_effective_config",
    "show_config_diff",
    "show_config_source",
    "validate_config",
    # Config migration (F-096)
    "migrate_config",
    "rollback_config",
    "needs_migration",
    # Help system (F-089)
    "show_extended_help",
    "show_examples",
    "list_help_topics",
    # Statistics (F-109)
    "IndexStatistics",
    "get_index_statistics",
    "format_statistics_table",
    "format_statistics_json",
    "format_statistics_plain",
    # Audit commands (F-112)
    "audit_list_command",
    "audit_show_command",
    "audit_clear_command",
    "audit_stats_command",
]
