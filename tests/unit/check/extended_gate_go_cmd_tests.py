"""Public Go gate behavior tests using protocol runners."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraGoGate, m
from tests import p, r, t, u


class TestGoGate:
    """Declarative public-contract tests for Go gate execution."""

    @staticmethod
    def make_ctx(root: Path) -> m.Infra.GateContext:
        return m.Infra.GateContext(workspace=root, reports_dir=root)

    @staticmethod
    def make_runner(
        *results: p.Result[m.Cli.CommandOutput],
    ) -> p.Cli.CommandRunner:
        return u.Infra.Tests.SequenceRunner(list(results))

    @pytest.mark.parametrize(
        ("go_mod", "go_file", "runner_results", "passed", "issues_len", "error_text"),
        [
            (False, False, (), True, 0, ""),
            (
                True,
                False,
                (
                    u.Infra.Tests.ok_result(
                        u.Infra.Tests.stub_run(
                            stdout="main.go:10:5: error message",
                            returncode=1,
                        ),
                    ),
                    u.Infra.Tests.ok_result(u.Infra.Tests.stub_run()),
                ),
                False,
                1,
                "",
            ),
            (
                True,
                True,
                (
                    u.Infra.Tests.ok_result(u.Infra.Tests.stub_run()),
                    u.Infra.Tests.ok_result(
                        u.Infra.Tests.stub_run(stdout="main.go", returncode=1),
                    ),
                ),
                False,
                1,
                "",
            ),
            (
                True,
                False,
                (
                    u.Infra.Tests.ok_result(
                        u.Infra.Tests.stub_run(stderr="go vet failed", returncode=1),
                    ),
                    u.Infra.Tests.ok_result(u.Infra.Tests.stub_run()),
                ),
                False,
                0,
                "",
            ),
            (
                True,
                False,
                (u.Infra.Tests.fail_result("execution failed"),),
                False,
                0,
                "execution failed",
            ),
        ],
    )
    def test_check(
        self,
        tmp_path: Path,
        go_mod: bool,
        go_file: bool,
        runner_results: tuple[r[m.Cli.CommandOutput], ...],
        passed: bool,
        issues_len: int,
        error_text: str,
    ) -> None:
        project_dir = u.Infra.Tests.mk_project(tmp_path, "go-project")
        if go_mod:
            (project_dir / "go.mod").write_text("module test\n", encoding="utf-8")
        if go_file:
            (project_dir / "main.go").write_text("package main\n", encoding="utf-8")

        gate = FlextInfraGoGate(
            tmp_path,
            runner=self.make_runner(*runner_results) if runner_results else None,
        )
        result = gate.check(project_dir, self.make_ctx(tmp_path))

        tm.that(result.result.passed, eq=passed)
        tm.that(len(result.issues), eq=issues_len)
        if error_text:
            tm.that(result.raw_output, contains=error_text)


__all__: t.StrSequence = []
