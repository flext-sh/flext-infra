"""Tier-whitelist / abstraction-boundary quality gate.

Replaces the legacy ``ban-direct-*.yml`` ast-grep rules with the
OWNERS-driven ``FlextInfraValidateTierWhitelist`` rope detector.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist


class FlextInfraTierWhitelistGate(FlextInfraGate):
    """Enforce the tier-whitelist abstraction boundary per project."""

    gate_id: ClassVar[str] = "tier-whitelist"
    gate_name: ClassVar[str] = "Tier Whitelist"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["tier-whitelist"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["tier-whitelist"][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run the tier-whitelist scan scoped to ``project_dir``."""
        _ = ctx
        started = time.monotonic()
        validator = FlextInfraValidateTierWhitelist(workspace_root=project_dir)
        result = validator.execute()
        passed = result.success and result.value is True
        errors: list[str] = []
        if result.failure:
            errors.append(result.error or "tier-whitelist validation failed")
        elif not passed:
            errors.append(result.error or "tier-whitelist violations found")
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
            raw_output="\n".join(errors),
        )

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """No external tool — execution happens in ``check``."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Unused — ``check`` is overridden directly."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraTierWhitelistGate"]
