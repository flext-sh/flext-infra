"""Profile the canonical infrastructure CLI and preserve its native outcome.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import signal
import sys
import traceback
from pathlib import Path
from uuid import uuid4

import flext_infra
from flext_infra._pytest_clock import FlextInfraPytestClock


class FlextInfraProfileEntry:
    """Own the profiler lifetime around the existing CLI composition root."""

    @staticmethod
    def run() -> int:
        """Retain the profile even when the CLI raises or is interrupted.

        Signal checkpoints update the elected report input and preserve the
        previous artifact. They describe work up to interruption, not success.

        Returns:
            The canonical CLI exit status.

        """
        output = Path(sys.argv[1])
        immutable_output = output.with_stem(f"{output.stem}-{uuid4().hex}")
        previous_output = output.with_stem(f"{output.stem}.previous-{uuid4().hex}")
        profiler = cProfile.Profile()
        previous = signal.getsignal(signal.SIGTERM)
        status: int | None = None

        FlextInfraPytestClock.register_signal_checkpoint(
            profiler,
            output,
            immutable_output=immutable_output.with_suffix(".checkpoint.pstats"),
            previous_output=previous_output.with_suffix(".checkpoint.pstats"),
        )
        profiler.enable()
        try:
            status = flext_infra.main(sys.argv[2:])
            return status
        finally:
            profiler.disable()
            signal.signal(signal.SIGTERM, previous)
            primary = sys.exception() if status is None else None
            try:
                FlextInfraPytestClock.publish_profile(
                    profiler,
                    output,
                    immutable_output=immutable_output,
                    previous_output=previous_output,
                )
            except BaseException as publication_failure:
                if primary is not None:
                    primary.add_note(
                        "profile publication failed:\n"
                        + "".join(
                            traceback.format_exception(publication_failure, chain=False)
                        )
                    )
                elif status:
                    traceback.print_exception(publication_failure)
                else:
                    raise


if __name__ == "__main__":
    raise SystemExit(FlextInfraProfileEntry.run())
