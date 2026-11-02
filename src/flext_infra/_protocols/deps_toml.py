# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/deps_toml
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDepsToml:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MemberRequirements(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[str, tuple[str | p.Infra.DependencyGroupInclude, ...]]: ...
        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def dependencies(self) -> Sequence[str]: ...
        @property
        def optional_dependencies(self) -> Mapping[str, Sequence[str]]: ...

    @runtime_checkable
    class SetOp(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["set"]: ...
        @property
        def key(self) -> str: ...
        @property
        def value(self) -> t.JsonValue: ...

    @runtime_checkable
    class ListOp(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["list"]: ...
        @property
        def key(self) -> str: ...
        @property
        def values(self) -> Sequence[str]: ...
        @property
        def strategy(self) -> c.Infra.TomlMergeMode: ...
        @property
        def sort(self) -> bool: ...

    @runtime_checkable
    class RemoveOp(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind(self) -> Literal["remove"]: ...
        @property
        def key(self) -> str: ...
        @property
        def table_path(self) -> Sequence[str]: ...

    @runtime_checkable
    class PhaseConfig(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str: ...
        @property
        def root_path(self) -> Sequence[str]: ...
        @property
        def table_path(self) -> Sequence[str]: ...
        @property
        def operations(
            self,
        ) -> Sequence[p.Infra.SetOp | p.Infra.ListOp | p.Infra.RemoveOp]: ...
        @property
        def nested_tables(self) -> Sequence[p.Infra.PhaseConfig]: ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToml",
]
