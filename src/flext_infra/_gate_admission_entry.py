"""Host-wide heavy-gate admission entrypoint for the generated Make recipes.

The generated Makefiles invoke ``python -m flext_infra._gate_admission_entry
<gate> -- <command...>`` before a heavy gate's budgeted command (FLEXT
ADR-032); the admission logic is owned by ``u.Infra`` and this module is its
``-m`` boundary only.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra._utilities.gate_admission import FlextInfraUtilitiesGateAdmission


def main() -> int:
    """Parse the Make boundary and return the admitted command's exact status.

    Returns:
        The exit status of the admitted command.

    """
    arguments = sys.argv[1:]
    if len(arguments) < 3 or arguments[1] != "--":
        sys.stderr.write(
            "usage: python -m flext_infra._gate_admission_entry <gate> -- <command...>\n"
        )
        return 2
    return FlextInfraUtilitiesGateAdmission.gate_admission_run(arguments[0], Path.cwd(), arguments[2:])


if __name__ == "__main__":
    sys.exit(main())
