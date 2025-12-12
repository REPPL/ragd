# F-206: Interactive Script Wizard

## Overview

**Milestone**: v1.4
**Priority**: P2
**Depends On**: [F-201](./F-201-workflow-automation.md) (Workflow Automation)
**Research**: [State-of-the-Art Automation Scripts](../../research/state-of-the-art-automation-scripts.md)

## Problem Statement

Even with YAML task definitions (F-201), non-expert users face barriers:
- Don't know what options are available
- Unsure which commands to combine
- Can't remember YAML syntax
- Need guidance on best practices

An interactive wizard guides users through task creation step-by-step.

## Design Approach

### Wizard Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  $ ragd script new                                              │
│                                                                 │
│  ╭─ Create New Automation Script ───────────────────────────╮   │
│  │                                                          │   │
│  │  What would you like to automate?                        │   │
│  │                                                          │   │
│  │  > [1] Batch document analysis                           │   │
│  │    [2] Scheduled indexing                                │   │
│  │    [3] Model comparison                                  │   │
│  │    [4] Report generation                                 │   │
│  │    [5] Describe in your own words...                     │   │
│  │                                                          │   │
│  ╰──────────────────────────────────────────────────────────╯   │
└─────────────────────────────────────────────────────────────────┘

[User selects option, then guided through steps...]

┌─────────────────────────────────────────────────────────────────┐
│  ╭─ Step 1/4: Select Documents ─────────────────────────────╮   │
│  │                                                          │   │
│  │  Which documents should be processed?                    │   │
│  │                                                          │   │
│  │  Path: ~/Research/Papers/incoming/                       │   │
│  │  Pattern: *.pdf (default) [enter to confirm]             │   │
│  │  Include subfolders? [Y/n]                               │   │
│  │                                                          │   │
│  ╰──────────────────────────────────────────────────────────╯   │
└─────────────────────────────────────────────────────────────────┘

[After all steps...]

┌─────────────────────────────────────────────────────────────────┐
│  ╭─ Review Your Automation ─────────────────────────────────╮   │
│  │                                                          │   │
│  │  Name: weekly-paper-analysis                             │   │
│  │                                                          │   │
│  │  This script will:                                       │   │
│  │   1. Index PDFs from ~/Research/Papers/incoming/         │   │
│  │   2. Tag documents as "weekly-intake"                    │   │
│  │   3. Generate summaries using llama3.2                   │   │
│  │   4. Save reports to ~/Research/reports/                 │   │
│  │                                                          │   │
│  │  [S]ave  [R]un now  [E]dit  [C]ancel                     │   │
│  │                                                          │   │
│  ╰──────────────────────────────────────────────────────────╯   │
└─────────────────────────────────────────────────────────────────┘
```

### UX Patterns (from Research)

Following Shneiderman's Golden Rules:

| Pattern | Implementation |
|---------|----------------|
| **Consistency** | Same prompting patterns as `ragd init` |
| **Shortcuts** | `ragd script new --preset research-batch` |
| **Informative feedback** | Progress indicators, validation messages |
| **Closure** | Clear completion with next steps |
| **Prevent errors** | Smart defaults, inline validation |
| **Permit reversal** | Edit before saving, undo options |
| **Internal locus of control** | User chooses path, not forced |

### Preset Templates

Pre-configured workflows for common use cases:

| Preset | Description |
|--------|-------------|
| `research-batch` | Index PDFs, generate summaries, export report |
| `model-comparison` | Same query to multiple models, compare results |
| `weekly-indexing` | Index new documents with auto-tagging |
| `report-generation` | Generate formatted reports from search results |

## Implementation Tasks

- [ ] Create `src/ragd/ui/cli/script_wizard.py`
- [ ] Implement task type selection menu
- [ ] Create step-by-step prompts for each task type
- [ ] Add input validation with helpful error messages
- [ ] Implement review/summary screen
- [ ] Add preset templates system
- [ ] Create `ragd script new --preset <name>` option
- [ ] Add Rich panels and formatting
- [ ] Support keyboard navigation (arrow keys, numbers)
- [ ] Add context help (? for help on any step)

## Success Criteria

- [ ] Non-expert users can create tasks without reading documentation
- [ ] Wizard validates all inputs before proceeding
- [ ] Summary screen clearly explains what will happen
- [ ] Generated YAML is valid and well-formatted
- [ ] Presets cover 80% of common use cases
- [ ] Wizard is accessible (works without colours, screen readers)

## Dependencies

- [F-201](./F-201-workflow-automation.md) - Task definition schema

## Technical Notes

### Wizard State Machine

```python
class WizardState(Enum):
    SELECT_TYPE = "select_type"
    CONFIGURE_INPUTS = "configure_inputs"
    CONFIGURE_TASKS = "configure_tasks"
    CONFIGURE_OUTPUT = "configure_output"
    REVIEW = "review"
    SAVE = "save"
```

### Integration with config_wizard.py

Reuse existing patterns from `src/ragd/ui/cli/config_wizard.py`:
- `rich.prompt.Prompt` for text input
- `rich.prompt.Confirm` for yes/no questions
- `rich.prompt.IntPrompt` for numeric input
- `rich.panel.Panel` for formatted sections

## Related Documentation

- [F-201](./F-201-workflow-automation.md) - Workflow Automation foundation
- [F-207](./F-207-shell-script-export.md) - Shell Script Export
- [State-of-the-Art Automation Scripts](../../research/state-of-the-art-automation-scripts.md)
- [State-of-the-Art CLI Modes](../../research/state-of-the-art-cli-modes.md)

---

**Status**: Planned
