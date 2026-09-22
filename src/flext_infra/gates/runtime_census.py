"""Runtime enforcement census quality gate.

Imports every ``flext_*`` module in the selected project and runs
``FlextUtilitiesEnforcement.check()`` against every locally-defined class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import m
from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator

from .base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraRuntimeCensusGate(FlextInfraGate):
    """Post-import runtime enforcement census gate."""

    gate_id: ClassVar[str] = "runtime-census"
    gate_name: ClassVar[str] = "Runtime Enforcement Census"
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run the runtime census scoped to ``project_dir``."""
        _ = ctx
        started = time.monotonic()
        validator = FlextInfraRuntimeCensusValidator(repository_root=project_dir)
        result = validator.execute()
        passed = result.success and result.value is True
        if result.failure:
            # A broken invocation is a blocking defect, not advisory residue.
            return self._build_project_error_gate_result(
                project_dir,
                passed=False,
                errors=[result.error or "runtime census failed"],
                started=started,
                ctx=ctx,
            )
        # Operator order 2026-09-22: census findings stay advisory (reported
        # as warnings, non-blocking) until the enforcement campaign
        # converges; they must never hide a broken invocation.
        violations: list[str] = (
            [] if passed else [result.error or "runtime census found violations"]
        )
        return self._build_project_error_gate_result(
            project_dir,
            passed=passed,
            errors=violations,
            started=started,
            ctx=ctx,
            advisory=True,
        )


__all__: list[str] = ["FlextInfraRuntimeCensusGate"]
