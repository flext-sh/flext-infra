"""``run_deptry`` executes the environment's real ``deptry`` executable."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from tests import c, t, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsDetectionDeptry:
    """Behaviour of ``run_deptry`` against a deptry executable on disk."""

    @staticmethod
    def _environment(
        tmp_path: Path, report: str | None, *, exit_code: int = 0
    ) -> t.Pair[Path, Path]:
        """Create a project and a ``deptry`` that writes ``report`` as its JSON."""
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / c.PYPROJECT_FILENAME).write_text("", encoding=c.Cli.ENCODING_DEFAULT)
        write = ""
        if report is not None:
            payload = tmp_path / "deptry-payload.json"
            payload.write_text(report, encoding=c.Cli.ENCODING_DEFAULT)
            write = (
                'while [ "$#" -gt 0 ]; do\n'
                '  if [ "$1" = "--json-output" ]; then cp '
                f'"{payload}" "$2"; fi\n'
                "  shift\n"
                "done\n"
            )
        deptry = venv_bin / c.Infra.DEPTRY
        deptry.write_text(
            f"#!/bin/sh\n{write}exit {exit_code}\n", encoding=c.Cli.ENCODING_DEFAULT
        )
        deptry.chmod(0o755)
        return venv_bin, project

    def test_issues_and_exit_code_are_reported(
        self, tmp_path: Path, deptry_report_payload: t.JsonPayload
    ) -> None:
        source = tmp_path / "source-report.json"
        tm.ok(u.Cli.json_write(source, deptry_report_payload))
        report = source.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        venv_bin, project = self._environment(tmp_path, report, exit_code=1)

        issues, exit_code = tm.ok(
            FlextInfraDependencyDetectionService().run_deptry(project, venv_bin)
        )

        tm.that(exit_code, eq=1)
        tm.that(len(issues), eq=1)

    def test_project_without_config_is_skipped(self, tmp_path: Path) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()

        result = FlextInfraDependencyDetectionService().run_deptry(project, venv_bin)

        tm.that(tm.ok(result), eq=([], 0))

    def test_unlaunchable_deptry_is_a_failure(self, tmp_path: Path) -> None:
        venv_bin, project = self._environment(tmp_path, None)
        (venv_bin / c.Infra.DEPTRY).chmod(0o644)

        tm.fail(FlextInfraDependencyDetectionService().run_deptry(project, venv_bin))

    def test_invalid_or_empty_report_is_a_failure(self, tmp_path: Path) -> None:
        for index, report in enumerate(("{ invalid json }", "")):
            venv_bin, project = self._environment(tmp_path / str(index), report)

            result = FlextInfraDependencyDetectionService().run_deptry(
                project, venv_bin
            )

            tm.that(result.failure, eq=True)

    def test_non_mapping_issue_is_a_failure(self, tmp_path: Path) -> None:
        venv_bin, project = self._environment(
            tmp_path, '["not_a_dict", {"error": {"code": "DEP001"}}]'
        )

        result = FlextInfraDependencyDetectionService().run_deptry(project, venv_bin)

        tm.fail(result, has="must be a mapping")

    def test_default_report_is_removed_after_parsing(self, tmp_path: Path) -> None:
        venv_bin, project = self._environment(tmp_path, "[]")

        result = FlextInfraDependencyDetectionService().run_deptry(
            project, venv_bin, extend_exclude=["tests", "docs"]
        )

        tm.that(tm.ok(result), eq=([], 0))
        tm.that((project / ".deptry-report.json").exists(), eq=False)
