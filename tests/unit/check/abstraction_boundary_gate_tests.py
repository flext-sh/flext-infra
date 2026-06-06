"""Tests for the abstraction-boundary gate (AGENTS.md §2.7).

Behaviour parity with the two retired scripts: banned CLI-domain libs are
flagged in consumers, ``click`` is exempt in Singer-SDK boundary files, and
concrete ``FlextCli<X>`` imports are flagged outside src extension files.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.gates.abstraction_boundary import FlextInfraAbstractionBoundaryGate
from tests import t, u


def _project(tmp_path: Path, *, name: str, filename: str, src: str) -> Path:
    return u.Tests.create_codegen_project(
        tmp_path=tmp_path,
        name=name,
        pkg_name=name.replace("-", "_"),
        files={filename: src},
    )


class TestAbstractionBoundaryGate:
    def test_gate_identity(self) -> None:
        tm.that(FlextInfraAbstractionBoundaryGate.gate_id, eq="boundary")
        tm.that(FlextInfraAbstractionBoundaryGate.can_fix, eq=False)

    def test_banned_cli_lib_is_flagged(self, tmp_path: Path) -> None:
        project = _project(
            tmp_path, name="flext-demo", filename="logic.py", src="import typer\n"
        )

        result = u.Tests.run_gate_check(
            FlextInfraAbstractionBoundaryGate, tmp_path, project
        )

        tm.that(not result.result.passed, eq=True)
        tm.that(any("typer" in issue.message for issue in result.issues), eq=True)

    def test_click_allowed_in_singer_boundary(self, tmp_path: Path) -> None:
        project = _project(
            tmp_path, name="flext-tap-demo", filename="logic.py", src="import click\n"
        )

        result = u.Tests.run_gate_check(
            FlextInfraAbstractionBoundaryGate, tmp_path, project
        )

        tm.that(result.result.passed, eq=True)

    def test_concrete_flext_cli_import_flagged(self, tmp_path: Path) -> None:
        project = _project(
            tmp_path,
            name="flext-demo",
            filename="service.py",
            src="from flext_cli import FlextCliService\n",
        )

        result = u.Tests.run_gate_check(
            FlextInfraAbstractionBoundaryGate, tmp_path, project
        )

        tm.that(not result.result.passed, eq=True)

    def test_concrete_flext_cli_allowed_in_extension_file(self, tmp_path: Path) -> None:
        project = _project(
            tmp_path,
            name="flext-demo",
            filename="models.py",
            src="from flext_cli import FlextCliService\n",
        )

        result = u.Tests.run_gate_check(
            FlextInfraAbstractionBoundaryGate, tmp_path, project
        )

        tm.that(result.result.passed, eq=True)


__all__: t.StrSequence = []
