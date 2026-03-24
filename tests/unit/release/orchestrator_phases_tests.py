"""Tests for FlextInfraReleaseOrchestrator phase methods.

Tests phase_validate, phase_version, and phase_build using monkeypatch
and tmp_path fixtures for isolated test environments.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import FlextInfraModels, FlextInfraReleaseOrchestrator, u
from tests import t

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

_m = FlextInfraModels


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Create workspace root with pyproject.toml."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "Makefile").touch()
    (root / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    return root


class TestPhaseValidate:
    """Tests for phase_validate."""

    def test_dry_run(self, workspace_root: Path) -> None:
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_validate(workspace_root, dry_run=True))

    def test_executes_make(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        called = False

        def _fake_run_checked(
            cmd: t.StrSequence,
            **kw: t.Scalar,
        ) -> r[bool]:
            nonlocal called
            called = True
            return r[bool].ok(True)

        monkeypatch.setattr(u.Infra, "run_checked", staticmethod(_fake_run_checked))
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_validate(workspace_root, dry_run=False))
        tm.that(called, eq=True)


class TestPhaseVersion:
    """Tests for phase_version."""

    def test_updates_files(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _parse_semver(version: str) -> r[str]:
            return r[str].ok(version)

        def _replace_version(path: Path, version: str) -> None:
            _ = path, version

        monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))
        monkeypatch.setattr(
            u.Infra, "replace_project_version", staticmethod(_replace_version),
        )
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_version(workspace_root, "1.0.0", [], dry_run=False))

    def test_invalid_semver(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _parse_semver_fail(version: str) -> r[str]:
            _ = version
            return r[str].fail("invalid version")

        monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver_fail))
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.fail(orchestrator.phase_version(workspace_root, "invalid", []))

    def test_with_dev_suffix(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _parse_semver(version: str) -> r[str]:
            return r[str].ok(version)

        def _replace_version(path: Path, version: str) -> None:
            _ = path, version

        monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))
        monkeypatch.setattr(
            u.Infra, "replace_project_version", staticmethod(_replace_version),
        )
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_version(workspace_root, "1.0.0", [], dev_suffix=True))

    def test_dry_run(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        def _parse_semver(version: str) -> r[str]:
            return r[str].ok(version)

        monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_version(workspace_root, "1.0.0", [], dry_run=True))

    def test_skips_missing_files(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        orchestrator = FlextInfraReleaseOrchestrator()

        def _fake_version_files(*a: t.Scalar, **kw: t.Scalar) -> Sequence[Path]:
            del a, kw
            return [workspace_root / "nonexistent.toml"]

        monkeypatch.setattr(orchestrator, "_version_files", _fake_version_files)

        def _parse_semver(version: str) -> r[str]:
            return r[str].ok(version)

        monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))
        tm.ok(orchestrator.phase_version(workspace_root, "1.0.0", []))


class TestPhaseBuild:
    """Tests for phase_build."""

    def test_creates_report_dir(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        ws_root = workspace_root

        def _get_report_dir(ws: Path | str, scope: str, verb: str) -> Path:
            _ = ws, scope, verb
            return ws_root / "reports"

        monkeypatch.setattr(u.Infra, "get_report_dir", staticmethod(_get_report_dir))

        def _fake_run_make(*a: t.Scalar, **kw: t.Scalar) -> r[tuple[int, str]]:
            del a, kw
            return r[tuple[int, str]].ok((0, "ok"))

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_run_make",
            _fake_run_make,
        )
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.ok(orchestrator.phase_build(workspace_root, "1.0.0", []))

    def test_report_dir_creation_fails(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        ws_root = workspace_root

        def _get_report_dir(ws: Path | str, scope: str, verb: str) -> Path:
            _ = ws, scope, verb
            return ws_root / "reports"

        monkeypatch.setattr(u.Infra, "get_report_dir", staticmethod(_get_report_dir))

        def _raise_mkdir(*a: t.Scalar, **kw: t.Scalar) -> None:
            del a, kw
            msg = "permission denied"
            raise OSError(msg)

        monkeypatch.setattr("pathlib.Path.mkdir", _raise_mkdir)
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.fail(orchestrator.phase_build(workspace_root, "1.0.0", []))

    def test_with_make_failure(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _fake_build_targets(
            *a: t.Scalar,
            **kw: t.Scalar,
        ) -> Sequence[tuple[str, Path]]:
            del a, kw
            return [("root", workspace_root)]

        def _fake_run_make_failure(*a: t.Scalar, **kw: t.Scalar) -> r[tuple[int, str]]:
            del a, kw
            return r[tuple[int, str]].fail("make failed")

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_build_targets",
            _fake_build_targets,
        )
        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_run_make",
            _fake_run_make_failure,
        )
        orchestrator = FlextInfraReleaseOrchestrator()
        tm.fail(orchestrator.phase_build(workspace_root, "1.0.0", []))
