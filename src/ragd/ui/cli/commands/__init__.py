"""CLI commands package for ragd.

This package contains command implementations organised by domain:
- core: Fundamental commands (init, index, search, status, etc.)
- chat: Ask and interactive chat commands
- models: LLM model management commands
- metadata: Document metadata and tag management
- archive: Export and import commands
- watch: Directory watch commands
- quality: Evaluation and quality assessment
"""

from ragd.ui.cli.commands.archive import (
    export_command,
    import_command,
)
from ragd.ui.cli.commands.chat import (
    ask_command,
    chat_command,
    compare_command,
)
from ragd.ui.cli.commands.core import (
    config_command,
    doctor_command,
    index_command,
    info_command,
    init_command,
    list_documents_command,
    reindex_command,
    search_command,
    stats_command,
    status_command,
)
from ragd.ui.cli.commands.metadata import (
    meta_edit_command,
    meta_show_command,
    tag_add_command,
    tag_list_command,
    tag_remove_command,
)
from ragd.ui.cli.commands.migrate import (
    migrate_command,
    migrate_status_command,
)
from ragd.ui.cli.commands.models import (
    models_card_edit_command,
    models_cards_command,
    models_discover_command,
    models_list_command,
    models_recommend_command,
    models_set_command,
    models_show_command,
)
from ragd.ui.cli.commands.profile import (
    profile_all_command,
    profile_chat_command,
    profile_compare_command,
    profile_index_command,
    profile_search_command,
    profile_startup_command,
)
from ragd.ui.cli.commands.quality import (
    evaluate_command,
    quality_command,
)
from ragd.ui.cli.commands.watch import (
    watch_start_command,
    watch_status_command,
    watch_stop_command,
)

# Re-export utilities for backwards compatibility
from ragd.ui.cli.utils import StreamingWordWrapper, get_console

__all__ = [
    # Utils
    "get_console",
    "StreamingWordWrapper",
    # Core commands
    "init_command",
    "index_command",
    "search_command",
    "info_command",
    "status_command",
    "stats_command",
    "doctor_command",
    "config_command",
    "reindex_command",
    "list_documents_command",
    # Chat commands
    "ask_command",
    "chat_command",
    "compare_command",
    # Model commands
    "models_list_command",
    "models_set_command",
    "models_recommend_command",
    "models_show_command",
    "models_discover_command",
    "models_cards_command",
    "models_card_edit_command",
    # Metadata commands
    "meta_show_command",
    "meta_edit_command",
    "tag_add_command",
    "tag_remove_command",
    "tag_list_command",
    # Archive commands
    "export_command",
    "import_command",
    # Watch commands
    "watch_start_command",
    "watch_stop_command",
    "watch_status_command",
    # Quality commands
    "evaluate_command",
    "quality_command",
    # Profile commands
    "profile_index_command",
    "profile_search_command",
    "profile_chat_command",
    "profile_all_command",
    "profile_compare_command",
    "profile_startup_command",
    # Migration commands
    "migrate_command",
    "migrate_status_command",
]
