"""Multi-project orchestration service.

Executes make verbs across projects with per-project logging and structured
results. Migrated from scripts/workspace_orchestrator.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_core import FlextLogger
from flext_infra import c, m, r, s, t, u

logger = FlextLogger.create_module_logger(__name__)


class FlextInfraOrchestratorService(s[bool]):
    """Infrastructure service for multi-project make orchestration.

    Executes a make verb across a list of projects sequentially, capturing
    per-project output and timing. Supports fail-fast mode to stop on
    first failure.

    """

    verb: Annotated[str, Field(description="Make verb to execute")]
    projects: Annotated[
        str,
        Field(default="", description="Comma-separated project directories"),
    ] = ""
    fail_fast: Annotated[
        bool,
        Field(default=False, description="Stop on first failure"),
    ] = False
    make_arg: Annotated[
        list[str],
        Field(default_factory=list, description="Additional make arguments"),
    ] = Field(default_factory=list)

    @property
    def project_names(self) -> list[str]:
        """Return normalized project names."""
        raw_projects = self.projects.replace(",", " ")
        return [project.strip() for project in raw_projects.split() if project.strip()]

    @property
    def make_args(self) -> list[str]:
        """Return normalized make arguments."""
        return [make_arg.strip() for make_arg in self.make_arg if make_arg.strip()]

    @override
    def execute(self) -> r[bool]:
        """Execute the workspace-orchestrate CLI flow."""
        allowed_verbs = c.Infra.Make.ORCHESTRATED_PROJECT_VERBS
        if self.verb not in allowed_verbs:
            allowed = ", ".join(allowed_verbs)
            return r[bool].fail(
                f"unsupported orchestrate verb '{self.verb}' (allowed: {allowed})",
            )
        if not self.project_names:
            return r[bool].fail("no projects specified")
        result = self.orchestrate(
            projects=self.project_names,
            verb=self.verb,
            fail_fast=self.fail_fast,
            make_args=self.make_args,
        )
        if result.is_failure:
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
    ) -> t.Infra.Pair[m.Infra.CommandOutput, bool]:
        """Run one project and return (output, succeeded)."""
        output_result = self._run_project(project, verb, idx, make_args=list(make_args))
        if output_result.is_failure:
            return (
                m.Infra.CommandOutput(
                    stdout="",
                    stderr=output_result.error or "project execution failed",
                    exit_code=1,
                    duration=0.0,
                ),
                False,
            )
        cmd_output: m.Infra.CommandOutput = output_result.value
        return (cmd_output, cmd_output.exit_code == 0)

    @staticmethod
    def _collect_failures(
        projects: t.StrSequence,
        results: Sequence[m.Infra.CommandOutput],
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
    ) -> r[Sequence[m.Infra.CommandOutput]]:
        """Execute make verb across projects with per-project logging.

        Args:
            projects: List of project directory names.
            verb: Make verb to execute (e.g. "check", "test", "help").
            fail_fast: Stop execution on first project failure.
            make_args: Additional arguments to pass to make.

        Returns:
            r containing list of CommandOutput per project.

        """
        u.Infra.header("Workspace Orchestration")
        try:
            allowed_verbs = c.Infra.Make.ORCHESTRATED_PROJECT_VERBS
            if verb not in allowed_verbs:
                allowed = ", ".join(allowed_verbs)
                return r[Sequence[m.Infra.CommandOutput]].fail(
                    f"unsupported orchestrate verb '{verb}' (allowed: {allowed})",
                )
            results: MutableSequence[m.Infra.CommandOutput] = []
            total = len(projects)
            success = 0
            failed = 0
            skipped = 0
            started_total = time.monotonic()
            for idx, project in enumerate(projects, start=1):
                u.Infra.progress(idx, total, project, verb)
                if skipped:
                    results.append(
                        m.Infra.CommandOutput(
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
            u.Infra.summary(
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
            return r[Sequence[m.Infra.CommandOutput]].ok(results)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return r[Sequence[m.Infra.CommandOutput]].fail(
                f"Orchestration failed: {exc}",
            )

    def _run_project(
        self,
        project: str,
        verb: str,
        _index: int,
        *,
        make_args: t.StrSequence,
    ) -> r[m.Infra.CommandOutput]:
        """Execute make verb for a single project.

        Args:
            project: Project directory name.
            verb: Make verb to execute.
            _index: 1-based project index.
            make_args: Additional make arguments.

        Returns:
            CommandOutput with log path in stdout, exit code, and timing.

        """
        log_path = u.Infra.get_report_path(
            Path.cwd(),
            c.Infra.ReportKeys.WORKSPACE,
            verb,
            f"{project}.log",
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        normalized_make_args = self._normalize_make_args_for_project(
            project=project,
            verb=verb,
            make_args=make_args,
        )
        proc_result = u.Infra.run_to_file(
            [c.Infra.MAKE, "-C", project, verb, *normalized_make_args],
            log_path,
            env={"NO_COLOR": "1", **os.environ},
        )
        return_code: int = proc_result.unwrap_or(1)
        stderr = "" if proc_result.is_success else proc_result.error or ""
        elapsed = time.monotonic() - started
        if return_code == 0:
            u.Infra.info(
                f"  ✓ {project} completed in {int(elapsed)}s  ({log_path})",
            )
        else:
            error_count, error_lines = u.Infra.extract_errors(log_path)
            u.Infra.project_failure(
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
        return r[m.Infra.CommandOutput].ok(
            m.Infra.CommandOutput(
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
        if (verb != c.Infra.Verbs.CHECK) or (not self._is_go_project(project)):
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
        return (Path(project) / c.Infra.Files.GO_MOD).exists()

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


__all__ = ["FlextInfraOrchestratorService"]
