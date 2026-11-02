# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsDepsToml:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class SetOp(Protocol):
        """Structural data contract projected from the owning model."""

        kind: Literal["set"] = ...
        key: str = ...
        value: t.JsonValue = ...

    @runtime_checkable
    class ListOp(Protocol):
        """Structural data contract projected from the owning model."""

        kind: Literal["list"] = ...
        key: str = ...
        values: Sequence[str] = ...
        strategy: c.Infra.TomlMergeMode = ...
        sort: bool = ...

    @runtime_checkable
    class RemoveOp(Protocol):
        """Structural data contract projected from the owning model."""

        kind: Literal["remove"] = ...
        key: str = ...
        table_path: Sequence[str] = ...

    @runtime_checkable
    class PhaseConfig(Protocol):
        """Structural data contract projected from the owning model."""

        name: str = ...
        root_path: Sequence[str] = ...
        table_path: Sequence[str] = ...
        operations: Sequence[
            FlextInfraModelsDepsToml.DepsToml.SetOp
            | FlextInfraModelsDepsToml.DepsToml.ListOp
            | FlextInfraModelsDepsToml.DepsToml.RemoveOp
        ] = ...
        nested_tables: Sequence[FlextInfraModelsDepsToml.DepsToml.PhaseConfig] = ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToml",
]
