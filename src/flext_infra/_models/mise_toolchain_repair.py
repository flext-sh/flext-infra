"""Validated authority for one explicit native installation repair.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path
from typing import Annotated

from flext_cli import m, t


class FlextInfraModelsMiseToolchainRepair:
    """Pure execution declarations of one locked native installation repair."""

    class MiseToolchainRepairPlan(m.FrozenModel):
        """One explicitly selected locked installation and its executables."""

        repository_root: Annotated[
            Path,
            m.Field(description="Repository owning the declaration and lock."),
        ]
        tool: Annotated[
            t.NonEmptyStr,
            m.Field(description="Declared native backend selector."),
        ]
        mise_executable: Annotated[
            Path,
            m.Field(description="Qualified self-managed Mise executable."),
        ]
        uv_executable: Annotated[
            Path,
            m.Field(description="Qualified UV executable for the complete proof."),
        ]


__all__ = ["FlextInfraModelsMiseToolchainRepair"]
