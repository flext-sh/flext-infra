"""Public behavior tests for the real Pyrefly and Mypy gate runners."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.gates.base_gate import FlextInfraGate


class TestRunnerPublicBehavior:
    """Exercise public gate behavior with the installed production tools."""

    @pytest.mark.parametrize("gate_class", [FlextInfraPyreflyGate, FlextInfraMypyGate])
    def test_real_type_error_is_reported(
        self, tmp_path: Path, gate_class: type[FlextInfraGate]
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "type-project", with_src=True)
        (project_dir / "src" / "main.py").write_text(
            'value: int = "not-an-int"\n', encoding="utf-8"
        )

        result = u.Tests.run_gate_check(gate_class, tmp_path, project_dir)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues) > 0, eq=True)

    @pytest.mark.parametrize("gate_class", [FlextInfraPyreflyGate, FlextInfraMypyGate])
    def test_valid_project_is_accepted(
        self, tmp_path: Path, gate_class: type[FlextInfraGate]
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "type-project", with_src=True)
        (project_dir / "src" / "main.py").write_text(
            "value: int = 1\n", encoding="utf-8"
        )

        result = u.Tests.run_gate_check(gate_class, tmp_path, project_dir)

        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    @pytest.mark.parametrize("gate_class", [FlextInfraPyreflyGate, FlextInfraMypyGate])
    def test_invalid_project_config_fails_loudly(
        self, tmp_path: Path, gate_class: type[FlextInfraGate]
    ) -> None:
        project_dir = u.Tests.mk_project(
            tmp_path, "type-project", pyproject="[tool\n", with_src=True
        )
        (project_dir / "src" / "main.py").write_text(
            "value: int = 1\n", encoding="utf-8"
        )

        result = u.Tests.run_gate_check(gate_class, tmp_path, project_dir)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues) > 0, eq=True)

    @pytest.mark.parametrize("gate_class", [FlextInfraPyreflyGate, FlextInfraMypyGate])
    def test_project_without_python_sources_is_a_noop(
        self, tmp_path: Path, gate_class: type[FlextInfraGate]
    ) -> None:
        project_dir = u.Tests.mk_project(tmp_path, "type-project")

        result = u.Tests.run_gate_check(gate_class, tmp_path, project_dir)

        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)


__all__: list[str] = []
