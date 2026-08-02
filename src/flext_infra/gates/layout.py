"""Project-layout quality gate (mro-0wuz, epic mro-hzox).

Reports layout-SSOT violations per project. Severity is config-driven
(``codegen.yaml layout.severity``): ``warning`` reports without failing the
pipeline; ``error`` fails on actionable (move/archive/gitignore) findings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, config, m
from flext_infra.codegen.layout import FlextInfraCodegenLayout
from flext_infra.gates.base_gate import FlextInfraGate


class FlextInfraLayoutGate(FlextInfraGate):
    """Layout-SSOT conformance gate backed by the layout engine check mode."""

    gate_id: ClassVar[str] = "layout"
    gate_name: ClassVar[str] = "Project Layout"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["layout"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["layout"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Report layout violations for ``project_dir`` from the layout SSOT."""
        started = time.monotonic()
        spec = config.Infra.codegen.layout
        engine = FlextInfraCodegenLayout(workspace_root=ctx.workspace_root)
        report = engine.check_project(project_dir)
        warning = spec.severity == "warning"
        issues = tuple(
            m.Infra.Issue(
                file=str(project_dir / finding.path),
                line=1,
                column=1,
                code=f"{self.gate_id}-{finding.rule}",
                message=finding.message,
                severity="WARNING" if warning or finding.rule == "review" else "ERROR",
            )
            for finding in report.findings
        )
        blocking = tuple(finding for finding in report.actionable if not warning)
        passed = warning or not blocking
        errors = [issue.formatted for issue in issues if not passed]
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=passed,
                errors=errors,
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
            ctx=ctx,
        )


__all__: list[str] = ["FlextInfraLayoutGate"]
