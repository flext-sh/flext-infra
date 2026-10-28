"""Source-live pytest entrypoint with a pre-import absolute clock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import traceback
from itertools import islice
from pathlib import Path

import flext_infra
from flext_infra import c, settings
from flext_infra._pytest import FlextInfraPytestClock
from flext_infra.validate import FlextInfraPytestRunner


class FlextInfraPytestEntry:
    """Facade for the pytest entrypoint with pre-import clock."""

    @classmethod
    def main(cls) -> int:
        """Parse the Make boundary and return the exact child process status.

        ``global`` incrementally selects from FULL's entire inventory, under
        the same green-check prerequisite. ``full`` explicitly executes that
        complete inventory once without Testmon or a preceding incremental
        run. ``profile`` profiles the global incremental run.
        ``coverage`` selects coverage alone; the default remains the local
        incremental operation. The ``slow`` operation runs the incremental
        phase over the slow marker
        only, as its own process with an aggregate operation deadline. The
        ``file`` runs the complete declared target once without Testmon within
        the shared deadline, including slow items. ``file-slow`` retains its
        incremental operation. Both require Make to export the single-file target.
        ``full-slow`` runs the full slow phase without Testmon under that budget.
        The declared operation elects database participation before the runner
        reads any environment-based database location.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If unsupported pytest operation.

        """
        # The clock module captures startup before these runtime imports.
        mode = next(islice(sys.argv, 1, None), "")
        if mode == "profile":
            return cls._run_profile()

        match mode:
            case "full" | "full-slow" | "file":
                execution_mode = c.Infra.PytestExecutionMode.FULL
            case "coverage":
                execution_mode = c.Infra.PytestExecutionMode.COVERAGE
            case "global":
                execution_mode = c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
            case "" | "slow" | "file-slow":
                execution_mode = c.Infra.PytestExecutionMode.INCREMENTAL
            case _:
                msg = f"unsupported pytest operation: {mode}"
                raise ValueError(msg)
        slow_phase = mode in {"slow", "full-slow", "file-slow"}
        runner = FlextInfraPytestRunner.from_environment(
            started_at_monotonic=FlextInfraPytestClock.started_at_monotonic,
            profile_enabled=settings.Infra.profile,
            slow_phase=slow_phase,
            execution_mode=execution_mode,
        )
        if mode in {"file", "file-slow"} and runner.target_file is None:
            msg = (
                f"pytest operation {mode} requires the Make boundary to export "
                "the single-file target variable"
            )
            raise ValueError(msg)
        if mode == "coverage":
            status = runner.execute_coverage().unwrap()
        elif mode == "file":
            status = runner.execute_file().unwrap()
        elif mode in {"full", "full-slow"}:
            status = runner.execute_full().unwrap()
        elif mode == "global":
            status = runner.execute_global().unwrap()
        else:
            status = runner.execute().unwrap()
        return status

    @staticmethod
    def _run_profile() -> int:
        """Run the profiled parent while preserving its primary failure.

        Returns:
            The profiled parent's exact process status.

        Raises:
            RuntimeError: If profiling was not activated before runtime imports.

        """
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
            primary = sys.exception()
            try:
                profiler.disable()
            except BaseException as cleanup_failure:
                if primary is None or (
                    isinstance(primary, SystemExit)
                    and (primary.code is None or primary.code == 0)
                ):
                    raise
                primary.add_note(
                    "profile stop failed:\n"
                    + "".join(traceback.format_exception(cleanup_failure, chain=False))
                )
        return status


__all__ = ["FlextInfraPytestEntry"]

if __name__ == "__main__":
    raise SystemExit(FlextInfraPytestEntry.main())
