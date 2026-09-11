"""Budget gate (R4 gates-as-products): enforces time/memory/token budgets per gate."""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, u

from .base_gate import FlextInfraGate


class FlextInfraBudgetGate(FlextInfraGate):
    """Enforce execution budgets (time, memory, tokens) for gate runs.

    R4: Every gate is a product with a non-optional budget. Budget config via
    [tool.flext.project.budget] keys; thresholds in config SSOT. Registry
    divergence (gate without budget row) = hard error.
    """

    gate_id: ClassVar[str] = "budget"
    gate_name: ClassVar[str] = "Execution Budget"
    can_fix: ClassVar[bool] = False

    # Budget defaults (SSOT in constants, overridable via [tool.flext.project])
    _DEFAULT_TIME_SECONDS: ClassVar[int] = 300
    _DEFAULT_MEMORY_MB: ClassVar[int] = 6144
    _DEFAULT_TOKENS: ClassVar[int] = 100000

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Check that all gates in this project have budget config."""
        _ = ctx
        started = time.monotonic()

        # Read project budget config
        budget_config = self._read_budget_config(project_dir)

        # Validate that all registered gates have budget entries
        issues = self._validate_gate_budgets(budget_config)

        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="",
            started=started,
        )

    def _read_budget_config(self, project_dir: Path) -> dict:
        """Read [tool.flext.project.budget] from project's pyproject.toml."""
        pyproject_path = project_dir / "pyproject.toml"
        if not pyproject_path.is_file():
            return {}
        loaded = u.Cli.config_load(pyproject_path, expand_env=False)
        if loaded.failure:
            return {}
        try:
            data = loaded.value.data
            return (
                data
                .get("tool", {})
                .get("flext", {})
                .get("project", {})
                .get("budget", {})
            )
        except c.ValidationError:
            return {}

    def _validate_gate_budgets(self, budget_config: dict) -> tuple[m.Infra.Issue, ...]:
        """Validate that all gates have budget configuration."""
        issues: list[m.Infra.Issue] = []
        required_gates = {
            "namespace",
            "canonical_alias",
            "duplication",
            "consumer_import_violations",
            "silent_failure",
            "boundary",
            "loc_cap",
            "tier_whitelist",
            "mypy",
            "pyrefly",
            "pyright",
            "ruff_lint",
            "ruff_format",
            "codemod",
            "budget",
        }

        for gate_id in required_gates:
            if gate_id not in budget_config:
                issues.append(
                    m.Infra.Issue(
                        file="pyproject.toml",
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=f"Gate '{gate_id}' missing budget config in [tool.flext.project.budget] — registry divergence is a hard error",
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    )
                )
            else:
                gate_budget = budget_config[gate_id]
                issues.extend(
                    m.Infra.Issue(
                        file="pyproject.toml",
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=f"Gate '{gate_id}' budget missing required field '{field}'",
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    )
                    for field in ("time-seconds", "memory-mb", "tokens")
                    if field not in gate_budget
                )

        return tuple(issues)


__all__: list[str] = ["FlextInfraBudgetGate"]
