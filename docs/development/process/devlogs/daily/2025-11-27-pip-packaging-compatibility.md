# Thinking Log: pip/packaging 25.0 Compatibility Fix

## Context

After releasing v0.2.0, `pip install -e .` failed with:
```
pip._vendor.packaging.version.InvalidVersion: Invalid version: 'pdf'
```

Additionally, `ragd --version` showed 0.1.1 instead of 0.2.0 because `__version__` in `__init__.py` wasn't updated.

## Approach Considered

1. **Upgrade pip** - Tried pip 25.3 and 24.3.1, both failed
2. **Clear caches** - Purged pip cache, removed egg-info, no effect
3. **Fresh venv** - Same error in clean environment
4. **Downgrade pip** - pip 24.0 worked
5. **Expand self-referential extras** - Remove `ragd[pdf,ocr,...]` syntax

## Decision Made

Applied both workarounds:

1. **Expand self-referential extras** in pyproject.toml:
   ```toml
   # Before (broken with packaging 25.0)
   v02 = ["ragd[pdf,ocr,metadata,export,watch,web]"]

   # After (compatible)
   v02 = [
       "docling>=2.0.0",
       "docling-core>=2.0.0",
       # ... all dependencies listed directly
   ]
   ```

2. **Document pip 24.0 requirement** until upstream fix

## Challenges Encountered

The root cause was subtle:
- `packaging` 25.0 (bundled in pip 24.3.1+) changed marker evaluation
- When evaluating `extra == "pdf"`, it treats "pdf" as a version string
- This breaks any package with optional dependencies using extra markers

Debugging required:
1. Verbose pip output showed error in `_check_metadata_consistency`
2. Testing with standalone `packaging` library confirmed the issue
3. Downgrading `packaging` to 24.2 fixed marker evaluation

## Outcome

- Released v0.2.1 with both fixes
- Users should use `pip install pip==24.0` until packaging issue resolved
- Upstream issue: https://github.com/pypa/packaging/issues/921

## Lesson Learned

- Keep `__version__` in `__init__.py` synchronised with `pyproject.toml`
- Self-referential extras (`pkg[extra1,extra2]`) are fragile across pip versions
- Always test `pip install -e .` after releases
