"""Runtime enforcement census quality gate.

Imports every ``flext_*`` module in the selected project and runs
``FlextUtilitiesEnforcement.check()`` against every locally-defined class.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, r
from flext_infra.gates import FlextInfraGate
from flext_infra.validate import FlextInfraRuntimeCensusValidator

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraRuntimeCensusGate(FlextInfraGate):
    """Post-import runtime enforcement census gate."""

    gate_id: ClassVar[str] = c.Infra.RUNTIME_CENSUS
    gate_name: ClassVar[str] = "Runtime Enforcement Census"
    can_fix: ClassVar[bool] = False
    requires_python_targets: ClassVar[bool] = True

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run the runtime census scoped to ``project_dir``.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        if ctx.runtime_root is not None:
            if ctx.candidate_runtime_report is None:
                return self._build_project_error_gate_result(
                    project_dir,
                    ctx=ctx,
                    passed=False,
                    errors=["sealed runtime census report is required"],
                    started=started,
                )
            return self._build_validation_report_result(
                project_dir,
                r[m.Infra.ValidationReport].ok(ctx.candidate_runtime_report),
                ctx=ctx,
                started=started,
            )
        validator = FlextInfraRuntimeCensusValidator.for_project(
            project_dir,
        )
        if validator.failure:
            return self._build_project_error_gate_result(
                project_dir,
                ctx=ctx,
                passed=False,
                errors=[validator.error or "runtime census scoping failed"],
                started=started,
            )
        # ``build_report`` (not ``execute``) keeps violations structured so the
        # gate can grade a broken invocation separately from found violations.
        return self._build_validation_report_result(
            project_dir,
            validator.value.build_report(),
            ctx=ctx,
            started=started,
        )


__all__: list[str] = ["FlextInfraRuntimeCensusGate"]
