"""Tests for the qlty code-smells gate through its public runtime boundary.

The typed gate configuration owns strict versus advisory finding posture.
Scanner and SARIF contract failures always fail closed. An owned temporary
``qlty`` executable exercises the real process boundary without replacing the
gate implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_core import e as core_e
from flext_infra import c, config, m, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.smells import FlextInfraSmellsGate
from flext_infra.transformers.smells.base import (
    auto_fixable_smell_tags,
    smell_fixer_for,
    smell_tag_for_code,
)
from flext_tests import tm
from tests import t

if TYPE_CHECKING:
    from typing import Literal

_SMELL_CODES: t.StrSequence = tuple(
    tag.removeprefix("smell_").replace("_", "-") for tag in c.ENFORCEMENT_SMELL_TAGS
)
_SMELLS_SPEC: m.Infra.MakeCheckGateSpec = next(
    gate
    for gate in config.Infra.codegen.make.check.gates
    if gate.id == FlextInfraSmellsGate.gate_id
)


def _sarif_fixture(
    project: str, codes: t.StrSequence = _SMELL_CODES, *, include_foreign: bool = True
) -> str:
    """One finding per smell type inside ``project`` + one foreign-project row."""
    source_uri = f"{project}/src/sample.py" if project else "src/sample.py"
    results: list[t.JsonValue] = [
        {
            "ruleId": f"qlty:{code}",
            "message": {"text": f"{code} finding"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": source_uri},
                        "region": {"startLine": index + 2, "startColumn": 2},
                    }
                }
            ],
        }
        for index, code in enumerate(codes)
    ]
    if include_foreign:
        results.append({
            "ruleId": "qlty:similar-code",
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
    payload = u.Cli.json_dumps({
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "qlty"}}, "results": results}],
    }).unwrap()
    tm.that(payload, is_=str)
    validated_payload: str = t.Infra.STR_ADAPTER.validate_python(payload)
    return validated_payload


def _scanner_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdout: str,
    stderr: str = "",
    exit_code: int = 0,
) -> FlextInfraSmellsGate:
    """Return a gate backed by an executable scanner at the external boundary."""
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    scanner = binary_dir / Path(_SMELLS_SPEC.command[0]).name
    counter = tmp_path / "qlty-invocations"
    scanner.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        f"counter = Path({str(counter)!r})\n"
        "count = int(counter.read_text(encoding='utf-8')) if counter.exists() else 0\n"
        "counter.write_text(str(count + 1), encoding='utf-8')\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.stderr.write({stderr!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    scanner.chmod(0o755)
    monkeypatch.setenv("PATH", str(binary_dir), prepend=":")
    return FlextInfraSmellsGate(tmp_path)


def _ctx(
    tmp_path: Path,
    *,
    apply_fixes: bool = False,
    gate_mode: Literal["error", "warn"] | None = None,
) -> m.Infra.GateContext:
    return m.Infra.GateContext(
        workspace=tmp_path,
        reports_dir=tmp_path / "reports",
        apply_fixes=apply_fixes,
        gate_mode=gate_mode or _SMELLS_SPEC.mode,
        gate_command=_SMELLS_SPEC.command,
        gate_execution_scope=_SMELLS_SPEC.execution_scope,
    )


class TestSmellsGate:
    def test_gate_identity(self, tmp_path: Path) -> None:
        tm.that(
            FlextInfraSmellsGate.gate_id in config.Infra.codegen.make.check.gate_ids,
            eq=True,
        )
        tm.that(FlextInfraSmellsGate.can_fix, eq=True)
        tm.that(_SMELLS_SPEC.command, empty=False)
        context = _ctx(tmp_path)
        tm.that(context.gate_command, eq=_SMELLS_SPEC.command)
        tm.that(context.gate_execution_scope, eq=_SMELLS_SPEC.execution_scope)

    def test_fix_applies_only_core_auto_strategies(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The public fix boundary applies the automatic boolean strategy only."""
        project_dir = tmp_path / "demo-project"
        source_file = project_dir / "src" / "sample.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text(
            "def f(a, b, c, d, e):\n"
            "    if a or b or c or d or e:\n"
            "        return True\n"
            "    return False\n",
            encoding="utf-8",
        )
        gate = _scanner_gate(
            tmp_path,
            monkeypatch,
            stdout=_sarif_fixture(
                project_dir.name, ("boolean-logic", "function-parameters")
            ),
        )

        with pytest.warns(core_e.SmellViolation):
            execution = gate.fix(project_dir, _ctx(tmp_path, apply_fixes=True))

        tm.that(execution.result.passed, eq=True)
        tm.that(len(execution.result.errors), eq=1)
        tm.that(
            source_file.read_text(encoding="utf-8"),
            has="any(_flext_boolean_operand() for _flext_boolean_operand in",
        )

    def test_registered_and_configured(self) -> None:
        registry = FlextInfraGateRegistry.default()
        expected_gate_ids = config.Infra.codegen.make.check.gate_ids
        tm.that(registry.gate_ids, eq=expected_gate_ids)
        tm.that(
            registry.get(FlextInfraSmellsGate.gate_id) is FlextInfraSmellsGate, eq=True
        )

    def test_check_filters_sarif_to_project(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path, monkeypatch, stdout=_sarif_fixture("demo-project")
        )
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path))

        issues = execution.issues
        tm.that(execution.result.passed, eq=False)
        tm.that(len(issues), eq=len(_SMELL_CODES))
        tm.that(tuple(issue.code for issue in issues), eq=_SMELL_CODES)
        tm.that(all(issue.file == "src/sample.py" for issue in issues), eq=True)
        tm.that(issues[0].line >= 1, eq=True)
        tm.that(
            all("foreign finding" not in issue.message for issue in issues), eq=True
        )

    def test_warn_mode_passes_with_issues_and_warns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path, monkeypatch, stdout=_sarif_fixture("demo-project")
        )
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path, gate_mode="warn"))

        tm.that(execution.result.passed, eq=True)
        tm.that(len(execution.issues), eq=len(_SMELL_CODES))
        tm.that(execution.result.errors, eq=[])
        tm.that(
            all(
                issue.severity.casefold()
                == c.Infra.GateSeverity.WARNING.value.casefold()
                for issue in execution.issues
            ),
            eq=True,
        )

    def test_failed_scanner_is_visible(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path, monkeypatch, stdout="", stderr="qlty exploded", exit_code=1
        )
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path, gate_mode="warn"))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that("qlty exploded" in execution.issues[0].message, eq=True)

    def test_unconfigured_scanner_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path,
            monkeypatch,
            stdout="",
            stderr="No qlty config file found. Try running `qlty init`",
            exit_code=1,
        )
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that("No qlty config file found" in execution.issues[0].message, eq=True)
        tm.that(len(execution.result.errors), eq=1)

    def test_invalid_sarif_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(tmp_path, monkeypatch, stdout="not-json")
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(project_dir, _ctx(tmp_path, gate_mode="warn"))

        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=1)
        tm.that(len(execution.result.errors), eq=1)

    def test_workspace_scan_invokes_qlty_once(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path, monkeypatch, stdout=_sarif_fixture("demo-project")
        )
        project_dir = tmp_path / "demo-project"
        project_dir.mkdir()

        with pytest.warns(core_e.SmellViolation):
            gate.check(project_dir, _ctx(tmp_path, gate_mode="warn"))
        with pytest.warns(core_e.SmellViolation):
            gate.check(project_dir, _ctx(tmp_path, gate_mode="warn"))

        tm.that((tmp_path / "qlty-invocations").read_text(encoding="utf-8"), eq="1")

    def test_standalone_root_reads_workspace_relative_uris(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = _scanner_gate(
            tmp_path,
            monkeypatch,
            stdout=_sarif_fixture("", ("boolean-logic",), include_foreign=False),
        )

        with pytest.warns(core_e.SmellViolation):
            execution = gate.check(tmp_path, _ctx(tmp_path))

        tm.that(execution.result.passed, eq=False)
        tm.that(tuple(issue.file for issue in execution.issues), eq=("src/sample.py",))

    def test_smell_tags_have_core_rule_text(self) -> None:
        """Core strategy rows own tags, rule text, and transformer dispatch."""
        missing = [
            tag
            for tag in c.ENFORCEMENT_SMELL_TAGS
            if smell_tag_for_code(tag.removeprefix("smell_").replace("_", "-")) != tag
            or tag not in c.ENFORCEMENT_RULES_TEXT
        ]
        tm.that(missing, eq=[])
        expected_auto = tuple(
            tag
            for tag, strategy in c.ENFORCEMENT_SMELL_FIX_STRATEGIES.items()
            if strategy.get("auto") and isinstance(strategy.get("fixer"), str)
        )
        tm.that(auto_fixable_smell_tags(), eq=expected_auto)
        tm.that(all(smell_fixer_for(tag) is not None for tag in expected_auto), eq=True)


__all__: t.StrSequence = []
