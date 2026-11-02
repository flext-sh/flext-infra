# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/mise_toolchain_repair
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import t


class FlextInfraProtocolsMiseToolchainRepair:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MiseToolchainRepairPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def tool(self) -> t.NonEmptyStr: ...
        @property
        def mise_executable(self) -> Path: ...
        @property
        def uv_executable(self) -> Path: ...


__all__: list[str] = [
    "FlextInfraProtocolsMiseToolchainRepair",
]
