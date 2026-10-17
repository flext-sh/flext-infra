"""Validated authority for one explicit native installation repair.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m, t


class FlextInfraModelsMiseToolchainRepair:
    """Pure execution declarations over the upstream atomic file contracts."""

    class MiseToolchainRepairPlan(m.FrozenModel):
        """One explicitly selected locked installation and its input authority."""

        repository_root: Annotated[
            Path,
            m.Field(description="Repository owning the declaration and lock."),
        ]
        tool: Annotated[
            t.NonEmptyStr,
            m.Field(description="Declared native backend selector."),
        ]
        version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact version authenticated from the current lock."),
        ]
        mise_executable: Annotated[
            Path,
            m.Field(description="Qualified self-managed Mise executable."),
        ]
        uv_executable: Annotated[
            Path,
            m.Field(description="Qualified UV executable for the complete proof."),
        ]
        source_states: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                exclude=True,
                description="Exact declaration, configuration and lock observations.",
            ),
        ]


__all__ = ["FlextInfraModelsMiseToolchainRepair"]
