"""Guard-gate snapshot + report domain models (Task 0.5).

``FileSnapshot`` carries the byte-for-byte original of a file plus its
``mtime`` so per-file gate failures restore the exact pre-edit state — no
git, no character-set assumptions, no separate "content" field. The
``GuardGateReport`` envelope tells consumers which paths had to be
reverted and which gate messages triggered the rollback.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m


class FlextInfraModelsGuard:
    """Guard-gate domain models exposed via ``m.Infra.*``."""

    class FileSnapshot(m.BaseModel):
        """Frozen byte-level snapshot of a file used by guard-gate rollback."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True, extra="forbid", arbitrary_types_allowed=True
        )

        path: Annotated[Path, m.Field(description="Absolute path of the snapshot.")]
        original_bytes: Annotated[
            bytes,
            m.Field(
                description="Byte-for-byte file content captured at snapshot time."
            ),
        ]
        original_mtime: Annotated[
            float,
            m.Field(description="POSIX mtime captured alongside the bytes."),
        ]

    class GuardGateReport(m.BaseModel):
        """Summary of a guard-gate run — which paths reverted and why."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        restored_paths: Annotated[
            tuple[Path, ...],
            m.Field(
                default_factory=tuple,
                description="Paths whose gate failure triggered a snapshot restore.",
            ),
        ]
        gate_failures: Annotated[
            tuple[str, ...],
            m.Field(
                default_factory=tuple,
                description="Gate failure messages collected during the run.",
            ),
        ]
