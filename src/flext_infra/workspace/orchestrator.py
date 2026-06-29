"""Multi-project orchestration service.

Executes make verbs across projects with per-project logging and structured
results. Migrated from scripts/workspace_orchestrator.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraProjectSelectionServiceBase, c, m, p, r, t, u
from flext_infra.workspace.sync import FlextInfraSyncService

logger = u.fetch_logger(__name__)


class FlextInfraOrchestratorService(FlextInfraProjectSelectionServiceBase[bool]):
    """Infrastructure service for multi-project make orchestration.

    Executes a make verb across a list of projects sequentially, capturing
    per-project output and timing. Supports fail-fast mode to stop on
    first failure.

    """

    verb: Annotated[str, m.Field(description="Make verb to execute")]
    fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = False
    make_arg: Annotated[
        t.StrSequence,
        m.Field(
            default_factory=tuple,
            description="Additional arguments passed to each make invocation.",
        ),
    ] = m.Field(default_factory=tuple)

    @property
    def make_args(self) -> t.StrSequence:
        """Return normalized make arguments."""
        return u.Infra.normalize_make_args(self.make_arg)

    def _resolved_projects(self) -> p.Result[t.SequenceOf[m.Infra.ProjectInfo]]:
        """Resolve the selected project names through canonical discovery."""
        return u.Infra.resolve_projects(
            self.root,
            self.project_names or (),
            include_attached=True,
        )

    @staticmethod
    def _project_target(
        project: m.Infra.ProjectInfo,
        *,
        workspace_root: Path,
    ) -> str:
        """Return the relative make target directory for one project."""
        return str(project.path.resolve().relative_to(workspace_root))

    def _prepare_projects(
        self,
        projects: t.SequenceOf[m.Infra.ProjectInfo],
        *,
        workspace_root: Path,
    ) -> p.Result[bool]:
        """Ensure selected projects have generated make infrastructure."""
        for project in projects:
            project_root = project.path.resolve()
            needs_sync = any(
                not (project_root / filename).is_file()
                for filename in (
                    c.Infra.BASE_MK,
                    c.Infra.MAKEFILE_FILENAME,
                )
            )
            if not needs_sync:
                continue
            sync_result = FlextInfraSyncService(
                workspace=project_root,
                canonical_root=workspace_root,
                apply_changes=True,
            ).execute()
            if sync_result.failure:
                sync_error = sync_result.error or "workspace sync failed"
                return r[bool].fail(f"{project.name}: {sync_error}")
        return r[bool].ok(True)

    @staticmethod
    def _failure_summary(
        verb: str,
        failures: t.SequenceOf[t.Triple[str, int, Path]],
    ) -> None:
        """Print compact failure summary for workspace orchestration."""
        if not failures:
            return
        u.Cli.error(f"{verb} failures: {len(failures)} project(s)")
        for project, error_count, log_path in failures:
            u.Cli.error(f"- {project}: {error_count} errors ({log_path})")

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the workspace-orchestrate CLI flow."""
        allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
        result: p.Result[bool]
        if self.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            result = r[bool].fail(
                f"unsupported orchestrate verb '{self.verb}' (allowed: {allowed})",
            )
        else:
            resolved_projects = self._resolved_projects()
            if resolved_projects.failure:
                result = r[bool].fail(
                    resolved_projects.error or "project resolution failed"
                )
            else:
                projects = resolved_projects.value
                if not projects:
                    result = r[bool].fail("no projects discovered")
                else:
                    workspace_root = self.root
                    prepare_result = self._prepare_projects(
                        projects, workspace_root=workspace_root
                    )
                    if prepare_result.failure:
                        result = prepare_result
                    else:
                        orchestrate_result = self.orchestrate(
                            projects=[
                                self._project_target(
                                    project, workspace_root=workspace_root
                                )
                                for project in projects
                            ],
                            verb=self.verb,
                            fail_fast=self.fail_fast,
                            make_args=self.make_args,
                        )
                        if orchestrate_result.failure:
                            result = r[bool].fail(
                                orchestrate_result.error
                                or "orchestration completed with failures"
                            )
                        else:
                            result = r[bool].ok(True)
        return result

    def _execute_project(
        self,
        project: str,
        verb: str,
        idx: int,
        *,
        make_args: t.StrSequence,
    ) -> t.Pair[m.Cli.CommandOutput, bool]:
        """Run one project and return (output, succeeded)."""
        output_result = self._run_project(project, verb, idx, make_args=make_args)
        if output_result.failure:
            return (
                m.Cli.CommandOutput(
                    stdout="",
                    stderr=output_result.error or "project execution failed",
                    exit_code=1,
                    duration=0.0,
                ),
                False,
            )
        cmd_output: m.Cli.CommandOutput = output_result.value
        return (cmd_output, cmd_output.exit_code == 0)

    @staticmethod
    def _collect_failures(
        projects: t.StrSequence,
        results: t.SequenceOf[m.Cli.CommandOutput],
    ) -> t.SequenceOf[t.Triple[str, int, Path]]:
        """Collect failure details for projects with non-zero exit codes."""
        failures: t.MutableSequenceOf[t.Triple[str, int, Path]] = []
        for proj_name, cmd_result in zip(projects, results, strict=False):
            if cmd_result.exit_code != 0:
                log_file = (
                    Path(cmd_result.stdout)
                    if cmd_result.stdout
                    else Path(f"{proj_name}.log")
                )
                err_count, _ = u.Infra.extract_errors(log_file)
                failures.append((proj_name, err_count, log_file))
        return failures

    def orchestrate(
        self,
        projects: t.StrSequence,
        verb: str,
        *,
        fail_fast: bool = False,
        make_args: t.StrSequence = (),
    ) -> p.Result[t.SequenceOf[m.Cli.CommandOutput]]:
        """Execute make verb across projects with per-project logging.

        Args:
            projects: List of project directory names.
            verb: Make verb to execute (e.g. "check", "test", "help").
            fail_fast: Stop execution on first project failure.
            make_args: Additional arguments to pass to make.

        Returns:
            r containing list of CommandOutput per project.

        """
        u.Cli.header("Workspace Orchestration")
        try:
            return self._orchestrate_checked(
                projects,
                verb,
                fail_fast=fail_fast,
                make_args=make_args,
            )
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[t.SequenceOf[m.Cli.CommandOutput]].fail_op("Orchestration", exc)

    def _orchestrate_checked(
        self,
        projects: t.StrSequence,
        verb: str,
        *,
        fail_fast: bool,
        make_args: t.StrSequence,
    ) -> p.Result[t.SequenceOf[m.Cli.CommandOutput]]:
        """Execute a validated orchestration run."""
        allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
        if verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            return r[t.SequenceOf[m.Cli.CommandOutput]].fail(
                f"unsupported orchestrate verb '{verb}' (allowed: {allowed})",
            )
        effective_make_args = self._normalize_fail_fast_make_args(
            make_args,
            fail_fast=fail_fast,
        )
        results: t.MutableSequenceOf[m.Cli.CommandOutput] = []
        total = len(projects)
        success = 0
        failed = 0
        skipped = 0
        started_total = time.monotonic()
        for idx, project in enumerate(projects, start=1):
            u.Cli.progress(idx, total, project, verb)
            cmd_output, succeeded = self._execute_project(
                project,
                verb,
                idx,
                make_args=effective_make_args,
            )
            results.append(cmd_output)
            if succeeded:
                success += 1
            else:
                failed += 1
                if fail_fast:
                    skipped = total - idx
                    break
        elapsed_total = time.monotonic() - started_total
        u.Cli.summary(
            m.Infra.SummaryStats(
                verb=verb,
                total=total,
                success=success,
                failed=failed,
                skipped=skipped,
                elapsed=elapsed_total,
            )
        )
        if failed > 0:
            failures = self._collect_failures(projects, results)
            self._failure_summary(verb, failures)
            return r[t.SequenceOf[m.Cli.CommandOutput]].fail(
                f"orchestration completed with failures: {failed}",
            )
        return r[t.SequenceOf[m.Cli.CommandOutput]].ok(results)

    def _run_project(
        self,
        project: str,
        verb: str,
        _index: int,
        *,
        make_args: t.StrSequence,
    ) -> p.Result[m.Cli.CommandOutput]:
        """Execute make verb for a single project.

        Args:
            project: Project directory name.
            verb: Make verb to execute.
            _index: 1-based project index.
            make_args: Additional make arguments.

        Returns:
            CommandOutput with log path in stdout, exit code, and timing.

        """
        log_path = u.Cli.resolve_report_path(
            Path.cwd(),
            c.Infra.RK_WORKSPACE,
            verb,
            f"{project}.log",
        )
        _ = u.Cli.ensure_dir(log_path.parent)
        started = time.monotonic()
        proc_result = u.Cli.run_to_file(
            [c.Infra.MAKE, "-C", project, verb, *make_args],
            log_path,
            env={"NO_COLOR": "1"},
        )
        return_code: int = proc_result.unwrap() if proc_result.success else 1
        stderr = "" if proc_result.success else proc_result.error or ""
        elapsed = time.monotonic() - started
        if return_code == 0:
            u.Cli.info(
                f"  ✓ {project} completed in {int(elapsed)}s  ({log_path})",
            )
        else:
            error_count, error_lines = u.Infra.extract_errors(log_path)
            u.Cli.project_failure(
                m.Infra.ProjectFailureInfo(
                    project=project,
                    elapsed=elapsed,
                    log_path=log_path,
                    error_count=error_count,
                    errors=list(error_lines),
                )
            )
            if error_lines:
                stderr = "\n".join(error_lines)
        return r[m.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(
                stdout=str(log_path),
                stderr=stderr,
                exit_code=return_code,
                duration=round(elapsed, 2),
            ),
        )

    @staticmethod
    def _normalize_fail_fast_make_args(
        make_args: t.StrSequence,
        *,
        fail_fast: bool,
    ) -> t.StrSequence:
        """Propagate orchestration fail-fast intent to project make invocations."""
        if not fail_fast:
            return make_args
        if any(make_arg.startswith("FAIL_FAST=") for make_arg in make_args):
            return make_args
        return (*make_args, "FAIL_FAST=1")


__all__: list[str] = ["FlextInfraOrchestratorService"]
