"""Interactive TUI for ragd search results using Textual."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ragd.search.searcher import SearchResult


class ResultPanel(Static):
    """A panel displaying a single search result."""

    def __init__(self, result: SearchResult) -> None:
        """Initialise the result panel.

        Args:
            result: The search result to display
        """
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        yield Static(self._render_content())

    def _truncate_title(self, title: str, max_len: int = 60) -> str:
        """Truncate title to max length with ellipsis."""
        if len(title) <= max_len:
            return title
        return title[: max_len - 3] + "..."

    def _render_content(self) -> Panel:
        """Render the result as a Rich Panel."""
        title = self._truncate_title(self.result.document_name)

        return Panel(
            self.result.content,
            title=title,
            title_align="center",
            border_style="blue",
            padding=(1, 2),
        )


class StatusBar(Static):
    """Status bar showing chunk, count, and score."""

    def __init__(self, result: SearchResult, index: int, total: int) -> None:
        """Initialise the status bar.

        Args:
            result: The search result
            index: Current result index (0-based)
            total: Total number of results
        """
        super().__init__()
        self.result = result
        self.index = index
        self.total = total

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        yield Static(self._render_status())

    def _render_status(self) -> Table:
        """Render the status bar as a table."""
        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="center", ratio=1)
        table.add_column(justify="right", ratio=1)

        chunk_text = Text(f"Chunk {self.result.chunk_index}", style="blue")
        count_text = Text(f"[{self.index + 1}/{self.total}]", style="blue")
        score_text = Text(f"{self.result.score:.4f}", style="red bold")

        table.add_row(chunk_text, count_text, score_text)

        return table


class SearchNavigator(App):
    """Interactive navigator for search results."""

    CSS = """
    Screen {
        background: $surface;
    }

    #result-container {
        height: 1fr;
        padding: 1 1 0 1;
    }

    #panel-wrapper {
        height: 1fr;
    }

    ResultPanel {
        height: 1fr;
        width: 100%;
    }

    ResultPanel > Static {
        height: 1fr;
    }

    StatusBar {
        height: 1;
        width: 100%;
        margin: 0 1 1 1;
    }
    """

    BINDINGS = [
        Binding("j", "next", "Next"),
        Binding("down", "next", "Next", show=False),
        Binding("k", "prev", "Previous"),
        Binding("up", "prev", "Previous", show=False),
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        results: list[SearchResult],
        query: str,
    ) -> None:
        """Initialise the search navigator.

        Args:
            results: List of search results to display
            query: The original search query
        """
        super().__init__()
        self.results = results
        self.query = query
        self.current_index = 0

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header(show_clock=False)
        yield Vertical(
            ResultPanel(self.results[self.current_index]),
            StatusBar(
                self.results[self.current_index],
                self.current_index,
                len(self.results),
            ),
            id="result-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the app on mount."""
        self.title = f'Results for "{self.query}"'
        self.sub_title = ""

    def action_next(self) -> None:
        """Navigate to the next result."""
        if self.current_index < len(self.results) - 1:
            self.current_index += 1
            self._update_display()

    def action_prev(self) -> None:
        """Navigate to the previous result."""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()

    def _update_display(self) -> None:
        """Update the displayed result."""
        container = self.query_one("#result-container")
        container.remove_children()
        container.mount(ResultPanel(self.results[self.current_index]))
        container.mount(
            StatusBar(
                self.results[self.current_index],
                self.current_index,
                len(self.results),
            )
        )


def run_search_navigator(results: list[SearchResult], query: str) -> None:
    """Run the interactive search navigator.

    Args:
        results: List of search results to display
        query: The original search query
    """
    if not results:
        return

    app = SearchNavigator(results, query)
    app.run()
