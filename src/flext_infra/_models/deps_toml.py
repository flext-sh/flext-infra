"""Declarative TOML phase models for dependency configuration synchronization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, Literal

from flext_cli import m

from flext_infra import c, t
from flext_infra._models._config.workspace import FlextInfraModelsConfigWorkspace


class FlextInfraModelsDepsToml:
    """TOML operation models exposed through ``m.Infra.DepsToml``."""

    """Dependency-management model domains."""

    class DepsToml:
        """Declarative TOML sync model domain."""

        class MemberRequirements(
            FlextInfraModelsConfigWorkspace.DependencyGroupDeclarations
        ):
            """Typed dependency declarations needed to provision one member."""

            name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Declared distribution identity"),
            ]
            dependencies: Annotated[
                Sequence[str],
                m.Field(description="Production requirement lines"),
            ]
            optional_dependencies: Annotated[
                Mapping[str, Sequence[str]],
                m.Field(description="Every declared optional requirement group"),
            ]

        class SetOp(m.ContractModel, str_strip_whitespace=False):
            """Set one TOML key to one JSON-compatible value."""

            kind: Annotated[
                Literal["set"],
                m.Field(description="Operation kind", validate_default=True),
            ] = "set"
            key: str = m.Field(description="TOML key name")
            value: t.JsonValue = m.Field(description="JSON-compatible value")

        class ListOp(m.ContractModel, str_strip_whitespace=False):
            """Set or merge one TOML string list."""

            kind: Annotated[
                Literal["list"],
                m.Field(description="Operation kind", validate_default=True),
            ] = "list"
            key: str = m.Field(description="TOML key name")
            values: Sequence[str] = m.Field(description="Expected values")
            strategy: Annotated[
                c.Infra.TomlMergeMode,
                m.Field(description="Merge strategy", validate_default=True),
            ] = c.Infra.TomlMergeMode.REPLACE
            sort: Annotated[
                bool,
                m.Field(description="Sort values before sync", validate_default=True),
            ] = True

        class RemoveOp(m.ContractModel):
            """Remove one TOML key, optionally from a nested relative table."""

            kind: Annotated[
                Literal["remove"],
                m.Field(description="Operation kind", validate_default=True),
            ] = "remove"
            key: str = m.Field(description="Key to remove")
            table_path: Annotated[
                Sequence[str],
                m.Field(description="Relative sub-table path", validate_default=True),
            ] = ()

        class PhaseConfig(m.ContractModel):
            """Declarative TOML phase with inline Builder DSL."""

            name: str = m.Field(description="Phase name")
            root_path: Annotated[
                Sequence[str],
                m.Field(description="Root path before table_path"),
            ] = (c.Infra.TOOL,)
            table_path: Annotated[
                Sequence[str],
                m.Field(description="Primary table path"),
            ] = ()
            operations: Annotated[
                Sequence[
                    Annotated[
                        FlextInfraModelsDepsToml.DepsToml.SetOp
                        | FlextInfraModelsDepsToml.DepsToml.ListOp
                        | FlextInfraModelsDepsToml.DepsToml.RemoveOp,
                        m.Field(discriminator="kind"),
                    ]
                ],
                m.Field(description="Declarative TOML operations"),
            ] = ()
            nested_tables: Annotated[
                Sequence[FlextInfraModelsDepsToml.DepsToml.PhaseConfig],
                m.Field(description="Nested TOML phase configs"),
            ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToml"]
