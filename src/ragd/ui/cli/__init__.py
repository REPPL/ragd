"""CLI interface components."""

from ragd.ui.cli.commands import (
    get_console,
    init_command,
    index_command,
    search_command,
    status_command,
    doctor_command,
    config_command,
    reindex_command,
    meta_show_command,
    meta_edit_command,
    tag_add_command,
    tag_remove_command,
    tag_list_command,
    list_documents_command,
)

__all__ = [
    "get_console",
    "init_command",
    "index_command",
    "search_command",
    "status_command",
    "doctor_command",
    "config_command",
    "reindex_command",
    "meta_show_command",
    "meta_edit_command",
    "tag_add_command",
    "tag_remove_command",
    "tag_list_command",
    "list_documents_command",
]
