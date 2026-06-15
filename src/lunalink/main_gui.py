"""GUI entry point (alias of :mod:`lunalink.main`).

Usage:
    python -m lunalink.main_gui
"""
from .main import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
