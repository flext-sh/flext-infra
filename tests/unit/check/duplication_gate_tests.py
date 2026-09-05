"""Observable contract tests for the real jscpd duplication gate.

The shared project fixture supplies an isolated Python package and the public
test facade invokes the mise-provisioned detector. No runner double, environment
rewrite, warning capture, or hand-authored successful report participates in
these tests: detector output is the authority.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraDuplicationGate, c, m
from flext_tests import tm
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path

_DUPLICATED_MODULE = """\
def normalize_records(records: list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for record in records:
        candidate = record.strip().casefold()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(sorted(normalized))
"""


def _report_path(project: Path) -> Path:
    return project / c.Infra.JSCPD_REPORT_DIRNAME / c.Infra.JSCPD_REPORT_FILENAME


def _run_gate(project: Path) -> m.Infra.GateExecution:
    return u.Tests.run_gate_check(
        FlextInfraDuplicationGate,
        project,
        project,
        reports_dir=project / c.Infra.JSCPD_REPORT_DIRNAME,
    )


def _write_clone_pair(project: Path) -> t.StrSequence:
    relative_paths = ("src/clone_alpha.py", "src/clone_beta.py")
    for relative_path in relative_paths:
        (project / relative_path).write_text(_DUPLICATED_MODULE, encoding="utf-8")
    return relative_paths


class TestDuplicationGate:
    def test_real_clone_is_red(self, real_python_package: Path) -> None:
        expected_files = _write_clone_pair(real_python_package)

        execution = _run_gate(real_python_package)

        tm.that(execution.result.passed, eq=False)
        tm.that(
            sorted({issue.file for issue in execution.issues}),
            eq=sorted(expected_files),
        )
        tm.that(
            all(
                issue.code == FlextInfraDuplicationGate.gate_id
                for issue in execution.issues
            ),
            eq=True,
        )
        tm.that(
            all(
                issue.severity == c.Infra.GateSeverity.ERROR.value
                for issue in execution.issues
            ),
            eq=True,
        )

    def test_real_clean_project_is_green(self, real_python_package: Path) -> None:
        execution = _run_gate(real_python_package)

        tm.that(execution.result.passed, eq=True)
        tm.that(execution.issues, eq=())
        tm.that(execution.result.errors, eq=())

    def test_real_scan_replaces_stale_report(self, real_python_package: Path) -> None:
        duplicate_files = _write_clone_pair(real_python_package)
        report_path = _report_path(real_python_package)
        first = _run_gate(real_python_package)
        tm.that(first.result.passed, eq=False)
        tm.that(report_path.is_file(), eq=True)
        for relative_path in duplicate_files:
            (real_python_package / relative_path).unlink()

        second = _run_gate(real_python_package)

        tm.that(second.result.passed, eq=True)
        tm.that(second.issues, eq=())
        fresh = u.Cli.json_as_mapping(
            u.Cli.json_parse(report_path.read_text(encoding="utf-8")).unwrap()
        )
        tm.that(u.Cli.json_deep_mapping_list(fresh, "duplicates"), eq=[])

    def test_real_report_write_failure_is_causal(
        self, real_python_package: Path
    ) -> None:
        report_path = _report_path(real_python_package)
        report_path.mkdir(parents=True)

        with pytest.raises(ValueError, match="report target is not a physical file"):
            _run_gate(real_python_package)


__all__: t.StrSequence = []
