"""Source-live pytest entrypoint for the generated Make test recipes.

The generated member Makefiles invoke ``python -m flext_infra._pytest_entry``
under a pre-import absolute clock; the execution logic is owned by
:class:`FlextInfraPytestEntry` and this module is its ``-m`` boundary only.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time

from flext_infra.validate import FlextInfraPytestRunner

_STARTED_AT_MONOTONIC = time.monotonic()


def main() -> int:
    """Parse the Make boundary and return the exact child process status.

    Returns:
        The exit status of the child process.

    """
    try:
        runner = FlextInfraPytestRunner.from_environment(
            started_at_monotonic=_STARTED_AT_MONOTONIC,
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
