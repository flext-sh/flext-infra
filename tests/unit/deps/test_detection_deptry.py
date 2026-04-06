from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, t

from flext_cli import u
from flext_infra import FlextInfraDependencyDetectionService


class _FakeResult:
    def __init__(
        self,
        success: bool,
        value: Sequence[m.Infra.ProjectInfo] | m.Cli.CommandOutput | None = None,
        error: str | None = None,
    ) -> None:
        self.is_success = success
        self.is_failure = not success
        self.value = value
        self.error = error


class _StubRunner:
    def __init__(self, result: _FakeResult) -> None:
        self._result = result

    def run_raw(
        self,
        *args: t.Infra.InfraValue,
        **kwargs: t.Infra.InfraValue,
    ) -> _FakeResult:
        _ = args
        _ = kwargs
        return self._result


class _StubSelector:
    def __init__(self, result: _FakeResult) -> None:
        self._result = result

    def resolve_projects(
        self,
        workspace_root: Path,
        names: t.StrSequence,
    ) -> _FakeResult:
        _ = workspace_root
        _ = names
        return self._result


class TestDiscoverProjects:
    def test_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        service = FlextInfraDependencyDetectionService()
        proj = m.Infra.ProjectInfo(
            name="proj",
            path=tmp_path / "proj",
            stack="py",
        )
        proj.path.mkdir()
        (proj.path / "pyproject.toml").write_text("")
        monkeypatch.setattr(
            service,
            "selector",
            _StubSelector(_FakeResult(True, [proj])),
        )
        result = service.discover_project_paths(tmp_path)
        tm.that(result.is_success, eq=True)
        if result.is_success:
            tm.that(len(result.value), eq=1)

    def test_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        service = FlextInfraDependencyDetectionService()
        monkeypatch.setattr(
            service,
            "selector",
            _StubSelector(_FakeResult(False, error="failed")),
        )
        tm.fail(service.discover_project_paths(tmp_path))

    def test_filters_without_pyproject(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        proj = m.Infra.ProjectInfo(
            name="no-pyproject",
            path=tmp_path / "no-pyproject",
            stack="py",
        )
        proj.path.mkdir()
        monkeypatch.setattr(
            service,
            "selector",
            _StubSelector(_FakeResult(True, [proj])),
        )
        result = service.discover_project_paths(tmp_path)
        tm.that(result.is_success, eq=True)
        if result.is_success:
            tm.that(result.value, eq=[])


class TestRunDeptry:
    def test_success_with_issues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        out_file = project / ".deptry-report.json"
        u.Cli.json_write(out_file, [{"error": {"code": "DEP001"}, "module": "foo"}])
        cmd_out = m.Cli.CommandOutput(
            exit_code=0,
            stdout="",
            stderr="",
            duration=0.0,
        )
        monkeypatch.setattr(service, "runner", _StubRunner(_FakeResult(True, cmd_out)))
        result = service.run_deptry(project, venv_bin, json_output_path=out_file)
        tm.that(result.is_success, eq=True)
        if result.is_success:
            issues, exit_code = result.value
            tm.that(exit_code, eq=0)
            tm.that(len(issues), eq=1)

    def test_no_config_file(self, tmp_path: Path) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        result = service.run_deptry(project, venv_bin)
        tm.that(result.is_success, eq=True)
        if result.is_success:
            assert result.value == ([], 0)

    def test_runner_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        monkeypatch.setattr(
            service,
            "runner",
            _StubRunner(_FakeResult(False, error="deptry crash")),
        )
        tm.fail(service.run_deptry(project, venv_bin))

    def test_invalid_and_empty_json_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        cmd_out = m.Cli.CommandOutput(
            exit_code=0,
            stdout="",
            stderr="",
            duration=0.0,
        )
        monkeypatch.setattr(service, "runner", _StubRunner(_FakeResult(True, cmd_out)))
        for payload in ["not valid json", ""]:
            out_file = project / ".deptry-report.json"
            out_file.write_text(payload)
            result = service.run_deptry(project, venv_bin, json_output_path=out_file)
            tm.that(result.is_success, eq=True)
            if result.is_success:
                assert result.value == ([], 0)

    def test_with_extend_exclude_and_cleanup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        default_out = project / ".deptry-report.json"
        default_out.write_text("[]")
        cmd_out = m.Cli.CommandOutput(
            exit_code=0,
            stdout="",
            stderr="",
            duration=0.0,
        )
        monkeypatch.setattr(service, "runner", _StubRunner(_FakeResult(True, cmd_out)))
        tm.that(
            service.run_deptry(
                project,
                venv_bin,
                extend_exclude=["tests", "docs"],
            ).is_success,
            eq=True,
        )
        tm.that(service.run_deptry(project, venv_bin).is_success, eq=True)
        tm.that(not default_out.exists(), eq=True)
