"""Public Mypy and Pyright gate behavior tests using protocol runners.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m, p, r
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyright import FlextInfraPyrightGate
from tests import TestsFlextInfraUtilities as u


class TestTypeGates:
    """Declarative public-contract tests for Python type gates."""

    @staticmethod
    def make_ctx(root: Path) -> p.Infra.GateContext:
        """Build a gate context rooted in the temporary workspace."""
        return m.Infra.GateContext(workspace=root, reports_dir=root)

    @staticmethod
    def make_runner(*results: p.Result[p.Cli.CommandOutput]) -> p.Cli.CommandRunner:
        """Build a deterministic command runner from prepared results."""
        return u.Tests.SequenceRunner(list(results))

    @pytest.mark.parametrize(
        ("gate_class", "project_has_src", "runner_result", "passed", "issues_len"),
        [
            (FlextInfraMypyGate, False, None, True, 0),
            (
                FlextInfraMypyGate,
                True,
                r.ok(
                    u.Tests.stub_run(
                        stdout=(
                            '{"file": "a.py", "line": 1, "column": 0, '
                            '"code": "E001", "message": "Error", '
                            '"severity": "error"}'
                        ),
                        returncode=1,
                    )
                ),
                False,
                1,
            ),
            (FlextInfraPyrightGate, False, None, True, 0),
            (
                FlextInfraPyrightGate,
                True,
                r.ok(
                    u.Tests.stub_run(
                        stdout=(
                            '{"generalDiagnostics": [{"file": "a.py", '
                            '"range": {"start": {"line": 0, '
                            '"character": 0}}, "rule": "E001", '
                            '"message": "Error", "severity": "error"}]}'
                        ),
                        returncode=1,
                    )
                ),
                False,
                1,
            ),
            (
                FlextInfraPyrightGate,
                True,
                r.ok(u.Tests.stub_run(stdout="invalid json", returncode=1)),
                False,
                1,
            ),
        ],
    )
    def test_check(
        self,
        tmp_path: Path,
        gate_class: type[FlextInfraGate],
        *,
        project_has_src: bool,
        runner_result: p.Result[p.Cli.CommandOutput] | None,
        passed: bool,
        issues_len: int,
    ) -> None:
        """Report Mypy and Pyright outcomes through the shared gate contract."""
        project_dir = u.Tests.mk_project(tmp_path, "type-project")
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

    def test_mypy_file_scope_honors_configured_exclude(self, tmp_path: Path) -> None:
        """Keep excluded test modules out of an explicit Mypy file scope."""
        project_dir = u.Tests.mk_project(
            tmp_path,
            "mypy-file-scope",
            pyproject='[tool.mypy]\nexclude = "^(?:tests)(?:/|$)"\n',
        )
        source_file = project_dir / "src" / "main.py"
        test_file = project_dir / "tests" / "test_main.py"
        source_file.parent.mkdir()
        test_file.parent.mkdir()
        source_file.write_text("value: int = 1\n", encoding="utf-8")
        test_file.write_text("value: int = 1\n", encoding="utf-8")
        runner = u.Tests.SequenceRunner([r.ok(u.Tests.stub_run())])
        gate = FlextInfraMypyGate(tmp_path, runner=runner)

        result = gate.check_files(
            (source_file, test_file), project_dir, self.make_ctx(tmp_path)
        )

        tm.that(result.result.passed, eq=True)
        tm.that(runner.commands[0], has="src/main.py", lacks="tests/test_main.py")


__all__: list[str] = []
