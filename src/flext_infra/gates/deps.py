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

from flext_infra import c, config, m, p, t, u
from flext_infra.gates import FlextInfraGates


class FlextInfraGatesDeps(FlextInfraGates):
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
    def selected_for(self, project_dir: Path, ctx: p.Infra.GateContext) -> bool:
        """Select packaged projects that declare dependencies (a pyproject exists).

        Deptry compares the imports of production source with the declaration; an
        unpackaged project (a consumer) ships no production source to compare.

        Returns:
            Whether the project declares a manifest and participates in packaging.

        """
        del ctx
        return (project_dir / c.PYPROJECT_FILENAME).is_file() and (
            u.Infra.project_package_participation(
                u.Infra.read_project_metadata_state(project_dir).unwrap().packaging
            )
        )

    @override
    def check(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
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
        # The scanner's own failure (an invalid or missing declaration among
        # them) is the first failure; reference alignment depends on a
        # declaration the scan could read.
        if execution.outcome == c.Infra.ToolOutcome.ERROR:
            return execution
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
                issues=tuple(
                    m.Infra.Issue.model_validate(issue, from_attributes=True)
                    for issue in (*execution.issues, *issues)
                ),
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
        """Move internal requirement references onto the FLEXT line.

        The line is the FLEXT line the checkout consumes
        (``u.Infra.flext_integration_line``), never the consumer's own
        ``branch_policy.integration_branch``: a consumer integrating on its own
        branch keeps its FLEXT dependencies on the FLEXT line. Mutates only the
        given parsed document through the existing Git-ref migration owner; the
        manifest keeps the URL and the lock alone pins the exact commit.

        Returns:
            The change notes of every reference moved onto the line.

        """
        migrations = u.Infra.internal_reference_migrations(
            document,
            target_ref=lambda: u.Infra.load_codegen_inputs(project_dir).flat_map(
                lambda inputs: u.Infra.flext_integration_line(
                    codegen=inputs.spec, repository_root=project_dir
                ).map(lambda line: line.branch)
            ),
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
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
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
        # Planning and the deptry scan are read-only: they run outside the
        # mutation lock, so a concurrent session never waits on them. Each
        # write is one verified publication batch.
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
            u.Cli.publish_file_changes(
                (
                    m.Cli.FileChange(
                        path=declaration.path,
                        before=declaration,
                        desired_content=document.as_string().encode(c.DEFAULT_ENCODING),
                        desired_mode=(
                            declaration.mode
                            if declaration.mode is not None
                            else c.Infra.CONFIG_SPEC[1]
                        ),
                    ),
                ),
                lock_path=u.Infra.mutation_lock_path(project_dir).unwrap(),
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
                    issues=tuple(
                        m.Infra.Issue.model_validate(issue, from_attributes=True)
                        for issue in (*execution.issues, issue)
                    ),
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
        ctx: p.Infra.GateContext,
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

    @staticmethod
    def _capture_with_retry(
        project_dir: Path,
        report_dir: Path,
    ) -> p.Infra.DeptryScan:
        """Capture the deptry scan, retrying transient concurrent-write races.

        Multi-agent worktrees mutate production sources while a scan runs; the
        atomic verification rejects that lost race. Retrying the whole capture
        on exactly this transient keeps the gate honest without masking real
        failures, which still unwrap loud.

        Returns:
            The resulting ``m.Infra.DeptryScan``.

        Raises:
            RuntimeError: If every attempt loses the capture race, or on the
                first non-transient capture failure.

        """
        attempts = c.Infra.SCAN_RACE_ATTEMPTS
        backoff = c.Infra.SCAN_RACE_BACKOFF_SECONDS
        last_error: str | None = None
        for attempt in range(1, attempts + 1):
            json_output_path = report_dir / "deptry.json"
            json_output_path.unlink(missing_ok=True)
            captured = u.Infra.capture_deptry_scan(
                project_dir,
                Path(sys.executable).parent,
                config_path=project_dir / c.PYPROJECT_FILENAME,
                json_output_path=json_output_path,
            )
            if captured.success:
                return captured.value
            detail = str(captured.error)
            if "changed during scanning" not in detail:
                captured.unwrap()  # non-transient: fail loud immediately
            last_error = detail
            time.sleep(backoff * attempt)
        msg = f"deptry capture lost the concurrent-write race {attempts}x: {last_error}"
        raise RuntimeError(msg)

    def _graded_receipt(
        self,
        scan: p.Infra.DeptryScan,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[str, tuple[m.Infra.Issue, ...], c.Infra.ToolOutcome]:
        """Build the native receipt with only the findings current usage leaves.

        Returns:
            The evidence text, the graded findings and their outcome.

        """
        retained, graded = self._grade_scan_items(scan, project_dir, ctx)
        raw_output = (
            f"cwd={project_dir} report={scan.report_state.path}\n"
            f"return-code={scan.native.outcome.raw_return_code}\n"
            f"stdout:\n{scan.native.stdout}\nstderr:\n{scan.native.stderr}\n"
            f"retained-by-declared-usage={retained}\n"
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
            for item in graded
        )
        if scan.report.root and not issues:
            return (raw_output, issues, c.Infra.ToolOutcome.CLEAN)
        return (
            raw_output,
            issues,
            u.Infra.tool_outcome(
                scan.native.outcome,
                findings=len(issues),
                findings_exit_codes=(1,),
            ),
        )

    def _grade_scan_items(
        self,
        scan: p.Infra.DeptryScan,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[int, tuple[p.Infra.DeptryDiagnostic, ...]]:
        """Separate native findings the declared usage already justifies.

        The repair planner retains a requirement used through a console script
        or a pytest plugin entry point and resolves an import whose supplier is
        unique and locked. A read-only verdict must apply the same facts, or
        ``make check`` reports what ``make fix`` deliberately keeps and the two
        owners disagree on the same declaration.

        Returns:
            The retained finding count and the findings still unexplained.

        """
        facts = self._declared_usage_facts(project_dir, scan, ctx)
        if facts is None:
            return (0, scan.report.root)
        graded = tuple(
            item
            for item in scan.report.root
            if not self._explained(item, retained_requirements=facts)
        )
        return (len(scan.report.root) - len(graded), graded)

    @staticmethod
    def _explained(
        item: p.Infra.DeptryDiagnostic,
        *,
        retained_requirements: frozenset[str],
    ) -> bool:
        """State whether current declared usage already covers one finding.

        Only an unused-requirement finding is explained by retention: an
        undeclared import still requires a declaration even when its supplier
        is uniquely resolvable, so it is never graded away here.

        Returns:
            Whether the finding is a requirement the declared usage retains.

        """
        if item.error.code != c.Infra.DEPTRY_UNUSED_DEPENDENCY_CODE:
            return False
        return u.Infra.distribution_identity(item.module) in retained_requirements

    @staticmethod
    def _declared_usage_facts(
        project_dir: Path,
        scan: p.Infra.DeptryScan,
        ctx: p.Infra.GateContext,
    ) -> frozenset[str] | None:
        """Read the retained requirements from the existing repair planner.

        Returns:
            The retained requirement identities, or ``None`` when provenance is
            unavailable and no finding is graded.

        """
        inputs = ctx.runtime_dependency_inputs
        if inputs is None and ctx.runtime_dependency_collector is not None:
            collected = ctx.runtime_dependency_collector(project_dir, scan)
            if collected.failure:
                return None
            inputs = collected.value
        if inputs is None:
            return None
        plan = u.Infra.runtime_dependency_plan(scan, inputs)
        if plan.failure:
            return None
        return frozenset(
            u.Infra.requirement_identity(raw) for raw in plan.value.dependencies
        )

    def _scan(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[p.Infra.GateExecution, p.Infra.DeptryScan | None]:
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
        scan: p.Infra.DeptryScan | None = None
        try:
            report_dir = self._prepare_report_dir(project_dir, ctx)
            scan = self._capture_with_retry(project_dir, report_dir)
            raw_output, issues, outcome = self._graded_receipt(
                scan,
                project_dir,
                ctx,
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


__all__: list[str] = ["FlextInfraGatesDeps"]
