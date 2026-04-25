"""Per-file ruff/pyrefly guard gates with snapshot rollback (Lane A-CH Task 0.5).

Runs each named gate against each file in the snapshot set. On failure,
restores the affected file from its in-memory snapshot — never via git.
Guarantees the workspace returns to a clean state after a handler regression
(per AGENTS.md §3.5 "Git is IMMUTABLE", §6 Quality Gates).

Per AGENT_COORDINATION.md §2.2, A-CH owns this surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from flext_core.result import FlextResult

from flext_infra import c, u


class FlextInfraUtilitiesGuardGates:
    """Per-file gate runner with in-memory snapshot rollback."""

    _DEFAULT_GATES: tuple[str, ...] = ("ruff", "pyrefly")

    class FileSnapshot(Protocol):
        """Minimal snapshot contract for per-file gate rollback."""

        path: Path
        content: str

    @staticmethod
    def guard_gates_run(
        *,
        workspace_root: Path,
        snapshots: Sequence[FileSnapshot],
        gates: Sequence[str] | None = None,
        revert_on_failure: bool = True,
    ) -> FlextResult[bool]:
        """Run each ``gate`` against each snapshotted file.

        On gate failure for a path, restore that path from its snapshot
        (when ``revert_on_failure``) and continue with the remaining files.

        Gate execution delegates to the canonical lint snapshot helper
        (``u.Infra.lint_snapshot``) to preserve SSOT command/environment
        behavior and cached snapshots.
        """
        resolved_workspace = workspace_root.resolve()
        active_gates = (
            tuple(gates)
            if gates is not None
            else FlextInfraUtilitiesGuardGates._DEFAULT_GATES
        )
        snapshots_by_path = {snap.path.resolve(): snap for snap in snapshots}
        reverted: list[Path] = []
        for snap in snapshots:
            target = snap.path.resolve()
            lint_errors = u.Infra.lint_snapshot(
                target,
                resolved_workspace,
                gates=active_gates,
            )
            if not lint_errors or not revert_on_failure or target in reverted:
                continue
            if target not in snapshots_by_path:
                return FlextResult[bool].fail(
                    f"gate failure on out-of-scope file: {target}",
                )
            snapshot = snapshots_by_path[target]
            try:
                target.write_text(
                    snapshot.content,
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
            except OSError as exc:
                return FlextResult[bool].fail(
                    f"restore failed for {target}: {exc}",
                )
            reverted.append(target)
        _ = reverted
        return FlextResult[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesGuardGates"]
