"""Profile the public Mypy API without its command-line hard exit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import resource
import signal
import sys
import time
from pathlib import Path
from types import FrameType

from mypy import api


class FlextInfraUtilitiesMypyProfile:
    """Preserve native reports and status while recording the checker profile."""

    @staticmethod
    def run(destination: Path, arguments: tuple[str, ...]) -> int:
        """Run the public checker API, whose clean exit lets cProfile save data.

        Returns:
            The resulting ``int``.

        Raises:
            RuntimeError: If native termination handlers cannot be observed.

        """
        profile = cProfile.Profile()
        started = time.monotonic()
        previous_interrupt = signal.getsignal(signal.SIGINT)
        previous_termination = signal.getsignal(signal.SIGTERM)
        if previous_interrupt is None or previous_termination is None:
            msg = "cannot observe native profiler termination handlers"
            raise RuntimeError(msg)
        previous = {
            signal.SIGINT.value: previous_interrupt,
            signal.SIGTERM.value: previous_termination,
        }

        def checkpoint(signum: int, frame: FrameType | None) -> None:
            """Save native profiling evidence before preserving termination."""
            profile.dump_stats(destination)
            handler = previous[signum]
            signal.signal(signum, handler)
            if callable(handler):
                handler(signum, frame)
            else:
                signal.raise_signal(signum)

        for signum in previous:
            signal.signal(signum, checkpoint)
        try:
            stdout, stderr, status = profile.runcall(
                api.run,
                list(arguments),
            )
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            profile.dump_stats(destination)
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_rss_bytes = peak_rss if sys.platform == "darwin" else peak_rss * 1024
        sys.stderr.write(
            "\nLOG:  Mypy profile telemetry: "
            f"elapsed_seconds={time.monotonic() - started:.6f} "
            f"peak_rss_bytes={peak_rss_bytes} exit_code={status}\n",
        )
        return status


if __name__ == "__main__":
    raise SystemExit(
        FlextInfraUtilitiesMypyProfile.run(Path(sys.argv[1]), tuple(sys.argv[2:])),
    )
