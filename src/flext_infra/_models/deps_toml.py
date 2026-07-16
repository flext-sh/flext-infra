"""TOML phase models with Builder DSL for deps configuration sync.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import chain
from typing import Annotated, Literal, Self

from flext_cli import m, t

from flext_infra._constants.base import FlextInfraConstantsBase


class FlextInfraModelsDepsToml:
    """TOML operation models exposed FLAT through ``m.Infra.Toml*``."""

    class TomlSetOp(m.ContractModel):
        """Set one TOML key to one JSON-compatible value."""

        kind: Literal[FlextInfraConstantsBase.TomlOperationKind.SET] = m.Field(
            FlextInfraConstantsBase.TomlOperationKind.SET,
            description="Operation kind",
            validate_default=True,
        )
        key: str = m.Field(description="TOML key name")
        value: t.JsonValue = m.Field(description="JSON-compatible value")

    class TomlListOp(m.ContractModel):
        """Set or merge one TOML string list."""

        kind: Literal[FlextInfraConstantsBase.TomlOperationKind.LIST] = m.Field(
            FlextInfraConstantsBase.TomlOperationKind.LIST,
            description="Operation kind",
            validate_default=True,
        )
        key: str = m.Field(description="TOML key name")
        values: t.StrSequence = m.Field(description="Expected values")
        strategy: Annotated[
            FlextInfraConstantsBase.TomlMergeMode,
            m.Field(description="Merge strategy", validate_default=True),
        ] = FlextInfraConstantsBase.TomlMergeMode.REPLACE
        sort: Annotated[
            bool,
            m.Field(
                description="Sort values before sync", validate_default=True
            ),
        ] = True

    class TomlRemoveOp(m.ContractModel):
        """Remove one TOML key, optionally from a nested relative table."""

        kind: Literal[FlextInfraConstantsBase.TomlOperationKind.REMOVE] = m.Field(
            FlextInfraConstantsBase.TomlOperationKind.REMOVE,
            description="Operation kind",
            validate_default=True,
        )
        key: str = m.Field(description="Key to remove")
        table_path: Annotated[
            t.StrSequence,
            m.Field(
                description="Relative sub-table path", validate_default=True
            ),
        ] = ()

    type TomlOperation = Annotated[
        TomlSetOp | TomlListOp | TomlRemoveOp, m.Field(discriminator="kind")
    ]

    class TomlPhaseConfig(m.ContractModel):
        """Declarative TOML phase with inline Builder DSL."""

        name: str = m.Field(description="Phase name")
        root_path: Annotated[
            t.StrSequence, m.Field(description="Root path before table_path")
        ] = (FlextInfraConstantsBase.TOOL,)
        table_path: Annotated[
            t.StrSequence, m.Field(description="Primary table path")
        ] = ()
        operations: Annotated[
            t.SequenceOf[FlextInfraModelsDepsToml.TomlOperation],
            m.Field(description="Declarative TOML operations"),
        ] = ()
        nested_tables: Annotated[
            t.SequenceOf[FlextInfraModelsDepsToml.TomlPhaseConfig],
            m.Field(description="Nested TOML phase configs"),
        ] = ()
        custom_handler: Annotated[
            Callable[..., t.StrSequence] | None,
            m.Field(exclude=True, description="Custom handler"),
        ] = None

        class Builder(
            m.Builder.Identity["FlextInfraModelsDepsToml.TomlPhaseConfig"]
        ):
            """Fluent builder for ``m.Infra.TomlPhaseConfig``."""

            def __init__(self, name: str) -> None:
                super().__init__(
                    state=FlextInfraModelsDepsToml.TomlPhaseConfig(
                        name=name
                    )
                )

            @classmethod
            def _nested_operations(
                cls,
                *,
                values: t.SequenceOf[tuple[str, t.JsonValue]] = (),
                lists: t.SequenceOf[t.StrSequencePair] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> tuple[FlextInfraModelsDepsToml.TomlOperation, ...]:
                """Nested operations."""
                return tuple(
                    chain(
                        (
                            FlextInfraModelsDepsToml.TomlSetOp(
                                key=key, value=value
                            )
                            for key, value in values
                        ),
                        (
                            FlextInfraModelsDepsToml.TomlListOp(
                                key=key, values=tuple(entries)
                            )
                            for key, entries in lists
                        ),
                        (
                            FlextInfraModelsDepsToml.TomlRemoveOp(key=key)
                            for key in deprecated_keys
                        ),
                    )
                )

            def operation(
                self,
                operation_type: type[m.ContractModel],
                /,
                **data: t.JsonValue
                | t.JsonPayload
                | t.SequenceOf[t.JsonPayload],
            ) -> Self:
                """Operation."""
                operation_item = operation_type.model_validate(data)
                replaced: Self = self._replace(
                    self.state.model_copy(
                        update={
                            "operations": (
                                *self.state.operations,
                                operation_item,
                            )
                        }
                    )
                )
                return replaced

            def root(self, *path: str) -> Self:
                """Root."""
                result: Self = self._path("root_path", *path)
                return result

            def table(self, *path: str) -> Self:
                """Table."""
                result: Self = self._path("table_path", *path)
                return result

            def value(self, key: str, value: t.JsonValue) -> Self:
                """Value."""
                return self.operation(
                    FlextInfraModelsDepsToml.TomlSetOp,
                    key=key,
                    value=value,
                )

            def list(
                self,
                key: str,
                values: t.StrSequence,
                *,
                strategy: FlextInfraConstantsBase.TomlMergeMode = FlextInfraConstantsBase.TomlMergeMode.REPLACE,
                sort: bool = True,
            ) -> Self:
                """List."""
                return self.operation(
                    FlextInfraModelsDepsToml.TomlListOp,
                    key=key,
                    values=tuple(values),
                    strategy=strategy,
                    sort=sort,
                )

            def deprecated(self, key: str, *sub_path: str) -> Self:
                """Mark a key as deprecated by scheduling its removal."""
                return self.operation(
                    FlextInfraModelsDepsToml.TomlRemoveOp,
                    key=key,
                    table_path=tuple(sub_path),
                )

            def nested(
                self,
                *path: str,
                values: t.SequenceOf[tuple[str, t.JsonValue]] = (),
                lists: t.SequenceOf[t.StrSequencePair] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> Self:
                """Nested."""
                nested_table = FlextInfraModelsDepsToml.TomlPhaseConfig(
                    name=self.state.name,
                    root_path=(),
                    table_path=tuple(path),
                    operations=tuple(
                        self._nested_operations(
                            values=values,
                            lists=lists,
                            deprecated_keys=deprecated_keys,
                        )
                    ),
                )
                replaced: Self = self._replace(
                    self.state.model_copy(
                        update={
                            "nested_tables": (
                                *self.state.nested_tables,
                                nested_table,
                            )
                        }
                    )
                )
                return replaced

            def handler(self, fn: Callable[..., t.StrSequence]) -> Self:
                """Set a custom handler function."""
                replaced: Self = self._replace(
                    self.state.model_copy(update={"custom_handler": fn})
                )
                return replaced


__all__: list[str] = ["FlextInfraModelsDepsToml"]
