"""Tests for release main() orchestration flow.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
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
    capture: list[SimpleNamespace] | None = None,
    error_calls: list[str] | None = None,
) -> None:
    """Patch all main() dependencies via monkeypatch."""
    effective_root = root_result

    def _workspace_root(hint: str) -> r[Path]:
        return effective_root if effective_root is not None else r[Path].ok(tmp_path)

    monkeypatch.setattr(u.Infra, "workspace_root", staticmethod(_workspace_root))

    def _parse_semver(version: str) -> r[str]:
        return r[str].ok(version)

    monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))

    def _current_workspace_version(root: Path) -> r[str]:
        return r[str].ok("1.0.0")

    monkeypatch.setattr(
        u.Infra,
        "current_workspace_version",
        staticmethod(_current_workspace_version),
    )

    def _bump_version(cur: str, kind: str) -> r[str]:
        return r[str].ok("1.1.0")

    monkeypatch.setattr(u.Infra, "bump_version", staticmethod(_bump_version))

    effective_release = release_result
    effective_capture = capture

    class _Or:
        def run_release(
            self,
            release_config: m.Infra.ReleaseOrchestratorConfig,
        ) -> r[bool]:
            if effective_capture is not None:
                effective_capture.append(
                    SimpleNamespace(
                        phases=release_config.phases,
                        push=release_config.push,
                        dry_run=release_config.dry_run,
                        project_names=release_config.project_names,
                    ),
                )
            return (
                effective_release if effective_release is not None else r[bool].ok(True)
            )

    monkeypatch.setattr(_main_mod, "FlextInfraReleaseOrchestrator", _Or)

    if error_calls is not None:
        ec: list[str] = error_calls

        class _Out:
            @staticmethod
            def error(msg: str) -> None:
                ec.append(msg)

        monkeypatch.setattr(_main_mod, "output", _Out)


def _argv(tmp_path: Path, *extra: str) -> list[str]:
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
        errors: list[str] = []
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
        errors: list[str] = []
        _patch_main_deps(monkeypatch, tmp_path, error_calls=errors)

        def _parse_semver_fail(version: str) -> r[str]:
            return r[str].fail("invalid")

        monkeypatch.setattr(
            u.Infra,
            "parse_semver",
            staticmethod(_parse_semver_fail),
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
        errors: list[str] = []
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
        calls: list[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].phases, eq=["validate", "version", "build", "publish"])

    def test_main_with_push(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--push", "--interactive", "0"),
        )
        calls: list[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].push, eq=True)

    def test_main_with_dry_run(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--dry-run", "--interactive", "0"),
        )
        calls: list[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].dry_run, eq=True)

    def test_main_with_projects(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            _argv(tmp_path, "--phase", "validate", "--projects", "proj1", "proj2"),
        )
        calls: list[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(main(), eq=0)
        tm.that(calls[0].project_names, eq=["proj1", "proj2"])
