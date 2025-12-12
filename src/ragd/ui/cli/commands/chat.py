"""Chat CLI commands for ragd.

This module contains ask and interactive chat commands for RAG-augmented conversation.
"""

from __future__ import annotations

import typer
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import (
    StreamingWordWrapper,
    format_citation_location,
    get_console,
)


def ask_command(
    question: str,
    model: str | None = None,
    temperature: float = 0.7,
    limit: int = 5,
    min_relevance: float | None = None,
    stream: bool = True,
    agentic: bool | None = None,
    show_confidence: bool = False,
    cite: str = "numbered",
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Ask a question using RAG with LLM generation.

    Retrieves relevant documents and generates an answer using Ollama.
    """
    from ragd.chat import (
        AgenticConfig,
        AgenticRAG,
        ChatConfig,
        ChatSession,
        check_chat_available,
    )
    from ragd.config import config_exists, load_config
    from ragd.ui.cli.commands.core import init_command

    # Auto-init if config doesn't exist
    if not config_exists():
        con = get_console(no_color)
        con.print("[yellow]ragd not initialised. Running first-time setup...[/yellow]\n")

        # Run init to detect hardware and create config
        init_command(no_color=no_color)
        con.print()  # Add spacing after init

    config = load_config()
    con = get_console(no_color, max_width=config.display.max_width)

    # Use config value as fallback for min_relevance
    effective_min_relevance = (
        min_relevance if min_relevance is not None else config.chat.min_relevance
    )

    # Check LLM availability
    available, message = check_chat_available(config)
    if not available:
        con.print(f"[red]LLM not available: {message}[/red]")
        con.print("\nTo use this feature:")
        con.print("  1. Install Ollama: https://ollama.ai")
        con.print("  2. Start Ollama: [cyan]ollama serve[/cyan]")
        con.print("  3. Pull a model: [cyan]ollama pull llama3.2:3b[/cyan]")
        raise typer.Exit(1)

    # Determine agentic mode
    use_agentic = agentic if agentic is not None else False

    if verbose:
        model_name = model or config.llm.model
        con.print(f"[dim]Model: {model_name}[/dim]")
        if use_agentic:
            con.print("[dim]Agentic mode: enabled (CRAG + Self-RAG)[/dim]")
        con.print("[dim]Retrieving context...[/dim]\n")

    try:
        if use_agentic:
            # Use AgenticRAG for CRAG + Self-RAG
            agentic_config = AgenticConfig(
                crag_enabled=True,
                self_rag_enabled=True,
                min_relevance=effective_min_relevance,
            )
            rag = AgenticRAG(config=config, agentic_config=agentic_config)

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=con,
                    transient=True,
                ) as progress:
                    progress.add_task("Generating answer (agentic)...", total=None)
                    response = rag.ask(question, max_results=limit, agentic=True)

                con.print("[bold]Answer:[/bold]\n")
                con.print(response.answer)

                # Show confidence if requested
                if show_confidence:
                    quality_color = {
                        "excellent": "green",
                        "good": "cyan",
                        "poor": "yellow",
                        "irrelevant": "red",
                    }.get(response.retrieval_quality.value, "white")
                    con.print(f"\n[dim]Confidence: {response.confidence:.0%} | "
                             f"Retrieval: [{quality_color}]{response.retrieval_quality.value}[/{quality_color}][/dim]")
                    if response.rewrites_attempted > 0:
                        con.print(f"[dim]Query rewrites: {response.rewrites_attempted}[/dim]")

                # Print citations (deduplicated)
                if response.citations and cite != "none":
                    from ragd.chat.context import deduplicate_citations
                    unique_citations = deduplicate_citations(response.citations)
                    con.print("\n[bold]Sources:[/bold]")
                    for i, cit in enumerate(unique_citations, 1):
                        loc = format_citation_location(cit)
                        con.print(f"  [{i}] {cit.filename}{loc}")
            finally:
                rag.close()

        else:
            # Standard chat mode
            chat_config = ChatConfig(
                model=model or config.llm.model,
                temperature=temperature,
                search_limit=limit,
                min_relevance=effective_min_relevance,
                auto_save=False,
            )

            session = ChatSession(config=config, chat_config=chat_config)

            try:
                if stream and output_format == "rich":
                    # Streaming output
                    con.print("[bold]Answer:[/bold]\n")

                    full_response = ""
                    citations = []

                    for chunk in session.ask(question, stream=True):
                        con.print(chunk, end="")
                        full_response += chunk

                    # Get citations from session history
                    if session.history.messages:
                        last_msg = session.history.messages[-1]
                        citations = last_msg.citations

                    con.print("\n")  # Newline after streaming

                    # Print citations (deduplicated)
                    if citations and cite != "none":
                        from ragd.chat.context import deduplicate_citations
                        unique_citations = deduplicate_citations(citations)
                        con.print("\n[bold]Sources:[/bold]")
                        for i, cit in enumerate(unique_citations, 1):
                            loc = format_citation_location(cit)
                            con.print(f"  [{i}] {cit.filename}{loc}")
                else:
                    # Non-streaming output
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=con,
                        transient=True,
                    ) as progress:
                        progress.add_task("Generating answer...", total=None)
                        answer = session.ask(question, stream=False)

                    con.print("[bold]Answer:[/bold]\n")
                    con.print(answer.answer)

                    # Print citations (deduplicated)
                    if answer.citations and cite != "none":
                        from ragd.chat.context import deduplicate_citations
                        unique_citations = deduplicate_citations(answer.citations)
                        con.print("\n[bold]Sources:[/bold]")
                        for i, cit in enumerate(unique_citations, 1):
                            loc = format_citation_location(cit)
                            con.print(f"  [{i}] {cit.filename}{loc}")
            finally:
                session.close()

    except Exception as e:
        con.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def chat_command(
    model: str | None = None,
    temperature: float = 0.7,
    limit: int = 5,
    min_relevance: float | None = None,
    session_id: str | None = None,
    cite: str | None = None,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Start an interactive chat session with RAG.

    Multi-turn conversation with your knowledge base.
    """
    from ragd.chat import ChatConfig, ChatSession, check_chat_available
    from ragd.config import config_exists, load_config
    from ragd.ui.cli.commands.core import init_command

    # Auto-init if config doesn't exist
    if not config_exists():
        con = get_console(no_color)
        con.print("[yellow]ragd not initialised. Running first-time setup...[/yellow]\n")

        # Run init to detect hardware and create config
        init_command(no_color=no_color)
        con.print()  # Add spacing after init

    config = load_config()
    con = get_console(no_color, max_width=config.display.max_width)

    # Get citation mode from config or parameter
    cite_mode = cite if cite is not None else config.chat.default_cite_mode

    # Use config value as fallback for min_relevance
    effective_min_relevance = (
        min_relevance if min_relevance is not None else config.chat.min_relevance
    )

    # Check LLM availability
    available, message = check_chat_available(config)
    if not available:
        con.print(f"[red]LLM not available: {message}[/red]")
        con.print("\nTo use this feature:")
        con.print("  1. Install Ollama: https://ollama.ai")
        con.print("  2. Start Ollama: [cyan]ollama serve[/cyan]")
        con.print("  3. Pull a model: [cyan]ollama pull llama3.2:3b[/cyan]")
        raise typer.Exit(1)

    # Build chat config
    chat_config = ChatConfig(
        model=model or config.llm.model,
        temperature=temperature,
        search_limit=limit,
        min_relevance=effective_min_relevance,
        auto_save=True,
    )

    session = ChatSession(config=config, chat_config=chat_config, session_id=session_id)

    # Print header
    from ragd.ui.styles import print_chat_header

    con.print()
    print_chat_header(con, chat_config.model)

    try:
        while True:
            try:
                user_input = con.input("[bold cyan]You:[/bold cyan] ")
            except EOFError:
                break
            except KeyboardInterrupt:
                con.print()
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/exit", "/quit", "/q"]:
                break
            elif user_input.lower() == "/help":
                con.print("\n[bold]Commands:[/bold]")
                con.print("  /search <query> [-n N]  - Search documents (default 15 results)")
                con.print("  /exit, /quit, /q        - Exit chat")
                con.print("  /clear                  - Clear conversation history")
                con.print("  /history                - Show conversation history")
                con.print("  /help                   - Show this help\n")
                continue
            elif user_input.lower() == "/clear":
                session.history.clear()
                con.print("[dim]Conversation history cleared.[/dim]\n")
                continue
            elif user_input.lower() == "/history":
                if not session.history.messages:
                    con.print("[dim]No conversation history.[/dim]\n")
                else:
                    con.print("\n[bold]History:[/bold]")
                    for msg in session.history.messages:
                        role = msg.role.value.capitalize()
                        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                        con.print(f"  [{role}] {content}")
                    con.print()
                continue
            elif user_input.lower().startswith("/search"):
                # Parse /search <query> [-n N] or [--limit N]
                search_text = user_input[7:].strip()

                if not search_text:
                    con.print("[yellow]Usage: /search <query> [-n N][/yellow]")
                    con.print("Example: /search machine learning")
                    con.print("Example: /search \"exact phrase\" -n 10\n")
                    continue

                # Parse optional limit argument
                search_limit = 15  # Default
                import re
                limit_match = re.search(r'(?:-n|--limit)\s+(\d+)', search_text)
                if limit_match:
                    search_limit = int(limit_match.group(1))
                    # Remove the limit argument from the query
                    search_text = re.sub(r'\s*(?:-n|--limit)\s+\d+', '', search_text).strip()

                # Remove surrounding quotes if present
                if (search_text.startswith('"') and search_text.endswith('"')) or \
                   (search_text.startswith("'") and search_text.endswith("'")):
                    search_text = search_text[1:-1]

                if not search_text:
                    con.print("[yellow]Please provide a search query.[/yellow]\n")
                    continue

                con.print(f"\n[dim]Searching for: {search_text} (limit: {search_limit})[/dim]\n")

                try:
                    from collections import OrderedDict
                    from ragd.search import SearchMode, hybrid_search

                    results = hybrid_search(
                        search_text,
                        limit=search_limit,
                        mode=SearchMode.HYBRID,
                        config=config,
                    )

                    if not results:
                        con.print("[yellow]No results found.[/yellow]\n")
                    else:
                        # Group results by document (using content_hash for dedup)
                        doc_results: OrderedDict[str, list] = OrderedDict()
                        for result in results:
                            doc_key = (
                                result.metadata.get("content_hash")
                                or result.document_id
                                or result.document_name
                                or "Unknown"
                            )
                            if doc_key not in doc_results:
                                doc_results[doc_key] = []
                            doc_results[doc_key].append(result)

                        con.print("[bold]Results:[/bold]")
                        for i, (doc_key, chunks) in enumerate(doc_results.items(), 1):
                            best_score = max(c.combined_score for c in chunks)
                            chunk_count = len(chunks)
                            display_name = chunks[0].document_name or doc_key

                            # Show document with best score and chunk count
                            if chunk_count > 1:
                                con.print(f"  [{i}] {display_name} (score: {best_score:.2f}, {chunk_count} chunks)")
                            else:
                                con.print(f"  [{i}] {display_name} (score: {best_score:.2f})")

                            # Show preview from highest-scoring chunk
                            best_chunk = max(chunks, key=lambda c: c.combined_score)
                            preview = best_chunk.content[:80].replace("\n", " ")
                            if len(best_chunk.content) > 80:
                                preview += "..."
                            con.print(f"      [dim]{preview}[/dim]")
                        con.print()
                except Exception as e:
                    con.print(f"[red]Search error: {e}[/red]\n")
                continue

            # Generate response with thinking indicator
            con.print()

            try:
                # Show thinking spinner
                from rich.status import Status
                response_started = False

                # Use word-aware wrapper for proper line wrapping
                wrapper = StreamingWordWrapper(
                    con, config.display.max_width, prefix_width=3
                )

                with Status("[dim]Thinking...[/dim]", console=con, spinner="dots") as status:
                    response_chunks = []
                    for chunk in session.chat(user_input, stream=True):
                        if not response_started:
                            # First chunk received - stop spinner and show prefix
                            status.stop()
                            con.print("[bold green]A:[/bold green] ", end="")
                            response_started = True
                        # Use wrapper for word-boundary aware output
                        wrapper.write(chunk)
                        response_chunks.append(chunk)

                    # Flush any remaining buffered content
                    wrapper.flush()

                if not response_started:
                    # No response received
                    con.print("[dim]No response generated.[/dim]")
                else:
                    con.print()  # End response line

                    # Display citations if enabled (deduplicated)
                    # Skip for "no information" responses (citations will be empty)
                    if cite_mode != "none" and session.history.messages:
                        last_msg = session.history.messages[-1]
                        if last_msg.citations:
                            from ragd.chat.context import deduplicate_citations
                            unique_citations = deduplicate_citations(last_msg.citations)
                            con.print("\n[bold]Sources:[/bold]")
                            for i, cit in enumerate(unique_citations, 1):
                                loc = format_citation_location(cit)
                                con.print(f"  [{i}] {cit.filename}{loc}")

                    con.print()  # Extra line before next prompt
            except Exception as e:
                con.print(f"\n[red]Error: {e}[/red]\n")

    except Exception as e:
        con.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()
        con.print("[dim]Chat session saved.[/dim]")


def compare_command(
    question: str,
    models: str | None = None,
    judge: str | None = None,
    ensemble: bool = False,
    limit: int = 5,
    temperature: float = 0.7,
    verbose: bool = False,
    no_color: bool = False,
) -> None:
    """Compare outputs from multiple LLM models.

    Query multiple models with the same context and compare responses
    side-by-side, with optional judge evaluation or ensemble voting.
    """
    from ragd.config import config_exists, load_config
    from ragd.llm.comparator import ModelComparator, get_available_models
    from ragd.search import SearchMode, hybrid_search
    from ragd.ui.cli.commands.core import init_command
    from ragd.ui.formatters.comparison import print_comparison

    # Auto-init if config doesn't exist
    if not config_exists():
        con = get_console(no_color)
        con.print("[yellow]ragd not initialised. Running first-time setup...[/yellow]\n")
        init_command(no_color=no_color)
        con.print()

    config = load_config()
    con = get_console(no_color, max_width=config.display.max_width)

    # Get available models
    available = get_available_models(config.llm.base_url)
    if not available:
        con.print("[red]No Ollama models available.[/red]")
        con.print("\nTo use this feature:")
        con.print("  1. Start Ollama: [cyan]ollama serve[/cyan]")
        con.print("  2. Pull models: [cyan]ollama pull llama3.2:3b[/cyan]")
        raise typer.Exit(1)

    # Parse model list
    if models == "all":
        model_list = available[:3]  # Limit to 3 for performance
    elif models:
        model_list = [m.strip() for m in models.split(",")]
    else:
        # Default: compare configured model with next available
        model_list = [config.llm.model]
        for m in available:
            if m != config.llm.model and len(model_list) < 2:
                model_list.append(m)

    if len(model_list) < 2:
        con.print("[red]Need at least 2 models for comparison[/red]")
        con.print(f"Available models: {', '.join(available)}")
        raise typer.Exit(1)

    # Validate models
    for m in model_list:
        if m not in available and not any(m.startswith(a.split(":")[0]) for a in available):
            con.print(f"[yellow]Warning: Model '{m}' may not be available[/yellow]")

    if verbose:
        con.print(f"[dim]Models: {', '.join(model_list)}[/dim]")
        if judge:
            con.print(f"[dim]Judge: {judge}[/dim]")
        if ensemble:
            con.print("[dim]Mode: Ensemble voting[/dim]")
        con.print("[dim]Retrieving context...[/dim]\n")

    # Get context via search
    try:
        results = hybrid_search(
            question,
            limit=limit,
            mode=SearchMode.HYBRID,
            config=config,
        )
        context = "\n\n".join([r.content for r in results[:limit]])
    except Exception as e:
        con.print(f"[red]Search error: {e}[/red]")
        context = ""

    # Create comparator
    comparator = ModelComparator(
        base_url=config.llm.base_url,
        timeout_seconds=config.retrieval.contextual.timeout_seconds,
    )

    # Run comparison
    try:
        if judge:
            result = comparator.compare_with_judge(
                query=question,
                models=model_list,
                judge_model=judge,
                context=context,
                temperature=temperature,
            )
        elif ensemble:
            result = comparator.compare_ensemble(
                query=question,
                models=model_list,
                context=context,
                temperature=temperature,
            )
        else:
            result = comparator.compare(
                query=question,
                models=model_list,
                context=context,
                temperature=temperature,
            )

        print_comparison(result, no_color=no_color)

    except Exception as e:
        con.print(f"[red]Comparison error: {e}[/red]")
        raise typer.Exit(1)


__all__ = [
    "ask_command",
    "chat_command",
    "compare_command",
]
