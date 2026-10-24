"""Run the canonical infrastructure CLI with admitted opt-in profiling.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import flext_infra
from flext_infra import settings
from flext_infra._pytest_clock import FlextInfraPytestClock


class FlextInfraProfileEntry:
    """Apply the shared runtime setting around the existing CLI composition root."""

    @staticmethod
    def run() -> int:
        """Preserve the CLI outcome and any explicitly requested profile.

        Settings admission precedes capture. Enabled signal checkpoints retain
        interrupted evidence without certifying successful execution.

        Returns:
            The canonical CLI exit status.

        """
        if not settings.Infra.profile:
            return flext_infra.main(sys.argv[2:])
        output = Path(sys.argv[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        return FlextInfraPytestClock.profile_command(
            lambda: flext_infra.main(sys.argv[2:]), output
        )


if __name__ == "__main__":
    raise SystemExit(FlextInfraProfileEntry.run())
