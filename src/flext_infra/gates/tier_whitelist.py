"""Tier-whitelist / abstraction-boundary quality gate.

Replaces the legacy ``ban-direct-*.yml`` ast-grep rules with the
OWNERS-driven ``FlextInfraValidateTierWhitelist`` rope detector.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraTierWhitelistGate(FlextInfraGate):
    """Enforce the tier-whitelist abstraction boundary per project."""

    gate_id: ClassVar[str] = "tier-whitelist"
    gate_name: ClassVar[str] = "Tier Whitelist"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["tier-whitelist"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["tier-whitelist"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run the tier-whitelist scan scoped to ``project_dir``."""
        started = time.monotonic()
        validator = FlextInfraValidateTierWhitelist(workspace_root=project_dir)
        report_result = validator.build_report(project_dir)
        if report_result.failure:
            passed = False
            errors = [report_result.error or "tier-whitelist validation failed"]
            raw_output = errors[0]
        else:
            report = report_result.value
            passed = report.passed
            errors = list(report.violations) if not passed else []
            raw_output = "\n".join([report.summary, *errors])
        issues = [
            m.Infra.Issue(
                file=str(project_dir),
                line=1,
                column=1,
                code=self.gate_id,
                message=error,
                severity="ERROR",
            )
            for error in errors
        ]
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output=raw_output,
            ctx=ctx,
        )


__all__: list[str] = ["FlextInfraTierWhitelistGate"]
