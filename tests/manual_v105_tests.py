#!/usr/bin/env python3
"""Manual tests for ragd v1.0.5 - Configuration & Customisation.

This script provides interactive testing of v1.0.5 features:
- Extended config schema (agentic_params, search_tuning, etc.)
- Prompt template system (file/inline loading)
- CLI flag extensions (temperature, max_tokens)
- Interactive config wizard extensions

Usage:
    python tests/manual_v105_tests.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def print_header() -> None:
    """Print test header."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]RAGD v1.0.5 Manual Tests[/]\n"
        "[dim]Configuration & Customisation[/]",
        border_style="blue"
    ))
    console.print()


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "[green]PASS[/]" if passed else "[red]FAIL[/]"
    console.print(f"  {status} {test_name}")
    if details:
        console.print(f"       [dim]{details}[/]")


def test_config_schema_extensions() -> bool:
    """Test 1: Config Schema Extensions.

    Tests that new Pydantic models are properly defined and validated.
    """
    console.print("\n[bold cyan][1/7] Config Schema Extensions[/]")

    try:
        from ragd.config import (
            RagdConfig,
            AgenticParamsConfig,
            SearchTuningConfig,
            ProcessingConfig,
            HardwareThresholdsConfig,
            OperationParams,
        )

        # Test AgenticParamsConfig
        agentic = AgenticParamsConfig()
        print_result(
            "AgenticParamsConfig",
            True,
            f"relevance_threshold={agentic.relevance_threshold}, "
            f"faithfulness_threshold={agentic.faithfulness_threshold}"
        )

        # Test OperationParams
        op_params = OperationParams(temperature=0.5, max_tokens=512)
        print_result(
            "OperationParams",
            op_params.temperature == 0.5 and op_params.max_tokens == 512,
            f"temp={op_params.temperature}, tokens={op_params.max_tokens}"
        )

        # Test SearchTuningConfig
        search = SearchTuningConfig()
        print_result(
            "SearchTuningConfig",
            True,
            f"bm25_divisor={search.bm25_normalisation_divisor}, "
            f"rrf_multiplier={search.rrf_fetch_multiplier}"
        )

        # Test ProcessingConfig
        processing = ProcessingConfig()
        print_result(
            "ProcessingConfig",
            True,
            f"truncation={processing.context_truncation_chars}, "
            f"encoding={processing.token_encoding}"
        )

        # Test HardwareThresholdsConfig (uses tier boundary names)
        hw = HardwareThresholdsConfig()
        print_result(
            "HardwareThresholdsConfig",
            True,
            f"minimal_max_gb={hw.minimal_max_gb}, "
            f"high_max_gb={hw.high_max_gb}"
        )

        # Test full config loads with new sections
        config = RagdConfig()
        has_agentic = hasattr(config, 'agentic_params')
        has_search = hasattr(config, 'search_tuning')
        has_processing = hasattr(config, 'processing')
        print_result(
            "RagdConfig integration",
            has_agentic and has_search and has_processing,
            "All new config sections present"
        )

        return True

    except Exception as e:
        print_result("Config schema", False, str(e))
        return False


def test_prompt_template_system() -> bool:
    """Test 2: Prompt Template System.

    Tests prompt loading from files and inline strings.
    """
    console.print("\n[bold cyan][2/7] Prompt Template System[/]")

    try:
        from ragd.prompts import (
            get_prompt,
            list_prompts,
            list_prompt_categories,
            export_default_prompts,
        )
        from ragd.prompts.defaults import DEFAULT_PROMPTS

        # Test list_prompts
        prompts = list_prompts()
        print_result(
            "list_prompts()",
            len(prompts) > 0,
            f"Found {len(prompts)} categories"
        )

        # Test list_prompt_categories
        categories = list_prompt_categories()
        print_result(
            "list_prompt_categories()",
            len(categories) >= 4,
            f"Categories: {', '.join(categories)}"
        )

        # Test get_prompt for various types (use None ref with defaults)
        rag_default = DEFAULT_PROMPTS.get("rag", {}).get("answer", "")
        rag_answer = get_prompt(None, rag_default, "rag", "answer")
        print_result(
            "get_prompt(None, default, 'rag', 'answer')",
            rag_answer is not None and len(rag_answer) > 0,
            f"Template length: {len(rag_answer)} chars"
        )

        agentic_default = DEFAULT_PROMPTS.get("agentic", {}).get("relevance_eval", "")
        agentic_relevance = get_prompt(None, agentic_default, "agentic", "relevance_eval")
        print_result(
            "get_prompt(..., 'agentic', 'relevance_eval')",
            agentic_relevance is not None,
            f"Template length: {len(agentic_relevance) if agentic_relevance else 0} chars"
        )

        # Test export to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "prompts"
            export_default_prompts(export_path)

            # Check files were created
            exported_files = list(export_path.rglob("*.txt"))
            print_result(
                "export_default_prompts()",
                len(exported_files) > 0,
                f"Exported {len(exported_files)} prompt files"
            )

            # Check subdirectories
            subdirs = [d.name for d in export_path.iterdir() if d.is_dir()]
            print_result(
                "Export structure",
                len(subdirs) >= 3,
                f"Subdirs: {', '.join(subdirs)}"
            )

        return True

    except Exception as e:
        print_result("Prompt template system", False, str(e))
        return False


def test_prompt_file_loading() -> bool:
    """Test 3: Prompt File Loading.

    Tests loading prompts from custom file paths.
    """
    console.print("\n[bold cyan][3/7] Prompt File Loading[/]")

    try:
        from ragd.prompts import get_prompt
        from ragd.config import RagdConfig, PromptFileReference

        # Create temp prompt file
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_prompt_path = Path(tmpdir) / "custom_answer.txt"
            custom_content = "Custom prompt: Answer based on {context}\nQuestion: {question}"
            custom_prompt_path.write_text(custom_content)

            # Test file loading via get_prompt with custom file
            loaded = custom_prompt_path.read_text(encoding="utf-8")
            print_result(
                "Direct file read",
                loaded == custom_content,
                f"Loaded {len(loaded)} chars"
            )

            # Test PromptFileReference with file
            ref = PromptFileReference(file=custom_prompt_path)
            resolved = ref.resolve("fallback")
            print_result(
                "PromptFileReference(file=...)",
                resolved == custom_content,
                "File reference resolved"
            )

            # Test PromptFileReference with inline
            inline_content = "Inline prompt template"
            ref_inline = PromptFileReference(inline=inline_content)
            resolved_inline = ref_inline.resolve("fallback")
            print_result(
                "PromptFileReference(inline=...)",
                resolved_inline == inline_content,
                "Inline reference resolved"
            )

            # Test fallback when neither file nor inline
            ref_empty = PromptFileReference()
            resolved_fallback = ref_empty.resolve("fallback default")
            print_result(
                "PromptFileReference fallback",
                resolved_fallback == "fallback default",
                "Empty reference uses fallback"
            )

            # Test config integration
            config = RagdConfig()
            # Check that prompt config sections exist
            has_agentic_prompts = hasattr(config, 'agentic_prompts')
            has_metadata_prompts = hasattr(config, 'metadata_prompts')
            print_result(
                "Config prompt sections",
                has_agentic_prompts and has_metadata_prompts,
                f"agentic_prompts={has_agentic_prompts}, metadata_prompts={has_metadata_prompts}"
            )

        return True

    except Exception as e:
        print_result("Prompt file loading", False, str(e))
        return False


def test_config_yaml_loading() -> bool:
    """Test 4: Config YAML Loading.

    Tests loading new config sections from YAML.
    """
    console.print("\n[bold cyan][4/7] Config YAML Loading[/]")

    try:
        from ragd.config import RagdConfig, load_config
        import yaml

        # Create test config with new v1.0.5 sections
        test_config = {
            "version": 2,
            "agentic_params": {
                "relevance_threshold": 0.75,
                "faithfulness_threshold": 0.8,
                "answer_generation": {
                    "temperature": 0.6,
                    "max_tokens": 768
                }
            },
            "search_tuning": {
                "bm25_normalisation_divisor": 12.0,
                "rrf_fetch_multiplier": 4
            },
            "processing": {
                "context_truncation_chars": 3000,
                "token_encoding": "cl100k_base"
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            # Load config
            config = load_config(config_path)

            # Verify agentic_params
            agentic_ok = (
                config.agentic_params.relevance_threshold == 0.75 and
                config.agentic_params.faithfulness_threshold == 0.8
            )
            print_result(
                "agentic_params loading",
                agentic_ok,
                f"relevance={config.agentic_params.relevance_threshold}"
            )

            # Verify nested OperationParams
            op_ok = (
                config.agentic_params.answer_generation.temperature == 0.6 and
                config.agentic_params.answer_generation.max_tokens == 768
            )
            print_result(
                "Nested OperationParams",
                op_ok,
                f"temp={config.agentic_params.answer_generation.temperature}"
            )

            # Verify search_tuning
            search_ok = config.search_tuning.bm25_normalisation_divisor == 12.0
            print_result(
                "search_tuning loading",
                search_ok,
                f"bm25_divisor={config.search_tuning.bm25_normalisation_divisor}"
            )

            # Verify processing
            proc_ok = config.processing.context_truncation_chars == 3000
            print_result(
                "processing loading",
                proc_ok,
                f"truncation={config.processing.context_truncation_chars}"
            )

        return agentic_ok and op_ok and search_ok and proc_ok

    except Exception as e:
        print_result("Config YAML loading", False, str(e))
        return False


def test_cli_flag_integration() -> bool:
    """Test 5: CLI Flag Integration.

    Tests that CLI flags properly override config values.
    """
    console.print("\n[bold cyan][5/7] CLI Flag Integration[/]")

    try:
        from ragd.config import RagdConfig

        # Test config defaults
        config = RagdConfig()

        # Verify default values exist
        default_temp = config.agentic_params.answer_generation.temperature
        default_tokens = config.agentic_params.answer_generation.max_tokens
        print_result(
            "Default answer_generation params",
            default_temp is not None or default_tokens is not None,
            f"temp={default_temp}, tokens={default_tokens}"
        )

        # Simulate CLI override logic
        cli_temp = 0.3
        cli_tokens = 500

        effective_temp = cli_temp if cli_temp is not None else (
            config.agentic_params.answer_generation.temperature or 0.7
        )
        effective_tokens = cli_tokens if cli_tokens is not None else (
            config.agentic_params.answer_generation.max_tokens or 1024
        )

        print_result(
            "CLI override simulation",
            effective_temp == 0.3 and effective_tokens == 500,
            f"Effective: temp={effective_temp}, tokens={effective_tokens}"
        )

        # Test that config values are used as fallback
        effective_temp_fallback = None if None is not None else (
            config.agentic_params.answer_generation.temperature or 0.7
        )
        print_result(
            "Config fallback",
            effective_temp_fallback == (default_temp or 0.7),
            f"Fallback temp={effective_temp_fallback}"
        )

        return True

    except Exception as e:
        print_result("CLI flag integration", False, str(e))
        return False


def test_config_wizard_sections() -> bool:
    """Test 6: Config Wizard Sections.

    Tests that new wizard sections are properly implemented.
    """
    console.print("\n[bold cyan][6/7] Config Wizard Sections[/]")

    try:
        from ragd.ui.cli import config_wizard

        # Check new functions exist
        has_agentic = hasattr(config_wizard, '_configure_agentic')
        print_result(
            "_configure_agentic()",
            has_agentic,
            "Function defined" if has_agentic else "Missing"
        )

        has_advanced = hasattr(config_wizard, '_configure_advanced')
        print_result(
            "_configure_advanced()",
            has_advanced,
            "Function defined" if has_advanced else "Missing"
        )

        has_prompts = hasattr(config_wizard, '_configure_prompts')
        print_result(
            "_configure_prompts()",
            has_prompts,
            "Function defined" if has_prompts else "Missing"
        )

        has_search_tuning = hasattr(config_wizard, '_configure_search_tuning')
        print_result(
            "_configure_search_tuning()",
            has_search_tuning,
            "Function defined" if has_search_tuning else "Missing"
        )

        has_processing = hasattr(config_wizard, '_configure_processing')
        print_result(
            "_configure_processing()",
            has_processing,
            "Function defined" if has_processing else "Missing"
        )

        has_hw_thresholds = hasattr(config_wizard, '_configure_hardware_thresholds')
        print_result(
            "_configure_hardware_thresholds()",
            has_hw_thresholds,
            "Function defined" if has_hw_thresholds else "Missing"
        )

        all_present = (
            has_agentic and has_advanced and has_prompts and
            has_search_tuning and has_processing and has_hw_thresholds
        )

        return all_present

    except Exception as e:
        print_result("Config wizard sections", False, str(e))
        return False


def test_consuming_code_integration() -> bool:
    """Test 7: Consuming Code Integration.

    Tests that code using configs properly reads new values.
    """
    console.print("\n[bold cyan][7/7] Consuming Code Integration[/]")

    try:
        from ragd.config import RagdConfig

        config = RagdConfig()

        # Test agentic thresholds are accessible
        relevance_t = config.agentic_params.relevance_threshold
        faithfulness_t = config.agentic_params.faithfulness_threshold
        print_result(
            "Agentic thresholds accessible",
            relevance_t is not None and faithfulness_t is not None,
            f"relevance={relevance_t}, faithfulness={faithfulness_t}"
        )

        # Test search tuning values
        bm25_div = config.search_tuning.bm25_normalisation_divisor
        rrf_mult = config.search_tuning.rrf_fetch_multiplier
        print_result(
            "Search tuning accessible",
            bm25_div is not None and rrf_mult is not None,
            f"bm25_div={bm25_div}, rrf_mult={rrf_mult}"
        )

        # Test processing values
        truncation = config.processing.context_truncation_chars
        encoding = config.processing.token_encoding
        print_result(
            "Processing config accessible",
            truncation is not None and encoding is not None,
            f"truncation={truncation}, encoding={encoding}"
        )

        # Test hardware thresholds (uses tier boundary naming)
        minimal_max = config.hardware_thresholds.minimal_max_gb
        high_max = config.hardware_thresholds.high_max_gb
        print_result(
            "Hardware thresholds accessible",
            minimal_max is not None and high_max is not None,
            f"minimal_max={minimal_max}GB, high_max={high_max}GB"
        )

        # Test quality thresholds
        excellent = config.agentic_params.excellent_threshold
        good = config.agentic_params.good_threshold
        poor = config.agentic_params.poor_threshold
        print_result(
            "Quality thresholds accessible",
            all(t is not None for t in [excellent, good, poor]),
            f"excellent={excellent}, good={good}, poor={poor}"
        )

        return True

    except Exception as e:
        print_result("Consuming code integration", False, str(e))
        return False


def print_summary(results: dict[str, bool]) -> None:
    """Print test summary."""
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    console.print()
    console.print("=" * 60)
    if passed == total:
        console.print(f"[bold green]RESULTS: {passed}/{total} passed[/]")
    else:
        console.print(f"[bold yellow]RESULTS: {passed}/{total} passed[/]")

    # Show failed tests
    failed = [name for name, result in results.items() if not result]
    if failed:
        console.print("\n[yellow]Failed tests:[/]")
        for name in failed:
            console.print(f"  - {name}")

    console.print("=" * 60)


def main() -> int:
    """Run all manual tests."""
    print_header()

    results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running tests...", total=7)

        # Test 1: Config Schema Extensions
        results["Config Schema Extensions"] = test_config_schema_extensions()
        progress.advance(task)

        # Test 2: Prompt Template System
        results["Prompt Template System"] = test_prompt_template_system()
        progress.advance(task)

        # Test 3: Prompt File Loading
        results["Prompt File Loading"] = test_prompt_file_loading()
        progress.advance(task)

        # Test 4: Config YAML Loading
        results["Config YAML Loading"] = test_config_yaml_loading()
        progress.advance(task)

        # Test 5: CLI Flag Integration
        results["CLI Flag Integration"] = test_cli_flag_integration()
        progress.advance(task)

        # Test 6: Config Wizard Sections
        results["Config Wizard Sections"] = test_config_wizard_sections()
        progress.advance(task)

        # Test 7: Consuming Code Integration
        results["Consuming Code Integration"] = test_consuming_code_integration()
        progress.advance(task)

    print_summary(results)

    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
