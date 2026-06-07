"""Multi-project orchestration loop + failure collection — extracted concern."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u


class FlextInfraOrchestratorLoopMixin:
    """Iterate projects, run each via ``_run_project``, summarize failures.

    Composed into FlextInfraOrchestratorService via inheritance; borrows
    ``_run_project`` from the run mixin via MRO.
    """

    if TYPE_CHECKING:

        def _run_project(
            self,
            project: str,
            verb: str,
            _index: int,
            *,
            make_args: t.StrSequence,
        ) -> p.Result[m.Cli.CommandOutput]: ...

    def _execute_project(
        self,
        project: str,
        verb: str,
        idx: int,
        *,
        make_args: t.StrSequence,
    ) -> t.Pair[m.Cli.CommandOutput, bool]:
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
            allowed_verbs = c.Infra.ORCHESTRATED_PROJECT_VERBS
            if verb not in allowed_verbs:
                allowed = ", ".join(allowed_verbs)
                return r[t.SequenceOf[m.Cli.CommandOutput]].fail(
                    f"unsupported orchestrate verb '{verb}' (allowed: {allowed})",
                )
            results: t.MutableSequenceOf[m.Cli.CommandOutput] = []
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
                self._failure_summary(verb, failures)
            return r[t.SequenceOf[m.Cli.CommandOutput]].ok(results)
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[t.SequenceOf[m.Cli.CommandOutput]].fail_op("Orchestration", exc)


__all__: list[str] = ["FlextInfraOrchestratorLoopMixin"]
