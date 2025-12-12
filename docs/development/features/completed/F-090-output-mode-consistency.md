# F-090: Output Mode Consistency

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

Output format options are inconsistent across commands. Some support JSON, some don't. Users need predictable output for scripting and automation.

## Design Approach

Standardise output format across all commands with consistent option naming and behaviour.

### Standard Output Formats
- **rich** (default) - Coloured, formatted for humans
- **plain** - Plain text, no colours
- **json** - Machine-readable JSON
- **csv** - Tabular data export (where applicable)

### Consistent Options
```bash
ragd search "query" --format json
ragd status --format plain
ragd list --format csv
```

### Global Override
```bash
export RAGD_OUTPUT_FORMAT=json
ragd search "query"  # Uses JSON
```

## Implementation Tasks

- [ ] Audit all commands for output format support
- [ ] Create OutputFormat enum in ragd.ui
- [ ] Add `--format` option to all relevant commands
- [ ] Implement JSON output for: search, list, status, stats, doctor
- [ ] Implement CSV output for: list, stats
- [ ] Add RAGD_OUTPUT_FORMAT environment variable support
- [ ] Create output formatting utilities
- [ ] Update command documentation

## Success Criteria

- [ ] All list/query commands support json/plain/rich
- [ ] Tabular commands support CSV
- [ ] Environment variable override works
- [ ] Output is valid JSON (parseable by jq)

## Dependencies

- v0.8.6 (Security Focus)

