from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import u


class TestDetectionUncoveredLines:
    def test_run_deptry_with_non_dict_issue(
        self,
        tmp_path: Path,
    ) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("", encoding="utf-8")
        out_file = project / ".deptry-report.json"
        u.Cli.json_write(out_file, ["not_a_dict", {"error": {"code": "DEP001"}}])
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )
        issues, exit_code = tm.ok(
            service.run_deptry(project, venv_bin, json_output_path=out_file),
        )
        tm.that(len(issues), eq=1)
        tm.that(exit_code, eq=0)

    def test_run_pip_check_with_empty_output(
        self,
        tmp_path: Path,
    ) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "pip").write_text("", encoding="utf-8")
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )
        lines, exit_code = tm.ok(service.run_pip_check(tmp_path, venv_bin))
        tm.that(lines, eq=[])
        tm.that(exit_code, eq=0)

    def test_get_required_typings_with_limits_applied(
        self,
        tmp_path: Path,
    ) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("", encoding="utf-8")
        limits_path = tmp_path / "dependency_limits.toml"
        limits_path.write_text(
            "[python]\nversion = '3.13'\n",
            encoding="utf-8",
        )
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )
        report = tm.ok(
            service.get_required_typings(tmp_path, venv_bin, limits_path=limits_path),
        )
        tm.that(report.limits_applied, eq=True)
        tm.that(report.python_version, eq="3.13")
