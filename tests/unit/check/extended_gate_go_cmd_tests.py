from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import (
    FlextInfraGoGate,
    FlextInfraMarkdownGate,
    m,
)
from tests import t, u


def run_command_failure_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    gate_class: t.Infra.Tests.GateClass,
) -> tuple[bool, str]:
    """Test _run failure by patching run_raw to return r.fail()."""
    monkeypatch.setattr(
        u.Cli,
        "run_raw",
        u.Infra.Tests.create_fake_run_raw("execution failed"),
    )
    gate = gate_class(tmp_path)
    result = gate._run(["echo"], tmp_path)
    return result.exit_code == 0, result.stderr


class TestsExtendedGateGoCmd:
    """Test FlextInfraWorkspaceChecker._run_go method."""

    def test_run_go_no_go_mod(self, tmp_path: Path) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        workspace_root = tmp_path
        result = u.Infra.Tests.run_gate_check(
            FlextInfraGoGate, workspace_root, proj_dir
        )
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_go_with_vet_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        workspace_root = tmp_path
        (proj_dir / "go.mod").write_text("module test")
        u.Infra.Tests.patch_gate_run_sequence(
            monkeypatch,
            FlextInfraGoGate,
            [
                u.Infra.Tests.stub_run(
                    stdout="main.go:10:5: error message", returncode=1
                ),
                u.Infra.Tests.stub_run(),
            ],
        )
        result = u.Infra.Tests.run_gate_check(
            FlextInfraGoGate, workspace_root, proj_dir
        )
        tm.that(not result.result.passed, eq=True)

    def test_run_go_with_format_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        workspace_root = tmp_path
        (proj_dir / "go.mod").write_text("module test")
        (proj_dir / "main.go").write_text("package main")
        u.Infra.Tests.patch_gate_run_sequence(
            monkeypatch,
            FlextInfraGoGate,
            [
                u.Infra.Tests.stub_run(),
                u.Infra.Tests.stub_run(stdout="main.go", returncode=1),
            ],
        )
        result = u.Infra.Tests.run_gate_check(
            FlextInfraGoGate, workspace_root, proj_dir
        )
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_go_without_parseable_vet_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, proj_dir = u.Infra.Tests.create_checker_project(tmp_path)
        workspace_root = tmp_path
        (proj_dir / "go.mod").write_text("module test")
        u.Infra.Tests.patch_gate_run_sequence(
            monkeypatch,
            FlextInfraGoGate,
            [
                u.Infra.Tests.stub_run(stderr="go vet failed", returncode=1),
                u.Infra.Tests.stub_run(),
            ],
        )
        result = u.Infra.Tests.run_gate_check(
            FlextInfraGoGate, workspace_root, proj_dir
        )
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)


class TestWorkspaceCheckerRunCommand:
    """Test FlextInfraWorkspaceChecker._run method."""

    def test_run_command_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "go.mod").write_text("module test")
        monkeypatch.setattr(
            u.Cli,
            "run_raw",
            u.Infra.Tests.create_fake_run_raw(
                r[m.Cli.CommandOutput].ok(u.Infra.Tests.stub_run()),
            ),
        )
        gate = FlextInfraGoGate(tmp_path)
        result = gate.check(
            tmp_path,
            m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=True)

    def test_run_command_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "go.mod").write_text("module test")
        passed, raw_output = run_command_failure_check(
            monkeypatch,
            tmp_path,
            FlextInfraGoGate,
        )
        tm.that(not passed, eq=True)
        tm.that(raw_output, contains="execution failed")


class TestWorkspaceCheckerCollectMarkdownFiles:
    """Test FlextInfraWorkspaceChecker._collect_markdown_files method."""

    def test_collect_markdown_files_finds_files(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / "docs").mkdir()
        (proj_dir / "docs" / "guide.md").write_text("# Guide")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=2)

    def test_collect_markdown_files_excludes_dirs(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1", with_git=True)
        (proj_dir / "README.md").write_text("# Test")
        (proj_dir / ".git" / "README.md").write_text("# Git")
        files = FlextInfraMarkdownGate(tmp_path)._collect_markdown_files(proj_dir)
        tm.that(len(files), eq=1)
