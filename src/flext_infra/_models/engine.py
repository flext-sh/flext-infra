"""TOML phase engine models with Builder DSL.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import chain
from typing import Annotated, Literal, Self

from pydantic import Field

from flext_cli import FlextCliTypes
from flext_core import FlextModels
from flext_infra._constants.base import FlextInfraConstantsBase


class FlextInfraEngineModels:
    """Engine models accessible via ``m.Infra.*``."""

    class TomlSetOp(FlextModels.ContractModel):
        """Set one TOML key to one JSON-compatible value."""

        kind: Literal["set"] = Field(default="set", description="Operation kind")
        key: str = Field(description="TOML key name")
        value: FlextCliTypes.Cli.JsonValue = Field(description="JSON-compatible value")

    class TomlListOp(FlextModels.ContractModel):
        """Set or merge one TOML string list."""

        kind: Literal["list"] = Field(default="list", description="Operation kind")
        key: str = Field(description="TOML key name")
        values: FlextCliTypes.StrSequence = Field(description="Expected values")
        strategy: str = Field(
            default=FlextInfraConstantsBase.TomlMerge.REPLACE,
            description="Merge strategy",
        )
        sort: bool = Field(default=True, description="Sort values before sync")

    class TomlRemoveOp(FlextModels.ContractModel):
        """Remove one TOML key, optionally from a nested relative table."""

        kind: Literal["remove"] = Field(default="remove", description="Operation kind")
        key: str = Field(description="Key to remove")
        table_path: FlextCliTypes.StrSequence = Field(
            default=(),
            description="Relative sub-table path",
        )

    type TomlOperation = Annotated[
        TomlSetOp | TomlListOp | TomlRemoveOp,
        Field(discriminator="kind"),
    ]

    class TomlPhaseConfig(FlextModels.ContractModel):
        """Declarative TOML phase with inline Builder DSL."""

        name: str = Field(description="Phase name")
        root_path: FlextCliTypes.StrSequence = Field(
            default=(FlextInfraConstantsBase.TOOL,),
            description="Root path before table_path",
        )
        table_path: FlextCliTypes.StrSequence = Field(
            default=(), description="Primary table path"
        )
        operations: Sequence[FlextInfraEngineModels.TomlOperation] = Field(
            default=(),
            description="Declarative TOML operations",
        )
        nested_tables: Sequence[FlextInfraEngineModels.TomlPhaseConfig] = Field(
            default=(), description="Nested TOML phase configs"
        )
        custom_handler: Callable[..., FlextCliTypes.StrSequence] | None = Field(
            default=None,
            exclude=True,
            description="Custom handler",
        )

        class Builder(
            FlextModels.Builder.Identity["FlextInfraEngineModels.TomlPhaseConfig"]
        ):
            """Fluent builder — ``m.Infra.TomlPhaseConfig.Builder("ruff").table(...).build()``."""

            def __init__(self, name: str) -> None:
                super().__init__(
                    state=FlextInfraEngineModels.TomlPhaseConfig(name=name)
                )

            @classmethod
            def _nested_operations(
                cls,
                *,
                values: Sequence[tuple[str, FlextCliTypes.Cli.JsonValue]] = (),
                lists: Sequence[tuple[str, FlextCliTypes.StrSequence]] = (),
                deprecated_keys: FlextCliTypes.StrSequence = (),
            ) -> tuple[FlextInfraEngineModels.TomlOperation, ...]:
                return tuple(
                    chain(
                        (
                            cls._model(
                                FlextInfraEngineModels.TomlSetOp, key=key, value=value
                            )
                            for key, value in values
                        ),
                        (
                            cls._model(
                                FlextInfraEngineModels.TomlListOp,
                                key=key,
                                values=tuple(entries),
                            )
                            for key, entries in lists
                        ),
                        (
                            cls._model(FlextInfraEngineModels.TomlRemoveOp, key=key)
                            for key in deprecated_keys
                        ),
                    ),
                )

            def _operation(
                self, operation_type: type[FlextModels.ContractModel], /, **data: object
            ) -> Self:
                return self._append_model("operations", operation_type, **data)

            def root(self, *path: str) -> Self:
                return self._path("root_path", *path)

            def table(self, *path: str) -> Self:
                return self._path("table_path", *path)

            def value(self, key: str, value: FlextCliTypes.Cli.JsonValue) -> Self:
                return self._operation(
                    FlextInfraEngineModels.TomlSetOp, key=key, value=value
                )

            def list(
                self,
                key: str,
                values: FlextCliTypes.StrSequence,
                *,
                strategy: str = FlextInfraConstantsBase.TomlMerge.REPLACE,
                sort: bool = True,
            ) -> Self:
                return self._operation(
                    FlextInfraEngineModels.TomlListOp,
                    key=key,
                    values=tuple(values),
                    strategy=strategy,
                    sort=sort,
                )

            def deprecated(self, key: str, *sub_path: str) -> Self:
                return self._operation(
                    FlextInfraEngineModels.TomlRemoveOp,
                    key=key,
                    table_path=tuple(sub_path),
                )

            def nested(
                self,
                *path: str,
                values: Sequence[tuple[str, FlextCliTypes.Cli.JsonValue]] = (),
                lists: Sequence[tuple[str, FlextCliTypes.StrSequence]] = (),
                deprecated_keys: FlextCliTypes.StrSequence = (),
            ) -> Self:
                return self._append_model(
                    "nested_tables",
                    FlextInfraEngineModels.TomlPhaseConfig,
                    name=self.state.name,
                    root_path=(),
                    table_path=tuple(path),
                    operations=self._nested_operations(
                        values=values, lists=lists, deprecated_keys=deprecated_keys
                    ),
                )

            def handler(self, fn: Callable[..., FlextCliTypes.StrSequence]) -> Self:
                return self._set(custom_handler=fn)


__all__ = ["FlextInfraEngineModels"]
