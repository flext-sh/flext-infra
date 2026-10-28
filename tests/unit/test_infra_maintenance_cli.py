"""CLI contract tests for maintenance entry point.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraCli
from tests import tm


class TestsFlextInfraInfraMaintenanceCli:
    """Behavior contract for test_infra_maintenance_cli."""

    @staticmethod
    def _run_maintenance(argv: Sequence[str] | None = None) -> int:
        args = ["maintenance"]
        if argv is not None:
            args.extend(argv)
        return FlextInfraCli.infra_main(args)

    def test_maintenance_rejects_apply_flag(self) -> None:
        """Test maintenance rejects apply flag."""
        tm.that(self._run_maintenance(["--apply"]), eq=2)
