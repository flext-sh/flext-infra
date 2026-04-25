"""Guard-gate models for flext-infra (Lane A-CH Phase 0 Task 0.5).

``m.Infra.FileSnapshot`` captures a file's bytes + mtime before a refactor
mutation. ``m.Infra.GuardGateReport`` documents the outcome of a per-file
ruff/pyrefly run with snapshot-rollback semantics. Both consumed by
``u.Infra.guard_gates_run``.

Per AGENTS.md §3.5 ("Git is IMMUTABLE") rollback is purely intra-handler
bookkeeping over the in-memory snapshot — never a git operation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m


class FlextInfraModelsGuard:
    """Guard-gate models exposed under ``m.Infra``."""

    class FileSnapshot(m.ContractModel):
        """Frozen pre-edit snapshot of a single file."""

        model_config = m.ConfigDict(frozen=True, extra="forbid")

        path: Annotated[
            Path,
            m.Field(description="Absolute file path captured."),
        ]
        original_bytes: Annotated[
            bytes,
            m.Field(description="Raw bytes of the file at snapshot time."),
        ]
        original_mtime: Annotated[
            float,
            m.Field(description="POSIX mtime at snapshot time."),
        ]

    class GuardGateOutcome(m.ContractModel):
        """Per-file outcome of a guard-gate run."""

        path: Annotated[
            Path,
            m.Field(description="File path the gate ran on."),
        ]
        gate: Annotated[
            str,
            m.Field(description="Gate name — 'ruff' / 'pyrefly' / etc."),
        ]
        passed: Annotated[
            bool,
            m.Field(description="True when the gate exited 0."),
        ]
        message: Annotated[
            str,
            m.Field(
                default="",
                description=(
                    "Truncated gate stdout/stderr captured when passed=False."
                ),
            ),
        ]

    class GuardGateReport(m.ContractModel):
        """Aggregate report returned by ``u.Infra.guard_gates_run``."""

        outcomes: Annotated[
            tuple[FlextInfraModelsGuard.GuardGateOutcome, ...],
            m.Field(
                default_factory=tuple,
                description="One entry per (file, gate) pair executed.",
            ),
        ]
        files_reverted: Annotated[
            tuple[Path, ...],
            m.Field(
                default_factory=tuple,
                description="Paths restored from snapshot after gate failure.",
            ),
        ]


__all__: list[str] = ["FlextInfraModelsGuard"]
