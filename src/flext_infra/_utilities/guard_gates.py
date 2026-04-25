"""Per-file ruff/pyrefly guard gates with snapshot rollback (Task 0.5).

Runs each named gate against each file in the snapshot set. On failure,
restores the affected file from its in-memory snapshot — never via git.
Returns a typed ``GuardGateReport`` so the orchestrator can surface
exactly which paths reverted and which gate messages triggered them.

Per AGENTS.md §3.5 "Git is IMMUTABLE" / §6 Quality Gates.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from flext_core import FlextResult as r

from flext_infra._models.guard import FlextInfraModelsGuard
from flext_infra._utilities.snapshot import FlextInfraUtilitiesSnapshot

LintCallback = Callable[..., Mapping[str, Sequence[str]]]
"""Callback signature accepted by ``guard_gates_run`` for testability.

Mirrors ``FlextInfraUtilitiesProtectedEdit.lint_snapshot`` — returns a
``Mapping[gate_name -> error_lines]``. Empty mapping means all gates
passed for the file.
"""


class FlextInfraUtilitiesGuardGates:
    """Per-file gate runner with in-memory snapshot rollback."""

    _DEFAULT_GATES: tuple[str, ...] = ("ruff", "pyrefly")

    @classmethod
    def guard_gates_run(
        cls,
        *,
        workspace_root: Path,
        snapshots: Sequence[FlextInfraModelsGuard.FileSnapshot],
        gates: Sequence[str] | None = None,
        revert_on_failure: bool = True,
        lint_callback: LintCallback | None = None,
        additional_paths: Sequence[Path] = (),
    ) -> r[FlextInfraModelsGuard.GuardGateReport]:
        """Run each ``gate`` against each snapshotted file.

        ``lint_callback`` is the dispatcher seam: real production wiring
        delegates to ``u.Infra.lint_snapshot`` (preserving SSOT command +
        env behaviour); tests inject a fake to avoid spawning real ruff /
        pyrefly subprocesses. ``additional_paths`` lets callers prove the
        gate refuses to silently revert files outside the declared scope.
        """
        active_gates = tuple(gates) if gates is not None else cls._DEFAULT_GATES
        callback: LintCallback
        if lint_callback is not None:
            callback = lint_callback
        else:
            from flext_infra import u  # noqa: PLC0415  (cycle break)

            callback = u.Infra.lint_snapshot

        snapshots_by_path = {snap.path.resolve(): snap for snap in snapshots}
        scoped_paths = tuple(snapshots_by_path)
        every_path = (*scoped_paths, *(extra.resolve() for extra in additional_paths))

        gate_failures: list[str] = []
        restored: list[Path] = []
        resolved_workspace = workspace_root.resolve()

        for target in every_path:
            failures = callback(
                target,
                workspace=resolved_workspace,
                gates=active_gates,
            )
            if not failures:
                continue
            for gate_name, error_lines in failures.items():
                gate_failures.extend(
                    f"{target.name}::{gate_name}: {line}" for line in error_lines
                )
            if not revert_on_failure:
                continue
            if target not in snapshots_by_path:
                return r[FlextInfraModelsGuard.GuardGateReport].fail(
                    f"gate failure on out-of-scope file: {target}",
                )
            if target in restored:
                continue
            restore_result = FlextInfraUtilitiesSnapshot.restore_snapshots(
                (snapshots_by_path[target],),
            )
            if restore_result.failure:
                return r[FlextInfraModelsGuard.GuardGateReport].fail(
                    restore_result.error or "restore failed",
                )
            restored.append(target)

        return r[FlextInfraModelsGuard.GuardGateReport].ok(
            FlextInfraModelsGuard.GuardGateReport(
                restored_paths=tuple(restored),
                gate_failures=tuple(gate_failures),
            ),
        )
