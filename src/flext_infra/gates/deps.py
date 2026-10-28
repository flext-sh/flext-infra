"""Deptry dependency-declaration gate over the project's import surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override
from uuid import uuid4

from flext_infra import c, config, m, t, u
from flext_infra.gates.base_gate import FlextInfraGate


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
    def selected_for(self, project_dir: Path, ctx: m.Infra.GateContext) -> bool:
        """Select projects that declare dependencies (a pyproject exists).

        Returns:
            The resulting ``bool``.

        """
        del ctx
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
            The complete scan receipt with every dependency issue, including
            each internal requirement reference off the integration line.

        Raises:
            ValueError: If the dependency declaration is not valid TOML.

        """
        execution = self._scan(project_dir, ctx)[0]
        pyproject = project_dir / c.PYPROJECT_FILENAME
        document = u.Cli.toml_parse_text(
            pyproject.read_text(encoding=c.DEFAULT_ENCODING)
        )
        if document is None:
            msg = f"invalid dependency declaration: {pyproject}"
            raise ValueError(msg)
        changes = self._aligned_references(project_dir, document)
        if not changes:
            return execution
        issues = tuple(
            m.Infra.Issue(
                file=str(pyproject),
                line=0,
                column=0,
                code=f"{self.gate_id}-internal-ref",
                message=change,
                severity=c.Infra.GateSeverity.ERROR.value,
            )
            for change in changes
        )
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=False,
                outcome=(
                    execution.outcome
                    if execution.outcome is c.Infra.ToolOutcome.ERROR
                    else c.Infra.ToolOutcome.FINDINGS
                ),
                issues=(*execution.issues, *issues),
                raw_output=execution.raw_output + "\n" + "\n".join(changes),
                started=time.monotonic(),
            ),
            ctx=ctx,
        )

    @staticmethod
    def _aligned_references(
        project_dir: Path,
        document: t.Cli.TomlDocument,
    ) -> Sequence[str]:
        """Move internal requirement references onto the integration line.

        Mutates only the given parsed document through the existing Git-ref
        migration owner; the manifest keeps the URL and the lock alone pins
        the exact commit.

        Returns:
            The change notes of every reference moved onto the line.

        """
        integration = (
            u.Infra
            .load_codegen_inputs(project_dir)
            .unwrap()
            .spec.branch_policy.integration_branch
        )
        migrations = u.Infra.internal_reference_migrations(
            document, target_ref=integration
        ).unwrap()
        if not migrations:
            return ()
        payload = u.validate_value(
            t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER,
            u.normalize_to_json_value(document.unwrap()),
        ).unwrap()
        changes = tuple(
            change
            for migration in migrations
            for change in u.Infra.rewrite_git_source_references(
                payload, migration
            ).unwrap()
        )
        u.Infra.sync_document_values(document, payload)
        return changes

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
        with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(project_dir).unwrap()):
            declaration = u.Cli.atomic_read_binary_file_state(
                project_dir / c.PYPROJECT_FILENAME, required=True
            ).unwrap()
            document = u.Cli.toml_parse_text(
                (declaration.content or b"").decode(c.DEFAULT_ENCODING)
            )
            if document is None:
                msg = f"invalid dependency declaration: {declaration.path}"
                raise ValueError(msg)
            if self._aligned_references(project_dir, document):
                u.Cli.atomic_write_binary_file_guarded(
                    declaration,
                    document.as_string().encode(c.DEFAULT_ENCODING),
                    permission_mode=declaration.mode,
                ).unwrap()
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
        issues: tuple[m.Infra.Issue, ...] = ()
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
