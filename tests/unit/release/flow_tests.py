"""Tests for release main() orchestration flow.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from types import SimpleNamespace

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm
from tests import m, u

from flext_core import r
from flext_infra import cli as release_cli, main as infra_main


def main(argv: list[str] | None = None) -> int:
    args = ["release"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


def _patch_main_deps(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    *,
    root_result: r[Path] | None = None,
    release_result: r[bool] | None = None,
    capture: MutableSequence[SimpleNamespace] | None = None,
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

    monkeypatch.setattr(release_cli, "FlextInfraReleaseOrchestrator", _Or)


def _argv(tmp_path: Path, *extra: str) -> list[str]:
    return ["run", "--workspace", str(tmp_path), *extra]


class TestReleaseMainFlow:
    """Test main() orchestration."""

    def test_main_success(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        _patch_main_deps(monkeypatch, tmp_path)
        tm.that(
            main(argv=_argv(tmp_path, "--phase", "validate", "--interactive", "0")),
            eq=0,
        )

    def test_main_workspace_root_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _patch_main_deps(
            monkeypatch,
            tmp_path,
            root_result=r[Path].fail("not found"),
        )
        tm.that(
            main(argv=_argv(tmp_path, "--phase", "validate", "--interactive", "0")),
            eq=1,
        )

    def test_main_version_resolution_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _patch_main_deps(monkeypatch, tmp_path)

        def _parse_semver_fail(version: str) -> r[str]:
            return r[str].fail("invalid")

        monkeypatch.setattr(
            u.Infra,
            "parse_semver",
            staticmethod(_parse_semver_fail),
        )
        tm.that(
            main(argv=_argv(tmp_path, "--phase", "version", "--version", "invalid")),
            eq=1,
        )

    def test_main_release_failure(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _patch_main_deps(
            monkeypatch,
            tmp_path,
            release_result=r[bool].fail("release failed"),
        )
        tm.that(
            main(argv=_argv(tmp_path, "--phase", "validate", "--interactive", "0")),
            eq=1,
        )

    def test_main_all_phases(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        calls: MutableSequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(
            main(argv=_argv(tmp_path, "--phase", "all", "--interactive", "0")),
            eq=0,
        )
        tm.that(calls[0].phases, eq=["validate", "version", "build", "publish"])

    def test_main_with_push(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        calls: MutableSequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(
            main(
                argv=_argv(
                    tmp_path, "--phase", "validate", "--push", "--interactive", "0"
                ),
            ),
            eq=0,
        )
        tm.that(calls[0].push, eq=True)

    def test_main_with_dry_run(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        calls: MutableSequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(
            main(
                argv=_argv(
                    tmp_path,
                    "--phase",
                    "validate",
                    "--no-apply",
                    "--interactive",
                    "0",
                ),
            ),
            eq=0,
        )
        tm.that(calls[0].dry_run, eq=True)

    def test_main_with_projects(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        calls: MutableSequence[SimpleNamespace] = []
        _patch_main_deps(monkeypatch, tmp_path, capture=calls)
        tm.that(
            main(
                argv=_argv(
                    tmp_path,
                    "--phase",
                    "validate",
                    "--projects",
                    "proj1",
                    "--projects",
                    "proj2",
                ),
            ),
            eq=0,
        )
        tm.that(calls[0].project_names, eq=["proj1", "proj2"])
