"""Workspace propagator — sequenced make-verb runner with snapshot rollback.

Iterates a verb sequence, dispatches each verb through ``run_make_verb``
(test-injectable callback), then runs ``u.Infra.guard_gates_run`` over the
snapshots accumulated by the verb's handlers. Verb failure (callback
returned False, or guard restored a path) marks the slot ``success=False``
in the report but never aborts the entire propagation — downstream verbs
still execute so the operator sees the full damage picture in one pass.

Per AGENTS.md §3.5 "Git is IMMUTABLE": rollback is purely in-memory snapshot
restoration; this class never invokes ``git``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra import p, r, u
from flext_infra._models.guard import FlextInfraModelsGuard
from flext_infra._models.workspace import FlextInfraModelsWorkspace

VerbCallback = Callable[..., bool]
"""Test-injectable callback that runs a single make verb against the workspace."""

SnapshotProvider = Callable[[str], Sequence[FlextInfraModelsGuard.FileSnapshot]]
"""Returns the snapshots accumulated by handlers during the named verb."""

LintCallback = Callable[..., Mapping[str, Sequence[str]]]
"""Mirrors ``FlextInfraUtilitiesProtectedEdit.lint_snapshot``."""


class FlextInfraWorkspacePropagator(m.ArbitraryTypesModel):
    """Sequenced verb runner with per-verb guard-gate restore.

    Pydantic v2 model so consumers can construct it via the canonical
    ``settings=``-style call form. Reuses ``u.Infra.guard_gates_run``
    (Task 0.5) and ``u.Infra.snapshot_files`` (Task 0.5) — no
    re-implementation of restore plumbing.
    """

    model_config = m.ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    workspace_root: Annotated[
        Path,
        m.Field(description="Workspace root forwarded to every verb invocation."),
    ]

    def propagate(
        self,
        *,
        verbs: Sequence[str],
        run_make_verb_callback: VerbCallback,
        snapshot_provider: SnapshotProvider,
        guard_gates: Sequence[str] | None = None,
        lint_callback: LintCallback | None = None,
    ) -> p.Result[FlextInfraModelsWorkspace.PropagateReport]:
        """Run each verb, guard-check, and assemble a typed report."""
        started_at = datetime.now(UTC)
        statuses: list[FlextInfraModelsWorkspace.VerbStatus] = []

        for verb in verbs:
            status = self._run_one_verb(
                verb=verb,
                run_make_verb_callback=run_make_verb_callback,
                snapshot_provider=snapshot_provider,
                guard_gates=guard_gates,
                lint_callback=lint_callback,
            )
            if status is None:
                return r[FlextInfraModelsWorkspace.PropagateReport].fail(
                    f"verb {verb!r} aborted: guard gate run failed",
                )
            statuses.append(status)

        ended_at = datetime.now(UTC)
        return r[FlextInfraModelsWorkspace.PropagateReport].ok(
            FlextInfraModelsWorkspace.PropagateReport(
                started_at=started_at,
                ended_at=ended_at,
                verb_statuses=tuple(statuses),
            ),
        )

    def _run_one_verb(
        self,
        *,
        verb: str,
        run_make_verb_callback: VerbCallback,
        snapshot_provider: SnapshotProvider,
        guard_gates: Sequence[str] | None,
        lint_callback: LintCallback | None,
    ) -> FlextInfraModelsWorkspace.VerbStatus | None:
        """Single-verb dispatch + guard run.

        Returns ``None`` when the guard run itself failed (out-of-scope
        path); otherwise a typed status with the guard report attached.
        """
        callback_success = bool(
            run_make_verb_callback(verb, workspace_root=self.workspace_root),
        )
        snapshots = tuple(snapshot_provider(verb))
        guard_result = u.Infra.guard_gates_run(
            workspace_root=self.workspace_root,
            snapshots=snapshots,
            gates=tuple(guard_gates) if guard_gates is not None else None,
            lint_callback=lint_callback,
        )
        if guard_result.failure:
            return None
        guard_report = guard_result.value
        success = callback_success and not guard_report.restored_paths
        message = "" if callback_success else "make verb callback returned False"
        return FlextInfraModelsWorkspace.VerbStatus(
            verb=verb,
            success=success,
            guard_report=guard_report,
            message=message,
        )
