"""Re-export dependency path sync service."""

from __future__ import annotations

import sys

from flext_infra._utilities.deps_path_sync import FlextInfraUtilitiesDependencyPathSync
from flext_infra.cli import main as cli_main


def main() -> int:
    """Run dependency path sync through canonical CLI routing."""
    return cli_main(["deps", "path-sync", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["FlextInfraUtilitiesDependencyPathSync", "main"]
