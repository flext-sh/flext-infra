"""Source-live pytest entrypoint with a pre-import absolute clock."""

from __future__ import annotations

import sys
import time

_STARTED_AT_MONOTONIC = time.monotonic()


def main() -> int:
    """Parse the Make boundary and return the exact child process status.

    ``coverage`` selects the coverage-only pass (never testmon); the default is
    the persistent-testmon pass (never the cov plugin).
    """
    from flext_infra.validate.pytest_runner import FlextInfraPytestRunner

    runner = FlextInfraPytestRunner.from_environment(
        started_at_monotonic=_STARTED_AT_MONOTONIC
    )
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "coverage":
        return runner.execute_coverage().unwrap()
    return runner.execute().unwrap()


if __name__ == "__main__":
    raise SystemExit(main())
