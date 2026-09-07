"""Source-live pytest entrypoint with a pre-import absolute clock."""

from __future__ import annotations

import time

_STARTED_AT_MONOTONIC = time.monotonic()


def main() -> int:
    """Parse the Make boundary and return the exact child process status."""
    from flext_infra.validate.pytest_runner import FlextInfraPytestRunner

    runner = FlextInfraPytestRunner.from_environment(
        started_at_monotonic=_STARTED_AT_MONOTONIC
    )
    return runner.execute().unwrap()


if __name__ == "__main__":
    raise SystemExit(main())
