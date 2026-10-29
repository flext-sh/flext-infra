"""Pyproject modernizer base joining its responsibility classes via MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

from flext_infra import p, r
from flext_infra.deps._modernizer import FlextInfraPyprojectModernizerRun


class FlextInfraPyprojectModernizerBase(
    FlextInfraPyprojectModernizerRun,
):
    """Modernize workspace pyproject.toml files to the canonical format."""

    @override
    def execute(self) -> p.Result[bool]:
        """Execute pyproject modernization for the configured workspace.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if self.run() != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraPyprojectModernizerBase"]
