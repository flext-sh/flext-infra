"""TOML operation models shared by ``m.Infra`` and ``t.Infra``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from flext_cli import FlextCliTypes
from flext_core import FlextModels
from flext_infra import FlextInfraConstantsBase


class FlextInfraEngineOperationModels:
    """TOML operation models used by the phase builder and executor."""

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


__all__ = ["FlextInfraEngineOperationModels"]
