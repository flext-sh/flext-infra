"""Shared gate template abstraction for workspace quality checks.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, config, m, u
from flext_infra.workspace import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraGate:
    """Abstract template implementing common check/fix execution flow for gates."""

    gate_id: ClassVar[str] = ""
    gate_name: ClassVar[str] = ""
    can_fix: ClassVar[bool] = False
    # A gate whose check command is one fixed ``python -m`` invocation wrapped
    # around its resolved check dirs declares the invocation here instead of
    # restating the ``_build_check_command`` override.
    check_module_command_prefix: ClassVar[t.StrSequence] = ()
    check_module_command_suffix: ClassVar[t.StrSequence] = ()
    # Name of the external scanner a gate provisions on PATH, when it uses one.
    scanner_binary: ClassVar[str] = ""
    checker_info_prefixes: ClassVar[t.StrSequence] = ()
    # A gate that analyzes Python sources is selected only for a project whose
    # detected content holds a first-party Python target.
    requires_python_targets: ClassVar[bool] = False
    # A gate whose tool natively accepts several project roots in one
    # invocation (resolving each file's nearest configuration) runs once over
    # the union of every selected project under a workspace-scope run.
    union_capable: ClassVar[bool] = False
    # Shared check-invocation defaults. A gate replaces the value, or overrides
    # the reader when the value depends on the project.
    check_timeout: ClassVar[int] = c.Infra.TIMEOUT_DEFAULT
    check_report_filename: ClassVar[str] = ""
    check_env: ClassVar[t.StrMapping | None] = None
    check_remove_env_keys: ClassVar[t.StrSequence] = (c.Infra.ENV_VAR_FORCE_COLOR,)
    check_report_evidence: ClassVar[t.StrSequence] = ()

    def selected_for(self, project_dir: Path, ctx: m.Infra.GateContext) -> bool:
        """Whether this project's detected content selects the gate at all.

        The single selection hook: a gate whose inputs depend on the project's
        content overrides it to declare that content, reading the invocation's
        injected ``ctx.scope_facts``. An unselected gate never runs, never
        passes, and is never listed.

        Returns:
            The resulting ``bool``.

        """
        del ctx
        return not self.requires_python_targets or bool(
            self._python_targets(project_dir),
        )

    @staticmethod
    def _python_targets(project_dir: Path) -> t.StrSequence:
        """First-party Python targets outside the workspace's analysis exclusions.

        Returns:
            The resulting ``t.StrSequence``.

        """
        return u.Infra.discover_python_targets(
            project_dir,
            workspace_excluded_top_dirs=(
                FlextInfraWorkspaceDetector.analysis_excluded_top_dirs(
                    project_dir,
                ).unwrap()
            ),
        )

    def __init__(
        self,
        repository_root: Path,
        *,
        runner: p.Cli.CommandRunner = u.Cli,
    ) -> None:
        """Bind repository root and the command runner (``u.Cli`` by default)."""
        self._repository_root = repository_root
        self._runner = runner

    @staticmethod
    def _python_module_command(module: str, *args: str) -> t.StrSequence:
        """Canonical venv-anchored tool invocation.

        Every linter/type-checker runs through the workspace interpreter
        (``sys.executable -m <module>``) so tool resolution is bound to the
        active ``.venv`` and never depends on ``PATH`` ordering or an external
        mise/system shim. This is the single source for building a Python
        module command shared by all gates.

        Returns:
            The resulting ``t.StrSequence``.

        """
        return (sys.executable, "-m", module, *args)

    @staticmethod
    def _python_console_script_command(tool: str, *args: str) -> t.StrSequence:
        """Invoke a uv-managed console script from the active interpreter directory.

        Returns:
            The resulting ``t.StrSequence``.

        """
        return (str(Path(sys.executable).with_name(tool)), *args)

    # ------------------------------------------------------------------
    # Template method: check
    # ------------------------------------------------------------------

    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Template method: timing + dirs + skip + run + parse + result.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        check_dirs = self._get_check_dirs(project_dir, ctx)
        if not check_dirs:
            # Content selection keeps the checker from running a gate without
            # inputs; a direct call without targets establishes no acceptance.
            return self._skip_result(project_dir, ctx, started)
        return self._execute_check_command(project_dir, ctx, check_dirs, started)

    def check_files(
        self,
        files: t.SequenceOf[Path],
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Check specific files instead of whole directory.

        Passes file paths directly to the tool CLI for scoped validation.
        Falls back to directory check if no files provided.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        if not files:
            return self.check(project_dir, ctx)
        started = time.monotonic()
        file_strs = [str(f.relative_to(project_dir)) for f in files if f.exists()]
        if not file_strs:
            return self._skip_result(project_dir, ctx, started)
        return self._execute_check_command(project_dir, ctx, file_strs, started)

    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
        started: float,
    ) -> m.Infra.GateExecution:
        """Build, run, parse the check command (check and check_files).

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        report_path = self._check_report_path(project_dir, ctx)
        if report_path is not None:
            report_path.unlink(missing_ok=True)
        cmd = self._build_check_command(project_dir, ctx, targets)
        result = self._run(
            cmd,
            project_dir,
            ctx,
        )
        if u.Cli.process_succeeded(result.outcome):
            self._validate_check_report(result, project_dir, ctx, targets)
        return self._parsed_gate_execution(project_dir, ctx, result, started)

    @classmethod
    def resolve_binary(cls) -> str | None:
        """Locate the provisioned scanner on PATH; None when absent.

        Returns:
            The resulting ``str | None``.

        """
        return shutil.which(cls.scanner_binary)

    def _native_error_issue(self, _project_dir: Path, stderr: str) -> m.Infra.Issue:
        """Report native checker stderr as one gate execution error.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        del _project_dir
        return m.Infra.Issue(
            file=c.PYPROJECT_FILENAME,
            line=1,
            column=1,
            code=f"{self.gate_id}-exec",
            message=stderr.strip(),
            severity=c.Infra.ERROR,
        )

    def _tool_failure_issue(self, scan: p.Cli.CommandOutput) -> m.Infra.Issue:
        """Scanner absence/crash must never read as a clean pass.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=c.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=self.gate_id,
            message=scan.stderr or f"{self.scanner_binary} execution failed",
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )

    @staticmethod
    def _command_error_issue(
        result: p.Cli.CommandOutput,
        tool: str,
        file: str,
    ) -> m.Infra.Issue:
        """Report an unsuccessful command that supplied no structured issues.

        The failure belongs to the whole ``file``, located at its first position.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        interrupted = (
            result.outcome.timed_out
            or result.outcome.forwarded_signal is not None
            or result.outcome.raw_return_code < 0
        )
        detail = (
            f"timed_out={result.outcome.timed_out}; "
            f"forwarded_signal={result.outcome.forwarded_signal}"
            if interrupted
            else "\n".join(
                stream.strip()
                for stream in (result.stderr, result.stdout)
                if stream.strip()
            )
            or "no diagnostics"
        )
        return m.Infra.Issue(
            file=file,
            line=1,
            column=1,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=(
                f"{tool} exited with code {result.outcome.raw_return_code}: {detail}"
            ),
            severity="ERROR",
        )

    def _finalize_parse_result(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        issues: t.SequenceOf[m.Infra.Issue],
        tool: str,
    ) -> t.Pair[bool, t.SequenceOf[m.Infra.Issue]]:
        """Surface a failed tool run that parsed no issues.

        If the tool exited unsuccessfully and no issues were parsed, add one
        ``c.Infra.ToolOutcome.ERROR`` issue so the failure is visible rather
        than silently passing.

        Returns:
            The native verdict and the same structural diagnostic instances.

        """
        if not u.Cli.process_succeeded(result.outcome) and not issues:
            issues = (
                *issues,
                self._command_error_issue(result, tool, str(project_dir)),
            )
        return u.Cli.process_succeeded(result.outcome), issues

    @staticmethod
    def _malformed_report_issue(detail: str, *, tool: str, file: str) -> p.Infra.Issue:
        """Report a checker whose structured report failed typed validation.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=file,
            line=0,
            column=0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=f"{tool} report is not a valid structured report: {detail}",
            severity="ERROR",
        )

    def _checker_issues(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        diagnostics: t.SequenceOf[p.Infra.Issue],
    ) -> t.SequenceOf[p.Infra.Issue]:
        """Join a type checker's report with its stderr and an unexplained exit.

        Stderr lines outside the checker's informational prefixes are failures;
        a failed run that leaves nothing else to report is surfaced as the
        ``<gate>-exec`` issue rather than silently passing.

        Returns:
            The report diagnostics, stderr failures and the bare-exit issue.

        """
        issues: t.SequenceOf[p.Infra.Issue] = (
            *diagnostics,
            *(
                m.Infra.Issue(
                    file=str(project_dir),
                    line=0,
                    column=0,
                    code=f"{self.gate_id}-stderr",
                    message=line,
                    severity="ERROR",
                )
                for line in result.stderr.splitlines()
                if line.strip()
                and line.lstrip().split(maxsplit=1)[0] not in self.checker_info_prefixes
            ),
        )
        if issues or u.Cli.process_succeeded(result.outcome):
            return issues
        message = (result.stderr or result.stdout).strip() or (
            f"{self.gate_id} exited with code {result.outcome.raw_return_code} "
            "without JSON diagnostics"
        )
        return (
            m.Infra.Issue(
                file=c.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=f"{self.gate_id}-exec",
                message=message,
                severity=c.Infra.ERROR,
            ),
        )

    def _parsed_gate_execution(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        result: p.Cli.CommandOutput,
        started: float,
    ) -> m.Infra.GateExecution:
        """Parse one tool result and assemble the gate execution it reports.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        evidence = self._publish_raw_receipt(ctx, self._raw_output(result))
        process = m.Cli.ProcessOutcome.model_validate(
            result.outcome, from_attributes=True
        )
        if (
            process.timed_out
            or process.forwarded_signal is not None
            or process.raw_return_code < 0
        ):
            return self._gate_execution_from(
                m.Infra.GateExecutionParams(
                    project_dir=project_dir,
                    verdict=False,
                    outcome=c.Infra.ToolOutcome.ERROR,
                    issues=(
                        self._command_error_issue(
                            result, self.gate_id, str(project_dir)
                        ),
                    ),
                    raw_output=evidence.raw_output,
                    started=started,
                ),
                evidence,
            ).model_copy(update={"process": process})
        passed, issues = self._parse_check_output(result, project_dir, ctx)
        if self.gate_id == c.Infra.LINT and result.stderr.strip():
            issues = (
                *issues,
                self._native_error_issue(project_dir, result.stderr),
            )
            passed = False
        outcome = u.Infra.tool_outcome(
            result.outcome,
            findings=len(issues),
            findings_exit_codes=self._findings_exit_codes(),
        )
        if any(
            issue.code == c.Infra.ToolOutcome.ERROR
            or issue.code in {f"{self.gate_id}-stderr", f"{self.gate_id}-exec"}
            for issue in issues
        ):
            outcome = c.Infra.ToolOutcome.ERROR
        return self._gate_execution_from(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=passed,
                outcome=outcome,
                issues=tuple(
                    m.Infra.Issue.model_validate(issue, from_attributes=True)
                    for issue in issues
                ),
                raw_output=evidence.raw_output,
                started=started,
            ),
            evidence,
        ).model_copy(update={"process": process})

    def _detected_gate_execution(
        self,
        project_dir: Path,
        *,
        ctx: m.Infra.GateContext,
        issues: t.SequenceOf[p.Infra.Issue],
        started: float,
    ) -> m.Infra.GateExecution:
        """Assemble one gate execution from detector-produced issues.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=not issues,
                issues=tuple(
                    m.Infra.Issue.model_validate(issue, from_attributes=True)
                    for issue in issues
                ),
                raw_output="\n".join(issue.formatted for issue in issues),
                started=started,
            ),
            ctx,
        )

    def _gate_result(
        self,
        project_dir: Path,
        *,
        passed: bool,
        errors: t.StrSequence,
        started: float,
    ) -> m.Infra.GateResult:
        """Summarize one gate run: identity, verdict, report lines and duration.

        Returns:
            The resulting ``m.Infra.GateResult``.

        """
        return m.Infra.GateResult(
            gate=self.gate_id,
            project=project_dir.name,
            passed=passed,
            errors=list(errors),
            duration=round(time.monotonic() - started, 3),
        )

    def _build_gate_execution(
        self,
        params: p.Infra.GateExecutionParams,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Publish the native output receipt, then assemble the gate execution.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        return self._gate_execution_from(
            params, self._publish_raw_receipt(ctx, params.raw_output)
        )

    def _gate_execution_from(
        self,
        params: p.Infra.GateExecutionParams,
        evidence: m.Infra.GateOutputReceipt,
    ) -> m.Infra.GateExecution:
        """Assemble a gate execution from its native outcome and findings.

        Native outcome and acceptance are separate. Every remaining finding
        blocks acceptance, keeping its native severity in the log and SARIF;
        a warning is never converted into approval. Without a declared
        native outcome, findings make it FINDINGS, a clean accepted run CLEAN
        and a failed run without findings ERROR.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        blocking = u.Infra.blocking_gate_findings(params.issues)
        return m.Infra.GateExecution(
            result=self._gate_result(
                params.project_dir,
                passed=params.verdict and not blocking,
                errors=[issue.formatted for issue in params.issues],
                started=params.started,
            ),
            issues=tuple(
                m.Infra.Issue.model_validate(issue, from_attributes=True)
                for issue in params.issues
            ),
            raw_output=evidence.raw_output,
            raw_receipt=evidence.path,
            outcome=(
                params.outcome
                or (
                    c.Infra.ToolOutcome.FINDINGS
                    if params.issues
                    else c.Infra.ToolOutcome.CLEAN
                    if params.verdict
                    else c.Infra.ToolOutcome.ERROR
                )
            ),
        )

    def _build_project_error_gate_result(
        self,
        project_dir: Path,
        errors: t.SequenceOf[str],
        ctx: m.Infra.GateContext,
        started: float,
    ) -> m.Infra.GateExecution:
        """Preserve project-level failures as blocking structured diagnostics.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=not errors,
                issues=tuple(
                    m.Infra.Issue(
                        file=str(project_dir),
                        line=1,
                        column=1,
                        code=self.gate_id,
                        message=error,
                        severity=c.Infra.GateSeverity.ERROR.value,
                    )
                    for error in errors
                ),
                raw_output="\n".join(errors),
                started=started,
            ),
            ctx,
        )

    def _build_validation_report_result(
        self,
        project_dir: Path,
        report_result: p.Result[m.Infra.ValidationReport],
        *,
        ctx: m.Infra.GateContext,
        started: float,
    ) -> m.Infra.GateExecution:
        """Grade a validator report: a broken run apart from found violations.

        Returns:
            The gate execution carrying the report's violations, or the
            validator's own failure as the single blocking diagnostic.

        """
        report = report_result.value if report_result.success else None
        errors = (
            [report_result.error or f"{self.gate_id} failed"]
            if report is None
            else list(report.violations)
            or ([] if report.passed else [f"{self.gate_id} failed"])
        )
        return self._build_project_error_gate_result(project_dir, errors, ctx, started)

    def _build_single_issue_result(
        self,
        project_dir: Path,
        message: str,
        ctx: m.Infra.GateContext,
        started: float,
    ) -> m.Infra.GateExecution:
        """Build a gate execution from one project-configuration failure.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=False,
                issues=(
                    m.Infra.Issue(
                        file=c.PYPROJECT_FILENAME,
                        line=1,
                        column=1,
                        code=self.gate_id,
                        message=message,
                        severity=c.Infra.GateSeverity.ERROR.value,
                    ),
                ),
                raw_output=message,
                started=started,
            ),
            ctx,
        )

    # ------------------------------------------------------------------
    # Template hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Return directories to check. Default: discover + filter for .py files.

        Returns:
            Directories to check. Default: discover + filter for .py files.

        """
        del ctx
        return self._dirs_with_py(project_dir, self._existing_check_dirs(project_dir))

    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Build the tool CLI command from the declared module invocation.

        Default: none, so a gate that overrides ``check`` directly still gets no
        command.

        Returns:
            The resulting ``t.StrSequence``.

        """
        _ = project_dir, ctx
        if not self.check_module_command_prefix:
            return []
        return self._python_module_command(
            *self.check_module_command_prefix,
            *check_dirs,
            *self.check_module_command_suffix,
        )

    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.Pair[bool, t.SequenceOf[p.Infra.Issue]]:
        """Parse tool output into (passed, issues).

        Concrete gates that run the template check implement this method.

        Raises:
            NotImplementedError: If the concrete gate did not implement parsing.

        """
        del result, project_dir, ctx
        msg = f"{type(self).__name__}._parse_check_output() must be implemented"
        raise NotImplementedError(msg)

    def _check_timeout(self, project_dir: Path, ctx: m.Infra.GateContext) -> int:
        """Timeout for the check command. Override for long-running tools.

        Returns:
            The resulting ``int``.

        """
        _ = project_dir, ctx
        return self.check_timeout

    def _check_report_path(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Path | None:
        """Name the native output replaced by this invocation, when required.

        Returns:
            The resulting ``Path | None``.

        """
        if not self.check_report_filename:
            return None
        return ctx.reports_dir / f"{project_dir.name}-{self.check_report_filename}"

    def _validate_check_report(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> None:
        """Validate native execution evidence against the exact submitted targets.

        Raises:
            ValueError: If declared native-report evidence is absent from the
                tool output.

        """
        _ = project_dir, ctx, targets
        missing = [
            token
            for token in self.check_report_evidence
            if token not in result.stdout and token not in result.stderr
        ]
        if not missing:
            return
        msg = "native report missing evidence: " + ", ".join(missing)
        raise ValueError(msg)

    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrMapping | None:
        """Return a custom environment for the check command. Default: None (inherit).

        Returns:
            A custom environment for the check command. Default: None (inherit).

        """
        _ = project_dir, ctx
        return self.check_env

    def _check_remove_env_keys(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Return inherited environment keys removed for this tool invocation.

        Every gate parses its tool's output, so the host color-forcing signal is
        never inherited: with the orchestrator's NO_COLOR it made Node-based
        tools print a warning on stderr that the gate then counted as a finding.

        Returns:
            Inherited environment keys removed for this tool invocation.

        """
        _ = project_dir, ctx
        return self.check_remove_env_keys

    # ------------------------------------------------------------------
    # Template method: fix
    # ------------------------------------------------------------------

    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        """Execute the declared repair once and retain its native result.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        self._require_repair(ctx)
        started = time.monotonic()
        targets = self._get_fix_targets(project_dir, ctx)
        if not targets:
            return self._skip_result(project_dir, ctx, started)
        return self._execute_fix_command(
            project_dir, ctx, targets, started, (project_dir,)
        )

    # ------------------------------------------------------------------
    # Union execution: one native invocation over several project roots
    # ------------------------------------------------------------------

    @staticmethod
    def union_group_key(project_dir: Path) -> str:
        """Identify the configuration a union invocation applies to a project.

        Projects sharing one key run in one invocation, configured by the
        first project of the group. A tool that resolves each file's nearest
        configuration natively needs no key.

        Returns:
            The configuration fingerprint shared by one union group.

        """
        del project_dir
        return ""

    def check_union(
        self,
        project_dirs: t.SequenceOf[Path],
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run the read-only check once over the union of every project's targets.

        The first project owns the invocation's working directory and
        configuration; every target is absolute.

        Returns:
            One execution covering every project of the group.

        """
        started = time.monotonic()
        owner = project_dirs[0].resolve()
        targets = self._union_targets(project_dirs, ctx, repair=False)
        if not targets:
            return self._skip_result(owner, ctx, started)
        return self._execute_check_command(owner, ctx, targets, started)

    def fix_union(
        self,
        project_dirs: t.SequenceOf[Path],
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Apply the declared repair once over the union of every project's targets.

        Every project's mutation lock is held for the single invocation.

        Returns:
            One execution covering every project of the group.

        """
        self._require_repair(ctx)
        started = time.monotonic()
        owner = project_dirs[0].resolve()
        targets = self._union_targets(project_dirs, ctx, repair=True)
        if not targets:
            return self._skip_result(owner, ctx, started)
        return self._execute_fix_command(owner, ctx, targets, started, project_dirs)

    def _union_targets(
        self,
        project_dirs: t.SequenceOf[Path],
        ctx: m.Infra.GateContext,
        *,
        repair: bool,
    ) -> t.StrSequence:
        """Resolve each project's own targets to absolute paths.

        Returns:
            The union of every project's targets as absolute paths.

        """
        collect = self._get_fix_targets if repair else self._get_check_dirs
        return tuple(
            (project_dir.resolve() / target).as_posix()
            for project_dir in project_dirs
            for target in collect(project_dir, ctx)
        )

    def _require_repair(self, ctx: m.Infra.GateContext) -> None:
        """Reject a repair request the context or the gate does not allow.

        Raises:
            ValueError: If the context requests another operation or the gate
                has no repair implementation.

        """
        if ctx.check_only or not ctx.apply_fixes:
            msg = "repair requires apply_fixes=True and check_only=False"
            raise ValueError(msg)
        if not self.can_fix:
            msg = f"Gate {self.gate_id} does not support repair"
            raise ValueError(msg)

    def _execute_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
        started: float,
        lock_owners: t.SequenceOf[Path],
    ) -> m.Infra.GateExecution:
        """Run the repair once under every owner's mutation lock.

        Returns:
            The repair's native execution, failing on a native tool error.

        """
        cmd = self._build_fix_command(project_dir, ctx, targets)
        with ExitStack() as locks:
            for owner in sorted({owner.resolve() for owner in lock_owners}):
                locks.enter_context(
                    u.Cli.file_changes_lock(u.Infra.mutation_lock_path(owner).unwrap()),
                )
            result = self._run(
                cmd,
                project_dir,
                ctx,
            )
            # Retain this operation's report. Independent verification belongs
            # to an explicit check, never an implicit second tool invocation.
            execution = self._parsed_gate_execution(project_dir, ctx, result, started)
            native_error = (
                result.outcome.timed_out
                or result.outcome.forwarded_signal is not None
                or (
                    not u.Cli.process_succeeded(result.outcome)
                    and result.outcome.raw_return_code
                    not in self._findings_exit_codes()
                )
            )
            if native_error:
                issues: t.SequenceOf[p.Infra.Issue] = execution.issues
                if not any(issue.code == c.Infra.ToolOutcome.ERROR for issue in issues):
                    issues = (
                        *issues,
                        self._command_error_issue(
                            result, self.gate_id, str(project_dir)
                        ),
                    )
                return self._build_gate_execution(
                    m.Infra.GateExecutionParams(
                        project_dir=project_dir,
                        verdict=False,
                        outcome=c.Infra.ToolOutcome.ERROR,
                        issues=tuple(
                            m.Infra.Issue.model_validate(issue, from_attributes=True)
                            for issue in issues
                        ),
                        raw_output=execution.raw_output,
                        started=started,
                    ),
                    ctx=ctx,
                )
        return execution

    @staticmethod
    def _findings_exit_codes() -> t.VariadicTuple[int]:
        """Exit statuses with which this gate's tool reports its findings.

        A tool that declares none completes only with a success status.

        Returns:
            The findings statuses the tool's config declares.

        """
        return ()

    # ------------------------------------------------------------------
    # Fix hooks — subclasses override these
    # ------------------------------------------------------------------

    def _get_fix_targets(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> t.StrSequence:
        """Use the validated literal selection, otherwise the project's check dirs.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if ctx.selected_files:
            return tuple(
                str(path.resolve().relative_to(project_dir.resolve()))
                for path in ctx.selected_files
            )
        return self._get_check_dirs(project_dir, ctx)

    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: t.StrSequence,
    ) -> t.StrSequence:
        """Build the fix CLI command. Must override if can_fix is True."""
        _ = project_dir, ctx, targets
        msg = (
            f"Gate {self.gate_id} set can_fix=True but did not "
            f"implement _build_fix_command"
        )
        raise NotImplementedError(msg)

    @staticmethod
    def _raw_output(result: p.Cli.CommandOutput) -> str:
        """Preserve diagnostics regardless of the stream selected by a tool.

        Returns:
            The resulting ``str``.

        """
        return "\n".join(output for output in (result.stdout, result.stderr) if output)

    @staticmethod
    def _runner_limits(
        timeout: int,
    ) -> t.Pair[int | None, p.Cli.ProcessDeadline | None]:
        """Return the runner's timeout and deadline for one tool invocation.

        A gate whose child owns its termination window overrides this to hand
        the runner an explicit deadline instead of a plain timeout.

        Returns:
            The runner timeout and the optional explicit deadline.

        """
        return timeout, None

    def _run(
        self,
        cmd: t.StrSequence,
        cwd: Path,
        ctx: m.Infra.GateContext,
    ) -> p.Cli.CommandOutput:
        """Run one native tool of this gate under the invocation's context.

        The gate's own timeout and environment readers decide the limits
        and child environment for ``cwd``; the context supplies the signal
        wave of a concurrent stage, so the child process group subscribes to
        the main thread's forwarding.

        Returns:
            The resulting ``p.Cli.CommandOutput``.

        Raises:
            RuntimeError: If ``result.failure``.

        """
        run_timeout, deadline = self._runner_limits(self._check_timeout(cwd, ctx))
        result = self._runner.run_raw(
            cmd,
            cwd=cwd,
            timeout=run_timeout,
            options=m.Cli.ProcessOptions(
                env=self._check_env(cwd, ctx),
                remove_env_keys=self._check_remove_env_keys(cwd, ctx),
                deadline=deadline,
                signal_wave=ctx.signal_wave,
            ),
        )
        if result.failure:
            # A failed Result here means the tool never ran -- it could not be
            # spawned, or the runner itself failed. Synthesizing a
            # CommandOutput with an invented raw_return_code=1 made that
            # indistinguishable from the tool running and reporting findings,
            # so a missing binary was reported as a code violation against
            # `<scc>` and an operator chased a finding in a file that was
            # never scanned. A nonzero exit from a tool that did run still
            # reaches the parser as a real outcome; this path did not run.
            msg = result.error or "command execution failed"
            raise RuntimeError(msg)
        return result.value

    def _existing_check_dirs(self, project_dir: Path) -> t.StrSequence:
        """Return every first-class project-owned Python target.

        Returns:
            Owned Python directories and standalone root modules.

        """
        return self._python_targets(project_dir)

    @staticmethod
    def _dirs_with_py(project_dir: Path, dirs: t.StrSequence) -> t.StrSequence:
        """Dirs with py.

        Returns:
            The resulting ``t.StrSequence``.

        """
        out: t.MutableSequenceOf[str] = []
        for directory in dirs:
            path = project_dir / directory
            if not path.is_dir():
                continue
            if next(path.rglob(c.Infra.EXT_PYTHON_GLOB), None) or next(
                path.rglob("*.pyi"),
                None,
            ):
                out.append(directory)
        return out

    def _publish_raw_receipt(
        self, ctx: m.Infra.GateContext, raw_output: str
    ) -> m.Infra.GateOutputReceipt:
        """Publish exact execution bytes before exposing their durable receipt.

        Returns:
            The exact output and its path after authenticated publication succeeds.

        """
        receipt = ctx.reports_dir / (
            f"{self.gate_id}{config.Infra.tooling.raw_check_receipt_suffix}"
        )
        u.Cli.atomic_write_text_file(receipt, raw_output).unwrap()
        return m.Infra.GateOutputReceipt(raw_output=raw_output, path=receipt)

    def _skip_result(
        self, project_dir: Path, ctx: m.Infra.GateContext, started: float
    ) -> m.Infra.GateExecution:
        """A selected gate with no inputs did not establish acceptance.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        message = f"{self.gate_id}: no check targets were collected"
        evidence = self._publish_raw_receipt(ctx, message)
        return m.Infra.GateExecution(
            result=self._gate_result(
                project_dir,
                passed=False,
                errors=(message,),
                started=started,
            ),
            raw_output=message,
            raw_receipt=evidence.path,
            outcome=c.Infra.ToolOutcome.ERROR,
        )


__all__: list[str] = ["FlextInfraGate"]
