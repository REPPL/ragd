# F-092: Configuration Reference

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

Configuration options are documented only in code docstrings. Users need comprehensive reference documentation.

## Design Approach

Generate and maintain authoritative configuration reference with all options, defaults, and examples.

### Reference Structure
```
docs/reference/
├── configuration.md       # Complete config reference
├── environment.md         # Environment variables
└── config-templates/      # Example configurations
    ├── minimal.yaml
    ├── full.yaml
    └── high-performance.yaml
```

### Documentation Format
For each config section:
- Section name and purpose
- All options with types
- Default values
- Valid ranges/choices
- Example usage

### Example
```yaml
# chunking:
#   strategy: sentence | fixed | recursive
#   chunk_size: 100-4096 (default: 512)
#   overlap: 0-chunk_size/2 (default: 50)
chunking:
  strategy: sentence
  chunk_size: 512
  overlap: 50
```

## Implementation Tasks

- [ ] Create docs/reference/configuration.md
- [ ] Document all config sections
- [ ] Create docs/reference/environment.md
- [ ] Create minimal.yaml template
- [ ] Create full.yaml template with all options
- [ ] Create high-performance.yaml template
- [ ] Add validation rules to documentation
- [ ] Cross-reference from CLI help

## Success Criteria

- [ ] Every config option documented
- [ ] Default values documented
- [ ] Valid ranges/choices documented
- [ ] Example templates provided

## Dependencies

- v0.8.6 (Security Focus)

## Related Documentation

- [Configuration Reference](../../../reference/configuration.md)
- [F-088: Interactive Config](./F-088-interactive-config.md)
- [v0.8.6 Milestone](../../milestones/v0.8.6.md)
