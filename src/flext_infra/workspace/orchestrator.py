"""Multi-project orchestration service.

Executes make verbs across projects with per-project logging and structured
results. Migrated from scripts/workspace_orchestrator.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraSyncService, c, m, p, r, s, t, u

logger = u.fetch_logger(__name__)


class FlextInfraOrchestratorService(s[bool]):
    """Infrastructure service for multi-project make orchestration.

    Executes a make verb across a list of projects sequentially, capturing
    per-project output and timing. Supports fail-fast mode to stop on
    first failure.

    """

    verb: Annotated[str, m.Field(description="Make verb to execute")]
    projects: Annotated[
        t.StrSequence,
        m.Field(
            default_factory=tuple,
            description="Project names targeted by the orchestration run.",
        ),
    ] = m.Field(default_factory=tuple)
    fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = False
    make_arg: Annotated[
        t.StrSequence,
        m.Field(
            default_factory=tuple,
            description="Additional arguments passed to each make invocation.",
        ),
    ] = m.Field(default_factory=tuple)

    @property
    def project_names(self) -> t.StrSequence:
        """Return normalized project names."""
        return [
            project_name
            for project in self.projects
            for project_name in project.split()
            if project_name.strip()
        ]

    @property
    def make_args(self) -> t.StrSequence:
        """Return normalized make arguments."""
        return [make_arg.strip() for make_arg in self.make_arg if make_arg.strip()]

    @staticmethod
    def _workspace_root() -> Path:
        """Resolve the active workspace root for orchestration."""
        return u.Infra.resolve_workspace_root_or_cwd()

    def _resolved_projects(self) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
        """Resolve the selected project names through canonical discovery."""
        return u.Infra.resolve_projects(
            self._workspace_root(),
            self.project_names,
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
        projects: Sequence[m.Infra.ProjectInfo],
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

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the workspace-orchestrate CLI flow."""
        allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
        if self.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            return r[bool].fail(
                f"unsupported orchestrate verb '{self.verb}' (allowed: {allowed})",
            )
        resolved_projects = self._resolved_projects()
        if resolved_projects.failure:
            return r[bool].fail(resolved_projects.error or "project resolution failed")
        projects = resolved_projects.value
        if not projects:
            return r[bool].fail("no projects discovered")
        workspace_root = self._workspace_root()
        prepare_result = self._prepare_projects(projects, workspace_root=workspace_root)
        if prepare_result.failure:
            return prepare_result
        result = self.orchestrate(
            projects=[
                self._project_target(project, workspace_root=workspace_root)
                for project in projects
            ],
            verb=self.verb,
            fail_fast=self.fail_fast,
            make_args=self.make_args,
        )
        if result.failure:
            return r[bool].fail(result.error or "orchestration completed with failures")
        failures = sum(1 for item in result.value if item.exit_code != 0)
        if failures:
            return r[bool].fail(f"orchestration completed with failures: {failures}")
        return r[bool].ok(True)

    def _execute_project(
        self,
        project: str,
        verb: str,
        idx: int,
        *,
        make_args: t.StrSequence,
    ) -> t.Infra.Pair[m.Cli.CommandOutput, bool]:
        """Run one project and return (output, succeeded)."""
        output_result = self._run_project(project, verb, idx, make_args=list(make_args))
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
        results: Sequence[m.Cli.CommandOutput],
    ) -> Sequence[t.Infra.Triple[str, int, Path]]:
        """Collect failure details for projects with non-zero exit codes."""
        failures: MutableSequence[t.Infra.Triple[str, int, Path]] = []
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
    ) -> p.Result[Sequence[m.Cli.CommandOutput]]:
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
            allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
            if verb not in allowed_verbs:
                allowed = ", ".join(allowed_verbs)
                return r[Sequence[m.Cli.CommandOutput]].fail(
                    f"unsupported orchestrate verb '{verb}' (allowed: {allowed})",
                )
            results: MutableSequence[m.Cli.CommandOutput] = []
            total = len(projects)
            success = 0
            failed = 0
            skipped = 0
            started_total = time.monotonic()
            for idx, project in enumerate(projects, start=1):
                u.Cli.progress(idx, total, project, verb)
                if skipped:
                    results.append(
                        m.Cli.CommandOutput(
                            stdout="",
                            stderr="",
                            exit_code=0,
                            duration=0.0,
                        ),
                    )
                    continue
                cmd_output, succeeded = self._execute_project(
                    project,
                    verb,
                    idx,
                    make_args=make_args,
                )
                results.append(cmd_output)
                if succeeded:
                    success += 1
                else:
                    failed += 1
                    if fail_fast:
                        skipped = total - idx
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
                u.Infra.failure_summary(verb, failures)
            return r[Sequence[m.Cli.CommandOutput]].ok(results)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return r[Sequence[m.Cli.CommandOutput]].fail(
                f"Orchestration failed: {exc}",
            )

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
        log_path = u.Cli.get_report_path(
            Path.cwd(),
            c.Infra.RK_WORKSPACE,
            verb,
            f"{project}.log",
        )
        _ = u.Cli.ensure_dir(log_path.parent)
        started = time.monotonic()
        normalized_make_args = self._normalize_make_args_for_project(
            project=project,
            verb=verb,
            make_args=make_args,
        )
        proc_result = u.Cli.run_to_file(
            [c.Infra.MAKE, "-C", project, verb, *normalized_make_args],
            log_path,
            env={"NO_COLOR": "1", **os.environ},
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

    def _normalize_make_args_for_project(
        self,
        *,
        project: str,
        verb: str,
        make_args: t.StrSequence,
    ) -> t.StrSequence:
        if (verb != c.Infra.VERB_CHECK) or (not self._is_go_project(project)):
            return make_args
        normalized_args: MutableSequence[str] = []
        for make_arg in make_args:
            if make_arg.startswith("CHECK_GATES="):
                _, _, gates_value = make_arg.partition("=")
                normalized_gates = self._normalize_check_gates_for_go(gates_value)
                normalized_args.append(f"CHECK_GATES={normalized_gates}")
                continue
            normalized_args.append(make_arg)
        return normalized_args

    def _is_go_project(self, project: str) -> bool:
        return (Path(project) / c.Infra.GO_MOD).exists()

    def _normalize_check_gates_for_go(self, gates_value: str) -> str:
        raw_gates = [gate.strip() for gate in gates_value.split(",") if gate.strip()]
        if not raw_gates:
            return gates_value
        normalized_gates: MutableSequence[str] = []
        go_supported = {
            c.Infra.LINT,
            c.Infra.FORMAT,
            c.Infra.SECURITY,
            c.Infra.MARKDOWN,
            c.Infra.GO,
            c.Infra.TYPE_ALIAS,
        }
        python_type_gates = {
            c.Infra.PYREFLY,
            c.Infra.MYPY,
            c.Infra.PYRIGHT,
        }
        for gate in raw_gates:
            mapped_gate = c.Infra.TYPE_ALIAS if gate in python_type_gates else gate
            if mapped_gate not in go_supported and mapped_gate not in python_type_gates:
                normalized_gates.append(mapped_gate)
                continue
            if mapped_gate in go_supported and mapped_gate not in normalized_gates:
                normalized_gates.append(mapped_gate)
        if not normalized_gates:
            normalized_gates.append(c.Infra.TYPE_ALIAS)
        return ",".join(normalized_gates)


__all__: list[str] = ["FlextInfraOrchestratorService"]
