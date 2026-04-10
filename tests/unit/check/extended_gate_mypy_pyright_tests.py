"""Public Mypy and Pyright gate behavior tests using protocol runners."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfraMypyGate, FlextInfraPyrightGate, m
from tests import p, t, u


class TestTypeGates:
    """Declarative public-contract tests for Python type gates."""

    @staticmethod
    def make_ctx(root: Path) -> m.Infra.GateContext:
        return m.Infra.GateContext(workspace=root, reports_dir=root)

    @staticmethod
    def make_runner(
        *results: r[m.Cli.CommandOutput],
    ) -> p.Cli.CommandRunner:
        return u.Infra.Tests.SequenceRunner(list(results))

    @pytest.mark.parametrize(
        ("gate_class", "project_has_src", "runner_result", "passed", "issues_len"),
        [
            (FlextInfraMypyGate, False, None, True, 0),
            (
                FlextInfraMypyGate,
                True,
                u.Infra.Tests.ok_result(
                    u.Infra.Tests.stub_run(
                        stdout='{"file": "a.py", "line": 1, "column": 0, "code": "E001", "message": "Error", "severity": "error"}',
                        returncode=1,
                    ),
                ),
                False,
                1,
            ),
            (FlextInfraPyrightGate, False, None, True, 0),
            (
                FlextInfraPyrightGate,
                True,
                u.Infra.Tests.ok_result(
                    u.Infra.Tests.stub_run(
                        stdout='{"generalDiagnostics": [{"file": "a.py", "range": {"start": {"line": 0, "character": 0}}, "rule": "E001", "message": "Error", "severity": "error"}]}',
                        returncode=1,
                    ),
                ),
                False,
                1,
            ),
            (
                FlextInfraPyrightGate,
                True,
                u.Infra.Tests.ok_result(
                    u.Infra.Tests.stub_run(stdout="invalid json", returncode=1),
                ),
                False,
                0,
            ),
        ],
    )
    def test_check(
        self,
        tmp_path: Path,
        gate_class: t.Infra.Tests.GateClass,
        project_has_src: bool,
        runner_result: r[m.Cli.CommandOutput] | None,
        passed: bool,
        issues_len: int,
    ) -> None:
        project_dir = u.Infra.Tests.mk_project(tmp_path, "type-project")
        if project_has_src:
            (project_dir / "src").mkdir()
            (project_dir / "src" / "main.py").write_text("# code\n", encoding="utf-8")

        gate = gate_class(
            tmp_path,
            runner=self.make_runner(runner_result)
            if runner_result is not None
            else None,
        )
        result = gate.check(project_dir, self.make_ctx(tmp_path))

        tm.that(result.result.passed, eq=passed)
        tm.that(len(result.issues), eq=issues_len)


__all__: t.StrSequence = []
