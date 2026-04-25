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

import subprocess
from collections.abc import Sequence
from pathlib import Path

from flext_core.result import FlextResult

from flext_infra._models.guard import FlextInfraModelsGuard
from flext_infra._utilities.snapshot import FlextInfraUtilitiesSnapshot

_DEFAULT_GATES: tuple[str, ...] = ("ruff", "pyrefly")
_GATE_OUTPUT_TRUNCATE: int = 500


class FlextInfraUtilitiesGuardGates:
    """Per-file gate runner with in-memory snapshot rollback."""

    @staticmethod
    def guard_gates_run(
        *,
        workspace_root: Path,
        snapshots: Sequence[FlextInfraModelsGuard.FileSnapshot],
        gates: Sequence[str] = _DEFAULT_GATES,
        revert_on_failure: bool = True,
    ) -> FlextResult[FlextInfraModelsGuard.GuardGateReport]:
        """Run each ``gate`` against each snapshotted file.

        On gate failure for a path, restore that path from its snapshot
        (when ``revert_on_failure``) and continue with the remaining files.
        Returns a ``GuardGateReport`` with per-(file, gate) outcomes plus
        the list of paths that were reverted.

        ``workspace_root`` is documented but not used to locate the venv —
        bare ``ruff`` / ``pyrefly`` commands resolve through the workspace
        ``.venv`` on PATH (per AGENTS.md §5/§6).
        """
        del workspace_root  # bare commands rely on PATH; param kept for callers
        snapshots_by_path = {snap.path.resolve(): snap for snap in snapshots}
        outcomes: list[FlextInfraModelsGuard.GuardGateOutcome] = []
        reverted: list[Path] = []
        for snap in snapshots:
            target = snap.path.resolve()
            for gate in gates:
                cmd = [gate, "check", str(target)]
                if gate == "ruff":
                    cmd.append("--no-fix")
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                passed = proc.returncode == 0
                message = ""
                if not passed:
                    raw = (proc.stdout or "") + (proc.stderr or "")
                    message = raw.strip()[:_GATE_OUTPUT_TRUNCATE]
                outcomes.append(
                    FlextInfraModelsGuard.GuardGateOutcome(
                        path=target,
                        gate=gate,
                        passed=passed,
                        message=message,
                    )
                )
                if not passed and revert_on_failure and target not in reverted:
                    if target not in snapshots_by_path:
                        return FlextResult[
                            FlextInfraModelsGuard.GuardGateReport
                        ].fail(
                            f"gate failure on out-of-scope file: {target}",
                        )
                    restore_outcome = (
                        FlextInfraUtilitiesSnapshot.restore_snapshots(
                            (snapshots_by_path[target],)
                        )
                    )
                    if restore_outcome.failure:
                        return FlextResult[
                            FlextInfraModelsGuard.GuardGateReport
                        ].fail(
                            restore_outcome.error
                            or f"restore failed for {target}",
                        )
                    reverted.append(target)
                    break
        return FlextResult[FlextInfraModelsGuard.GuardGateReport].ok(
            FlextInfraModelsGuard.GuardGateReport(
                outcomes=tuple(outcomes),
                files_reverted=tuple(reverted),
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesGuardGates"]
