"""Tests for dry-run mode (F-118)."""

from io import StringIO
from pathlib import Path
import tempfile

import pytest
from rich.console import Console

from ragd.operations.dry_run import (
    OperationType,
    ActionType,
    PlannedAction,
    OperationPlan,
    display_plan,
    create_index_plan,
    create_delete_plan,
    create_repair_plan,
)


class TestOperationType:
    """Tests for OperationType enum."""

    def test_has_index(self):
        """Should have INDEX operation type."""
        assert OperationType.INDEX.value == "index"

    def test_has_delete(self):
        """Should have DELETE operation type."""
        assert OperationType.DELETE.value == "delete"

    def test_has_repair(self):
        """Should have REPAIR operation type."""
        assert OperationType.REPAIR.value == "repair"

    def test_has_clean(self):
        """Should have CLEAN operation type."""
        assert OperationType.CLEAN.value == "clean"


class TestActionType:
    """Tests for ActionType enum."""

    def test_has_add(self):
        """Should have ADD action type."""
        assert ActionType.ADD.value == "add"

    def test_has_update(self):
        """Should have UPDATE action type."""
        assert ActionType.UPDATE.value == "update"

    def test_has_remove(self):
        """Should have REMOVE action type."""
        assert ActionType.REMOVE.value == "remove"

    def test_has_skip(self):
        """Should have SKIP action type."""
        assert ActionType.SKIP.value == "skip"

    def test_has_fix(self):
        """Should have FIX action type."""
        assert ActionType.FIX.value == "fix"


class TestPlannedAction:
    """Tests for PlannedAction dataclass."""

    def test_create_action(self):
        """Should create a planned action."""
        action = PlannedAction(
            action=ActionType.ADD,
            target=Path("/test/file.pdf"),
            reason="new file",
        )
        assert action.action == ActionType.ADD
        assert action.target == Path("/test/file.pdf")
        assert action.reason == "new file"

    def test_icon_for_add(self):
        """ADD action should have + icon."""
        action = PlannedAction(ActionType.ADD, "/test")
        assert action.icon == "+"

    def test_icon_for_update(self):
        """UPDATE action should have ~ icon."""
        action = PlannedAction(ActionType.UPDATE, "/test")
        assert action.icon == "~"

    def test_icon_for_remove(self):
        """REMOVE action should have - icon."""
        action = PlannedAction(ActionType.REMOVE, "/test")
        assert action.icon == "-"

    def test_icon_for_skip(self):
        """SKIP action should have circle icon."""
        action = PlannedAction(ActionType.SKIP, "/test")
        assert action.icon == "○"

    def test_icon_for_fix(self):
        """FIX action should have check icon."""
        action = PlannedAction(ActionType.FIX, "/test")
        assert action.icon == "✓"

    def test_colour_for_add(self):
        """ADD action should have green colour."""
        action = PlannedAction(ActionType.ADD, "/test")
        assert action.colour == "green"

    def test_colour_for_update(self):
        """UPDATE action should have yellow colour."""
        action = PlannedAction(ActionType.UPDATE, "/test")
        assert action.colour == "yellow"

    def test_colour_for_remove(self):
        """REMOVE action should have red colour."""
        action = PlannedAction(ActionType.REMOVE, "/test")
        assert action.colour == "red"

    def test_colour_for_skip(self):
        """SKIP action should have dim colour."""
        action = PlannedAction(ActionType.SKIP, "/test")
        assert action.colour == "dim"

    def test_colour_for_fix(self):
        """FIX action should have cyan colour."""
        action = PlannedAction(ActionType.FIX, "/test")
        assert action.colour == "cyan"

    def test_default_empty_details(self):
        """Should have empty details by default."""
        action = PlannedAction(ActionType.ADD, "/test")
        assert action.details == {}

    def test_details_with_values(self):
        """Should store details dict."""
        action = PlannedAction(
            ActionType.ADD,
            "/test",
            details={"file_size": 1024},
        )
        assert action.details["file_size"] == 1024


class TestOperationPlan:
    """Tests for OperationPlan dataclass."""

    def test_create_plan(self):
        """Should create an operation plan."""
        plan = OperationPlan(operation=OperationType.INDEX)
        assert plan.operation == OperationType.INDEX
        assert plan.actions == []

    def test_add_action(self):
        """Should add actions to plan."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/test/file.pdf", reason="new")

        assert len(plan.actions) == 1
        assert plan.actions[0].action == ActionType.ADD

    def test_add_action_with_details(self):
        """Should add action with details."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(
            ActionType.ADD,
            "/test/file.pdf",
            reason="new",
            file_size=1024,
        )

        assert plan.actions[0].details["file_size"] == 1024

    def test_total_count(self):
        """Should count total actions."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/a.pdf")
        plan.add_action(ActionType.SKIP, "/b.pdf")
        plan.add_action(ActionType.ADD, "/c.pdf")

        assert plan.total == 3

    def test_adds_count(self):
        """Should count add actions."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/a.pdf")
        plan.add_action(ActionType.SKIP, "/b.pdf")
        plan.add_action(ActionType.ADD, "/c.pdf")

        assert plan.adds == 2

    def test_updates_count(self):
        """Should count update actions."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.UPDATE, "/a.pdf")
        plan.add_action(ActionType.ADD, "/b.pdf")

        assert plan.updates == 1

    def test_removes_count(self):
        """Should count remove actions."""
        plan = OperationPlan(operation=OperationType.DELETE)
        plan.add_action(ActionType.REMOVE, "/a.pdf")
        plan.add_action(ActionType.REMOVE, "/b.pdf")

        assert plan.removes == 2

    def test_skips_count(self):
        """Should count skip actions."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.SKIP, "/a.pdf")
        plan.add_action(ActionType.ADD, "/b.pdf")

        assert plan.skips == 1

    def test_fixes_count(self):
        """Should count fix actions."""
        plan = OperationPlan(operation=OperationType.REPAIR)
        plan.add_action(ActionType.FIX, "issue1")
        plan.add_action(ActionType.SKIP, "issue2")

        assert plan.fixes == 1

    def test_get_by_type(self):
        """Should filter actions by type."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/a.pdf")
        plan.add_action(ActionType.SKIP, "/b.pdf")
        plan.add_action(ActionType.ADD, "/c.pdf")

        adds = plan.get_by_type(ActionType.ADD)
        assert len(adds) == 2
        assert all(a.action == ActionType.ADD for a in adds)

    def test_source_path(self):
        """Should store source path."""
        plan = OperationPlan(
            operation=OperationType.INDEX,
            source_path=Path("/test/docs"),
        )
        assert plan.source_path == Path("/test/docs")


class TestDisplayPlan:
    """Tests for display_plan function."""

    def test_displays_header(self):
        """Should display dry-run header."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/test.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "DRY RUN" in text

    def test_displays_operation_type(self):
        """Should display operation type."""
        plan = OperationPlan(operation=OperationType.DELETE)
        plan.add_action(ActionType.REMOVE, "/test.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "delete" in text.lower()

    def test_displays_source_path(self):
        """Should display source path if set."""
        plan = OperationPlan(
            operation=OperationType.INDEX,
            source_path=Path("/my/docs"),
        )
        plan.add_action(ActionType.ADD, "/test.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=False)
        display_plan(plan, console=console)

        text = output.getvalue()
        # Check both path components are present (ANSI codes may split them)
        assert "my" in text and "docs" in text

    def test_displays_no_actions_message(self):
        """Should display message when no actions."""
        plan = OperationPlan(operation=OperationType.INDEX)

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "No actions" in text

    def test_displays_summary_counts(self):
        """Should display summary counts."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/a.pdf")
        plan.add_action(ActionType.ADD, "/b.pdf")
        plan.add_action(ActionType.SKIP, "/c.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "add" in text.lower()
        assert "skip" in text.lower()

    def test_displays_action_list(self):
        """Should display action list."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/test/document.pdf", reason="new file")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "document.pdf" in text
        assert "new file" in text

    def test_truncates_long_lists(self):
        """Should truncate long action lists."""
        plan = OperationPlan(operation=OperationType.INDEX)
        for i in range(30):
            plan.add_action(ActionType.ADD, f"/file{i}.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console, max_items=20)

        text = output.getvalue()
        assert "more" in text.lower()
        assert "--verbose" in text

    def test_verbose_shows_all(self):
        """Verbose mode should show all items."""
        plan = OperationPlan(operation=OperationType.INDEX)
        for i in range(30):
            plan.add_action(ActionType.ADD, f"/file{i}.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console, max_items=20, verbose=True)

        text = output.getvalue()
        # Should show file29 (last file) in verbose mode
        assert "file29.pdf" in text

    def test_displays_no_changes_message(self):
        """Should display no changes made message."""
        plan = OperationPlan(operation=OperationType.INDEX)
        plan.add_action(ActionType.ADD, "/test.pdf")

        output = StringIO()
        console = Console(file=output, force_terminal=True)
        display_plan(plan, console=console)

        text = output.getvalue()
        assert "No changes made" in text


class TestCreateIndexPlan:
    """Tests for create_index_plan function."""

    def test_plans_new_files(self):
        """Should plan to add new files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "doc1.pdf"
            file1.write_text("content 1")
            file2 = Path(tmpdir) / "doc2.pdf"
            file2.write_text("content 2")

            plan = create_index_plan([file1, file2])

            assert plan.operation == OperationType.INDEX
            assert plan.adds == 2
            assert plan.skips == 0

    def test_skips_nonexistent_files(self):
        """Should skip files that don't exist."""
        plan = create_index_plan([Path("/nonexistent/file.pdf")])

        assert plan.skips == 1
        assert plan.adds == 0
        assert "not found" in plan.actions[0].reason

    def test_skips_directories(self):
        """Should skip directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = create_index_plan([Path(tmpdir)])

            assert plan.skips == 1
            assert "not a file" in plan.actions[0].reason

    def test_skips_already_indexed(self):
        """Should skip already indexed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "doc.pdf"
            file1.write_text("existing content")

            # Generate hash for this content
            from ragd.storage.chromadb import generate_content_hash
            existing_hash = generate_content_hash("existing content")

            plan = create_index_plan([file1], existing_hashes={existing_hash})

            assert plan.skips == 1
            assert "already indexed" in plan.actions[0].reason

    def test_includes_file_size(self):
        """Should include file size in details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "doc.pdf"
            file1.write_text("some content here")

            plan = create_index_plan([file1])

            assert plan.actions[0].details.get("file_size") is not None


class TestCreateDeletePlan:
    """Tests for create_delete_plan function."""

    def test_plans_deletions(self):
        """Should plan to remove documents."""
        doc_ids = ["doc1", "doc2", "doc3"]
        doc_paths = {
            "doc1": "/path/to/doc1.pdf",
            "doc2": "/path/to/doc2.pdf",
            "doc3": "/path/to/doc3.pdf",
        }

        plan = create_delete_plan(doc_ids, doc_paths)

        assert plan.operation == OperationType.DELETE
        assert plan.removes == 3

    def test_includes_document_id(self):
        """Should include document ID in details."""
        plan = create_delete_plan(
            ["doc1"],
            {"doc1": "/path/doc1.pdf"},
        )

        assert plan.actions[0].details["document_id"] == "doc1"

    def test_uses_id_when_path_missing(self):
        """Should use document ID when path not found."""
        plan = create_delete_plan(["unknown_doc"], {})

        assert plan.removes == 1
        assert str(plan.actions[0].target) == "unknown_doc"


class TestCreateRepairPlan:
    """Tests for create_repair_plan function."""

    def test_plans_fixable_issues(self):
        """Should plan to fix fixable issues."""
        issues = [
            {"type": "orphaned_chunk", "target": "chunk1", "fixable": True},
            {"type": "missing_embedding", "target": "chunk2", "fixable": True},
        ]

        plan = create_repair_plan(issues)

        assert plan.operation == OperationType.REPAIR
        assert plan.fixes == 2

    def test_skips_unfixable_issues(self):
        """Should skip unfixable issues."""
        issues = [
            {"type": "corrupted_data", "target": "chunk1", "fixable": False},
        ]

        plan = create_repair_plan(issues)

        assert plan.skips == 1
        assert plan.fixes == 0
        assert "manual fix required" in plan.actions[0].reason

    def test_mixed_issues(self):
        """Should handle mixed fixable and unfixable issues."""
        issues = [
            {"type": "orphaned_chunk", "target": "chunk1", "fixable": True},
            {"type": "corrupted_data", "target": "chunk2", "fixable": False},
            {"type": "missing_embedding", "target": "chunk3", "fixable": True},
        ]

        plan = create_repair_plan(issues)

        assert plan.fixes == 2
        assert plan.skips == 1
