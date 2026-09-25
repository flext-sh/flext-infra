"""Declarative TOML phase models with a fluent builder for deps configuration sync.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal, Self

from flext_core import m
from flext_infra import c, t


class FlextInfraModelsDepsToml:
    """TOML operation models exposed through ``m.Infra.DepsToml``."""

    """Dependency-management model domains."""

    class DepsToml:
        """Declarative TOML sync model domain."""

        class SetOp(m.ContractModel):
            """Set one TOML key to one JSON-compatible value."""

            kind: Literal[c.Infra.TomlOperationKind.SET] = m.Field(
                c.Infra.TomlOperationKind.SET,
                description="Operation kind",
                validate_default=True,
            )
            key: str = m.Field(description="TOML key name")
            value: t.JsonValue = m.Field(description="JSON-compatible value")

        class ListOp(m.ContractModel):
            """Set or merge one TOML string list."""

            kind: Literal[c.Infra.TomlOperationKind.LIST] = m.Field(
                c.Infra.TomlOperationKind.LIST,
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

            kind: Literal[c.Infra.TomlOperationKind.REMOVE] = m.Field(
                c.Infra.TomlOperationKind.REMOVE,
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
                t.StrSequence, m.Field(description="Root path before table_path")
            ] = (c.Infra.TOOL,)
            table_path: Annotated[
                t.StrSequence, m.Field(description="Primary table path")
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

            class Builder(m.Identity["FlextInfraModelsDepsToml.DepsToml.PhaseConfig"]):
                """Fluent builder for ``m.Infra.DepsToml.PhaseConfig``."""

                def __init__(self, name: str) -> None:
                    super().__init__(
                        state=FlextInfraModelsDepsToml.DepsToml.PhaseConfig(name=name)
                    )

                def table(self, *path: str) -> Self:
                    """Select the primary table path below the root path."""
                    return self._path("table_path", *path)

                def value(self, key: str, value: t.JsonValue) -> Self:
                    """Schedule one scalar or structured value sync."""
                    return self._set(
                        operations=(
                            *self.state.operations,
                            FlextInfraModelsDepsToml.DepsToml.SetOp(
                                key=key, value=value
                            ),
                        )
                    )

                def list(
                    self,
                    key: str,
                    values: t.StrSequence,
                    *,
                    strategy: c.Infra.TomlMergeMode = c.Infra.TomlMergeMode.REPLACE,
                    sort: bool = True,
                ) -> Self:
                    """Schedule one string-list sync."""
                    return self._set(
                        operations=(
                            *self.state.operations,
                            FlextInfraModelsDepsToml.DepsToml.ListOp(
                                key=key,
                                values=tuple(values),
                                strategy=strategy,
                                sort=sort,
                            ),
                        )
                    )

                def deprecated(self, key: str, *sub_path: str) -> Self:
                    """Schedule the removal of one deprecated key."""
                    return self._set(
                        operations=(
                            *self.state.operations,
                            FlextInfraModelsDepsToml.DepsToml.RemoveOp(
                                key=key, table_path=sub_path
                            ),
                        )
                    )

                def nested(
                    self,
                    *path: str,
                    values: t.SequenceOf[t.Pair[str, t.JsonValue]] = (),
                    lists: t.SequenceOf[t.StrSequencePair] = (),
                    deprecated_keys: t.StrSequence = (),
                ) -> Self:
                    """Append one nested table phase built from inline operations."""
                    toml = FlextInfraModelsDepsToml.DepsToml
                    nested_table = toml.PhaseConfig(
                        name=self.state.name,
                        root_path=(),
                        table_path=path,
                        operations=(
                            *(toml.SetOp(key=key, value=item) for key, item in values),
                            *(
                                toml.ListOp(key=key, values=tuple(entries))
                                for key, entries in lists
                            ),
                            *(toml.RemoveOp(key=key) for key in deprecated_keys),
                        ),
                    )
                    return self._set(
                        nested_tables=(*self.state.nested_tables, nested_table)
                    )


__all__: list[str] = ["FlextInfraModelsDepsToml"]
