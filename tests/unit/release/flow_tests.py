"""Tests for release main() orchestration flow.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace

from _pytest.monkeypatch import MonkeyPatch
from flext_core import r
from flext_tests import tm

import flext_infra.release.__main__ as _main_mod
from flext_infra import m, u
from flext_infra.release.__main__ import main


def _patch_main_deps(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    *,
    root_result: r[Path] | None = None,
    release_result: r[bool] | None = None,
    capture: Sequence[SimpleNamespace] | None = None,
    error_calls: t.StrSequence | None = None,
) -> None:
    """Patch all main() dependencies via monkeypatch."""
    monkeypatch.setattr(
        u.Infra,
        "workspace_root",
        staticmethod(
            lambda hint: (
                root_result if root_result is not None else r[Path].ok(tmp_path)
            ),
        ),
    )
    monkeypatch.setattr(
        u.Infra,
        "parse_semver",
        staticmethod(lambda version: r[str].ok(version)),
    )
    monkeypatch.setattr(
        u.Infra,
        "current_workspace_version",
        staticmethod(lambda root: r[str].ok("1.0.0")),
    )
    monkeypatch.setattr(
        u.Infra,
        "bump_version",
        staticmethod(lambda cur, kind: r[str].ok("1.1.0")),
    )

    class _Or:
        def run_release(
            self,
            release_config: m.Infra.ReleaseOrchestratorConfig,
        ) -> r[bool]:
            if capture is not None:
                capture.append(
                    SimpleNamespace(
                        phases=release_config.phases,
                        push=release_config.push,
                        dry_run=release_config.dry_run,
                        project_names=release_config.project_names,
                    ),
                )
            return release_result if release_result is not None else r[bool].ok(True)

    monkeypatch.setattr(_main_mod, "FlextInfraReleaseOrchestrator", _Or)

    if error_calls is not None:
        ec: t.StrSequence = error_calls

        class _Out:
            @staticmethod
            def error(msg: str) -> None:
                ec.append(msg)

        monkeypatch.setattr(_main_mod, "output", _Out)


def _argv(tmp_path: Path, *extra: str) -> t.StrSequence:
    return ["prog", "--workspace", str(tmp_path), *extra]


class TestReleaseMainFlow:
    """Test main() orchestration."""

    def test_main_success(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--interactive", "0"),
        )
        _patch_main_deps(monkeypatch, tmp_path)
        tm.that(main(), eq=0)

    def test_main_workspace_root_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--interactive", "0"),
        )
        errors: t.StrSequence = []
        _patch_main_deps(
            monkeypatch,
            tmp_path,
            root_result=r[Path].fail("not found"),
            error_calls=errors,
        )
        tm.that(main(), eq=1)

    def test_main_version_resolution_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "version", "--version", "invalid"),
        )
        errors: t.StrSequence = []
        _patch_main_deps(monkeypatch, tmp_path, error_calls=errors)
        monkeypatch.setattr(
            u.Infra,
            "parse_semver",
            staticmethod(lambda version: r[str].fail("invalid")),
        )
        tm.that(main(), eq=1)
        tm.that(len(errors), eq=1)

    def test_main_release_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--interactive", "0"),
        )
        errors: t.StrSequence = []
        _patch_main_deps(
            monkeypatch,
            tmp_path,
            release_result=r[bool].fail("release failed"),
            error_calls=errors,
        )
        tm.that(main(), eq=1)

    def test_main_all_phases(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "all", "--interactive", "0"),
        )
        calls: Sequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].phases, eq=["validate", "version", "build", "publish"])

    def test_main_with_push(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--push", "--interactive", "0"),
        )
        calls: Sequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].push, eq=True)

    def test_main_with_dry_run(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--dry-run", "--interactive", "0"),
        )
        calls: Sequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].dry_run, eq=True)

    def test_main_with_projects(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--projects", "proj1", "proj2"),
        )
        calls: Sequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].project_names, eq=["proj1", "proj2"])
