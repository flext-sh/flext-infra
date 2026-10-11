"""Source-live pytest entrypoint with a pre-import absolute clock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

<<<<<<< HEAD
=======
import cProfile
>>>>>>> upload-20261007
import sys
from pathlib import Path

<<<<<<< HEAD
from flext_infra._pytest_clock import FlextInfraPytestClock
from flext_infra._pytest_profile import FlextInfraPytestProfile
from flext_infra.validate import FlextInfraPytestRunner
=======
import flext_infra
>>>>>>> upload-20261007


class FlextInfraPytestEntry:
    """Facade for the pytest entrypoint with pre-import clock."""

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
<<<<<<< HEAD
        # The clock module captures startup before these runtime imports.
=======
        # Resolve public lazy exports after taking the entry clock.
>>>>>>> upload-20261007
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        if mode == "profile":
            profiler = FlextInfraPytestClock.profiler
            if profiler is None:
                msg = "pytest profile requires its pre-import profiler"
                raise RuntimeError(msg)
            try:
<<<<<<< HEAD
                profile = FlextInfraPytestProfile(Path(sys.argv[2]))
=======
                profile = flext_infra.FlextInfraPytestProfile(Path(sys.argv[2]))
>>>>>>> upload-20261007
                status = profile.run_parent(
                    started_at_monotonic=FlextInfraPytestClock.started_at_monotonic,
                    profile=profiler,
                )
            finally:
                profiler.disable()
            return status

        slow_phase = mode in {"slow", "full-slow", "file-slow"}
<<<<<<< HEAD
        runner = FlextInfraPytestRunner.from_environment(
            started_at_monotonic=FlextInfraPytestClock.started_at_monotonic,
=======
        runner = flext_infra.FlextInfraPytestRunner.from_environment(
            started_at_monotonic=cls._STARTED_AT_MONOTONIC,
>>>>>>> upload-20261007
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
