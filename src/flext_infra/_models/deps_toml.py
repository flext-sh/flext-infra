"""Declarative TOML phase models for dependency configuration synchronization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal

from flext_cli import m

from flext_infra import c, t


class FlextInfraModelsDepsToml:
    """TOML operation models exposed through ``m.Infra.DepsToml``."""

    """Dependency-management model domains."""

    class DepsToml:
        """Declarative TOML sync model domain."""

        class GroupInclude(m.ContractModel):
            """One PEP 735 reference to another dependency group."""

            include_group: Annotated[
                t.NonEmptyStr,
                m.Field(alias="include-group", description="Referenced group name"),
            ]

        class MemberRequirements(m.ContractModel):
            """Typed dependency declarations needed to provision one member."""

            name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Declared distribution identity"),
            ]
            dependencies: Annotated[
                t.StrTuple,
                m.Field(description="Production requirement lines"),
            ]
            optional_dependencies: Annotated[
                t.MappingKV[str, t.StrTuple],
                m.Field(description="Every declared optional requirement group"),
            ]
            dependency_groups: Annotated[
                t.MappingKV[
                    str,
                    t.VariadicTuple[
                        str | FlextInfraModelsDepsToml.DepsToml.GroupInclude
                    ],
                ],
                m.Field(description="PEP 735 requirement and inclusion entries"),
            ]

            @m.field_validator("dependency_groups")
            @classmethod
            def declared_group_references(
                cls,
                groups: t.MappingKV[
                    str,
                    t.VariadicTuple[
                        str | FlextInfraModelsDepsToml.DepsToml.GroupInclude
                    ],
                ],
            ) -> t.MappingKV[
                str,
                t.VariadicTuple[str | FlextInfraModelsDepsToml.DepsToml.GroupInclude],
            ]:
                """Require every inclusion to name a declared group.

                Returns:
                    The validated dependency groups.

                Raises:
                    ValueError: If an inclusion names an undeclared group.
                """
                for name, entries in groups.items():
                    if any(
                        not isinstance(entry, str) and entry.include_group not in groups
                        for entry in entries
                    ):
                        message = f"invalid member dependency group {name}"
                        raise ValueError(message)
                return groups

        class SetOp(m.ContractModel):
            """Set one TOML key to one JSON-compatible value."""

            kind: Literal["set"] = m.Field(
                "set",
                description="Operation kind",
                validate_default=True,
            )
            key: str = m.Field(description="TOML key name")
            value: t.JsonValue = m.Field(description="JSON-compatible value")

        class ListOp(m.ContractModel):
            """Set or merge one TOML string list."""

            kind: Literal["list"] = m.Field(
                "list",
                description="Operation kind",
                validate_default=True,
            )
            key: str = m.Field(description="TOML key name")
            values: t.StrSequence = m.Field(description="Expected values")
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

            kind: Literal["remove"] = m.Field(
                "remove",
                description="Operation kind",
                validate_default=True,
            )
            key: str = m.Field(description="Key to remove")
            table_path: Annotated[
                t.StrSequence,
                m.Field(description="Relative sub-table path", validate_default=True),
            ] = ()

        class PhaseConfig(m.ContractModel):
            """Declarative TOML phase with inline Builder DSL."""

            name: str = m.Field(description="Phase name")
            root_path: Annotated[
                t.StrSequence,
                m.Field(description="Root path before table_path"),
            ] = (c.Infra.TOOL,)
            table_path: Annotated[
                t.StrSequence,
                m.Field(description="Primary table path"),
            ] = ()
            operations: Annotated[
                t.SequenceOf[
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
                t.SequenceOf[FlextInfraModelsDepsToml.DepsToml.PhaseConfig],
                m.Field(description="Nested TOML phase configs"),
            ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToml"]
