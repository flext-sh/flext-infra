# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/mise_toolchain_repair
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsMiseToolchainRepair:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MiseToolchainRepairPlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository owning the declaration and lock."""
            ...

        @property
        def tool(self) -> t.NonEmptyStr:
            """Declared native backend selector."""
            ...

        @property
        def mise_executable(self) -> Path:
            """Qualified self-managed Mise executable."""
            ...

        @property
        def uv_executable(self) -> Path:
            """Qualified UV executable for the complete proof."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsMiseToolchainRepair",
]
