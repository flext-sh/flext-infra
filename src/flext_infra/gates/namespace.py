"""Static namespace-rule quality gate (NS-000..003)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t, p


class FlextInfraNamespaceGate(FlextInfraGate):
    """Rope-backed namespace rule gate."""

    gate_id: ClassVar[str] = "namespace"
    gate_name: ClassVar[str] = "Namespace Rules"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["namespace"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["namespace"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run NS-000..003 validation scoped to ``project_dir``."""
        _ = ctx
        started = time.monotonic()
        validator = FlextInfraNamespaceValidator()
        report_result = validator.validate_project(project_dir)
        passed = report_result.success and report_result.value.passed
        errors: list[str] = []
        if report_result.failure:
            errors.append(report_result.error or "namespace validation failed")
        elif not passed:
            errors.extend(report_result.value.violations)
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
            ctx=ctx,
        )

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """No external tool — execution happens in ``check``."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Unused — ``check`` is overridden directly."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraNamespaceGate"]
