# State-of-the-Art: Automation Script Generation for Non-Expert Users

## Executive Summary

**Key Recommendations for ragd:**

1. **Hybrid Approach: Wizard + LLM Enhancement** - Use interactive wizards for structured task specification with optional LLM-powered natural language input for complex scenarios
2. **Mandatory Dry-Run Preview** - Always show users what will happen before execution (following Terraform/PowerShell patterns)
3. **YAML-Based Task Definitions** - Store automation tasks as human-readable YAML files that can be version-controlled and shared
4. **Dual-Mode Generation** - Generate both shell scripts (for automation/cron) and direct ragd commands (for immediate use)
5. **Progressive Disclosure** - Start with simple presets, reveal complexity only when users need it
6. **Explain Everything** - Auto-generate comments explaining what each part of the script does

---

## The Challenge: Non-Expert Users and Automation

### Why This Matters

| User Type | Technical Level | Pain Point |
|-----------|-----------------|------------|
| **Researcher** | Low-Medium | "I want to analyse 50 PDFs weekly but don't know shell scripting" |
| **Knowledge Worker** | Low | "I need consistent processing but can't remember CLI flags" |
| **Small Team Lead** | Medium | "I want to share my workflow with colleagues" |
| **Data Analyst** | Medium | "I want to batch-compare models but find CLI intimidating" |

### Current Gap in ragd

- Rich CLI with many options (23+ command groups)
- Interactive `config` wizard exists for settings
- `watch` command provides file monitoring automation
- **Missing**: Guided automation script generation for complex workflows

---

## Approaches: State-of-the-Art Survey

### 1. LLM-Based Natural Language to Script

**Tools Surveyed:**
- [Shell GPT](https://github.com/TheR1D/shell_gpt) - CLI productivity with GPT-4
- [LLMScript](https://github.com/statico/llmscript) - Natural language shell scripts
- [arkterm](https://saadman.dev/blog/2025-05-31-shell-shocked-wire-llm-directly-in-linux-terminal/) - Context-aware terminal assistant

**Key Findings:**

| Aspect | Best Practice | Source |
|--------|---------------|--------|
| **Context Awareness** | Include current directory, project type, system environment | arkterm |
| **Safety First** | Disabled execution by default, require confirmation | Shell GPT |
| **Explanation** | Show what commands do before executing | arkterm, Shell GPT |
| **Testing** | Generate feature script + test script together | LLMScript |

**Research Insight:** [NL2SH Translation (NAACL 2025)](https://arxiv.org/html/2502.06858v1) shows LLMs achieve 95% functional equivalence on Bash generation with proper evaluation heuristics. However, LLMs cannot emulate command execution—they generate plausible but potentially incorrect scripts for novel/proprietary commands.

**Recommendation for ragd:** LLM can assist with natural language → intent parsing, but ragd should handle actual script generation from validated intent (not raw LLM output).

---

### 2. Interactive Wizard Patterns

**Key Sources:**
- [CLI UX Patterns (Lucas Costa)](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html)
- [Wizard UI Pattern (Eleken)](https://www.eleken.co/blog-posts/wizard-ui-pattern-explained)
- [PatternFly Wizard Guidelines](https://www.patternfly.org/components/wizard/design-guidelines/)
- [Top 8 CLI UX Patterns (Medium)](https://medium.com/@kaushalsinh73/top-8-cli-ux-patterns-users-will-brag-about-4427adb548b7)

**Best Practices:**

| Pattern | Description | Implementation |
|---------|-------------|----------------|
| **First-Run Wizard** | Guided setup with safe defaults and escape hatch | ragd already has `init` |
| **Input Validation** | Validate immediately, not at the end | Show errors inline |
| **Plain Language** | Avoid jargon; fit user's frame of reference | "Which documents?" not "Specify corpus paths" |
| **Summary Before Commit** | Show all choices before final action | Review step before generation |
| **Dual Mode** | Interactive for discovery, flags for automation | `ragd script new --interactive` vs `ragd script new --from-yaml task.yaml` |

**Shneiderman's Golden Rules Applied:**

1. Strive for consistency (same patterns across all wizards)
2. Enable shortcuts for frequent users (`--preset research-batch`)
3. Offer informative feedback (progress, validation)
4. Design for closure (clear completion signals)
5. Prevent errors (smart defaults, validation)
6. Permit reversal (edit generated script before saving)
7. Support internal locus of control (user feels in charge)

---

### 3. Dry-Run and Preview Patterns

**Industry Standards:**

| Tool | Pattern | Command |
|------|---------|---------|
| **PowerShell** | `-WhatIf` switch | `Remove-Item file.txt -WhatIf` |
| **Terraform** | `plan` command | `terraform plan` |
| **Ansible** | `--check` mode | `ansible-playbook site.yml --check` |
| **Git** | `--dry-run` flag | `git clean --dry-run` |
| **Kubernetes** | `--dry-run=client` | `kubectl apply --dry-run=client` |

**Why This Matters:**
- [PowerShell Best Practices](https://www.computerperformance.co.uk/powershell/whatif-confirm/) - "By appending -WhatIf, you get a preview without risking damage"
- [Git Dry-Run Safety](https://thelinuxcode.com/dry-run-git-commands/) - "Essential safeguard against damaging loss"

**Recommendation:** Every generated script should support `--dry-run` and `--explain` flags. The generation wizard MUST show a preview before writing any file.

---

### 4. Configuration-Driven Automation

**Approaches Surveyed:**
- [Home Assistant YAML](https://www.home-assistant.io/docs/automation/yaml/) - Declarative automation
- [MidsceneJS](https://midscenejs.com/automate-with-scripts-in-yaml.html) - AI automation in YAML
- [Hyperpotamus](https://github.com/pmarkert/hyperpotamus) - YAML/JSON automation scripting

**YAML Task Definition Pattern:**

```yaml
# Example: ~/.ragd/tasks/weekly-research-analysis.yaml
name: Weekly Research Analysis
description: Analyse new papers using multiple models

trigger:
  schedule: "0 9 * * MON"  # Every Monday at 9am
  # OR manual: true

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

  - name: Compare with Claude
    command: ask
    args:
      query: "Summarise the key findings and methodology"
      model: claude-sonnet
      output: ~/Research/summaries/{{date}}-summaries-claude.md

output:
  format: markdown
  location: ~/Research/reports/
  notify: true  # Desktop notification when complete
```

**Benefits:**
- Human-readable and editable
- Version-controllable (share with team)
- Declarative (what, not how)
- Validatable (Pydantic schema)

---

### 5. Low-Code/No-Code AI Workflow Patterns

**Platforms Surveyed:**
- [n8n](https://n8n.io/ai-agents/) - Visual workflow builder with AI agents
- [Langflow](https://www.bluebash.co/blog/langflow-vs-n8n-ai-workflow-automation/) - Visual LLM workflow builder

**Key Insights:**
- n8n users built workflows 3x faster than writing Python for LangChain
- Visual builders excel for business users; CLI excels for developers
- Best approach: Support both visual (future WebUI) and CLI (now)

**n8n Design Patterns for AI Workflows:**

| Pattern | Description | ragd Application |
|---------|-------------|------------------|
| **Single Agent** | One AI maintains state throughout | Default for simple tasks |
| **Multi-Agent** | Specialised agents collaborate | Model comparison tasks |
| **Tool Integration** | Agents can call external tools | ragd commands as tools |
| **Memory/Scratchpad** | Retain intermediate state | Session persistence |

---

### 6. Code Explanation for Non-Experts

**Best Practices from [Google Cloud](https://cloud.google.com/use-cases/ai-code-generation) and [AWS](https://aws.amazon.com/what-is/ai-coding/):**

| Practice | Implementation |
|----------|----------------|
| **Comments explain "why"** | Not just what—explain the purpose |
| **Self-documenting code** | Variable names that reveal intent |
| **Principle of Least Surprise** | Behaviour matches expectations |
| **Target audience clarity** | Write for users, not developers |

**Recommendation:** Generated scripts should include:
```bash
#!/bin/bash
# Weekly Research Analysis Script
# Generated by ragd on 2025-01-15
#
# This script:
#   1. Indexes all new PDFs in ~/Research/Papers/incoming/
#   2. Generates summaries using Llama 3.2
#   3. Compares with Claude for cross-validation
#   4. Saves reports to ~/Research/reports/
#
# To run: ./weekly-research.sh
# To preview without changes: ./weekly-research.sh --dry-run

# Step 1: Index new documents
# Adds all PDFs to your knowledge base with automatic tagging
ragd index ~/Research/Papers/incoming/ --recursive --tags weekly-intake,auto-indexed
```

---

## Recommended Architecture for ragd

### Proposed Command Structure

```
ragd script                    # List saved scripts/tasks
ragd script new               # Interactive wizard
ragd script new --from-yaml   # From YAML definition
ragd script show <name>       # Preview script
ragd script run <name>        # Execute script
ragd script run <name> --dry-run  # Preview what would happen
ragd script export <name>     # Export to shell script
ragd script edit <name>       # Edit YAML definition
```

### User Journey: Creating an Automation

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

[User selects "Batch document analysis"]

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
│  │  Estimated time: ~5 minutes (depends on document count)  │   │
│  │                                                          │   │
│  │  [S]ave  [R]un now  [E]dit  [C]ancel                     │   │
│  │                                                          │   │
│  ╰──────────────────────────────────────────────────────────╯   │
└─────────────────────────────────────────────────────────────────┘
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

---

## Implementation Approach Comparison

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Pure LLM Generation** | Most flexible, handles novel requests | Unpredictable, security risks, requires API | Use for intent parsing only |
| **Template-Based** | Predictable, fast, works offline | Limited flexibility | Primary approach |
| **Visual Builder** | Most accessible | Requires WebUI (future) | Defer to v1.0 |
| **YAML + Wizard Hybrid** | Predictable + flexible, shareable | More complex to implement | **Recommended** |

---

## Security Considerations

| Risk | Mitigation |
|------|------------|
| **Script injection** | Validate all user inputs; escape shell characters |
| **Path traversal** | Restrict to configured directories |
| **Credential exposure** | Never embed credentials; use environment variables |
| **Destructive operations** | Require explicit `--force` flag; default to dry-run |

---

## Integration Points with Existing ragd

| Existing Component | Integration |
|--------------------|-------------|
| `config_wizard.py` | Reuse Rich prompting patterns |
| `config.py` | Store tasks in similar Pydantic models |
| `watch.py` | Tasks could trigger watch-style callbacks |
| `help_system.py` | Extended help for script commands |
| `commands/core.py` | New `script` command group |

---

## Recommended Implementation Phases

### Phase 1: Foundation
- YAML task definition schema (Pydantic model)
- `ragd script` command group skeleton
- `ragd script show` / `ragd script run` for manual YAML files

### Phase 2: Interactive Wizard
- `ragd script new` wizard using Rich prompts
- Template-based script generation
- Dry-run preview before saving

### Phase 3: Shell Export
- `ragd script export` generates standalone bash scripts
- Auto-generated comments explaining each step
- Cron-compatible output

### Phase 4: Advanced Features (Future)
- Natural language input ("describe in your own words")
- Scheduling integration
- Desktop notifications on completion

---

## Current Capabilities

While the full `ragd script` command group is planned for v1.4, ragd already supports automation through:

### CLI Features Available Now

| Feature | Command | Use Case |
|---------|---------|----------|
| **JSON output** | `--format json` | Parse results in shell scripts |
| **Non-interactive mode** | `--no-interactive` | Prevent prompts in cron jobs |
| **Health checks** | `ragd doctor --format json` | Monitor health in scripts |
| **Watch mode** | `ragd watch` | Auto-index on file changes |
| **Verbose logging** | `--verbose` | Debug automation issues |

### Exit Codes

ragd uses standard sysexits.h codes for scripting:

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1 | General error | Check logs |
| 64 | Usage error | Fix command |
| 65 | Data error | Fix input |
| 78 | Config error | Check config |

### Ready-to-Use Scripts

See **[Recipes](../../guides/recipes.md)** for copy-paste automation scripts:

- Daily backup with rotation
- Batch indexing from multiple directories
- Health monitoring for cron
- Model comparison reports
- Search results to Markdown export
- Weekly re-indexing

---

## Related Documentation

- [Recipes](../../guides/recipes.md) - Ready-to-use automation scripts
- [state-of-the-art-cli-modes.md](./state-of-the-art-cli-modes.md) - CLI dual-mode design patterns
- [state-of-the-art-setup-ux.md](./state-of-the-art-setup-ux.md) - Easy setup and onboarding
- [state-of-the-art-configuration.md](./state-of-the-art-configuration.md) - Configuration management patterns
- [cli-best-practices.md](./cli-best-practices.md) - Modern CLI design principles

---

## Sources

### LLM-Based Script Generation
- [Shell GPT](https://github.com/TheR1D/shell_gpt) - GPT-powered CLI productivity
- [LLMScript](https://github.com/statico/llmscript) - Natural language shell scripts
- [NL2SH Translation (NAACL 2025)](https://arxiv.org/html/2502.06858v1) - Academic evaluation of LLM bash generation
- [arkterm](https://saadman.dev/blog/2025-05-31-shell-shocked-wire-llm-directly-in-linux-terminal/) - Context-aware terminal assistant

### CLI UX Patterns
- [UX Patterns for CLI Tools](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html) - Comprehensive CLI UX guide
- [Wizard UI Pattern](https://www.eleken.co/blog-posts/wizard-ui-pattern-explained) - When and how to use wizards
- [PatternFly Wizard Guidelines](https://www.patternfly.org/components/wizard/design-guidelines/) - Enterprise wizard patterns
- [Top 8 CLI UX Patterns](https://medium.com/@kaushalsinh73/top-8-cli-ux-patterns-users-will-brag-about-4427adb548b7) - Modern CLI best practices

### Dry-Run and Safety
- [PowerShell WhatIf/Confirm](https://www.computerperformance.co.uk/powershell/whatif-confirm/) - PowerShell safety patterns
- [Git Dry-Run Commands](https://thelinuxcode.com/dry-run-git-commands/) - Git safety best practices
- [Terraform Plan](https://scalr.com/learning-center/ultimate-guide-to-using-terraform-with-ansible/) - Infrastructure preview patterns

### Low-Code Automation
- [n8n AI Agents](https://n8n.io/ai-agents/) - Visual AI workflow builder
- [Langflow vs n8n](https://www.bluebash.co/blog/langflow-vs-n8n-ai-workflow-automation/) - AI workflow tool comparison
- [AI Agentic Workflows Guide](https://blog.n8n.io/ai-agentic-workflows/) - n8n design patterns

### Configuration-Driven Automation
- [Home Assistant YAML](https://www.home-assistant.io/docs/automation/yaml/) - Declarative automation config
- [MidsceneJS YAML Automation](https://midscenejs.com/automate-with-scripts-in-yaml.html) - AI automation scripting

### Code Explanation
- [Google Cloud AI Code Generation](https://cloud.google.com/use-cases/ai-code-generation) - AI coding best practices
- [AWS AI Coding Explained](https://aws.amazon.com/what-is/ai-coding/) - Code explanation guidelines
- [Five Best Practices for AI Coding Assistants](https://cloud.google.com/blog/topics/developers-practitioners/five-best-practices-for-using-ai-coding-assistants) - Google Cloud recommendations

---

**Status**: Complete
