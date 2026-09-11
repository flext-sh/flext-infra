"""Budget gate (R4 gates-as-products): enforces time/memory/token budgets per gate."""

from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, u

from .base_gate import FlextInfraGate


class FlextInfraBudgetGate(FlextInfraGate):
    """Enforce execution budgets (time, memory, tokens) for gate runs.

    R4: every gate is a product with a non-optional budget. The gate set is
    derived from ``c.Infra.ALLOWED_GATES`` (the SARIF vocabulary SSOT) — never
    a frozen enumeration in this class. Budget config lives in
    ``[tool.flext.project.budget]``; a missing row, a missing required field,
    or an unreadable pyproject is a declared error, never a skip: registry
    divergence between the gate registry and consumer configuration is a
    hard error by design.
    """

    gate_id: ClassVar[str] = "budget"
    gate_name: ClassVar[str] = "Execution Budget"
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Check that every registered gate has a complete budget row."""
        _ = ctx
        started = time.monotonic()
        budget_config = self._read_budget_config(project_dir)
        issues = self._validate_gate_budgets(budget_config)
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="",
            started=started,
        )

    def _read_budget_config(self, project_dir: Path) -> dict[str, t.JsonValue]:
        """Read ``[tool.flext.project.budget]`` from the project manifest.

        Input shapes stay untrusted until the collapse into typed shells
        below; a failed manifest load or a non-mapping projection escapes
        with its cause instead of degrading into an empty config.
        """
        pyproject_path = project_dir / "pyproject.toml"
        if not pyproject_path.is_file():
            return {}
        loaded = u.Cli.config_load(pyproject_path, expand_env=False)
        if loaded.failure:
            msg = f"budget gate cannot read {pyproject_path}: {loaded.error}"
            raise ValueError(msg)
        tool = u.Cli.json_as_mapping(loaded.value.data).get("tool", {})
        flext = u.Cli.json_as_mapping(tool).get("flext", {})
        project = u.Cli.json_as_mapping(flext).get("project", {})
        budget = u.Cli.json_as_mapping(project).get("budget", {})
        return dict(u.Cli.json_as_mapping(budget))

    def _validate_gate_budgets(
        self, budget_config: dict[str, t.JsonValue]
    ) -> tuple[m.Infra.Issue, ...]:
        """Validate one budget row per ``c.Infra.ALLOWED_GATES`` entry."""
        required_fields = c.Infra.BUDGET_REQUIRED_FIELDS
        issues = (
            FlextInfraBudgetGate._budget_issue(
                gate_id, budget_config, required_fields=required_fields
            )
            for gate_id in sorted(c.Infra.ALLOWED_GATES)
        )
        return tuple(issue for issue in issues if issue is not None)

    @staticmethod
    def _budget_issue(
        gate_id: str,
        budget_config: dict[str, t.JsonValue],
        *,
        required_fields: tuple[str, ...],
    ) -> m.Infra.Issue | None:
        """Return the declared error for one gate's budget row, when broken."""
        gate_budget = budget_config.get(gate_id)
        if gate_budget is None:
            return FlextInfraBudgetGate._issue(gate_id, "missing budget row")
        if not isinstance(gate_budget, Mapping):
            return FlextInfraBudgetGate._issue(gate_id, "budget row must be a table")
        for field in required_fields:
            if field not in gate_budget:
                return FlextInfraBudgetGate._issue(
                    gate_id, f"missing required field {field!r}"
                )
            value = gate_budget[field]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                return FlextInfraBudgetGate._issue(
                    gate_id, f"field {field!r} must be a positive integer"
                )
        return None

    @staticmethod
    def _issue(gate_id: str, detail: str) -> m.Infra.Issue:
        """Build one strict budget issue targeted at the project manifest."""
        return m.Infra.Issue(
            file=c.Infra.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=FlextInfraBudgetGate.gate_id,
            message=(
                f"gate {gate_id!r}: {detail} in [tool.flext.project.budget] "
                "— registry divergence is a hard error"
            ),
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )


__all__: list[str] = ["FlextInfraBudgetGate"]
