"""Pydantic projection parity gate.

The gate compares every shipped protocol projection with its canonical render
from the existing model projector. It owns no projection logic: a drift row is
exactly the projector's verdict on the authenticated source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.gates import FlextInfraGates
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraGatesPydanticCensus(FlextInfraGates):
    """Fail when a model projection is missing or differs from its render."""

    gate_id: ClassVar[str] = c.Infra.PYDANTIC_CENSUS
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def selected_for(self, project_dir: Path, ctx: p.Infra.GateContext) -> bool:
        """Run once on the workspace owner, never per member.

        Returns:
            Whether this project owns the governed workspace census.

        """
        del ctx
        return project_dir.resolve() == self._repository_root.resolve()

    @override
    def check(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Compare shipped projections with the canonical render.

        Returns:
            The gate execution carrying one issue per divergent projection.

        """
        started = time.monotonic()
        with FlextInfraRopeWorkspace.open_workspace(self._repository_root) as workspace:
            sources = {
                Path(resource.real_path): resource.read()
                for resource in workspace.rope_project.get_python_files()
            }
            report = u.Infra.pydantic_census(workspace, sources=sources)
        issues = tuple(
            m.Infra.Issue(
                file=str(row.file_path),
                line=row.line,
                column=0,
                code=self.gate_id,
                message=f"{row.kind}: {row.protocol or row.model} ({row.detail})",
                severity=c.Infra.GateSeverity.ERROR.value,
            )
            for row in report.parity
        )
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=not issues,
                issues=issues,
                raw_output=f"parity={len(report.parity)}",
                started=started,
            ),
            ctx,
        )


__all__: list[str] = ["FlextInfraGatesPydanticCensus"]
