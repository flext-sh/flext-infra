from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, t, u


class TestDiscoverProjectPathsDeptry:
    def test_success(self, tmp_path: Path) -> None:
        project = u.Infra.Tests.create_project_info(
            tmp_path / "test-project",
        )
        project.path.mkdir()
        (project.path / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        service = u.Infra.Tests.create_deptry_service(projects=[project])

        result = service.discover_project_paths(tmp_path)

        tm.ok(result)
        tm.that(result.value, eq=[project.path])

    def test_failure(self, tmp_path: Path) -> None:
        service = u.Infra.Tests.create_deptry_service(
            selection_error="selector failed",
        )

        tm.fail(service.discover_project_paths(tmp_path))

    def test_filters_without_pyproject(self, tmp_path: Path) -> None:
        project = u.Infra.Tests.create_project_info(
            tmp_path / "empty-project",
            name="empty-project",
        )
        project.path.mkdir()
        service = u.Infra.Tests.create_deptry_service(projects=[project])

        result = service.discover_project_paths(tmp_path)

        tm.ok(result)
        tm.that(result.value, empty=True)


class TestRunDeptry:
    def test_success_with_issues(
        self,
        tmp_path: Path,
        deptry_report_payload: t.JsonPayload,
    ) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "test-project-dir"
        project.mkdir()
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        out_file = project / ".deptry-report.json"
        write_result = u.Cli.json_write(out_file, deptry_report_payload)
        tm.ok(write_result)
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )

        result = service.run_deptry(project, venv_bin, json_output_path=out_file)

        tm.ok(result)
        issues, exit_code = result.value
        tm.that(exit_code, eq=0)
        tm.that(len(issues), eq=1)

    def test_no_config_file(self, tmp_path: Path) -> None:
        service = u.Infra.Tests.create_deptry_service()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "test-project-dir"
        project.mkdir()

        result = service.run_deptry(project, venv_bin)

        tm.ok(result)
        tm.that(result.value, eq=([], 0))

    def test_runner_failure(self, tmp_path: Path) -> None:
        service = u.Infra.Tests.create_deptry_service(
            run_error="runner failed",
        )
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "test-project-dir"
        project.mkdir()
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        tm.fail(service.run_deptry(project, venv_bin))

    def test_invalid_and_empty_json_output(self, tmp_path: Path) -> None:
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "test-project-dir"
        project.mkdir()
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        for payload in ("{ invalid json }", ""):
            out_file = project / ".deptry-report.json"
            out_file.write_text(payload, encoding=c.Cli.ENCODING_DEFAULT)

            result = service.run_deptry(project, venv_bin, json_output_path=out_file)

            tm.ok(result)
            tm.that(result.value, eq=([], 0))

    def test_with_extend_exclude_and_cleanup(self, tmp_path: Path) -> None:
        service = u.Infra.Tests.create_deptry_service(
            command_output=u.Infra.Tests.create_command_output(),
        )
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "test-project-dir"
        project.mkdir()
        (project / c.Infra.PYPROJECT_FILENAME).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        default_out = project / ".deptry-report.json"
        default_out.write_text("[]", encoding=c.Cli.ENCODING_DEFAULT)

        extend_result = service.run_deptry(
            project,
            venv_bin,
            extend_exclude=["tests", "docs"],
        )
        default_result = service.run_deptry(project, venv_bin)

        tm.ok(extend_result)
        tm.ok(default_result)
        tm.that(default_out.exists(), eq=False)
