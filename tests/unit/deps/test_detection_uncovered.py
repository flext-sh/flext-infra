"""Test detection uncovered behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsDetectionUncovered:
    """Test flext infra deps detection uncovered behavior."""

    def test_run_deptry_with_non_dict_issue(self, tmp_path: Path) -> None:
        """Verify run deptry with non dict issue."""
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("", encoding="utf-8")
        out_file = project / ".deptry-report.json"
        payload = t.Cli.JSON_LIST_ADAPTER.validate_python([
            "not_a_dict",
            {"error": {"code": "DEP001"}},
        ])
        u.Cli.json_write(out_file, payload)
        service = u.Tests.create_deptry_service(
            command_output=u.Tests.create_command_output()
        )
        deptry_result: t.Pair[t.SequenceOf[t.JsonMapping], int] = tm.ok(
            service.run_deptry(project, venv_bin, json_output_path=out_file)
        )
        issues, exit_code = deptry_result
        tm.that(len(issues), eq=1)
        tm.that(exit_code, eq=0)

    def test_run_pip_check_with_empty_output(self, tmp_path: Path) -> None:
        """Verify run pip check with empty output."""
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "pip").write_text("", encoding="utf-8")
        service = u.Tests.create_deptry_service(
            command_output=u.Tests.create_command_output()
        )
        pip_check_result: t.Pair[t.StrSequence, int] = tm.ok(
            service.run_pip_check(tmp_path, venv_bin)
        )
        lines, exit_code = pip_check_result
        tm.that(list(lines), eq=[])
        tm.that(exit_code, eq=0)
