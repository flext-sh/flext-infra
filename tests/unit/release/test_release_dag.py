"""Tests for release orchestrator DAG pipeline execution.

Validates phase ordering, selective phase execution, and failure propagation
through the DAG-based release pipeline.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import FlextInfraReleaseOrchestrator
from tests import c, m, r, t

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

# Canonical phase order as used by _build_release_stages.
_ALL_PHASES: list[str] = [
    c.Infra.Verbs.VALIDATE,
    c.Infra.VERSION,
    c.Infra.Directories.BUILD,
    "publish",
]


def _make_config(
    workspace_root: Path,
    phases: list[str] | None = None,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        phases=phases or _ALL_PHASES,
        project_names=None,
        dry_run=False,
        push=False,
        dev_suffix=False,
        create_branches=False,
        next_dev=False,
        next_bump="minor",
    )


def _noop_branches(
    *args: t.Scalar,
    **kwargs: t.Scalar,
) -> r[bool]:
    return r[bool].ok(True)


class TestReleaseDag:
    """Tests for DAG-based release pipeline execution."""

    def test_release_phases_execute_via_dag(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """All 4 phases execute in canonical order via DAG pipeline."""
        executed_phases: list[str] = []

        def _tracking_dispatch(
            _self: FlextInfraReleaseOrchestrator,
            dispatch_config: m.Infra.ReleasePhaseDispatchConfig,
        ) -> r[bool]:
            executed_phases.append(dispatch_config.phase)
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_dispatch_phase",
            _tracking_dispatch,
        )
        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_create_branches",
            _noop_branches,
        )

        config = _make_config(tmp_path)
        result = FlextInfraReleaseOrchestrator().run_release(config)
        tm.ok(result)
        tm.that(executed_phases, eq=_ALL_PHASES)

    def test_release_selective_phases(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Request only validate+build; version+publish are skipped."""
        executed_phases: list[str] = []

        def _tracking_dispatch(
            _self: FlextInfraReleaseOrchestrator,
            dispatch_config: m.Infra.ReleasePhaseDispatchConfig,
        ) -> r[bool]:
            executed_phases.append(dispatch_config.phase)
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_dispatch_phase",
            _tracking_dispatch,
        )

        selected = [c.Infra.Verbs.VALIDATE, c.Infra.Directories.BUILD]
        config = _make_config(tmp_path, phases=selected)
        result = FlextInfraReleaseOrchestrator().run_release(config)
        tm.ok(result)
        tm.that(executed_phases, eq=selected)
        # version and publish must not appear.
        tm.that(c.Infra.VERSION not in executed_phases, eq=True)
        tm.that("publish" not in executed_phases, eq=True)

    def test_release_failure_propagates(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """If validate fails, version/build/publish don't run."""
        executed_phases: list[str] = []

        def _failing_dispatch(
            _self: FlextInfraReleaseOrchestrator,
            dispatch_config: m.Infra.ReleasePhaseDispatchConfig,
        ) -> r[bool]:
            executed_phases.append(dispatch_config.phase)
            if dispatch_config.phase == c.Infra.Verbs.VALIDATE:
                return r[bool].fail("validation failed")
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_dispatch_phase",
            _failing_dispatch,
        )

        config = _make_config(tmp_path)
        result = FlextInfraReleaseOrchestrator().run_release(config)
        tm.fail(result)
        # Only validate should have been dispatched.
        tm.that(executed_phases, eq=[c.Infra.Verbs.VALIDATE])
        tm.that(c.Infra.VERSION not in executed_phases, eq=True)


__all__: t.StrSequence = []
