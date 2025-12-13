"""Allow running ragd as a module: python -m ragd."""

from ragd.cli import app

if __name__ == "__main__":
    app()
