"""Tests for the silent-failure quality gate."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraSilentFailureGate
from tests import u


def _create_gate_project(tmp_path: Path, *, name: str) -> Path:
    return u.Infra.Tests.create_codegen_project(
        tmp_path=tmp_path,
        name=name,
        pkg_name=name.replace("-", "_"),
        files={
            "utilities.py": (
                "from __future__ import annotations\n\n"
                "from collections.abc import Mapping, Sequence\n\n"
                "from flext_core import r\n\n"
                "def run(validation_result: r[bool]) -> r[bool]:\n"
                "    if validation_result.failure:\n"
                "        return False\n"
                "    return r[bool].ok(True)\n"
            ),
        },
    )


class TestSilentFailureGate:
    def test_first_wave_project_fails_on_silent_failure(self, tmp_path: Path) -> None:
        project = _create_gate_project(tmp_path, name="flext-cli")

        result = u.Infra.Tests.run_gate_check(
            FlextInfraSilentFailureGate, tmp_path, project
        )

        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].code, eq="silent-failure-guard")

    def test_non_first_wave_project_is_not_enforced(self, tmp_path: Path) -> None:
        project = _create_gate_project(tmp_path, name="demo-project")

        result = u.Infra.Tests.run_gate_check(
            FlextInfraSilentFailureGate, tmp_path, project
        )

        tm.that(result.result.passed, eq=True)
        tm.that(result.raw_output, has="not enforced")


__all__: Sequence[str] = []
