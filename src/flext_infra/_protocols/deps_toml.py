# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_toml
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols._config import FlextInfraProtocolsConfigWorkspace

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._constants import FlextInfraConstantsBase


class FlextInfraProtocolsDepsToml:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MemberRequirements(
        FlextInfraProtocolsConfigWorkspace.DependencyGroupDeclarations, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Declared distribution identity."""
            ...

        @property
        def dependencies(self) -> Sequence[str]:
            """Production requirement lines."""
            ...

        @property
        def optional_dependencies(self) -> Mapping[str, Sequence[str]]:
            """Every declared optional requirement group."""
            ...

    @runtime_checkable
    class SetOp(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["set"]:
            """Operation kind."""
            ...

        @property
        def key(self) -> str:
            """TOML key name."""
            ...

        @property
        def value(self) -> t.JsonValue:
            """JSON-compatible value."""
            ...

    @runtime_checkable
    class ListOp(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["list"]:
            """Operation kind."""
            ...

        @property
        def key(self) -> str:
            """TOML key name."""
            ...

        @property
        def values(self) -> Sequence[str]:
            """Expected values."""
            ...

        @property
        def strategy(self) -> FlextInfraConstantsBase.TomlMergeMode:
            """Merge strategy."""
            ...

        @property
        def sort(self) -> bool:
            """Sort values before sync."""
            ...

    @runtime_checkable
    class RemoveOp(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["remove"]:
            """Operation kind."""
            ...

        @property
        def key(self) -> str:
            """Key to remove."""
            ...

        @property
        def table_path(self) -> Sequence[str]:
            """Relative sub-table path."""
            ...

    @runtime_checkable
    class PhaseConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Phase name."""
            ...

        @property
        def root_path(self) -> Sequence[str]:
            """Root path before table_path."""
            ...

        @property
        def table_path(self) -> Sequence[str]:
            """Primary table path."""
            ...

        @property
        def operations(
            self,
        ) -> Sequence[
            FlextInfraProtocolsDepsToml.SetOp
            | FlextInfraProtocolsDepsToml.ListOp
            | FlextInfraProtocolsDepsToml.RemoveOp
        ]:
            """Declarative TOML operations."""
            ...

        @property
        def nested_tables(self) -> Sequence[FlextInfraProtocolsDepsToml.PhaseConfig]:
            """Nested TOML phase configs."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToml",
]
