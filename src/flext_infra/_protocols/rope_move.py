# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/rope_move
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsRopeMove:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ClassMoveRequest(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.PositiveInt
        rope_project: t.Infra.RopeProject
        source_file: Path
        target_file: Path
        class_name: t.NonEmptyStr
        apply: bool

    @runtime_checkable
    class ResolvedClassMove(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def request(self) -> p.Infra.ClassMoveRequest: ...
        @property
        def declaration(self) -> t.Infra.RopePyName: ...
        @property
        def origin_module(self) -> str: ...
        @property
        def target_module(self) -> str: ...


__all__: list[str] = [
    "FlextInfraProtocolsRopeMove",
]
