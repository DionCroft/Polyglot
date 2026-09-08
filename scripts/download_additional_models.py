"""Compatibility entry point. Use setup.ps1 or setup_assets.py for pinned setup."""
from setup_assets import main
if __name__ == "__main__":
    raise SystemExit(main())
