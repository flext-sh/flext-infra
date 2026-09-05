"""Tests for the blocking jscpd code-duplication gate.

The gate runs one workspace scan through the mise-provisioned ``jscpd``
binary, reads jscpd's JSON report from disk (jscpd never writes findings to
stdout), maps each clone cluster touching ``project_dir`` to one issue naming
its counterpart. Findings and failed/absent binaries are blocking issues, not
warnings. All assertions run
against a literal report fixture written by an owned temporary ``jscpd``
executable, exercising only the public gate boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, m, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.duplication import FlextInfraDuplicationGate
from flext_tests import tm
from tests import t

if TYPE_CHECKING:
    from pathlib import Path


def _project(tmp_path: Path) -> Path:
    """Materialize a discoverable standalone project at ``tmp_path``.

    ``src``/``tests`` carry one Python file each so the gate's scope
    resolution (``_existing_check_dirs``) selects both trees.
    """
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "src" / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "demo" / "a.py").write_text(
        "def first() -> int:\n"
        "    value = 1\n"
        "    return value\n\n"
        "def second() -> int:\n"
        "    value = 2\n"
        "    return value\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_behavior() -> None:\n    value = 1\n    assert value == 1\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    return tmp_path


def _report_fixture(project: Path) -> str:
    """Two clones: one fully inside ``project`` and one whose twin is foreign."""
    own_a = str(project / "src" / "demo" / "a.py")
    own_test = str(project / "tests" / "test_a.py")
    foreign = str(project.parent / "other-project" / "src" / "z.py")
    payload: t.JsonValue = {
        "duplicates": [
            {
                "format": "python",
                "lines": 12,
                "tokens": 61,
                "firstFile": {
                    "name": own_a,
                    "startLoc": {"line": 2, "column": 4},
                    "endLoc": {"line": 3, "column": 16},
                },
                "secondFile": {
                    "name": own_test,
                    "startLoc": {"line": 2, "column": 4},
                    "endLoc": {"line": 3, "column": 21},
                },
            },
            {
                "format": "python",
                "lines": 8,
                "tokens": 40,
                "firstFile": {"name": foreign, "startLoc": {"line": 1, "column": 0}},
                "secondFile": {
                    "name": own_a,
                    "startLoc": {"line": 6, "column": 2},
                    "endLoc": {"line": 7, "column": 16},
                },
            },
        ],
        "statistics": {},
    }
    rendered = u.Cli.json_dumps(payload).unwrap()
    tm.that(rendered, is_=str)
    validated: str = t.Infra.STR_ADAPTER.validate_python(rendered)
    return validated


def _runner_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    report: str | None,
    stderr: str = "",
    exit_code: int = 0,
) -> FlextInfraDuplicationGate:
    """Return a gate backed by a ``jscpd`` executable at the external boundary.

    Unlike a stdout-reporting scanner, the fake ``jscpd`` must locate the
    ``--output`` directory it is told to write into and place the report
    file there; ``report=None`` leaves no file behind (a crashed run).
    """
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    runner = binary_dir / c.Infra.JSCPD_BINARY
    report_name = c.Infra.JSCPD_REPORT_FILENAME
    write_report = (
        ""
        if report is None
        else (
            "output_dir = sys.argv[sys.argv.index('--output') + 1]\n"
            "os.makedirs(output_dir, exist_ok=True)\n"
            f"with open(os.path.join(output_dir, {report_name!r}), 'w') as fh:\n"
            f"    fh.write({report!r})\n"
        )
    )
    runner.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n\n"
        f"{write_report}"
        f"sys.stderr.write({stderr!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    monkeypatch.setenv("PATH", str(binary_dir), prepend=":")
    return FlextInfraDuplicationGate(tmp_path)


def _ctx(tmp_path: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path / "reports")


class TestDuplicationGate:
    def test_gate_identity(self) -> None:
        tm.that(FlextInfraDuplicationGate.gate_id, eq="duplication")
        tm.that(FlextInfraDuplicationGate.can_fix, eq=False)
        tm.that(FlextInfraDuplicationGate.tool_name, eq="jscpd")

    def test_registered_and_allowed(self) -> None:
        tm.that("duplication" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("duplication" in c.Infra.PROJECT_CHECK_GATES_ALLOWED_VALUES, eq=True)
        tm.that(
            "duplication" not in c.Infra.PROJECT_CHECK_GATES_FIXABLE_VALUES, eq=True
        )
        tm.that(
            FlextInfraGateRegistry.default().get("duplication") is not None, eq=True
        )

    def test_check_reports_each_clone_cluster_once_naming_its_twin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = _project(tmp_path)
        gate = _runner_gate(tmp_path, monkeypatch, report=_report_fixture(project))

        execution = gate.check(project, _ctx(tmp_path))

        issues = execution.issues
        # Clone 1 is one intra-project cluster. Clone 2 is one cross-project
        # cluster touching this project. The foreign side is never the issue file.
        tm.that(len(issues), eq=2)
        tm.that(
            sorted(issue.file for issue in issues),
            eq=["src/demo/a.py", "src/demo/a.py"],
        )
        tm.that(all(issue.code == "duplication" for issue in issues), eq=True)
        tm.that(
            all(
                str(project.parent / "other-project") not in issue.file
                for issue in issues
            ),
            eq=True,
        )
        by_line = {(issue.file, issue.line): issue for issue in issues}
        first = by_line["src/demo/a.py", 2]
        tm.that(first.column, eq=4)
        tm.that(first.message, has="12-line (61-token) clone of")
        tm.that(first.message, has="tests/test_a.py")
        foreign_twin = by_line["src/demo/a.py", 6]
        tm.that(foreign_twin.message, has="other-project/src/z.py")

    def test_findings_fail_the_gate_without_warning_normalization(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = _project(tmp_path)
        gate = _runner_gate(tmp_path, monkeypatch, report=_report_fixture(project))

        execution = gate.check(project, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=2)
        tm.that(len(execution.result.errors), eq=2)
        tm.that(
            all(
                issue.severity == c.Infra.GateSeverity.ERROR.value
                for issue in execution.issues
            ),
            eq=True,
        )

    def test_scan_is_cached_per_repository_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A second check in the same process reuses the first scan's report."""
        project = _project(tmp_path)
        gate = _runner_gate(tmp_path, monkeypatch, report=_report_fixture(project))
        first = gate.check(project, _ctx(tmp_path))
        # Retire the runner: a re-scan would now fail loudly instead of passing.
        (tmp_path / "bin" / c.Infra.JSCPD_BINARY).unlink()

        second = gate.check(project, _ctx(tmp_path))

        tm.that(len(second.issues), eq=len(first.issues))

    def test_crashed_runner_without_report_is_visible(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = _project(tmp_path)
        gate = _runner_gate(
            tmp_path, monkeypatch, report=None, stderr="jscpd exploded", exit_code=2
        )

        execution = gate.check(project, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(execution.issues[0].message, has="jscpd exploded")

    def test_missing_runner_is_visible(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = _project(tmp_path)
        (tmp_path / "empty-bin").mkdir()
        monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
        gate = FlextInfraDuplicationGate(tmp_path)

        execution = gate.check(project, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(execution.issues[0].message, has=c.Infra.JSCPD_BINARY)
        tm.that(execution.issues[0].message, has="not found")

    def test_config_is_rendered_from_typed_ssot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The scan-time config projection carries exactly the typed constants."""
        project = _project(tmp_path)
        gate = _runner_gate(tmp_path, monkeypatch, report=_report_fixture(project))
        _ = gate.check(project, _ctx(tmp_path))

        config_path = (
            tmp_path / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_CONFIG_FILENAME
        )
        tm.that(config_path.is_file(), eq=True)
        rendered = u.Cli.json_as_mapping(
            u.Cli.json_parse(config_path.read_text(encoding="utf-8")).unwrap()
        )
        tm.that(rendered["mode"], eq=c.Infra.JSCPD_MODE)
        tm.that(rendered["minLines"], eq=c.Infra.JSCPD_MIN_LINES)
        tm.that(rendered["ignore"], eq=list(c.Infra.JSCPD_IGNORE_PATTERNS))
        tm.that(rendered["reporters"], eq=["json"])


__all__: t.StrSequence = []
