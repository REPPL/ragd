# State-of-the-Art Easy Setup for Local RAG

## Executive Summary

**Key Recommendations for ragd:**

1. **Use uv for dependency management** - 10-100x faster than pip, single binary, excellent Python version management
2. **Auto-download models on first use** - Don't require manual model setup; download what's needed when needed
3. **Hardware detection at startup** - Detect GPU/CPU capabilities and recommend appropriate models
4. **Progressive onboarding** - Work immediately with defaults, reveal configuration as users grow
5. **Health check command** - Provide `ragd doctor` to verify installation and diagnose issues

---

## The Setup Challenge

### Why Local RAG Setup is Hard

| Challenge | Impact | User Frustration |
|-----------|--------|------------------|
| **Python version conflicts** | Code fails silently | "It worked yesterday" |
| **GPU driver mismatches** | CUDA errors | "My GPU isn't detected" |
| **Large model downloads** | Long first-run time | "Is it broken?" |
| **Multiple components** | Complex orchestration | "Too many things to install" |
| **Platform differences** | Inconsistent behaviour | "Works on Mac, not Windows" |

### Target User Personas

| Persona | Technical Level | Expectations |
|---------|-----------------|--------------|
| **Developer** | High | Full control, customisation |
| **Data Scientist** | Medium-High | Jupyter integration, GPU support |
| **Knowledge Worker** | Low-Medium | "Just works" experience |
| **IT Admin** | Medium | Deployment, security, updates |

---

## Dependency Management Approaches

### Comparison Matrix

| Approach | Complexity | Speed | Isolation | Reproducibility | Best For |
|----------|------------|-------|-----------|-----------------|----------|
| **pip + venv** | Low | Slow | Good | Medium | Simple projects |
| **uv** | Low | Very Fast | Good | High | Modern Python projects |
| **conda** | Medium | Slow | Excellent | High | Data science, GPU |
| **Docker** | High | Medium | Perfect | Perfect | Deployment, CI/CD |
| **Standalone binary** | Lowest | N/A | Perfect | Perfect | End-user distribution |

### Recommendation: uv as Primary

**Why uv for ragd:**
- 10-100x faster than pip (Rust-based)
- Single static binary (no Python dependency for installer)
- Built-in Python version management
- Lock file support for reproducibility
- Drop-in pip compatibility

**Basic Setup with uv:**

```bash
# Install uv (works without Python installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with specific Python version
uv init ragd --python 3.12
cd ragd

# Install dependencies (creates lock file automatically)
uv add chromadb sentence-transformers typer rich

# Run the application
uv run ragd --help
```

**uv for End Users:**

```bash
# One-liner installation
curl -LsSf https://astral.sh/uv/install.sh | sh && \
uv tool install ragd
```

### Fallback: pip with pyproject.toml

```toml
# pyproject.toml - works with pip, uv, or poetry
[project]
name = "ragd"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "chromadb>=0.4.0",
    "sentence-transformers>=2.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
gpu = ["torch>=2.0.0"]
dev = ["pytest", "ruff"]

[project.scripts]
ragd = "ragd.cli:app"
```

### Docker for Deployment

```dockerfile
# Multi-stage build for minimal image
FROM python:3.12-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["ragd"]
```

**Source:** [Python UV: The Ultimate Guide](https://www.datacamp.com/tutorial/python-uv)

---

## Model Provisioning Strategies

### Download Strategies

| Strategy | First Run | Offline Support | Disk Usage |
|----------|-----------|-----------------|------------|
| **Eager (pre-bundle)** | Fast | Full | High (~5GB+) |
| **Lazy (on-demand)** | Slow first use | None until cached | Minimal |
| **Hybrid (essential only)** | Medium | Partial | Medium |

### Recommended: Lazy with Progress

```python
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn

class ModelManager:
    """Manages model downloads with user feedback."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path.home() / ".ragd" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_model(self, model_id: str) -> Path:
        """Get model path, downloading if necessary."""
        model_path = self.cache_dir / model_id.replace("/", "--")

        if model_path.exists():
            return model_path

        return self._download_model(model_id, model_path)

    def _download_model(self, model_id: str, target: Path) -> Path:
        from huggingface_hub import snapshot_download

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(f"Downloading {model_id}...", total=None)

            snapshot_download(
                repo_id=model_id,
                local_dir=target,
                local_dir_use_symlinks=False
            )

        return target
```

### Ollama Integration (Simplest Path)

Ollama handles model management entirely:

```python
import subprocess
import shutil

def ensure_ollama_model(model: str = "llama3.2:3b") -> bool:
    """Ensure Ollama model is available."""
    if not shutil.which("ollama"):
        raise RuntimeError(
            "Ollama not found. Install from https://ollama.ai"
        )

    # Check if model exists
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )

    if model in result.stdout:
        return True

    # Pull model with progress
    print(f"Downloading {model}... (this may take a few minutes)")
    subprocess.run(["ollama", "pull", model], check=True)
    return True
```

### Offline Bundle Creation

```python
def create_offline_bundle(output_dir: Path, models: list[str]):
    """Create an offline-capable installation bundle."""
    from huggingface_hub import snapshot_download

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"models": [], "created": datetime.now().isoformat()}

    for model_id in models:
        print(f"Bundling {model_id}...")
        local_path = output_dir / "models" / model_id.replace("/", "--")
        snapshot_download(
            repo_id=model_id,
            local_dir=local_path,
            local_dir_use_symlinks=False
        )
        manifest["models"].append({
            "id": model_id,
            "path": str(local_path.relative_to(output_dir))
        })

    # Write manifest
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Bundle created at {output_dir}")
```

**Source:** [How to Load Hugging Face LLMs Locally](https://medium.com/@gaurav.phatkare/how-to-load-llama-or-other-hugging-face-llm-models-locally-a-step-by-step-guide-d1778ff1be00)

---

## Hardware Detection

### GPU Detection Strategy

```python
from dataclasses import dataclass
from enum import Enum, auto

class ComputeBackend(Enum):
    CUDA = auto()
    MPS = auto()  # Apple Silicon
    CPU = auto()

@dataclass
class HardwareProfile:
    backend: ComputeBackend
    device_name: str
    memory_gb: float
    compute_capability: str | None = None

    @property
    def recommended_model_size(self) -> str:
        """Suggest model size based on available memory."""
        if self.memory_gb >= 24:
            return "70B (quantised) or 13B (full)"
        elif self.memory_gb >= 12:
            return "13B (quantised) or 7B (full)"
        elif self.memory_gb >= 8:
            return "7B (quantised) or 3B (full)"
        elif self.memory_gb >= 4:
            return "3B (quantised)"
        else:
            return "1B or smaller"

def detect_hardware() -> HardwareProfile:
    """Detect available compute hardware."""
    import platform

    # Try CUDA first
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.cuda.get_device_properties(0)
            return HardwareProfile(
                backend=ComputeBackend.CUDA,
                device_name=device.name,
                memory_gb=device.total_memory / (1024**3),
                compute_capability=f"{device.major}.{device.minor}"
            )
    except ImportError:
        pass

    # Try MPS (Apple Silicon)
    try:
        import torch
        if torch.backends.mps.is_available():
            # MPS doesn't expose memory easily, estimate from system
            import psutil
            return HardwareProfile(
                backend=ComputeBackend.MPS,
                device_name=f"Apple {platform.processor()}",
                memory_gb=psutil.virtual_memory().total / (1024**3) * 0.7
            )
    except (ImportError, AttributeError):
        pass

    # Fall back to CPU
    import psutil
    return HardwareProfile(
        backend=ComputeBackend.CPU,
        device_name=platform.processor() or "Unknown CPU",
        memory_gb=psutil.virtual_memory().total / (1024**3)
    )
```

### User-Friendly Hardware Report

```python
from rich.console import Console
from rich.table import Table

def show_hardware_report():
    """Display hardware capabilities to user."""
    console = Console()
    profile = detect_hardware()

    table = Table(title="Hardware Detection")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Compute Backend", profile.backend.name)
    table.add_row("Device", profile.device_name)
    table.add_row("Memory", f"{profile.memory_gb:.1f} GB")
    if profile.compute_capability:
        table.add_row("CUDA Compute", profile.compute_capability)
    table.add_row("Recommended Model", profile.recommended_model_size)

    console.print(table)

    if profile.backend == ComputeBackend.CPU:
        console.print(
            "\n[yellow]Note:[/yellow] Running on CPU. "
            "For better performance, consider using a GPU or Apple Silicon.",
            style="dim"
        )
```

**Source:** [PyTorch Check If GPU Is Available](https://techrebooter.com/pytorch-check-if-gpu-is-available/)

---

## First-Run Experience Design

### Progressive Onboarding Flow

```
First Run
    ↓
┌─────────────────────────────────────────────────────┐
│ Welcome to ragd!                                    │
│                                                     │
│ Let me check your system...                         │
│                                                     │
│ ✓ Python 3.12 detected                              │
│ ✓ 16 GB RAM available                               │
│ ✓ Apple M2 GPU detected                             │
│ ✓ Ollama installed                                  │
│                                                     │
│ Recommended configuration:                          │
│   • Embedding: nomic-embed-text (137M params)       │
│   • LLM: llama3.2:3b (via Ollama)                   │
│                                                     │
│ [Continue with defaults] [Customise]                │
└─────────────────────────────────────────────────────┘
    ↓
(User selects "Continue with defaults")
    ↓
┌─────────────────────────────────────────────────────┐
│ Setting up ragd...                                  │
│                                                     │
│ ⠋ Downloading embedding model (275 MB)...          │
│   [████████████░░░░░░░░] 60%                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ ✓ Setup complete!                                   │
│                                                     │
│ Quick start:                                        │
│   ragd index ~/Documents       # Index your documents   │
│   ragd search "your question"  # Search and ask questions │
│                                                     │
│ Configuration saved to ~/.ragd/config.yaml          │
│ Run 'ragd doctor' to verify your setup anytime.     │
└─────────────────────────────────────────────────────┘
```

### Implementation

```python
import typer
from rich.console import Console
from rich.prompt import Confirm

app = typer.Typer()
console = Console()

@app.command()
def init(
    interactive: bool = typer.Option(True, "--interactive/--no-interactive"),
    force: bool = typer.Option(False, "--force", "-f")
):
    """Initialize ragd with guided setup."""
    config_path = Path.home() / ".ragd" / "config.yaml"

    if config_path.exists() and not force:
        console.print("[yellow]ragd is already configured.[/yellow]")
        if not Confirm.ask("Reconfigure?"):
            return

    console.print("\n[bold]Welcome to ragd![/bold]\n")
    console.print("Let me check your system...\n")

    # Hardware detection
    profile = detect_hardware()
    show_hardware_report()

    # Check dependencies
    checks = run_dependency_checks()
    show_dependency_status(checks)

    if interactive:
        # Offer customisation
        use_defaults = Confirm.ask(
            "\nUse recommended configuration?",
            default=True
        )

        if not use_defaults:
            config = interactive_configuration()
        else:
            config = generate_default_config(profile)
    else:
        config = generate_default_config(profile)

    # Save configuration
    save_config(config, config_path)

    # Download required models
    setup_models(config)

    # Show success
    console.print("\n[bold green]✓ Setup complete![/bold green]\n")
    show_quick_start_guide()
```

---

## Health Check System

### The `ragd doctor` Command

```python
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    PASS = "✓"
    WARN = "⚠"
    FAIL = "✗"

@dataclass
class HealthCheck:
    name: str
    status: CheckStatus
    message: str
    fix_hint: str | None = None

def run_health_checks() -> list[HealthCheck]:
    """Run all health checks."""
    checks = []

    # Python version
    import sys
    py_version = sys.version_info
    if py_version >= (3, 10):
        checks.append(HealthCheck(
            "Python version",
            CheckStatus.PASS,
            f"Python {py_version.major}.{py_version.minor}"
        ))
    else:
        checks.append(HealthCheck(
            "Python version",
            CheckStatus.FAIL,
            f"Python {py_version.major}.{py_version.minor} (need 3.10+)",
            fix_hint="Install Python 3.10 or later"
        ))

    # Ollama
    if shutil.which("ollama"):
        checks.append(HealthCheck(
            "Ollama",
            CheckStatus.PASS,
            "Installed and available"
        ))
    else:
        checks.append(HealthCheck(
            "Ollama",
            CheckStatus.WARN,
            "Not found (optional for local LLM)",
            fix_hint="Install from https://ollama.ai"
        ))

    # Configuration
    config_path = Path.home() / ".ragd" / "config.yaml"
    if config_path.exists():
        checks.append(HealthCheck(
            "Configuration",
            CheckStatus.PASS,
            f"Found at {config_path}"
        ))
    else:
        checks.append(HealthCheck(
            "Configuration",
            CheckStatus.WARN,
            "Not found (using defaults)",
            fix_hint="Run 'ragd init' to configure"
        ))

    # Vector database
    db_path = Path.home() / ".ragd" / "chroma_db"
    if db_path.exists():
        checks.append(HealthCheck(
            "Vector database",
            CheckStatus.PASS,
            f"Found at {db_path}"
        ))
    else:
        checks.append(HealthCheck(
            "Vector database",
            CheckStatus.WARN,
            "Not initialised",
            fix_hint="Run 'ragd index <path>' to index documents"
        ))

    # GPU/Compute
    profile = detect_hardware()
    if profile.backend in (ComputeBackend.CUDA, ComputeBackend.MPS):
        checks.append(HealthCheck(
            "GPU acceleration",
            CheckStatus.PASS,
            f"{profile.backend.name}: {profile.device_name}"
        ))
    else:
        checks.append(HealthCheck(
            "GPU acceleration",
            CheckStatus.WARN,
            "Not available (using CPU)",
            fix_hint="Install CUDA or use Apple Silicon for better performance"
        ))

    return checks

@app.command()
def doctor():
    """Check ragd installation health."""
    console = Console()
    console.print("\n[bold]ragd Health Check[/bold]\n")

    checks = run_health_checks()

    for check in checks:
        status_color = {
            CheckStatus.PASS: "green",
            CheckStatus.WARN: "yellow",
            CheckStatus.FAIL: "red"
        }[check.status]

        console.print(
            f"[{status_color}]{check.status.value}[/{status_color}] "
            f"{check.name}: {check.message}"
        )

        if check.fix_hint and check.status != CheckStatus.PASS:
            console.print(f"    [dim]→ {check.fix_hint}[/dim]")

    # Summary
    passes = sum(1 for c in checks if c.status == CheckStatus.PASS)
    total = len(checks)

    console.print(f"\n{passes}/{total} checks passed\n")

    if all(c.status == CheckStatus.PASS for c in checks):
        console.print("[bold green]ragd is healthy![/bold green]")
    elif any(c.status == CheckStatus.FAIL for c in checks):
        console.print("[bold red]Some issues need attention.[/bold red]")
        raise typer.Exit(1)
```

---

## Platform-Specific Considerations

### Installation by Platform

| Platform | Recommended Approach | Notes |
|----------|---------------------|-------|
| **macOS** | Homebrew + uv | Native Metal support on Apple Silicon |
| **Windows** | winget/scoop + uv | CUDA requires separate driver install |
| **Linux** | apt/dnf + uv | GPU support varies by distribution |
| **Docker** | Pre-built image | Most consistent, best for deployment |

### macOS Setup

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Ollama
brew install ollama

# Install uv
brew install uv

# Install ragd
uv tool install ragd

# Verify
ragd doctor
```

### Windows Setup

```powershell
# Install uv (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Install Ollama (download from website or winget)
winget install Ollama.Ollama

# Install ragd
uv tool install ragd

# Verify
ragd doctor
```

### Linux Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install ragd
uv tool install ragd

# Verify
ragd doctor
```

---

## Lessons from Existing Tools

### LM Studio

**What works:**
- Model discovery via search (HuggingFace integration)
- Visual model download progress
- Hardware compatibility indicators
- One-click model loading

**What to improve:**
- Model search UX is not immediately obvious
- Closed-source license concerns

### Jan.ai

**What works:**
- Model tags indicate compatibility ("slow on your device")
- Clean, modern UI
- Built-in provider integrations
- Open-source

**What to improve:**
- Document upload is experimental
- Some stability issues

### Ollama

**What works:**
- Single binary installation
- Simple CLI (`ollama run llama3`)
- Automatic model management
- Cross-platform consistency

**What to improve:**
- No built-in RAG capability
- Limited configuration options

### PrivateGPT

**What works:**
- Complete RAG solution
- Ollama integration
- Document ingestion built-in

**What to improve:**
- Complex setup (Poetry, multiple components)
- Configuration via YAML files requires technical knowledge

**Source:** [AnythingLLM Review 2025](https://skywork.ai/blog/anythingllm-review-2025-local-ai-rag-agents-setup/), [Free LLM Desktop Tools Comparison](https://sailingbyte.com/blog/the-ultimate-comparison-of-free-desktop-tools-for-running-local-llms/)

---

## Recommended Architecture for ragd

### Installation Flow

```
Install ragd
    ↓
┌─────────────────────────────────────────────────────┐
│ 1. Check uv availability                            │
│    └─ If missing: provide install command           │
│                                                     │
│ 2. uv tool install ragd                             │
│    └─ Creates isolated environment                  │
│    └─ Installs all Python dependencies              │
│                                                     │
│ 3. ragd init (first run)                            │
│    └─ Hardware detection                            │
│    └─ Dependency verification                       │
│    └─ Model recommendation                          │
│    └─ Configuration generation                      │
│    └─ Optional model download                       │
└─────────────────────────────────────────────────────┘
```

### Configuration Structure

```yaml
# ~/.ragd/config.yaml
version: 1

# Hardware profile (auto-detected, can override)
hardware:
  backend: mps  # cuda, mps, or cpu
  device: "Apple M2"

# Embedding configuration
embedding:
  model: "nomic-ai/nomic-embed-text-v1.5"
  device: auto  # Uses hardware.backend

# LLM configuration
llm:
  provider: ollama  # ollama, openai, anthropic, local
  model: "llama3.2:3b"
  # For API providers:
  # api_key_env: "OPENAI_API_KEY"

# Vector store
vector_store:
  type: chromadb
  path: "~/.ragd/chroma_db"

# First-run behaviour
setup:
  auto_download_models: true
  show_welcome: true
```

### CLI Commands for Setup

```bash
# Full installation and setup
ragd init                    # Interactive setup wizard
ragd init --defaults         # Non-interactive with defaults

# Verification
ragd doctor                  # Health check
ragd doctor --fix            # Attempt automatic fixes

# Model management
ragd models list             # Show installed models
ragd models pull <model>     # Download a model
ragd models remove <model>   # Remove a model

# Configuration
ragd config show             # Display current config
ragd config set llm.model llama3:8b  # Update config
ragd config reset            # Reset to defaults
```

---

## References

### Package Management
- [uv Documentation](https://docs.astral.sh/uv/) - Modern Python package manager
- [PyInstaller](https://pyinstaller.org/) - Standalone executable creation
- [Python Packaging Options](https://pythonspeed.com/articles/distributing-software/)

### Local LLM Tools
- [Ollama](https://ollama.ai) - Local LLM runtime
- [LM Studio](https://lmstudio.ai) - Desktop LLM application
- [Jan.ai](https://jan.ai) - Open-source local AI
- [PrivateGPT](https://docs.privategpt.dev/) - RAG with local LLMs

### Hardware Detection
- [PyTorch CUDA Guide](https://pytorch.org/docs/stable/cuda.html)
- [GPU Detection in Python](https://saturncloud.io/blog/how-to-check-whether-your-code-is-running-on-the-gpu-or-cpu/)

---

## Related Documentation

- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [State-of-the-Art CLI Modes](./state-of-the-art-cli-modes.md) - User/expert interface design
- [CLI Best Practices](./cli-best-practices.md) - General CLI design principles
- [F-001: CLI Framework](../features/planned/F-001-cli-framework.md) - Feature specification

---

**Status:** Research complete
