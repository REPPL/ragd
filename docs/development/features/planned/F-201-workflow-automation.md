# F-201: Workflow Automation

## Overview

**Milestone**: v1.4
**Priority**: P1
**Research**: [State-of-the-Art Automation Scripts](../../research/state-of-the-art-automation-scripts.md)

## Problem Statement

Non-expert users face several challenges with ragd automation:

| User Type | Pain Point |
|-----------|------------|
| **Researcher** | "I want to analyse 50 PDFs weekly but don't know shell scripting" |
| **Knowledge Worker** | "I need consistent processing but can't remember CLI flags" |
| **Small Team Lead** | "I want to share my workflow with colleagues" |
| **Data Analyst** | "I want to batch-compare models but find CLI intimidating" |

Currently ragd has:
- Rich CLI with 23+ command groups
- Interactive `config` wizard for settings
- `watch` command for file monitoring

**Missing**: Guided automation script generation for complex workflows.

## Design Approach

### YAML-Based Task Definitions

Store automation tasks as human-readable YAML files:

```yaml
# ~/.ragd/tasks/weekly-research-analysis.yaml
name: Weekly Research Analysis
description: Analyse new papers using multiple models

inputs:
  documents:
    path: ~/Research/Papers/incoming/
    pattern: "*.pdf"

tasks:
  - name: Index new documents
    command: index
    args:
      recursive: true
      tags: ["weekly-intake", "auto-indexed"]

  - name: Generate summaries
    command: ask
    args:
      query: "Summarise the key findings and methodology"
      model: llama3.2
      output: ~/Research/summaries/{{date}}-summaries.md

output:
  format: markdown
  location: ~/Research/reports/
```

### Benefits

- **Human-readable**: Non-experts can understand and edit
- **Version-controllable**: Share with team via git
- **Declarative**: Specify "what", not "how"
- **Validatable**: Pydantic schema catches errors early

### Command Structure

```
ragd script                    # List saved tasks
ragd script new               # Interactive wizard (F-206)
ragd script new --from-yaml   # Import YAML definition
ragd script show <name>       # Preview task
ragd script run <name>        # Execute task
ragd script run <name> --dry-run  # Preview what would happen
ragd script export <name>     # Export to shell script (F-207)
ragd script edit <name>       # Edit YAML definition
```

### File Structure

```
~/.ragd/
├── config.yaml              # Existing configuration
├── tasks/                   # NEW: Task definitions
│   ├── weekly-paper-analysis.yaml
│   └── model-comparison.yaml
└── scripts/                 # NEW: Generated shell scripts
    ├── weekly-paper-analysis.sh
    └── model-comparison.sh
```

## Implementation Tasks

### Phase 1: Foundation
- [ ] Create Pydantic model for task definitions (`src/ragd/task.py`)
- [ ] Add `ragd script` command group to CLI
- [ ] Implement `ragd script show` - display task details
- [ ] Implement `ragd script run` - execute task
- [ ] Implement `ragd script run --dry-run` - preview mode
- [ ] Add YAML validation with helpful error messages
- [ ] Create `~/.ragd/tasks/` directory on first use
- [ ] Add task examples to documentation

### Phase 2: Management
- [ ] Implement `ragd script list` - show all saved tasks
- [ ] Implement `ragd script edit <name>` - open in $EDITOR
- [ ] Implement `ragd script delete <name>` - remove task
- [ ] Implement `ragd script validate <file>` - check YAML
- [ ] Add task templates for common workflows

## Success Criteria

- [ ] Users can create YAML task definitions manually
- [ ] `ragd script run` executes all tasks in sequence
- [ ] `ragd script run --dry-run` shows what would happen without executing
- [ ] Validation errors provide clear, actionable messages
- [ ] Task execution shows progress and results
- [ ] Documentation includes task definition reference

## Dependencies

- None (builds on existing CLI infrastructure)

## Technical Notes

### Task Definition Schema

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TaskInput(BaseModel):
    path: str
    pattern: Optional[str] = "*"
    recursive: bool = False

class TaskStep(BaseModel):
    name: str
    command: str  # ragd command: index, search, ask, etc.
    args: Dict[str, Any] = {}
    condition: Optional[str] = None  # Optional: only run if...

class TaskOutput(BaseModel):
    format: str = "markdown"
    location: Optional[str] = None

class TaskDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    inputs: Dict[str, TaskInput] = {}
    tasks: List[TaskStep]
    output: Optional[TaskOutput] = None
```

### Security Considerations

| Risk | Mitigation |
|------|------------|
| **Script injection** | Validate all inputs; escape shell characters |
| **Path traversal** | Restrict to configured directories |
| **Credential exposure** | Never embed credentials; use environment variables |
| **Destructive operations** | Require explicit `--force` flag; default to dry-run |

### Integration with Existing Components

| Component | Integration |
|-----------|-------------|
| `config_wizard.py` | Reuse Rich prompting patterns |
| `config.py` | Store tasks in similar Pydantic models |
| `watch.py` | Tasks could trigger watch-style callbacks |
| `help_system.py` | Extended help for script commands |
| `commands/core.py` | New `script` command group |

## Related Documentation

- [F-206](./F-206-interactive-script-wizard.md) - Interactive wizard for creating tasks
- [F-207](./F-207-shell-script-export.md) - Export to shell scripts
- [State-of-the-Art Automation Scripts](../../research/state-of-the-art-automation-scripts.md)
- [State-of-the-Art CLI Modes](../../research/state-of-the-art-cli-modes.md)

---

**Status**: Planned
