"""Source-live pytest entrypoint with a pre-import absolute clock."""

from __future__ import annotations

import sys
import time

_STARTED_AT_MONOTONIC = time.monotonic()


def main() -> int:
    """Parse the Make boundary and return the exact child process status."""
    from flext_infra.validate.pytest_runner import FlextInfraPytestRunner

    try:
        runner = FlextInfraPytestRunner.from_environment(
            started_at_monotonic=_STARTED_AT_MONOTONIC
        )
    except ValueError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 2
    result = runner.execute()
    if result.failure:
        sys.stderr.write(f"ERROR: {result.error or 'pytest runner failed'}\n")
        return 2
    return result.value


if __name__ == "__main__":
    raise SystemExit(main())
