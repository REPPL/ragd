#!/usr/bin/env python3
"""Version sync validation hook for pre-commit.

This script validates that version numbers are synchronised across
pyproject.toml and src/ragd/__init__.py.

Usage:
    python scripts/check-version-sync.py

Exit codes:
    0 - Versions match
    1 - Version mismatch or file not found
"""

import re
import sys
from pathlib import Path

PYPROJECT_PATH = Path("pyproject.toml")
INIT_PATH = Path("src") / "ragd" / "__init__.py"


def extract_pyproject_version(path: Path) -> str | None:
    """Extract version from pyproject.toml."""
    if not path.exists():
        return None
    content = path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return match.group(1) if match else None


def extract_init_version(path: Path) -> str | None:
    """Extract __version__ from __init__.py."""
    if not path.exists():
        return None
    content = path.read_text()
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    """Check version consistency and return exit code."""
    pyproject_version = extract_pyproject_version(PYPROJECT_PATH)
    init_version = extract_init_version(INIT_PATH)

    if pyproject_version is None:
        print(f"ERROR: Could not find version in {PYPROJECT_PATH}")
        return 1

    if init_version is None:
        print(f"ERROR: Could not find __version__ in {INIT_PATH}")
        return 1

    if pyproject_version != init_version:
        print("VERSION MISMATCH:")
        print(f"  pyproject.toml:        {pyproject_version}")
        print(f"  src/ragd/__init__.py:  {init_version}")
        print()
        print("Both files must have the same version.")
        print("Update both files to match before committing.")
        return 1

    print(f"Version sync OK: {pyproject_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
