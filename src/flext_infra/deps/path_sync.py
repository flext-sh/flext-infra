"""Re-export dependency path sync service."""

from __future__ import annotations

import sys
from importlib import import_module


def main() -> int:
    """Run dependency path sync through canonical CLI routing."""
    cli_main = import_module("flext_infra.cli").main
    exit_code: int = cli_main(["deps", "path-sync", *sys.argv[1:]])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())


__all__: list[str] = ["main"]
