"""Re-export dependency path sync service."""

from __future__ import annotations

import sys

from flext_infra._utilities.deps_path_sync import FlextInfraUtilitiesDependencyPathSync


def main() -> int:
    """Run dependency path sync through the canonical implementation."""
    return FlextInfraUtilitiesDependencyPathSync.main()


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["FlextInfraUtilitiesDependencyPathSync", "main"]
