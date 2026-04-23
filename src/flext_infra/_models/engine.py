"""TOML phase engine models with Builder DSL.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from itertools import chain
from typing import Annotated, Self

from flext_cli import m

from flext_infra import FlextInfraModelsEngineOperation, c, t


class FlextInfraModelsEngine(FlextInfraModelsEngineOperation):
    """Engine models accessible via ``m.Infra.*``."""

    type TomlOperation = Annotated[
        FlextInfraModelsEngineOperation.TomlSetOp
        | FlextInfraModelsEngineOperation.TomlListOp
        | FlextInfraModelsEngineOperation.TomlRemoveOp,
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
                values: Sequence[tuple[str, t.JsonValue]] = (),
                lists: Sequence[tuple[str, t.StrSequence]] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> tuple[FlextInfraModelsEngine.TomlOperation, ...]:
                return tuple(
                    chain(
                        (
                            FlextInfraModelsEngine.TomlSetOp.model_validate({
                                "key": key,
                                "value": value,
                            })
                            for key, value in values
                        ),
                        (
                            FlextInfraModelsEngine.TomlListOp.model_validate({
                                "key": key,
                                "values": tuple(entries),
                            })
                            for key, entries in lists
                        ),
                        (
                            FlextInfraModelsEngine.TomlRemoveOp.model_validate({
                                "key": key
                            })
                            for key in deprecated_keys
                        ),
                    ),
                )

            def _operation(
                self,
                operation_type: type[m.ContractModel],
                /,
                **data: t.JsonValue | t.RuntimeData | Sequence[t.RuntimeData],
            ) -> Self:
                operation_item = operation_type.model_validate(data)
                return self._replace(
                    self.state.model_copy(
                        update={
                            "operations": (*self.state.operations, operation_item),
                        }
                    )
                )

            def root(self, *path: str) -> Self:
                return self._path("root_path", *path)

            def table(self, *path: str) -> Self:
                return self._path("table_path", *path)

            def value(self, key: str, value: t.JsonValue) -> Self:
                return self._operation(
                    FlextInfraModelsEngine.TomlSetOp, key=key, value=value
                )

            def list(
                self,
                key: str,
                values: t.StrSequence,
                *,
                strategy: c.Infra.TomlMergeMode = c.Infra.TomlMergeMode.REPLACE,
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
                values: Sequence[tuple[str, t.JsonValue]] = (),
                lists: Sequence[tuple[str, t.StrSequence]] = (),
                deprecated_keys: t.StrSequence = (),
            ) -> Self:
                nested_table = FlextInfraModelsEngine.TomlPhaseConfig(
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
                return self._replace(
                    self.state.model_copy(
                        update={
                            "nested_tables": (
                                *self.state.nested_tables,
                                nested_table,
                            )
                        }
                    )
                )

            def handler(self, fn: Callable[..., t.StrSequence]) -> Self:
                return self._replace(
                    self.state.model_copy(update={"custom_handler": fn})
                )


__all__: list[str] = ["FlextInfraModelsEngine"]
