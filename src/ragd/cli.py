"""CLI interface for ragd using Typer.

This module provides the command-line interface for ragd, including commands
for initialisation, indexing, searching, and system status.

Command implementations are in ragd.ui.cli.commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragd import __version__
from ragd.ui.cli import (
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
    # Backend commands
    backend_show_command,
    backend_list_command,
    backend_health_command,
    backend_set_command,
    backend_benchmark_command,
)

app = typer.Typer(
    name="ragd",
    help="Local RAG for personal knowledge management.",
    no_args_is_help=True,
)
console = Console()

# Subcommand groups
meta_app = typer.Typer(help="Manage document metadata.")
tag_app = typer.Typer(help="Manage document tags.")
watch_app = typer.Typer(help="Watch folders for automatic indexing.")
models_app = typer.Typer(help="Manage LLM models.")
backend_app = typer.Typer(help="Manage vector store backends.")
app.add_typer(meta_app, name="meta")
app.add_typer(tag_app, name="tag")
app.add_typer(watch_app, name="watch")
app.add_typer(models_app, name="models")
app.add_typer(backend_app, name="backend")


# Output format option
FormatOption = Annotated[
    str,
    typer.Option(
        "--format",
        "-f",
        help="Output format: rich, plain, or json.",
    ),
]


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ragd version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """ragd - Local RAG for personal knowledge management."""


@app.command()
def init(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Initialise ragd with guided setup.

    Detects hardware capabilities and creates optimal configuration.
    """
    init_command(no_color=no_color)


@app.command()
def index(
    path: Annotated[Path, typer.Argument(help="File or directory to index.")],
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Search directories recursively."
    ),
    skip_duplicates: bool = typer.Option(
        True, "--skip-duplicates/--no-skip-duplicates", help="Skip already-indexed documents."
    ),
    contextual: bool = typer.Option(
        None, "--contextual/--no-contextual", "-c",
        help="Enable contextual retrieval (requires Ollama). Uses config if not specified."
    ),
    late_chunking: bool = typer.Option(
        None, "--late-chunking/--no-late-chunking", "-l",
        help="Enable late chunking for context-aware embeddings. Uses config if not specified."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Show per-file progress instead of progress bar."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Index documents from a file or directory.

    Supported formats: PDF, TXT, MD, HTML

    Contextual retrieval generates AI-powered context for each chunk,
    improving search accuracy. Requires Ollama to be running locally.

    Late chunking embeds chunks with full document context, improving
    embedding quality for retrieval.
    """
    index_command(
        path=path,
        recursive=recursive,
        skip_duplicates=skip_duplicates,
        contextual=contextual,
        late_chunking=late_chunking,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


SearchModeOption = Annotated[
    str,
    typer.Option(
        "--mode",
        "-m",
        help="Search mode: hybrid (default), semantic, or keyword.",
    ),
]

CitationOption = Annotated[
    str,
    typer.Option(
        "--cite",
        help="Citation style: none, inline, apa, mla, chicago, bibtex, markdown.",
    ),
]


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results."),
    min_score: float = typer.Option(
        None, "--min-score", help="Minimum similarity score (0-1). Default: 0.3"
    ),
    mode: SearchModeOption = "hybrid",
    cite: CitationOption = "none",
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Disable interactive navigator, print results directly."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks using hybrid search (semantic + keyword).
    By default, opens an interactive navigator to browse results (use j/k or arrows to navigate, q to quit).

    Search modes:
      - hybrid: Combines semantic and keyword search (default)
      - semantic: Pure vector similarity search
      - keyword: Pure BM25 keyword search

    Citation styles:
      - none: No citations (default)
      - inline: Simple (filename, p. X) format
      - apa: APA 7th edition
      - mla: MLA 9th edition
      - chicago: Chicago notes-bibliography
      - bibtex: BibTeX for LaTeX
      - markdown: Markdown link format
    """
    search_command(
        query=query,
        limit=limit,
        min_score=min_score,
        mode=mode,
        cite=cite,
        no_interactive=no_interactive,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def status(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show ragd status and statistics."""
    status_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def doctor(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run health checks on ragd components.

    Validates configuration, storage, embedding model, and dependencies.
    """
    doctor_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration."),
    path: bool = typer.Option(False, "--path", "-p", help="Show configuration file path."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Manage ragd configuration."""
    config_command(
        show=show,
        path=path,
        no_color=no_color,
    )


@app.command()
def reindex(
    document_id: Annotated[
        str | None, typer.Argument(help="Specific document ID to re-index.")
    ] = None,
    all_docs: bool = typer.Option(False, "--all", "-a", help="Re-index all documents."),
    file_type: str = typer.Option(None, "--type", "-t", help="Re-index by file type (pdf, html)."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show per-file progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Re-index documents with improved text extraction.

    Use this command after upgrading ragd to apply the latest text
    quality improvements to existing documents.

    Examples:
        ragd reindex --all              # Re-index all documents
        ragd reindex --type pdf         # Re-index only PDFs
        ragd reindex doc-123            # Re-index specific document
        ragd reindex --all --force      # Re-index without confirmation
    """
    reindex_command(
        document_id=document_id,
        all_docs=all_docs,
        file_type=file_type,
        force=force,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Metadata subcommands ---

@meta_app.command("show")
def meta_show(
    document_id: Annotated[str, typer.Argument(help="Document ID to show metadata for.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show metadata for a document.

    Displays Dublin Core metadata and RAG-specific fields.
    """
    meta_show_command(
        document_id=document_id,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@meta_app.command("edit")
def meta_edit(
    document_id: Annotated[str, typer.Argument(help="Document ID to edit.")],
    title: str = typer.Option(None, "--title", help="Set document title."),
    creator: str = typer.Option(None, "--creator", help="Set creator(s), semicolon-separated."),
    description: str = typer.Option(None, "--description", help="Set description."),
    doc_type: str = typer.Option(None, "--type", help="Set document type."),
    project: str = typer.Option(None, "--project", help="Set project name."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Edit metadata for a document.

    Update specific metadata fields. Use semicolons to separate multiple creators.

    Examples:
        ragd meta edit doc-123 --title "My Document"
        ragd meta edit doc-123 --creator "Smith, J.; Doe, J."
        ragd meta edit doc-123 --project "Research"
    """
    meta_edit_command(
        document_id=document_id,
        title=title,
        creator=creator,
        description=description,
        doc_type=doc_type,
        project=project,
        no_color=no_color,
    )


# --- Tag subcommands ---

@tag_app.command("add")
def tag_add(
    document_id: Annotated[str, typer.Argument(help="Document ID to tag.")],
    tags: Annotated[list[str], typer.Argument(help="Tags to add.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Add tags to a document.

    Examples:
        ragd tag add doc-123 important
        ragd tag add doc-123 "topic:ml" "status:reading"
    """
    tag_add_command(
        document_id=document_id,
        tags=tags,
        no_color=no_color,
    )


@tag_app.command("remove")
def tag_remove(
    document_id: Annotated[str, typer.Argument(help="Document ID to untag.")],
    tags: Annotated[list[str], typer.Argument(help="Tags to remove.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Remove tags from a document.

    Examples:
        ragd tag remove doc-123 draft
    """
    tag_remove_command(
        document_id=document_id,
        tags=tags,
        no_color=no_color,
    )


@tag_app.command("list")
def tag_list(
    document_id: Annotated[str | None, typer.Argument(help="Document ID (optional).")] = None,
    show_counts: bool = typer.Option(False, "--counts", "-c", help="Show document counts per tag."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List tags.

    Without a document ID, lists all tags in the knowledge base.
    With a document ID, lists tags for that document.

    Examples:
        ragd tag list              # All tags
        ragd tag list --counts     # Tags with document counts
        ragd tag list doc-123      # Tags for specific document
    """
    tag_list_command(
        document_id=document_id,
        show_counts=show_counts,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- List command ---

@app.command("list")
def list_docs(
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag."),
    project: str = typer.Option(None, "--project", "-p", help="Filter by project."),
    limit: int = typer.Option(None, "--limit", "-n", help="Maximum results."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List documents in the knowledge base.

    Filter documents by tag, project, or other criteria.

    Examples:
        ragd list                     # All documents
        ragd list --tag important     # Documents with tag
        ragd list --project Research  # Documents in project
        ragd list -n 10               # First 10 documents
    """
    list_documents_command(
        tag=tag,
        project=project,
        limit=limit,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Export/Import commands ---

@app.command("export")
def export_archive(
    output_path: Annotated[Path, typer.Argument(help="Path for output archive (.tar.gz).")],
    no_embeddings: bool = typer.Option(False, "--no-embeddings", help="Exclude embeddings (smaller archive)."),
    tag: str = typer.Option(None, "--tag", "-t", help="Only export documents with tag."),
    project: str = typer.Option(None, "--project", "-p", help="Only export documents in project."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Export knowledge base to an archive.

    Creates a portable tar.gz archive containing documents, chunks,
    embeddings, and metadata.

    Examples:
        ragd export ~/backup.tar.gz              # Full export
        ragd export ~/backup.tar.gz --no-embeddings  # Smaller archive
        ragd export ~/ml.tar.gz --tag "topic:ml"     # Export by tag
    """
    export_command(
        output_path=output_path,
        no_embeddings=no_embeddings,
        tag=tag,
        project=project,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command("import")
def import_archive_cmd(
    archive_path: Annotated[Path, typer.Argument(help="Path to archive (.tar.gz).")],
    skip_conflicts: bool = typer.Option(False, "--skip-conflicts", help="Skip documents that already exist."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing documents."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Import knowledge base from an archive.

    Restores documents, chunks, embeddings, and metadata from
    a portable tar.gz archive.

    Examples:
        ragd import ~/backup.tar.gz               # Import with default settings
        ragd import ~/backup.tar.gz --dry-run     # Validate only
        ragd import ~/backup.tar.gz --overwrite   # Replace existing documents
    """
    import_command(
        archive_path=archive_path,
        skip_conflicts=skip_conflicts,
        overwrite=overwrite,
        dry_run=dry_run,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Watch subcommands ---

@watch_app.command("start")
def watch_start(
    directories: Annotated[list[Path], typer.Argument(help="Directories to watch.")],
    patterns: list[str] = typer.Option(
        None, "--pattern", "-p", help="File patterns to watch (e.g., '*.pdf')."
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Watch subdirectories."
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Start watching folders for automatic indexing.

    Monitors specified directories for new or modified files and
    automatically indexes them.

    Examples:
        ragd watch start ~/Documents
        ragd watch start ~/PDFs ~/Notes --pattern "*.pdf"
        ragd watch start ~/Research --no-recursive
    """
    watch_start_command(
        directories=directories,
        patterns=patterns,
        recursive=recursive,
        no_color=no_color,
    )


@watch_app.command("stop")
def watch_stop(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Stop the folder watcher.

    Stops the background watcher process if running.
    """
    watch_stop_command(no_color=no_color)


@watch_app.command("status")
def watch_status_cmd(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show watcher status.

    Displays whether the watcher is running and which folders are being monitored.
    """
    watch_status_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Models subcommands ---

@models_app.command("list")
def models_list(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List available LLM models.

    Shows all models downloaded in Ollama and current configuration.
    """
    models_list_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("recommend")
def models_recommend(
    use_case: Annotated[
        str | None, typer.Option("--use-case", "-u", help="Use case (quick_qa, research, coding, etc.).")
    ] = None,
    model_type: str = typer.Option("llm", "--type", "-t", help="Model type (llm, embedding)."),
    all_models: bool = typer.Option(False, "--all", "-a", help="Include non-installed models."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Recommend models based on your hardware.

    Analyses your hardware capabilities and recommends optimal models
    for your use case.

    Use cases:
      - quick_qa: Fast Q&A, low latency
      - research: In-depth analysis, quality priority
      - coding: Code-related queries
      - summarisation: Document summarisation
      - multilingual: Non-English documents
      - agentic: CRAG/Self-RAG evaluation
      - embedding: Document embedding
      - contextual: Contextual retrieval

    Examples:
        ragd models recommend
        ragd models recommend --use-case research
        ragd models recommend --type embedding
        ragd models recommend --all  # Include non-installed models
    """
    models_recommend_command(
        use_case=use_case,
        model_type=model_type,
        require_installed=not all_models,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("show")
def models_show(
    model_id: Annotated[str, typer.Argument(help="Model ID to show details for.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show model card details.

    Displays detailed information about a model including capabilities,
    hardware requirements, strengths, weaknesses, and limitations.

    Examples:
        ragd models show llama3.2:3b
        ragd models show nomic-embed-text
        ragd models show qwen2.5:7b --format json
    """
    models_show_command(
        model_id=model_id,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Ask/Chat commands ---

@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Question to ask.")],
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use (default: from config)."),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature (0.0-1.0)."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results for context."),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output."),
    agentic: bool = typer.Option(None, "--agentic/--no-agentic", help="Enable/disable agentic RAG (CRAG + Self-RAG)."),
    show_confidence: bool = typer.Option(False, "--show-confidence", "-c", help="Show confidence score."),
    cite: str = typer.Option("numbered", "--cite", help="Citation style: none, numbered, inline."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Ask a question using your knowledge base.

    Retrieves relevant documents and generates an answer using Ollama LLM.
    Requires Ollama to be running locally.

    Agentic mode (--agentic) enables:
    - CRAG: Evaluates retrieval quality and rewrites queries if needed
    - Self-RAG: Assesses response faithfulness and refines if needed

    Examples:
        ragd ask "What authentication methods are recommended?"
        ragd ask "Summarise the security policy" --model llama3.2:8b
        ragd ask "Compare the approaches" --agentic --show-confidence
    """
    ask_command(
        question=question,
        model=model,
        temperature=temperature,
        limit=limit,
        stream=not no_stream,
        agentic=agentic,
        show_confidence=show_confidence,
        cite=cite,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use (default: from config)."),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature (0.0-1.0)."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results per query."),
    session_id: str = typer.Option(None, "--session", "-s", help="Resume a previous chat session."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Start an interactive chat with your knowledge base.

    Multi-turn conversation with RAG-powered responses. Each question
    retrieves relevant context from your documents.

    Requires Ollama to be running locally.

    Chat commands:
        /exit, /quit, /q  - Exit chat
        /clear            - Clear conversation history
        /history          - Show conversation history
        /help             - Show available commands

    Examples:
        ragd chat
        ragd chat --model llama3.2:8b
        ragd chat --session abc123  # Resume previous session
    """
    chat_command(
        model=model,
        temperature=temperature,
        limit=limit,
        session_id=session_id,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def evaluate(
    query: Annotated[str | None, typer.Option("--query", "-q", help="Single query to evaluate.")] = None,
    test_file: Annotated[Path | None, typer.Option("--test-file", "-f", help="YAML/JSON file with test queries.")] = None,
    expected: str = typer.Option(None, "--expected", "-e", help="Expected answer for recall computation."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results."),
    threshold: float = typer.Option(0.5, "--threshold", help="Relevance threshold (0-1)."),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save evaluation results."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Evaluate RAG retrieval quality.

    Computes metrics for your RAG system:
    - Context Precision: Are retrieved docs relevant?
    - Relevance Score: Weighted relevance with position decay

    Single query:
        ragd evaluate --query "What is machine learning?"

    With expected answer:
        ragd evaluate --query "..." --expected "ML is a subset of AI..."

    Batch evaluation:
        ragd evaluate --test-file queries.yaml

    Output as JSON:
        ragd evaluate --query "..." --format json
    """
    evaluate_command(
        query=query,
        test_file=test_file,
        expected=expected,
        limit=limit,
        threshold=threshold,
        save=not no_save,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def quality(
    document_id: Annotated[str | None, typer.Argument(help="Document ID to assess (omit for all).")] = None,
    below: float = typer.Option(None, "--below", "-b", help="Only show documents below quality threshold (0-1)."),
    file_type: str = typer.Option(None, "--type", "-t", help="Filter by file type (pdf, html, txt)."),
    test_corpus: Path = typer.Option(None, "--test", help="Test corpus path for CI/batch testing."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed breakdown."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Assess extraction quality for indexed documents.

    Shows quality metrics including completeness, character quality,
    structure preservation, and image/table handling.

    Modes:
      - No arguments: Report on all indexed documents
      - With document_id: Detailed report for specific document
      - With --test: Batch test a corpus (for CI)

    Examples:
        ragd quality                      # All documents summary
        ragd quality doc-123              # Specific document
        ragd quality --below 0.7          # Low-quality documents
        ragd quality --type pdf           # Only PDFs
        ragd quality --test ~/corpus/     # CI batch testing
        ragd quality --verbose            # Detailed breakdown
    """
    quality_command(
        document_id=document_id,
        below=below,
        file_type=file_type,
        test_corpus=test_corpus,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Backend subcommands ---

@backend_app.command("show")
def backend_show(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show current backend information.

    Displays the active vector store backend, status, and statistics.

    Examples:
        ragd backend show
        ragd backend show --format json
    """
    backend_show_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("list")
def backend_list(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List available backends.

    Shows all supported vector store backends and their installation status.

    Examples:
        ragd backend list
        ragd backend list --format json
    """
    backend_list_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("health")
def backend_health(
    backend: Annotated[
        str | None, typer.Argument(help="Backend to check (default: current).")
    ] = None,
    all_backends: bool = typer.Option(
        False, "--all", "-a", help="Check all available backends."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run health checks on backends.

    Validates backend connectivity, performance, and data integrity.

    Examples:
        ragd backend health              # Current backend
        ragd backend health chromadb     # Specific backend
        ragd backend health --all        # All available backends
    """
    backend_health_command(
        backend=backend,
        all_backends=all_backends,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("set")
def backend_set(
    backend: Annotated[str, typer.Argument(help="Backend to set as default.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Set the default backend.

    Changes the vector store backend used for new operations.
    Existing data remains in the previous backend until migrated.

    Available backends: chromadb, faiss

    Examples:
        ragd backend set faiss
        ragd backend set chromadb
    """
    backend_set_command(
        backend=backend,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("benchmark")
def backend_benchmark(
    backend: Annotated[
        str | None, typer.Argument(help="Backend to benchmark (default: current).")
    ] = None,
    vectors: int = typer.Option(1000, "--vectors", "-v", help="Number of vectors to add."),
    queries: int = typer.Option(100, "--queries", "-q", help="Number of search queries."),
    dimension: int = typer.Option(768, "--dimension", "-d", help="Vector dimension."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run performance benchmarks on a backend.

    Measures add, search, delete, and health check performance
    with synthetic data.

    Examples:
        ragd backend benchmark              # Benchmark current backend
        ragd backend benchmark chromadb     # Benchmark ChromaDB
        ragd backend benchmark --vectors 5000 --queries 500
    """
    backend_benchmark_command(
        backend=backend,
        vectors=vectors,
        queries=queries,
        dimension=dimension,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


if __name__ == "__main__":
    app()
