"""Runtime enforcement census quality gate.

Imports every ``flext_*`` module in the selected project and runs
``FlextUtilitiesEnforcement.check()`` against every locally-defined class.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import config, m
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
        # Operator ruling 2026-09-22 (make.check_gates_advisory): while the
        # structural wave grinds, census findings render as warnings and never
        # block the run. The validator reports violations as a failed Result
        # whose error carries the full findings report — advisory keeps that
        # report visible while passing. A census that truly crashes raises:
        # the runner's crash path still fails, never reading as a clean pass.
        advisory = self.gate_id in config.Infra.codegen.make.check_gates_advisory
        passed = (result.success and result.value is True) or advisory
        errors: list[str] = []
        if result.failure or (not passed and result.success):
            errors.append(result.error or "runtime census found violations")
        return self._build_project_error_gate_result(
            project_dir, passed=passed, errors=errors, started=started, ctx=ctx
        )


__all__: list[str] = ["FlextInfraRuntimeCensusGate"]
