"""CLI entrypoint for the canonical flext-infra command surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from flext_infra import FlextInfraPytestClock, c, settings
from flext_infra.services import FlextInfraCliDispatchService
from flext_infra.validate import FlextInfraCProfileReport


class FlextInfraCli(FlextInfraCliDispatchService):
    """Single CLI entry surface for every flext-infra command group."""

    @staticmethod
    def docs_main(args: Sequence[str] | None = None) -> int:
        """Run the docs group directly (``flext-docs`` == ``flext-infra docs``).

        Returns:
            The resulting ``int``.

        """
        cli_args = list(args) if args is not None else sys.argv[1:]
        return FlextInfraCli().main([c.Infra.CLI_GROUP_DOCS, *cli_args])

    @staticmethod
    def infra_main(args: Sequence[str] | None = None) -> int:
        """Run the canonical flext-infra CLI (console script ``flext-infra``).

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If FLEXT_INFRA_PROFILE requires FLEXT_INFRA_PROFILE_OUTPUT.

        """
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not settings.Infra.profile:
            return FlextInfraCli().main(cli_args)
        output = settings.Infra.profile_output
        if output is None:
            msg = "FLEXT_INFRA_PROFILE requires FLEXT_INFRA_PROFILE_OUTPUT"
            raise ValueError(msg)
        return FlextInfraPytestClock.profile_command(
            lambda: FlextInfraCli().main(cli_args),
            output,
            after_profile=FlextInfraCProfileReport.report_capture,
        )


__all__: list[str] = ["FlextInfraCli"]
