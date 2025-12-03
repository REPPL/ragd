"""CLI interface components."""

from ragd.ui.cli.commands import (
    get_console,
    init_command,
    index_command,
    search_command,
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

from ragd.ui.cli.errors import (
    handle_dependency_errors,
    format_error_for_cli,
)

__all__ = [
    "get_console",
    "init_command",
    "index_command",
    "search_command",
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
    # Error handling
    "handle_dependency_errors",
    "format_error_for_cli",
]
