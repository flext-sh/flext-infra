"""Process entrypoint for the canonical centralized flext-infra CLI.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import u

from flext_infra import FlextInfraCli


class FlextInfraMain:
    """Facade for the flext-infra CLI process entrypoint."""

    @staticmethod
    def run() -> None:
        """Run the sole facade-backed CLI as the whole process."""
        u.Cli.process_main(FlextInfraCli.infra_main)


if __name__ == "__main__":
    FlextInfraMain.run()
