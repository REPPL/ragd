# F-088: Interactive Configuration

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

Users must manually edit YAML configuration files, which is error-prone and intimidating for newcomers. An interactive wizard provides guided configuration.

## Design Approach

Use `questionary` for rich interactive prompts with validation and sensible defaults.

### User Experience
```
$ ragd config
? What would you like to configure?
  > Model settings
  > Search behaviour
  > Storage backend
  > Security options
  > Show current config
```

### Configuration Sections
1. **Model Settings** - Embedding model, LLM provider/model
2. **Search Behaviour** - Mode (hybrid/semantic/keyword), weights
3. **Storage Backend** - Data directory, ChromaDB path
4. **Security Options** - Encryption, session timeout

## Implementation Tasks

- [ ] Add `questionary` dependency
- [ ] Create `ragd config` interactive entry point
- [ ] Implement model settings wizard
- [ ] Implement search behaviour wizard
- [ ] Implement storage backend wizard
- [ ] Implement security options wizard
- [ ] Add validation with helpful error messages
- [ ] Save configuration changes atomically
- [ ] Add `--interactive` flag for explicit mode

## Success Criteria

- [ ] Users can configure ragd without editing YAML
- [ ] All major settings configurable via wizard
- [ ] Invalid input caught with helpful messages
- [ ] Changes saved atomically (no partial updates)

## Dependencies

- questionary (new dependency)
- v0.8.6 (Security Focus)

## Related Documentation

- [F-036: Guided Setup](./F-036-guided-setup.md)
- [F-092: Configuration Reference](./F-092-configuration-reference.md)
- [v0.8.6 Milestone](../../milestones/v0.8.6.md)
