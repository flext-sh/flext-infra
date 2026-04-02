"""Tests for CLI entry surfaces: workspace_check, fix_pyrefly_config, check group, run_cli.

Uses monkeypatch to inject controlled service behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest
from flext_tests import tm

import flext_infra.check.workspace_check as ws_mod
import flext_infra.deps.fix_pyrefly_config as fix_pyrefly_mod
from flext_core import r
from flext_infra import (
    FlextInfraCliCheck,
    FlextInfraWorkspaceChecker,
    main as infra_main,
)
from tests import m, t


def _fake_checker_cls(
    parse_result: t.StrSequence,
    run_result: (
        r[Sequence[SimpleNamespace]]
        | r[Sequence[m.Infra.ProjectResult]]
        | r[list[SimpleNamespace]]
        | r[list[m.Infra.ProjectResult]]
    ),
) -> type:
    class _Fake:
        def __init__(self, **_kw: t.Scalar) -> None:
            _ = _kw

        @staticmethod
        def parse_gate_csv(_gates: str) -> t.StrSequence:
            return parse_result

        def run_projects(
            self,
            projects: t.StrSequence | None = None,
            gates: t.StrSequence | None = None,
            **kw: t.Scalar,
        ) -> (
            r[Sequence[SimpleNamespace]]
            | r[Sequence[m.Infra.ProjectResult]]
            | r[list[SimpleNamespace]]
            | r[list[m.Infra.ProjectResult]]
        ):
            _ = projects, gates, kw
            return run_result

    return _Fake


def _fake_fixer_cls(
    run_result: r[t.StrSequence],
) -> type:
    class _Fake:
        def __init__(self, **_kw: t.Scalar) -> None:
            _ = _kw

        def run(
            self,
            _projects: t.StrSequence | None = None,
            **kw: t.Scalar,
        ) -> r[t.StrSequence]:
            _ = _projects, kw
            return run_result

        @staticmethod
        def main(argv: t.StrSequence | None = None) -> int:
            _ = argv
            instance = _Fake()
            result = instance.run()
            return 0 if result.is_success else 1

    return _Fake


class TestWorkspaceCheckCLI:
    def test_no_projects_error(self) -> None:
        tm.that(ws_mod.main([]), eq=1)

    def test_with_projects_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ok_result = r[list[SimpleNamespace]].ok([SimpleNamespace(passed=True)])
        monkeypatch.setattr(
            ws_mod,
            "FlextInfraWorkspaceChecker",
            _fake_checker_cls(["lint"], ok_result),
        )
        tm.that(ws_mod.main(["p1", "--gates", "lint"]), eq=0)

    def test_with_projects_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ok_result = r[list[SimpleNamespace]].ok([SimpleNamespace(passed=False)])
        monkeypatch.setattr(
            ws_mod,
            "FlextInfraWorkspaceChecker",
            _fake_checker_cls(["lint"], ok_result),
        )
        tm.that(ws_mod.main(["p1", "--gates", "lint"]), eq=1)

    def test_run_projects_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fail_result = r[Sequence[SimpleNamespace]].fail("error")
        monkeypatch.setattr(
            ws_mod,
            "FlextInfraWorkspaceChecker",
            _fake_checker_cls(["lint"], fail_result),
        )
        tm.that(ws_mod.main(["p1", "--gates", "lint"]), eq=2)


class TestFixPyrelfyCLI:
    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_fixer_cls(r[t.StrSequence].ok([]))
        monkeypatch.setattr(
            fix_pyrefly_mod,
            "FlextInfraConfigFixer",
            fake,
        )
        tm.that(fix_pyrefly_mod.FlextInfraConfigFixer.main([]), eq=0)

    def test_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_fixer_cls(r[t.StrSequence].fail("error"))
        monkeypatch.setattr(
            fix_pyrefly_mod,
            "FlextInfraConfigFixer",
            fake,
        )
        tm.that(fix_pyrefly_mod.FlextInfraConfigFixer.main([]), eq=1)


def _const_cli_result(code: int) -> Callable[[t.StrSequence | None], int]:
    def _runner(argv: t.StrSequence | None = None) -> int:
        _ = argv
        return code

    return _runner


_fake_run_cli_zero = _const_cli_result(0)
_fake_run_cli_42 = _const_cli_result(42)


class TestCheckMainEntryPoint:
    def test_calls_run_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraCliCheck, "run", staticmethod(_fake_run_cli_zero))
        tm.that(infra_main(["check", "run"]), eq=0)

    def test_returns_exit_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraCliCheck, "run", staticmethod(_fake_run_cli_42))
        tm.that(infra_main(["check", "run"]), eq=42)


class TestRunCLIExtended:
    def test_fix_pyrefly_config_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            ws_mod,
            "FlextInfraConfigFixer",
            _fake_fixer_cls(r[t.StrSequence].ok([])),
        )
        tm.that(FlextInfraWorkspaceChecker.run_cli(["fix-pyrefly-config"]), eq=0)

    def test_fix_pyrefly_config_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            ws_mod,
            "FlextInfraConfigFixer",
            _fake_fixer_cls(r[t.StrSequence].fail("error")),
        )
        tm.that(FlextInfraWorkspaceChecker.run_cli(["fix-pyrefly-config"]), eq=1)

    def test_no_command_prints_help(self) -> None:
        tm.that(FlextInfraWorkspaceChecker.run_cli([]), eq=1)

    def test_with_relative_reports_dir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        gate = m.Infra.GateResult(
            gate="lint",
            project="p",
            passed=True,
            errors=[],
            duration=0.0,
        )
        gate_exec = m.Infra.GateExecution(result=gate, issues=[], raw_output="")
        project = m.Infra.ProjectResult(project="p", gates={"lint": gate_exec})
        ok_result = r[list[m.Infra.ProjectResult]].ok([project])

        def _fake_init(
            _self: ws_mod.FlextInfraWorkspaceChecker,
            **_kw: t.Scalar,
        ) -> None:
            pass

        def _fake_run_projects(
            _self: ws_mod.FlextInfraWorkspaceChecker,
            projects: t.StrSequence | None = None,
            gates: t.StrSequence | None = None,
            **kw: t.Scalar,
        ) -> r[list[m.Infra.ProjectResult]]:
            _ = projects, gates, kw
            return ok_result

        monkeypatch.setattr(FlextInfraWorkspaceChecker, "__init__", _fake_init)
        monkeypatch.setattr(
            FlextInfraWorkspaceChecker,
            "run_projects",
            _fake_run_projects,
        )
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
        exit_code = FlextInfraWorkspaceChecker.run_cli([
            "run",
            "--gates",
            "lint",
            "--project",
            "p",
            "--reports-dir",
            "reports/check",
        ])
        tm.that(exit_code, eq=0)
