"""Tests for the qlty code-smells gate (report-only posture, warnings always).

The gate parses a qlty SARIF payload into per-project issues, emits one
``FlextSmellViolation`` warning per finding on every run, and passes while
``SMELLS_GATE_MODE`` is WARN. A failed/absent scanner surfaces as a visible
issue instead of a silent pass. All assertions run against a literal SARIF
fixture seeded into the process-level scan cache — no subprocess.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_core import FlextSmellViolation, c as core_c
from flext_infra import c, m, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.smells import FlextInfraSmellsGate
from flext_infra.transformers.smells.boolean_logic import FlextInfraBooleanLogicFixer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from tests import t

_SMELL_CODES: t.StrSequence = tuple(sorted(c.Infra.SMELLS_RULE_TAGS))


def _sarif_fixture(project: str) -> str:
    """One finding per smell type inside ``project`` + one foreign-project row."""
    results: list[t.JsonValue] = [
        {
            "ruleId": f"{c.Infra.SMELLS_RULE_PREFIX}{code}",
            "message": {"text": f"{code} finding"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": f"{project}/src/sample.py"},
                        "region": {"startLine": index + 1, "startColumn": 2},
                    }
                }
            ],
        }
        for index, code in enumerate(_SMELL_CODES)
    ]
    results.append({
        "ruleId": f"{c.Infra.SMELLS_RULE_PREFIX}similar-code",
        "message": {"text": "foreign finding"},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": "other-project/src/y.py"},
                    "region": {"startLine": 3},
                }
            }
        ],
    })
    payload = u.Cli.json_dumps({"runs": [{"results": results}]}).unwrap()
    tm.that(payload, is_=str)
    return payload


def _seeded_gate(
    tmp_path: Path, *, stdout: str, stderr: str = "", exit_code: int = 0
) -> FlextInfraSmellsGate:
    """Gate whose workspace scan is pre-seeded (no qlty subprocess)."""
    FlextInfraSmellsGate._scan_cache[str(tmp_path)] = m.Cli.CommandOutput(
        stdout=stdout, stderr=stderr, exit_code=exit_code
    )
    return FlextInfraSmellsGate(tmp_path)


def _ctx(tmp_path: Path) -> m.Infra.GateContext:
    return m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path / "reports")


@pytest.fixture
def clean_scan_cache() -> Iterator[None]:
    """Isolate the class-level scan cache between tests."""
    yield
    FlextInfraSmellsGate._scan_cache.clear()


pytestmark = pytest.mark.usefixtures("clean_scan_cache")


class TestSmellsGate:
    def test_gate_identity(self) -> None:
        tm.that(FlextInfraSmellsGate.gate_id, eq="smells")
        tm.that(FlextInfraSmellsGate.can_fix, eq=True)

    def test_is_auto_fixable_reads_core_strategy(self) -> None:
        """Only smells marked auto=true in flext-core are auto-fixable."""
        boolean_issue = m.Infra.Issue(
            file="src/sample.py",
            line=1,
            column=0,
            code="boolean-logic",
            message="boolean logic",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        params_issue = m.Infra.Issue(
            file="src/sample.py",
            line=1,
            column=0,
            code="function-parameters",
            message="too many params",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        tm.that(FlextInfraSmellsGate._is_auto_fixable(boolean_issue), eq=True)
        tm.that(FlextInfraSmellsGate._is_auto_fixable(params_issue), eq=False)

    def test_boolean_logic_fixer_simplifies_or_chain(self, tmp_path: Path) -> None:
        """BooleanLogicFixer rewrites a long or-chain into any()."""
        source_file = tmp_path / "sample.py"
        source_file.write_text(
            "def f(p):\n    return p.a or p.b or p.c or p.d or p.e\n", encoding="utf-8"
        )
        issue = m.Infra.Issue(
            file="sample.py",
            line=2,
            column=0,
            code="smell_boolean_logic",
            message="boolean logic",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        fixer = FlextInfraBooleanLogicFixer()
        fixed, changes = fixer.fix(tmp_path, issue)
        tm.that(fixed, eq=True)
        tm.that(len(changes), eq=1)
        updated = source_file.read_text(encoding="utf-8")
        tm.that("any((p.a, p.b, p.c, p.d, p.e))" in updated, eq=True)

    def test_boolean_logic_fixer_ignores_short_chain(self, tmp_path: Path) -> None:
        """BooleanLogicFixer leaves short chains untouched."""
        original = "def f(p):\n    return p.a or p.b or p.c\n"
        source_file = tmp_path / "sample.py"
        source_file.write_text(original, encoding="utf-8")
        issue = m.Infra.Issue(
            file="sample.py",
            line=2,
            column=0,
            code="smell_boolean_logic",
            message="boolean logic",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        fixer = FlextInfraBooleanLogicFixer()
        fixed, _changes = fixer.fix(tmp_path, issue)
        tm.that(fixed, eq=False)
        tm.that(source_file.read_text(encoding="utf-8"), eq=original)

    def test_registered_and_allowed(self) -> None:
        tm.that("smells" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that(FlextInfraGateRegistry.default().get("smells") is not None, eq=True)

    def test_issues_from_sarif_filters_project(self) -> None:
        issues = FlextInfraSmellsGate._issues_from_sarif(
            _sarif_fixture("demo-project"), "demo-project"
        )

        tm.that(len(issues), eq=len(_SMELL_CODES))
        tm.that(sorted(issue.code for issue in issues), eq=list(_SMELL_CODES))
        tm.that(all(issue.file == "src/sample.py" for issue in issues), eq=True)
        tm.that(issues[0].line >= 1, eq=True)
        tm.that(
            all("foreign finding" not in issue.message for issue in issues), eq=True
        )

    def test_warn_mode_passes_with_issues_and_warns(self, tmp_path: Path) -> None:
        gate = _seeded_gate(tmp_path, stdout=_sarif_fixture("demo-project"))
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(FlextSmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=True)
        tm.that(len(execution.issues), eq=len(_SMELL_CODES))
        tm.that(len(execution.result.errors), eq=len(_SMELL_CODES))

    def test_missing_scanner_is_visible(self, tmp_path: Path) -> None:
        gate = _seeded_gate(tmp_path, stdout="", stderr="qlty exploded", exit_code=1)
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(FlextSmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=True)
        tm.that(len(execution.issues), eq=1)
        tm.that("qlty exploded" in execution.issues[0].message, eq=True)

    def test_severity_is_warning_while_report_only(self) -> None:
        tm.that(FlextInfraSmellsGate._severity(), eq=c.Infra.GateSeverity.WARNING.value)

    def test_smell_tags_have_core_rule_text(self) -> None:
        """Every qlty smell tag mapped by the gate has a FLEXT problem/fix text."""
        missing = [
            enforcement_tag
            for enforcement_tag in c.Infra.SMELLS_RULE_TAGS.values()
            if enforcement_tag not in core_c.ENFORCEMENT_RULES_TEXT
        ]
        tm.that(missing, eq=[])


__all__: t.StrSequence = []
