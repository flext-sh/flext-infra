"""Runtime enforcement census quality gate.

Imports every ``flext_*`` module in the selected project and runs
``FlextUtilitiesEnforcement.check()`` against every locally-defined class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraRuntimeCensusGate(FlextInfraGate):
    """Post-import runtime enforcement census gate."""

    gate_id: ClassVar[str] = "runtime-census"
    gate_name: ClassVar[str] = "Runtime Enforcement Census"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["runtime-census"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["runtime-census"][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run the runtime census scoped to ``project_dir``."""
        _ = ctx
        started = time.monotonic()
        validator = FlextInfraRuntimeCensusValidator(
            workspace_root=self._workspace_root,
            project_filter=project_dir.name,
        )
        result = validator.execute()
        passed = result.success and result.value is True
        errors: list[str] = []
        if result.failure:
            errors.append(result.error or "runtime census failed")
        elif not passed:
            errors.append(result.error or "runtime census found violations")
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=errors,
                duration=round(time.monotonic() - started, 3),
            ),
            issues=[],
            raw_output="\n".join(errors),
            ctx=ctx,
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


__all__: list[str] = ["FlextInfraRuntimeCensusGate"]
