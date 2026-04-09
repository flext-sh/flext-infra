"""Re-export dependency path sync service."""

from __future__ import annotations

import sys

from flext_infra._utilities.deps_path_sync import FlextInfraUtilitiesDependencyPathSync

if __name__ == "__main__":
    sys.exit(FlextInfraUtilitiesDependencyPathSync.main())


__all__ = ["FlextInfraUtilitiesDependencyPathSync"]
