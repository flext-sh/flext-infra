"""Deptry dependency-declaration gate over the project's import surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override
from uuid import uuid4

from flext_infra import c, config, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraDepsGate(FlextInfraGate):
    """Fail every import the project's declared dependencies never declare.

    Why (aihub-l42it.11): undeclared runtime imports surface today only deep
    inside the generation pipeline's rope pass, minutes into a failing run;
    this gate states the same fact in seconds at check time, so a racing
    consolidation can never land an orphan import unnoticed.
    """

    gate_id: ClassVar[str] = c.Infra.DEPS
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = True

    @override
    def selected_for(self, project_dir: Path) -> bool:
        """Select projects that declare dependencies (a pyproject exists).

        Returns:
            The resulting ``bool``.

        """
        return (project_dir / c.PYPROJECT_FILENAME).is_file()

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run deptry over the checkout and fail on any declared-surface gap.

        Native execution and report failures remain ERROR receipts, not findings.

        Args:
            project_dir: The root directory of the project to check.
            ctx: The gate context containing configuration and report directories.

        Returns:
            The complete scan receipt with every dependency issue.

        """
        return self._scan(project_dir, ctx)[0]

    @override
    def fix(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Repair native-evidenced declarations under the shared mutation lease.

        Args:
            project_dir: The root directory of the project to repair.
            ctx: The gate context containing configuration and report directories.

        Returns:
            The native planning scan when no repair is needed, an ERROR receipt
            when interpreter provenance is missing, or the guarded publication
            receipt retaining the pre-repair diagnostic.

        Raises:
            ValueError: If the context does not request a mutating operation.

        """
        if ctx.check_only or not ctx.apply_fixes:
            msg = "repair requires apply_fixes=True and check_only=False"
            raise ValueError(msg)
        started = time.monotonic()
        with self._mutation_lease(project_dir):
            execution, scan = self._scan(project_dir, ctx)
            if execution.outcome is not c.Infra.ToolOutcome.FINDINGS or scan is None:
                return execution
            inputs = ctx.runtime_dependency_inputs
            if inputs is None and ctx.runtime_dependency_collector is not None:
                inputs = ctx.runtime_dependency_collector(project_dir, scan).unwrap()
            if inputs is None or inputs.python != Path(sys.executable).absolute():
                issue = m.Infra.Issue(
                    file=str(project_dir / c.PYPROJECT_FILENAME),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=(
                        "dependency repair requires provenance"
                        " from the selected interpreter"
                    ),
                    severity=c.Infra.GateSeverity.ERROR.value,
                )
                return self._build_gate_execution(
                    m.Infra.GateExecutionParams(
                        project_dir=project_dir,
                        verdict=False,
                        outcome=c.Infra.ToolOutcome.ERROR,
                        issues=(*execution.issues, issue),
                        raw_output=execution.raw_output + "\n" + issue.message,
                        started=started,
                    ),
                    ctx=ctx,
                )
            plan = u.Infra.runtime_dependency_plan(scan, inputs).unwrap()
            changed = u.Infra.publish_runtime_dependency_plan(plan).unwrap()
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=True,
                outcome=c.Infra.ToolOutcome.CLEAN,
                issues=(),
                raw_output=execution.raw_output
                + f"\ndependency declaration changed={changed}; "
                "independent verification requires an explicit check",
                started=started,
            ),
            ctx=ctx,
        )

    def _prepare_report_dir(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Path:
        """Plan and create the private report directory for one deptry run.

        Guarded creation failures surface as ``OSError`` to the caller.

        Args:
            project_dir: The root directory of the project being scanned.
            ctx: The gate context holding the base reports directory.

        Returns:
            The absolute report directory path for this gate execution.

        Raises:
            FileExistsError: If the planned directory chain resolves empty.

        """
        report_dir = ctx.reports_dir.absolute() / (
            f"{project_dir.name}-{self.gate_id}-{uuid4().hex}"
        )
        planned = u.Cli.atomic_plan_directory_chain(report_dir).unwrap()
        if not planned.directories:
            raise FileExistsError(report_dir)
        u.Cli.atomic_create_directory_chain_guarded(
            planned,
            permission_mode=config.Infra.codegen.modes.directory_private,
        ).unwrap()
        return report_dir

    def _scan(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[m.Infra.GateExecution, m.Infra.DeptryScan | None]:
        """Capture and grade one native report for checking or guarded repair.

        Args:
            project_dir: The root directory of the project to scan.
            ctx: The gate context containing configuration and report directories.

        Returns:
            The gate execution receipt plus the native scan when captured,
            or ``None`` after a guarded capture failure.

        """
        started = time.monotonic()
        raw_output = ""
        issues: t.VariadicTuple[m.Infra.Issue] = ()
        outcome = c.Infra.ToolOutcome.ERROR
        scan: m.Infra.DeptryScan | None = None
        try:
            report_dir = self._prepare_report_dir(project_dir, ctx)
            scan = u.Infra.capture_deptry_scan(
                project_dir,
                Path(sys.executable).parent,
                config_path=project_dir / c.PYPROJECT_FILENAME,
                json_output_path=report_dir / "deptry.json",
            ).unwrap()
            raw_output = (
                f"cwd={project_dir} report={scan.report_state.path}\n"
                f"return-code={scan.native.outcome.raw_return_code}\n"
                f"stdout:\n{scan.native.stdout}\nstderr:\n{scan.native.stderr}\n"
                f"report-sha256={scan.report_sha256}"
            )
            issues = tuple(
                m.Infra.Issue(
                    file=item.location.file,
                    line=item.location.line or 0,
                    column=item.location.column or 0,
                    code=f"{self.gate_id}-{item.error.code}",
                    message=item.error.message,
                    severity=c.Infra.GateSeverity.ERROR.value,
                )
                for item in scan.report.root
            )
            outcome = u.Infra.tool_outcome(
                scan.native.outcome,
                findings=len(issues),
                findings_exit_codes=(1,),
            )
        except (OSError, ValueError, RuntimeError):
            outcome = c.Infra.ToolOutcome.ERROR
            scan = None
            issues = (
                *issues,
                m.Infra.Issue(
                    file=str(project_dir),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=traceback.format_exc(),
                    severity=c.Infra.GateSeverity.ERROR.value,
                ),
            )
            raw_output += "\n" + issues[-1].message
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=outcome is c.Infra.ToolOutcome.CLEAN,
                outcome=outcome,
                issues=issues,
                raw_output=raw_output,
                started=started,
            ),
            ctx=ctx,
        ), scan


__all__: list[str] = ["FlextInfraDepsGate"]
