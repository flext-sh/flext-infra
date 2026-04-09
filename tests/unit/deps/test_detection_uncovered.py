from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService
from tests import m, r, t, u


class _StubRunner:
    def __init__(self, result: r[m.Cli.CommandOutput]) -> None:
        self._result = result

    def run_raw(
        self,
        *args: t.Infra.InfraValue,
        **kwargs: t.Infra.InfraValue,
    ) -> r[m.Cli.CommandOutput]:
        _ = args
        _ = kwargs
        return self._result


class TestDetectionUncoveredLines:
    def test_run_deptry_with_non_dict_issue(
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
        u.Cli.json_write(out_file, ["not_a_dict", {"error": {"code": "DEP001"}}])
        out = m.Cli.CommandOutput(exit_code=0, stdout="", stderr="")
        monkeypatch.setattr(
            service,
            "runner",
            _StubRunner(r[m.Cli.CommandOutput].ok(out)),
        )
        issues, _ = tm.ok(
            service.run_deptry(project, venv_bin, json_output_path=out_file),
        )
        tm.that(len(issues), eq=1)

    def test_run_pip_check_with_empty_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "pip").write_text("")
        out = m.Cli.CommandOutput(exit_code=0, stdout="", stderr="")
        monkeypatch.setattr(
            service,
            "runner",
            _StubRunner(r[m.Cli.CommandOutput].ok(out)),
        )
        lines, exit_code = tm.ok(service.run_pip_check(tmp_path, venv_bin))
        tm.that(lines, eq=[])
        tm.that(exit_code, eq=0)

    def test_get_required_typings_with_limits_applied(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("")
        out = m.Cli.CommandOutput(exit_code=0, stdout="", stderr="")
        monkeypatch.setattr(
            service,
            "runner",
            _StubRunner(r[m.Cli.CommandOutput].ok(out)),
        )

        class _Toml:
            def __init__(self) -> None:
                self._i = 0

            def read_plain(self, path: Path) -> r[Mapping[str, t.Infra.InfraValue]]:
                _ = path
                self._i += 1
                if self._i == 1:
                    return r[t.Infra.ContainerDict].ok({"python": {"version": "3.13"}})
                return r[t.Infra.ContainerDict].ok({})

        report = tm.ok(service.get_required_typings(tmp_path, venv_bin))
        tm.that(report.limits_applied, eq=True)
