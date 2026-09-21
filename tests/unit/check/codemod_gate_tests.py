"""Public acceptance behavior for codemod migration findings."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c
from flext_infra.gates.codemod import FlextInfraCodemodGate
from tests import m


class TestsFlextInfraCodemodGate:
    """Keep actionable matches visible without blocking the standard check."""

    def test_rule_match_is_a_non_blocking_warning(self, tmp_path: Path) -> None:
        (tmp_path / "candidate.py").write_text(
            "from flext_infra._utilities._git.semantic import Legacy\n",
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
        )

        execution = FlextInfraCodemodGate(tmp_path).check(tmp_path, context)

        tm.that(execution.result.passed, eq=True)
        tm.that(len(execution.issues) > 0, eq=True)
        tm.that(
            all(
                issue.severity == str(c.Infra.GateSeverity.WARNING.value)
                for issue in execution.issues
            ),
            eq=True,
        )
