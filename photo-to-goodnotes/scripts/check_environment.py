"""Small dependency and layout check; never downloads models or changes config."""

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    if sys.version_info[:2] != (3, 11):
        print(f"Expected Python 3.11 for the core environment; found {sys.version.split()[0]}")
        return 1
    missing = [
        name
        for name in ("inkbridge", "pydantic", "yaml", "typer")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        print(f"Missing packages: {', '.join(missing)}. Run the bootstrap script.")
        return 1
    if not (project / "tests/fixtures/ink_document.json").is_file():
        print("Missing illustrative schema fixture.")
        return 1
    print(f"InkBridge scaffold environment ready: {project}")
    print("InkSight model and Goodnotes renderer are not configured by this check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
