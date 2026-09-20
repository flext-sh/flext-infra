"""Tests for the module-cap SUPREME LAW (§3.1) gate.

The gate flags any module whose real scc `Code` line count exceeds the
config-owned ceiling and accepts modules under it, exercised through the public
gate runner. Fixtures derive from that config-owned ceiling so a legitimate cap
change never silently inverts these assertions (UNIVERSAL_CORE P0).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import config
from flext_infra.gates.loc_cap import FlextInfraLocCapGate
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraLocCapGate:
    @staticmethod
    def gate_project(tmp_path: Path, *, code_lines: int) -> Path:
        """Create one real project whose sample module carries ``code_lines``."""
        module = "from __future__ import annotations\n\n" + "".join(
            f"x{index} = {index}\n" for index in range(code_lines)
        )
        return u.Tests.create_codegen_project(
            tmp_path=tmp_path,
            name="demo-project",
            pkg_name="demo_project",
            files={"sample.py": module},
        )

    def test_gate_identity(self) -> None:
        tm.that(FlextInfraLocCapGate.gate_id, eq="loc-cap")
        tm.that(FlextInfraLocCapGate.can_fix, eq=False)

    @pytest.mark.parametrize(
        ("code_lines", "passed"),
        [(config.Infra.codegen.loc_cap.max_lines + 50, False), (1, True)],
    )
    def test_cap_is_enforced_on_real_scc_counts(
        self, tmp_path: Path, code_lines: int, *, passed: bool
    ) -> None:
        project = self.gate_project(tmp_path, code_lines=code_lines)

        result = u.Tests.run_gate_check(FlextInfraLocCapGate, tmp_path, project)

        tm.that(result.result.passed, eq=passed)
        flagged = [issue.file for issue in result.issues if issue.code == "LOC_CAP"]
        tm.that(len(flagged), eq=0 if passed else 1)
        tm.that(all(path.endswith("sample.py") for path in flagged), eq=True)

    def test_unavailable_scanner_is_not_silenced(self, tmp_path: Path) -> None:
        project = self.gate_project(tmp_path, code_lines=1)
        empty_path = tmp_path / "empty-path"
        empty_path.mkdir()

        with (
            tm.scope(env={"PATH": str(empty_path)}),
            pytest.raises(RuntimeError, match=c.Infra.SCC_BINARY),
        ):
            u.Tests.run_gate_check(FlextInfraLocCapGate, tmp_path, project)


__all__: t.StrSequence = ["TestsFlextInfraLocCapGate"]
