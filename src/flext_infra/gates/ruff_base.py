"""Shared Ruff gate surface — cache isolation owned once.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

from flext_infra import c, m, u
from flext_infra.gates import FlextInfraGates


class FlextInfraGatesRuffGate(FlextInfraGates):
    """Own the environment facts every Ruff-backed gate shares."""

    @override
    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Mapping[str, str]:
        """Keep native cache writes outside authenticated source candidates.

        Returns:
            The resulting ``Mapping[str, str]``.

        """
        return {
            **(super()._check_env(project_dir, ctx) or {}),
            c.Infra.RUFF_CACHE_ENVIRONMENT_VARIABLE: str(
                u.Infra.ruff_cache_directory(project_dir)
            ),
        }


__all__: list[str] = ["FlextInfraGatesRuffGate"]
