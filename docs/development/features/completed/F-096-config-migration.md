# F-096: Config Migration Tool

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

Configuration schema evolves between versions. Users need automatic migration to avoid manual updates.

## Design Approach

Implement version-aware configuration migration with backup and rollback.

### Migration Flow
```
$ ragd config migrate
Detected config version: 1
Current version: 2
Creating backup: config.yaml.v1.backup
Migrating...
  ✓ Added retrieval.contextual section
  ✓ Renamed search.mode values
  ✓ Added security.session options
Migration complete!
```

### Migration System
```python
# migrations/v1_to_v2.py
def migrate(config: dict) -> dict:
    """Migrate config from v1 to v2."""
    config["version"] = 2
    # Add new sections with defaults
    config.setdefault("retrieval", {}).setdefault("contextual", {...})
    return config
```

## Implementation Tasks

- [ ] Add version field to config schema
- [ ] Create migrations directory
- [ ] Implement migration registry
- [ ] Implement backup before migration
- [ ] Create `ragd config migrate` command
- [ ] Write v1 to v2 migration (if needed)
- [ ] Add `--dry-run` option
- [ ] Add `--rollback` option
- [ ] Document migration in upgrade guide

## Success Criteria

- [ ] Automatic migration on version mismatch
- [ ] Backup created before migration
- [ ] Dry-run shows changes without applying
- [ ] Rollback restores previous config

## Dependencies

- v0.8.6 (Security Focus)

---

## Related Documentation

- [v0.8.7 Milestone](../../milestones/v0.8.7.md)
- [F-092 Configuration Reference](./F-092-configuration-reference.md)

---

**Status**: Completed
