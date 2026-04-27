from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService, m
from tests import p, t, u


class TestsFlextInfraDepsDetectionPipCheck:
    @staticmethod
    def make_runner(result: p.Result[m.Cli.CommandOutput]) -> p.Cli.CommandRunner:
        return u.Tests.DeptryRunner(result)

    @pytest.mark.parametrize(
        ("create_pip", "runner", "expected_lines", "expected_exit_code", "failed"),
        [
            (False, None, [], 0, False),
            (
                True,
                u.Tests.command_runner(
                    stdout="pkg1 has requirement\npkg2 conflict\n",
                    returncode=1,
                ),
                ["pkg1 has requirement", "pkg2 conflict"],
                1,
                False,
            ),
            (
                True,
                u.Tests.DeptryRunner(
                    u.Tests.fail_result("pip failed"),
                ),
                [],
                0,
                True,
            ),
            (
                True,
                u.Tests.command_runner(),
                [],
                0,
                False,
            ),
        ],
    )
    def test_run_pip_check(
        self,
        tmp_path: Path,
        create_pip: bool,
        runner: p.Cli.CommandRunner | None,
        expected_lines: t.StrSequence,
        expected_exit_code: int,
        failed: bool,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        service.runner = runner
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        if create_pip:
            (venv_bin / "pip").write_text("", encoding="utf-8")

        result = service.run_pip_check(tmp_path, venv_bin)

        if failed:
            tm.fail(result)
            return

        lines, exit_code = tm.ok(result)
        tm.that(lines, eq=expected_lines)
        tm.that(exit_code, eq=expected_exit_code)


__all__: t.StrSequence = []
