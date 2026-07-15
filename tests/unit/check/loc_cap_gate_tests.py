"""Tests for the 200-LOC SUPREME LAW (§3.1) module-cap gate.

The gate flags any module whose tokei `code` line count exceeds 200 and
accepts modules under the cap, exercised through the public gate runner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.gates.loc_cap import FlextInfraLocCapGate
from tests import t, u

_OVER_CAP = (
    "from __future__ import annotations\n\n"
    + "\n".join(f"x{i} = {i}" for i in range(250))
    + "\n"
)
_UNDER_CAP = "from __future__ import annotations\n\nx = 1\n"


def _gate_project(tmp_path: Path, *, name: str, module_src: str) -> Path:
    project_path: Path = u.Tests.create_codegen_project(
        tmp_path=tmp_path,
        name=name,
        pkg_name=name.replace("-", "_"),
        files={"sample.py": module_src},
    )
    return project_path


class TestLocCapGate:
    def test_gate_identity(self) -> None:
        tm.that(FlextInfraLocCapGate.gate_id, eq="loc-cap")
        tm.that(FlextInfraLocCapGate.can_fix, eq=False)

    def test_over_cap_module_is_flagged(self, tmp_path: Path) -> None:
        project = _gate_project(tmp_path, name="demo-project", module_src=_OVER_CAP)

        result = u.Tests.run_gate_check(FlextInfraLocCapGate, tmp_path, project)

        tm.that(not result.result.passed, eq=True)
        tm.that(any(issue.code == "LOC_CAP" for issue in result.issues), eq=True)

    def test_under_cap_module_passes(self, tmp_path: Path) -> None:
        project = _gate_project(tmp_path, name="demo-project", module_src=_UNDER_CAP)

        result = u.Tests.run_gate_check(FlextInfraLocCapGate, tmp_path, project)

        tm.that(result.result.passed, eq=True)


__all__: t.StrSequence = []
