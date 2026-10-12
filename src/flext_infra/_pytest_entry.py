"""Source-live pytest entrypoint with a pre-import absolute clock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import flext_infra
from flext_infra._pytest_clock import FlextInfraPytestClock


class FlextInfraPytestEntry:
    """Facade for the pytest entrypoint with pre-import clock."""

    @classmethod
    def main(cls) -> int:
        """Parse the Make boundary and return the exact child process status.

        ``full`` runs incremental then complete testmon execution. ``coverage``
        selects coverage alone; the default is the incremental operation. The
        ``slow`` operation runs the incremental phase over the slow marker
        only, as its own bounded process outside the budgeted clock. The
        ``file`` and ``file-slow`` run the declared target's regular and slow
        phases. Both require Make to export the single-file target variable.
        ``full-slow`` runs the full slow phase without the incremental budget.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If unsupported pytest operation.
            RuntimeError: If profiling was not activated before runtime imports.

        """
        # The clock module captures startup before these runtime imports.
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        if mode == "profile":
            profiler = FlextInfraPytestClock.profiler
            if profiler is None:
                msg = "pytest profile requires its pre-import profiler"
                raise RuntimeError(msg)
            try:
                profile = flext_infra.FlextInfraPytestProfile(Path(sys.argv[2]))
                status = profile.run_parent(
                    started_at_monotonic=FlextInfraPytestClock.started_at_monotonic,
                    profile=profiler,
                )
            finally:
                profiler.disable()
            return status

        slow_phase = mode in {"slow", "full-slow", "file-slow"}
        runner = flext_infra.FlextInfraPytestRunner.from_environment(
            started_at_monotonic=FlextInfraPytestClock.started_at_monotonic,
            slow_phase=slow_phase,
            unbounded=mode in {"full", "full-slow"},
        )
        if mode in {"file", "file-slow"} and runner.target_file is None:
            msg = (
                f"pytest operation {mode} requires the Make boundary to export "
                "the single-file target variable"
            )
            raise ValueError(msg)
        if mode == "coverage":
            status = runner.execute_coverage().unwrap()
        elif mode in {"full", "full-slow"}:
            status = runner.execute_full().unwrap()
        elif mode in {"", "slow", "file", "file-slow"}:
            status = runner.execute().unwrap()
        else:
            msg = f"unsupported pytest operation: {mode}"
            raise ValueError(msg)
        return status


if __name__ == "__main__":
    raise SystemExit(FlextInfraPytestEntry.main())
