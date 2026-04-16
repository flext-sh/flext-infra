"""TOML phase engine models with Builder DSL.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import chain
from typing import Annotated, Literal, Self

from flext_core import m
from flext_infra import c, t


class FlextInfraModelsEngine:
    """Engine models accessible via ``m.Infra.*``."""

    class TomlSetOp(m.ContractModel):
        """Set one TOML key to one JSON-compatible value."""

        kind: Annotated[Literal["set"], m.Field(description="Operation kind")] = "set"
        key: str = m.Field(description="TOML key name")
        value: t.Cli.JsonValue = m.Field(description="JSON-compatible value")

    class TomlListOp(m.ContractModel):
        """Set or merge one TOML string list."""

        kind: Annotated[Literal["list"], m.Field(description="Operation kind")] = "list"
        key: str = m.Field(description="TOML key name")
        values: t.StrSequence = m.Field(description="Expected values")
        strategy: Annotated[
            str,
            m.Field(
                description="Merge strategy",
            ),
        ] = c.Infra.TOML_MERGE_REPLACE
        sort: Annotated[bool, m.Field(description="Sort values before sync")] = True

    class TomlRemoveOp(m.ContractModel):
        """Remove one TOML key, optionally from a nested relative table."""

        kind: Annotated[Literal["remove"], m.Field(description="Operation kind")] = (
            "remove"
        )
        key: str = m.Field(description="Key to remove")
        table_path: Annotated[
            t.StrSequence,
            m.Field(
                description="Relative sub-table path",
            ),
        ] = ()

    type TomlOperation = Annotated[
        TomlSetOp | TomlListOp | TomlRemoveOp,
        m.Field(discriminator="kind"),
    ]

    class TomlPhaseConfig(m.ContractModel):
        """Declarative TOML phase with inline Builder DSL."""

        name: str = m.Field(description="Phase name")
        root_path: Annotated[
            t.StrSequence,
            m.Field(
                description="Root path before table_path",
            ),
        ] = (c.Infra.TOOL,)
        table_path: Annotated[
            t.StrSequence, m.Field(description="Primary table path")
        ] = ()
        operations: Annotated[
            Sequence[FlextInfraModelsEngine.TomlOperation],
            m.Field(
                description="Declarative TOML operations",
            ),
        ] = ()
        nested_tables: Annotated[
            Sequence[FlextInfraModelsEngine.TomlPhaseConfig],
            m.Field(description="Nested TOML phase configs"),
        ] = ()
        custom_handler: Annotated[
            Callable[..., t.StrSequence] | None,
            m.Field(
                exclude=True,
                description="Custom handler",
            ),
        ] = None

        class Builder(m.Builder.Identity["FlextInfraModelsEngine.TomlPhaseConfig"]):
            """Fluent builder — ``m.Infra.TomlPhaseConfig.Builder("ruff").table(...).build()``."""

            def __init__(self, name: str) -> None:
                super().__init__(
                    state=FlextInfraModelsEngine.TomlPhaseConfig(name=name)
                )

            @classmethod
            def _nested_operations(
                cls,
                *,
                values: Sequence[tuple[str, t.Cli.JsonValue]] = (),
                lists: Sequence[tuple[str, t.StrSequence]] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> tuple[FlextInfraModelsEngine.TomlOperation, ...]:
                return tuple(
                    chain(
                        (
                            cls._model(
                                FlextInfraModelsEngine.TomlSetOp, key=key, value=value
                            )
                            for key, value in values
                        ),
                        (
                            cls._model(
                                FlextInfraModelsEngine.TomlListOp,
                                key=key,
                                values=tuple(entries),
                            )
                            for key, entries in lists
                        ),
                        (
                            cls._model(FlextInfraModelsEngine.TomlRemoveOp, key=key)
                            for key in deprecated_keys
                        ),
                    ),
                )

            def _operation(
                self,
                operation_type: type[m.ContractModel],
                /,
                **data: t.ValueOrModel | t.RecursiveContainer,
            ) -> Self:
                return self._append_model("operations", operation_type, **data)

            def root(self, *path: str) -> Self:
                return self._path("root_path", *path)

            def table(self, *path: str) -> Self:
                return self._path("table_path", *path)

            def value(self, key: str, value: t.Cli.JsonValue) -> Self:
                return self._operation(
                    FlextInfraModelsEngine.TomlSetOp, key=key, value=value
                )

            def list(
                self,
                key: str,
                values: t.StrSequence,
                *,
                strategy: str = c.Infra.TOML_MERGE_REPLACE,
                sort: bool = True,
            ) -> Self:
                return self._operation(
                    FlextInfraModelsEngine.TomlListOp,
                    key=key,
                    values=tuple(values),
                    strategy=strategy,
                    sort=sort,
                )

            def deprecated(self, key: str, *sub_path: str) -> Self:
                return self._operation(
                    FlextInfraModelsEngine.TomlRemoveOp,
                    key=key,
                    table_path=tuple(sub_path),
                )

            def nested(
                self,
                *path: str,
                values: Sequence[tuple[str, t.Cli.JsonValue]] = (),
                lists: Sequence[tuple[str, t.StrSequence]] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> Self:
                nested_operations = tuple(
                    op.model_dump(mode="python")
                    for op in self._nested_operations(
                        values=values,
                        lists=lists,
                        deprecated_keys=deprecated_keys,
                    )
                )
                return self._append_model(
                    "nested_tables",
                    FlextInfraModelsEngine.TomlPhaseConfig,
                    name=self.state.name,
                    root_path=(),
                    table_path=tuple(path),
                    operations=nested_operations,
                )

            def handler(self, fn: Callable[..., t.StrSequence]) -> Self:
                return self._replace(
                    self.state.model_copy(update={"custom_handler": fn})
                )


__all__: list[str] = ["FlextInfraModelsEngine"]
