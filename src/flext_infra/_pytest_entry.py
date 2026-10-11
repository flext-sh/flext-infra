"""Source-live pytest entrypoint with a pre-import absolute clock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import sys
import time
from pathlib import Path

import flext_infra


class FlextInfraPytestEntry:
    """Facade for the pytest entrypoint with pre-import clock."""

    _STARTED_AT_MONOTONIC: float = time.monotonic()

    @classmethod
    def main(cls) -> int:
        """Parse the Make boundary and return the exact child process status.

        ``full`` runs incremental then complete testmon execution. ``coverage``
        selects coverage alone; the default is the incremental operation. The
        ``slow`` operation runs the incremental phase over the slow marker
        only, as its own bounded process outside the budgeted clock. The
        ``file`` runs one complete declared target file in a bounded
        operation, including its slow tests; it requires the Make
        boundary to export the single-file target environment variable.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If unsupported pytest operation.

        """
        # Resolve public lazy exports after taking the entry clock.
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        slow_phase = mode == "full-slow"
        runner_module = importlib.import_module("flext_infra.validate.pytest_runner")
        if mode == "profile":
            profiler = cProfile.Profile()
            profiler.enable()
            try:
                profile = flext_infra.FlextInfraPytestProfile(Path(sys.argv[2]))
                status = profile.run_parent(
                    started_at_monotonic=cls._STARTED_AT_MONOTONIC,
                    profile=profiler,
                )
            finally:
                profiler.disable()
            return status

        slow_phase = mode == "slow"
        runner = flext_infra.FlextInfraPytestRunner.from_environment(
            started_at_monotonic=cls._STARTED_AT_MONOTONIC,
            slow_phase=slow_phase,
            unbounded=mode == "full",
        )
        if mode == "file" and runner.target_file is None:
            msg = (
                f"pytest operation {mode} requires the Make boundary to export "
                "the single-file target variable"
            )
            raise ValueError(msg)
        if mode == "coverage":
            status = runner.execute_coverage().unwrap()
        elif mode == "full":
            status = runner.execute_full().unwrap()
        elif mode in {"", "slow", "file"}:
            status = runner.execute().unwrap()
        else:
            msg = f"unsupported pytest operation: {mode}"
            raise ValueError(msg)
        return status


if __name__ == "__main__":
    raise SystemExit(FlextInfraPytestEntry.main())
