# .claude/ Configuration

This directory contains Claude Code configuration for the ragd project.

## Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project-specific standards and guidelines |
| `config.json` | Structured project configuration |
| `inherits.json` | Inheritance chain declaration |
| `settings.local.json` | Permission overrides (local only) |

## Inheritance Chain

This project inherits from:
1. `~/.claude/` - Global essentials (British English, SSOT)
2. `~/Development/.claude/` - Development standards (docs structure)
3. `~/Development/Sandboxed/.claude/` - Docker/experimental standards

## Configuration Details

### config.json
Structured settings for:
- Project metadata (name, type)
- Python configuration (version, venvs, CLI)
- AI transparency settings
- Documentation preferences
- Privacy rules

### inherits.json
Declares the inheritance chain and activated profiles:
- Inherits from 3 parent levels
- Activates `python` and `docker` profiles

### settings.local.json
Local permission overrides. These are NOT committed to git on other projects but included here as reference implementation.

## Profile Activation

This project auto-activates:
- **python** - Via `pyproject.toml` detection
- **docker** - Via `docker-compose.yml` detection

## Related

- [Permission Profiles](~/.claude/profiles/README.md)
- [JSON Schemas](~/.claude/schemas/README.md)
- [Hooks](~/.claude/hooks/README.md)
