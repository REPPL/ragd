# State-of-the-Art User Interfaces: TUI & WebUI

## Executive Summary

**Key Recommendations for ragd:**

1. **TUI Framework:** Use Textual (built on Rich) - async-native, CSS styling, excellent widget library
2. **WebUI for v0.6+:** Gradio for quick RAG demos; consider Reflex for full-featured application
3. **Prototyping Tools:** Excalidraw for quick wireframes, Penpot for detailed designs
4. **Interface Hierarchy:** CLI (v0.1) → TUI (v0.3) → WebUI (v0.6) - progressively richer interfaces
5. **Learn from Open WebUI:** Feature-rich reference for RAG interface patterns

---

## Interface Strategy Overview

### When to Use Each Interface

| Interface | Best For | User Type | Complexity |
|-----------|----------|-----------|------------|
| **CLI** | Scripts, automation, power users | Developers | Low |
| **TUI** | Interactive sessions, richer display | Technical users | Medium |
| **WebUI** | Collaboration, non-technical users | Everyone | High |

### Progressive Interface Architecture

```
v0.1: CLI (Core)
├─ All functionality accessible
├─ Scripts and automation
└─ Foundation for other interfaces

v0.3: TUI (Enhancement)
├─ Rich interactive experience
├─ Same backend as CLI
└─ No browser required

v0.6: WebUI (Expansion)
├─ Browser-based access
├─ Multi-user support
└─ Mobile-friendly
```

---

## Part 1: Terminal User Interfaces (TUI)

### Python TUI Framework Comparison

| Framework | Stars | Maturity | Best For |
|-----------|-------|----------|----------|
| **Textual** | 25K+ | Production | Modern TUIs, async apps |
| **Rich** | 49K+ | Stable | Output formatting (ragd already uses) |
| **Urwid** | 2.7K | Mature | Traditional ncurses-style |
| **Blessed** | 1K | Stable | Terminal manipulation |
| **Prompt Toolkit** | 9K | Stable | Interactive prompts |

### Recommendation: Textual

**Why Textual for ragd:**
- Built on Rich (already a dependency)
- Modern async architecture
- CSS-like styling
- Comprehensive widget library
- Active development (Textualize team)
- Web deployment option via textual-web

**Source:** [Textual Documentation](https://textual.textualize.io/)

### Textual Architecture

```
┌──────────────────────────────────────────────┐
│              Textual Application             │
├──────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────┐  │
│  │   Header   │  │  Sidebar   │  │  Main  │  │
│  │   Widget   │  │   Widget   │  │  Area  │  │
│  └────────────┘  └────────────┘  └────────┘  │
├──────────────────────────────────────────────┤
│              Message System                  │
│         (Events, Actions, Workers)           │
├──────────────────────────────────────────────┤
│           Rich Console Renderer              │
└──────────────────────────────────────────────┘
```

### Key Features

**Widgets Available:**
- Input, TextArea (text input)
- Button, Checkbox, Switch (controls)
- DataTable, Tree, ListView (data display)
- Markdown, RichLog (formatted text)
- Tabs, ContentSwitcher (navigation)
- ProgressBar, LoadingIndicator (feedback)

**Styling:**
```css
/* textual.tcss - CSS-like styling */
Screen {
    background: $surface;
}

#query-input {
    dock: bottom;
    height: 3;
    border: solid $primary;
}

.result-item {
    padding: 1 2;
    margin: 1 0;
}

.result-item:hover {
    background: $primary-darken-2;
}
```

### Example: RAG TUI Structure

```python
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Input, Button,
    RichLog, Static, DataTable
)

class RAGApp(App):
    """TUI for ragd."""

    CSS_PATH = "ragd.tcss"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "search", "Search"),
        ("ctrl+n", "new_conversation", "New"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            # Sidebar: Sources and history
            with Vertical(id="sidebar"):
                yield Static("Sources", classes="section-title")
                yield DataTable(id="sources-table")
                yield Static("History", classes="section-title")
                yield DataTable(id="history-table")

            # Main area: Conversation
            with Vertical(id="main"):
                yield RichLog(id="conversation", wrap=True)

                with Horizontal(id="input-area"):
                    yield Input(
                        placeholder="Ask a question...",
                        id="query-input"
                    )
                    yield Button("Send", id="send-btn", variant="primary")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            await self.handle_query()

    async def handle_query(self) -> None:
        input_widget = self.query_one("#query-input", Input)
        log = self.query_one("#conversation", RichLog)

        query = input_widget.value
        input_widget.value = ""

        # Show user query
        log.write(f"[bold blue]You:[/bold blue] {query}")

        # Show thinking indicator
        log.write("[dim]Thinking...[/dim]")

        # Run RAG pipeline (in worker to not block UI)
        self.run_worker(self.execute_query(query))

    async def execute_query(self, query: str) -> str:
        # Call ragd backend
        from ragd.pipeline import query as rag_query
        return await rag_query(query)
```

### Terminal Compatibility

| Terminal | Colour Support | Mouse | Unicode | Notes |
|----------|---------------|-------|---------|-------|
| **iTerm2** | 24-bit | Yes | Full | Excellent |
| **Windows Terminal** | 24-bit | Yes | Full | Excellent |
| **macOS Terminal** | 256 | Yes | Full | Good |
| **GNOME Terminal** | 24-bit | Yes | Full | Excellent |
| **VS Code Terminal** | 24-bit | Yes | Full | Excellent |
| **SSH (remote)** | Varies | Maybe | Varies | Test carefully |
| **tmux** | 24-bit* | Yes | Full | Needs config |

**Detection Strategy:**
```python
import os
import sys

def get_terminal_capabilities():
    """Detect terminal capabilities."""
    caps = {
        "color_depth": 24 if os.environ.get("COLORTERM") == "truecolor" else 256,
        "unicode": sys.stdout.encoding.lower().startswith("utf"),
        "mouse": sys.stdout.isatty(),
        "width": os.get_terminal_size().columns if sys.stdout.isatty() else 80,
    }
    return caps
```

**Source:** [Real Python: Python Textual](https://realpython.com/python-textual/)

---

## Part 2: Web User Interfaces

### Python WebUI Framework Comparison

| Framework | Best For | Learning Curve | Customisation |
|-----------|----------|----------------|---------------|
| **Gradio** | ML demos, quick prototypes | Low | Limited |
| **Streamlit** | Data dashboards, visualisation | Low | Medium |
| **NiceGUI** | Multi-page apps, custom UI | Medium | High |
| **Reflex** | Full-stack apps, React-like | Medium | Very High |
| **Chainlit** | Chat interfaces, LLM apps | Low | Medium |
| **Panel** | Scientific apps, dashboards | Medium | High |

### Quick Recommendations

| Use Case | Framework |
|----------|-----------|
| Quick RAG demo | Gradio |
| Data exploration UI | Streamlit |
| Production chat interface | Chainlit or Reflex |
| Full-featured application | Reflex |
| Dashboard with charts | Streamlit or Panel |

### Gradio for Quick Demos

**Pros:**
- Fastest path to working demo
- Built-in chat interface components
- Hugging Face integration
- Auto-generated API

**Cons:**
- Limited layout flexibility
- Styling constraints
- Not ideal for complex applications

```python
import gradio as gr

def query_rag(message: str, history: list) -> str:
    """Handle RAG query."""
    from ragd.pipeline import query
    response = query(message)
    return response

demo = gr.ChatInterface(
    fn=query_rag,
    title="ragd",
    description="Ask questions about your documents",
    examples=[
        "What is machine learning?",
        "Summarise the main points",
        "Find documents about Python",
    ],
    retry_btn="Retry",
    undo_btn="Undo",
    clear_btn="Clear",
)

demo.launch(server_port=8080)
```

**Source:** [Gradio vs Streamlit Comparison](https://towardsdatascience.com/gradio-vs-streamlit-vs-dash-vs-flask-d3defb1209a2/)

### Reflex for Full Applications

**Pros:**
- Pure Python, compiles to React
- Full-stack (frontend + backend)
- Access to React ecosystem
- WebSocket state sync
- Production-ready

**Cons:**
- Steeper learning curve
- More complex than Gradio/Streamlit
- Newer, smaller community

```python
import reflex as rx

class State(rx.State):
    """Application state."""
    messages: list[dict] = []
    query: str = ""
    loading: bool = False

    async def send_query(self):
        """Handle query submission."""
        if not self.query.strip():
            return

        self.loading = True
        self.messages.append({
            "role": "user",
            "content": self.query
        })

        # Call RAG backend
        from ragd.pipeline import query as rag_query
        response = await rag_query(self.query)

        self.messages.append({
            "role": "assistant",
            "content": response
        })

        self.query = ""
        self.loading = False

def message_bubble(msg: dict) -> rx.Component:
    """Render a chat message."""
    is_user = msg["role"] == "user"
    return rx.box(
        rx.text(msg["content"]),
        bg="blue.100" if is_user else "gray.100",
        p=3,
        border_radius="lg",
        align_self="flex-end" if is_user else "flex-start",
        max_width="80%",
    )

def chat_area() -> rx.Component:
    """Main chat interface."""
    return rx.vstack(
        rx.foreach(State.messages, message_bubble),
        width="100%",
        spacing=2,
        overflow_y="auto",
        flex=1,
    )

def input_area() -> rx.Component:
    """Query input area."""
    return rx.hstack(
        rx.input(
            placeholder="Ask a question...",
            value=State.query,
            on_change=State.set_query,
            flex=1,
        ),
        rx.button(
            "Send",
            on_click=State.send_query,
            loading=State.loading,
        ),
        width="100%",
    )

def index() -> rx.Component:
    """Main page."""
    return rx.vstack(
        rx.heading("ragd", size="lg"),
        chat_area(),
        input_area(),
        height="100vh",
        p=4,
    )

app = rx.App()
app.add_page(index)
```

**Source:** [Reflex Architecture](https://reflex.dev/blog/2024-03-21-reflex-architecture/)

### Learning from Open WebUI

Open WebUI is the leading open-source web interface for LLMs. Key features to learn from:

| Feature | Implementation | Relevance to ragd |
|---------|----------------|-------------------|
| **Chat History** | Persistent conversations | Essential for v0.6 |
| **RAG Integration** | Multiple vector DBs | Core functionality |
| **Model Switching** | Dropdown selector | Useful for multi-model |
| **Web Search** | 15+ providers | Good for enhancement |
| **Voice Input** | Whisper integration | Accessibility |
| **Document Upload** | Drag-and-drop | Document ingestion UX |
| **Markdown Rendering** | Full support | Response formatting |
| **Code Highlighting** | Syntax highlighting | Developer-friendly |

**Source:** [Open WebUI Features](https://docs.openwebui.com/features/)

---

## Part 3: Rapid Prototyping Tools

### Wireframing Comparison

| Tool | Type | Cost | Collaboration | Best For |
|------|------|------|---------------|----------|
| **Excalidraw** | Whiteboard | Free | Real-time | Quick sketches |
| **Penpot** | Design tool | Free/Open | Real-time | Full designs |
| **tldraw** | Whiteboard | Free | Real-time | Quick diagrams |
| **Figma** | Design tool | Freemium | Real-time | Professional |
| **Balsamiq** | Wireframes | Paid | Limited | Lo-fi wireframes |

### Recommendation: Penpot + Excalidraw

**Excalidraw for quick sketches:**
- Instant collaborative whiteboard
- No account required
- Export to PNG/SVG
- Perfect for initial ideas

**Penpot for detailed designs:**
- Open-source Figma alternative
- CSS-based (developer-friendly)
- Self-hostable
- Free Inspect tab (code export)
- Real-time collaboration

**Source:** [Penpot vs Figma](https://penpot.app/penpot-vs-figma)

### Prototyping Workflow

```
1. IDEATION (Excalidraw)
   ├─ Rough sketches
   ├─ Layout options
   └─ Quick iteration

2. WIREFRAMES (Penpot)
   ├─ Low-fidelity mockups
   ├─ Component structure
   └─ User flow diagrams

3. HIGH-FIDELITY (Penpot)
   ├─ Final designs
   ├─ Style guide
   └─ Component library

4. IMPLEMENTATION
   ├─ Export CSS from Penpot
   ├─ Reference designs
   └─ Component-by-component build
```

### Design System for ragd

```css
/* ragd Design Tokens (Penpot → Textual/WebUI) */

:root {
  /* Colours */
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-secondary: #64748b;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;

  /* Surfaces */
  --surface-background: #ffffff;
  --surface-elevated: #f8fafc;
  --surface-overlay: rgba(0, 0, 0, 0.5);

  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

---

## Part 4: Accessibility Considerations

### TUI Accessibility

| Feature | Implementation |
|---------|----------------|
| **Screen reader support** | Plain text mode via `--plain` |
| **High contrast** | Alternative colour scheme |
| **Keyboard navigation** | Full keyboard support (Textual default) |
| **Font scaling** | Respect terminal font size |
| **Colour blindness** | Avoid red/green only distinctions |

### WebUI Accessibility

| Feature | WCAG Level | Implementation |
|---------|------------|----------------|
| **Keyboard navigation** | A | Tab order, focus indicators |
| **Screen reader** | A | ARIA labels, semantic HTML |
| **Colour contrast** | AA | 4.5:1 minimum ratio |
| **Text scaling** | AA | Relative units (rem, em) |
| **Focus indicators** | AA | Visible focus states |
| **Error messages** | A | Associated with inputs |

### Accessibility Testing

```python
# TUI accessibility check
def ensure_accessible_output(text: str, use_colour: bool = True) -> str:
    """Ensure output is accessible."""
    if not use_colour:
        # Strip Rich markup for plain text
        from rich.text import Text
        return Text.from_markup(text).plain

    # Check for colour-only information
    # Add text indicators alongside colours
    return text

# WebUI accessibility (Reflex example)
def accessible_button(text: str, **props) -> rx.Component:
    """Create an accessible button."""
    return rx.button(
        text,
        aria_label=props.get("aria_label", text),
        **props
    )
```

---

## Recommended Architecture for ragd

### Interface Roadmap

```
v0.1 (Foundation)
└── CLI
    ├── Core commands (add, search, ask)
    ├── Rich output formatting
    └── JSON mode for scripts

v0.3 (Enhancement)
└── TUI (Textual)
    ├── Interactive chat mode
    ├── Document browser
    ├── Search interface
    └── Status dashboard

v0.6 (Expansion)
└── WebUI (Gradio → Reflex)
    ├── v0.6.0: Gradio demo interface
    ├── v0.6.x: Full Reflex application
    ├── Multi-user support
    └── Document upload UI
```

### Shared Backend Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Interfaces                 │
├─────────────────┬─────────────┬─────────────────┤
│       CLI       │     TUI     │     WebUI       │
│    (Typer)      │  (Textual)  │ (Gradio/Reflex) │
├─────────────────┴─────────────┴─────────────────┤
│                   Core API                       │
│              (Python functions)                  │
├─────────────────────────────────────────────────┤
│             RAG Pipeline                         │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│   │Retriever│  │Generator│  │ Reranker│        │
│   └─────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────┤
│                  Storage                         │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│   │VectorDB │  │Documents│  │  Config │        │
│   └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────┘
```

### Configuration for Interfaces

```yaml
# ~/.ragd/config.yaml

interfaces:
  cli:
    enabled: true
    default_format: rich  # rich, plain, json

  tui:
    enabled: true
    theme: default  # default, dark, light, high-contrast
    keybindings: vim  # vim, emacs, default

  webui:
    enabled: false  # Enable in v0.6
    framework: gradio  # gradio, reflex
    host: "127.0.0.1"
    port: 8080
    auth:
      enabled: false
      users: []
```

---

## References

### TUI Frameworks
- [Textual Documentation](https://textual.textualize.io/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Real Python: Building UIs with Textual](https://realpython.com/python-textual/)
- [Awesome TUIs](https://github.com/rothgar/awesome-tuis)

### WebUI Frameworks
- [Gradio Documentation](https://www.gradio.app/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Reflex Documentation](https://reflex.dev/docs/)
- [NiceGUI Documentation](https://nicegui.io/documentation)
- [Chainlit Documentation](https://docs.chainlit.io/)

### Design Tools
- [Penpot](https://penpot.app/)
- [Excalidraw](https://excalidraw.com/)
- [tldraw](https://www.tldraw.com/)

### Reference Implementations
- [Open WebUI](https://github.com/open-webui/open-webui)
- [text-generation-webui](https://github.com/oobabooga/text-generation-webui)
- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm)

---

## Related Documentation

- [CLI Best Practices](./cli-best-practices.md) - CLI design principles
- [State-of-the-Art CLI Modes](./state-of-the-art-cli-modes.md) - User/expert interface design
- [State-of-the-Art Setup UX](./state-of-the-art-setup-ux.md) - Installation experience
- [Features Roadmap](../features/planned/README.md) - Planned features (TUI/WebUI pending)

---

**Status:** Research complete
