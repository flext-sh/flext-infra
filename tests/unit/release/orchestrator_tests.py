"""Tests for FlextInfraReleaseOrchestrator run_release and execute.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence

from typing import TYPE_CHECKING

import pytest
from flext_core import r, t
from flext_tests import tm

from flext_infra import FlextInfraReleaseOrchestrator, m as infra_models

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

_CLS = FlextInfraReleaseOrchestrator


def _make_config(
    workspace_root: Path,
    version: str = "1.0.0",
    tag: str = "v1.0.0",
    phases: t.StrSequence | None = None,
    project_names: t.StrSequence | None = None,
    dry_run: bool = False,
    push: bool = False,
    dev_suffix: bool = False,
    create_branches: bool = True,
    next_dev: bool = False,
    next_bump: str = "minor",
) -> infra_models.Infra.ReleaseOrchestratorConfig:
    """Create a ReleaseOrchestratorConfig with test defaults."""
    return infra_models.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version=version,
        tag=tag,
        phases=phases or [],
        project_names=project_names,
        dry_run=dry_run,
        push=push,
        dev_suffix=dev_suffix,
        create_branches=create_branches,
        next_dev=next_dev,
        next_bump=next_bump,
    )


def _noop_branches(*args: t.Scalar, **kwargs: t.Scalar) -> r[bool]:
    return r[bool].ok(True)


def _noop_dispatch(*args: t.Scalar, **kwargs: t.Scalar) -> r[bool]:
    return r[bool].ok(True)


def _noop_bump(*args: t.Scalar, **kwargs: t.Scalar) -> r[bool]:
    return r[bool].ok(True)


def _stub_branches(mp: MonkeyPatch) -> None:
    mp.setattr(_CLS, "_create_branches", _noop_branches)


def _stub_dispatch(mp: MonkeyPatch) -> None:
    mp.setattr(_CLS, "_dispatch_phase", _noop_dispatch)


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Create workspace root with pyproject.toml."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "Makefile").touch()
    (root / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    return root


class TestReleaseOrchestratorExecute:
    """Tests for execute() and run_release() top-level."""

    def test_execute_returns_ok(self) -> None:
        tm.ok(_CLS().execute(), eq=True)

    def test_run_release_invalid_phase(self, workspace_root: Path) -> None:
        config = _make_config(workspace_root, phases=["invalid_phase"])
        result = _CLS().run_release(config)
        tm.fail(result)

    def test_run_release_empty_phases(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_branches(monkeypatch)
        config = _make_config(workspace_root, phases=[])
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_with_project_filter(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_branches(monkeypatch)
        _stub_dispatch(monkeypatch)
        config = _make_config(
            workspace_root,
            phases=["validate"],
            project_names=["flext-core", "flext-api"],
        )
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_dry_run(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_dispatch(monkeypatch)
        config = _make_config(workspace_root, phases=["validate"], dry_run=True)
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_with_push(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_branches(monkeypatch)
        _stub_dispatch(monkeypatch)
        config = _make_config(workspace_root, phases=["validate"], push=True)
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_with_dev_suffix(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_branches(monkeypatch)
        _stub_dispatch(monkeypatch)
        config = _make_config(
            workspace_root,
            version="1.0.0-dev",
            tag="v1.0.0-dev",
            phases=["version"],
            dev_suffix=True,
        )
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_next_dev(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_branches(monkeypatch)
        _stub_dispatch(monkeypatch)
        monkeypatch.setattr(_CLS, "_bump_next_dev", _noop_bump)
        config = _make_config(
            workspace_root,
            phases=["version"],
            next_dev=True,
            next_bump="minor",
        )
        result = _CLS().run_release(config)
        tm.ok(result)

    def test_run_release_phase_failure_stops(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        call_count = 0

        def fake_dispatch(
            _self: FlextInfraReleaseOrchestrator,
            dispatch_config: infra_models.Infra.ReleasePhaseDispatchConfig,
        ) -> r[bool]:
            nonlocal call_count
            call_count += 1
            if dispatch_config.phase == "validate":
                return r[bool].fail("validation failed")
            return r[bool].ok(True)

        _stub_branches(monkeypatch)
        monkeypatch.setattr(_CLS, "_dispatch_phase", fake_dispatch)
        config = _make_config(
            workspace_root,
            phases=["validate", "version"],
        )
        result = _CLS().run_release(config)
        tm.fail(result)
        tm.that(call_count, eq=1)

    def test_run_release_create_branches_disabled(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _stub_dispatch(monkeypatch)
        config = _make_config(
            workspace_root,
            phases=["validate"],
            create_branches=False,
        )
        result = _CLS().run_release(config)
        tm.ok(result)
