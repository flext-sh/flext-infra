"""Exercise budget validation through the public gate against real manifests."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraBudgetGate, c, m
from tests import u


class TestsFlextInfraBudgetGate:
    """Registry-derived fixtures never freeze current gate names or defaults."""

    @staticmethod
    def _manifest(
        root: Path, *, missing_gate: str = "", invalid_field: str = "", value: str = "1"
    ) -> Path:
        selected = min(c.Infra.ALLOWED_GATES)
        rows = []
        for gate_id in sorted(c.Infra.ALLOWED_GATES):
            if gate_id == missing_gate:
                continue
            fields = ", ".join(
                f'"{field}" = {value if gate_id == selected and field == invalid_field else "1"}'
                for field in c.Infra.BUDGET_REQUIRED_FIELDS
            )
            rows.append(f'"{gate_id}" = {{ {fields} }}')
        path = root / c.Infra.PYPROJECT_FILENAME
        path.write_text(
            "[tool.flext.project.budget]\n" + "\n".join(rows) + "\n", encoding="utf-8"
        )
        return path

    @staticmethod
    def _check(root: Path) -> m.Infra.GateExecution:
        return FlextInfraBudgetGate(root).check(root, u.Tests.gate_context(root))

    def test_complete_budget_has_no_issues(self, tmp_path: Path) -> None:
        manifest = self._manifest(tmp_path)
        before = manifest.read_bytes()

        result = self._check(tmp_path)

        tm.that(result.result.passed, eq=True)
        tm.that(result.issues, empty=True)
        tm.that(manifest.read_bytes(), eq=before)

    def test_missing_row_reports_only_that_gate(self, tmp_path: Path) -> None:
        missing = min(c.Infra.ALLOWED_GATES)
        self._manifest(tmp_path, missing_gate=missing)

        result = self._check(tmp_path)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].message, has=missing)

    @pytest.mark.parametrize("field", c.Infra.BUDGET_REQUIRED_FIELDS)
    @pytest.mark.parametrize("value", ['"invalid"', "true", "0", "-1", "1.5"])
    def test_invalid_limit_is_rejected(
        self, tmp_path: Path, field: str, value: str
    ) -> None:
        self._manifest(tmp_path, invalid_field=field, value=value)

        result = self._check(tmp_path)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=1)
        tm.that(result.issues[0].message, has=field)

    def test_missing_manifest_reports_every_required_gate(self, tmp_path: Path) -> None:
        result = self._check(tmp_path)

        tm.that(result.result.passed, eq=False)
        tm.that(len(result.issues), eq=len(c.Infra.ALLOWED_GATES))
