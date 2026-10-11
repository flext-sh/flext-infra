"""Profile the canonical infrastructure CLI and preserve its native outcome.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import signal
import sys
from pathlib import Path
from types import FrameType

from flext_infra.cli import main


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

        def terminate(number: int, frame: FrameType | None) -> None:
            profiler.dump_stats(str(output))
            signal.signal(number, previous)
            if callable(previous):
                previous(number, frame)
            elif previous == signal.SIG_DFL:
                signal.raise_signal(number)

        signal.signal(signal.SIGTERM, terminate)
        try:
            return profiler.runcall(main, sys.argv[2:])
        finally:
            signal.signal(signal.SIGTERM, previous)
            profiler.dump_stats(str(output))


if __name__ == "__main__":
    raise SystemExit(FlextInfraProfileEntry.run())
