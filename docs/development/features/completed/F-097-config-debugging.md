# F-097: Config Debugging

**Status:** Planned
**Milestone:** v0.8.7

## Problem Statement

Users can't easily see effective configuration or diagnose config issues. Need tools for debugging configuration.

## Design Approach

Add configuration debugging commands to show effective config and diagnose issues.

### Commands
```bash
# Show effective configuration (with defaults)
ragd config show --effective

# Show only non-default values
ragd config show --diff

# Validate configuration
ragd config validate

# Show config source
ragd config show --source
# Output: ~/.ragd/config.yaml (line 15)
```

### Effective Config Output
```yaml
# Effective configuration (with defaults)
version: 1
hardware:
  backend: mps  # detected
  tier: high    # detected
embedding:
  model: all-MiniLM-L6-v2  # default
  dimension: 384            # default
llm:
  model: llama3.2:3b       # from config.yaml:12
```

## Implementation Tasks

- [ ] Implement `ragd config show --effective`
- [ ] Implement `ragd config show --diff`
- [ ] Implement `ragd config validate`
- [ ] Add source tracking for config values
- [ ] Implement `ragd config show --source`
- [ ] Add JSON output format
- [ ] Show validation errors with line numbers
- [ ] Document debugging workflow

## Success Criteria

- [ ] `--effective` shows complete config with defaults
- [ ] `--diff` shows only changed values
- [ ] `--source` shows where values come from
- [ ] Validation errors include line numbers

## Dependencies

- v0.8.6 (Security Focus)

---

## Related Documentation

- [v0.8.7 Milestone](../../milestones/v0.8.7.md)
- [F-092 Configuration Reference](./F-092-configuration-reference.md)

---

**Status**: Planned
