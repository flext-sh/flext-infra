# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsRopeMove:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ResolvedClassMove(Protocol):
        """Structural data contract projected from the owning model."""

        request: FlextInfraModelsRopeMove.ClassMoveRequest
        declaration: t.Port[t.Infra.RopePyName]
        origin_module: str
        target_module: str


__all__: list[str] = [
    "FlextInfraProtocolsRopeMove",
]
