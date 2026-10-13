"""Profile the canonical infrastructure CLI and preserve its native outcome.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import signal
import sys
from pathlib import Path

from flext_infra import main
from flext_infra._pytest_clock import FlextInfraPytestClock


class FlextInfraProfileEntry:
    """Own the profiler lifetime around the existing CLI composition root."""

    @staticmethod
    def run() -> int:
        """Retain the profile even when the CLI raises or is interrupted.

        Returns:
            The canonical CLI exit status.
        """
        output = Path(sys.argv[1])
        profiler = cProfile.Profile()
        previous = signal.getsignal(signal.SIGTERM)

        FlextInfraPytestClock.register_signal_checkpoint(profiler, output)
        try:
            return profiler.runcall(main, sys.argv[2:])
        finally:
            signal.signal(signal.SIGTERM, previous)
            FlextInfraPytestClock.publish_profile(profiler, output)


if __name__ == "__main__":
    raise SystemExit(FlextInfraProfileEntry.run())
