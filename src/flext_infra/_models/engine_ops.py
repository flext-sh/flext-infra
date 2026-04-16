"""TOML operation models shared by ``m.Infra`` and ``t.Infra``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal

from flext_core import m
from flext_infra import c, t


class FlextInfraModelsEngineOperation:
    """TOML operation models used by the phase builder and executor."""

    class TomlSetOp(m.ContractModel):
        """Set one TOML key to one JSON-compatible value."""

        kind: Literal["set"] = m.Field(
            "set", description="Operation kind", validate_default=True
        )
        key: str = m.Field(description="TOML key name")
        value: t.Cli.JsonValue = m.Field(description="JSON-compatible value")

    class TomlListOp(m.ContractModel):
        """Set or merge one TOML string list."""

        kind: Literal["list"] = m.Field(
            "list", description="Operation kind", validate_default=True
        )
        key: str = m.Field(description="TOML key name")
        values: t.StrSequence = m.Field(description="Expected values")
        strategy: Annotated[
            str,
            m.Field(
                description="Merge strategy",
                validate_default=True,
            ),
        ] = c.Infra.TOML_MERGE_REPLACE
        sort: Annotated[
            bool, m.Field(description="Sort values before sync", validate_default=True)
        ] = True

    class TomlRemoveOp(m.ContractModel):
        """Remove one TOML key, optionally from a nested relative table."""

        kind: Literal["remove"] = m.Field(
            "remove", description="Operation kind", validate_default=True
        )
        key: str = m.Field(description="Key to remove")
        table_path: Annotated[
            t.StrSequence,
            m.Field(description="Relative sub-table path", validate_default=True),
        ] = ()


__all__: list[str] = ["FlextInfraModelsEngineOperation"]
