"""Profile the canonical infrastructure CLI and preserve its native outcome.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import flext_infra
from flext_infra._pytest_clock import FlextInfraPytestClock


class FlextInfraProfileEntry:
    """Own the profiler lifetime around the existing CLI composition root."""

    @staticmethod
    def run() -> int:
        """Retain the profile even when the CLI raises or is interrupted.

        Signal checkpoints update the elected report input and preserve the
        previous artifact. They describe work up to interruption, not success.

        Returns:
            The canonical CLI exit status.

        """
        return FlextInfraPytestClock.profile_command(
            lambda: flext_infra.main(sys.argv[2:]), Path(sys.argv[1])
        )


if __name__ == "__main__":
    raise SystemExit(FlextInfraProfileEntry.run())
