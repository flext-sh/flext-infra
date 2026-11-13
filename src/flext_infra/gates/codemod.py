"""Codemod enforcement quality gate.

Runs ``ast-grep scan`` with the codemod rules discovered via
``importlib.resources`` cascade (ADR-014). Policy findings block the final
check; incomplete scans and native machinery failures remain distinct errors.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tempfile
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, config, m, p, settings, u
from flext_infra.gates import FlextInfraGates


class FlextInfraGatesCodemod(FlextInfraGates):
    """Report codemod rule findings for the selected repository."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][1]

    @override
    def check(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Run ast-grep only on this repository's first-class source roots.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            FileNotFoundError: If ``not targets``.

        """
        targets = u.Infra.ast_grep_scan_targets(project_dir)
        if not targets:
            raise FileNotFoundError(project_dir)
        return self._execute_check_command(
            project_dir,
            ctx,
            targets,
            time.monotonic(),
        )

    @override
    def check_files(
        self,
        files: Sequence[Path],
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Scan every requested file against every elected provider ruleset.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            FileNotFoundError: If ``not path.is_file()``.

        """
        if not files:
            return self.check(project_dir, ctx)
        for path in files:
            if not path.is_file():
                raise FileNotFoundError(path)
        return self._execute_check_command(
            project_dir,
            ctx,
            u.Infra.ast_grep_scan_targets(project_dir, source_files=files),
            time.monotonic(),
        )

    @override
    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        targets: Sequence[str],
        started: float,
    ) -> p.Infra.GateExecution:
        """Keep whole-project and file-scoped scans on the same native contract.

        A whole-project scan excludes the repository's nonparticipant paths; a
        literal file selection scans exactly the selected files.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            RuntimeError: If codemod rule planning failed without a diagnostic.

        """
        nonparticipants = (
            frozenset()
            if ctx.selected_files
            else u.Infra.repository_nonparticipant_paths(project_dir)
        )
        with u.Infra.codemod_workspace_snapshot(project_dir) as snapshot:
            planned = u.Infra.codemod_rule_plan(snapshot)
        if planned.failure:
            failure = planned.error
            if not failure:
                failure = "codemod rule planning failed without a diagnostic"
                raise RuntimeError(failure)
            return self._failure_gate_execution(project_dir, ctx, failure, started)

        native_targets = tuple(
            target for target in targets if Path(target).suffix != ".pyi"
        )
        binary = u.Infra.managed_mise_binary(c.Infra.SG, self._repository_root)
        if binary.failure:
            failure = binary.error
            if not failure:
                failure = "managed scanner resolution failed without a diagnostic"
                raise RuntimeError(failure)
            return self._failure_gate_execution(project_dir, ctx, failure, started)
        failures: list[p.Infra.Issue] = []
        raw_output: list[str] = []
        found: list[p.Infra.AstGrepDiagnostic] = list(
            u.Infra.codemod_path_findings(
                project_dir,
                tuple((project_dir / target).absolute() for target in targets),
                planned.value.rules,
            )
        )
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="check-codemod-", dir=settings.work_dir
        ) as directory:
            for index, (project, project_targets) in enumerate(
                u.Infra.project_targets(planned.value, native_targets)
            ):
                stage = Path(directory) / str(index)
                try:
                    ruleset = u.Infra.codemod_stage_scan_ruleset(
                        u.Infra.project_plan(planned.value, project), stage
                    )
                except ValueError as exc:
                    # Staging runs ast-grep over the projected ruleset; its
                    # refusal is a native failure of this gate, not a crash.
                    failures.append(
                        m.Infra.Issue(
                            file=str(stage / c.Infra.CODEMOD_CONFIG_FILENAME),
                            line=1,
                            column=1,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=str(exc),
                            severity="ERROR",
                        )
                    )
                    raw_output.append(str(exc))
                    break
                if not self._scan_ruleset(
                    (project_dir, ctx, binary.value, nonparticipants),
                    ruleset,
                    project_targets,
                    (found, failures, raw_output),
                ):
                    break
        findings = (
            *self._policy_issues(found),
            *u.Infra.codemod_import_cycle_issues(project_dir),
        )

        # Each finding counts under its declared catalog rule: a partitioned
        # rule's documents fold into the rule they were partitioned from.
        origins = {
            c.Infra.CODEMOD_IMPORT_CYCLE_CODE: c.Infra.CODEMOD_IMPORT_CYCLE_CODE,
            **{rule.id: rule.partition_of or rule.id for rule in planned.value.rules},
        }
        counts = Counter(origins[issue.code] for issue in findings)

        # A completed scan still blocks when elected policy rules find code.
        # Native scanner failures retain their distinct failure diagnostics.
        issues = (*failures, *findings)
        return self._build_gate_execution(
            m.Infra.GateExecutionParams.model_validate({
                "project_dir": (project_dir),
                "verdict": (not issues),
                "issues": (issues),
                "started": (started),
                "outcome": (
                    c.Infra.ToolOutcome.ERROR
                    if failures
                    else c.Infra.ToolOutcome.FINDINGS
                    if findings
                    else c.Infra.ToolOutcome.CLEAN
                ),
                "raw_output": (
                    "\n".join((
                        (
                            f"{len(findings)} policy findings; {len(failures)} native "
                            f"failures"
                        ),
                        *(
                            f"  {rule_id}: {count}"
                            for rule_id, count in sorted(
                                counts.items(), key=lambda item: (-item[1], item[0])
                            )
                        ),
                        *raw_output,
                    ))
                ),
            }),
            ctx=ctx,
        )

    def _scan_ruleset(
        self,
        scope: tuple[Path, p.Infra.GateContext, Path, frozenset[str]],
        ruleset: p.Infra.CodemodRuleset,
        targets: Sequence[str],
        sinks: tuple[list[p.Infra.AstGrepDiagnostic], list[p.Infra.Issue], list[str]],
    ) -> bool:
        """Scan one project's staged ruleset and collect its native report.

        Returns:
            Whether the scan completed; a native failure stops the gate.

        """
        project_dir, ctx, binary, nonparticipants = scope
        found, failures, raw_output = sinks
        scan = self._run(
            self._scan_command(ruleset, targets, binary, nonparticipants),
            project_dir,
            ctx,
        )
        outcome = scan.outcome
        raw_output.extend((
            (
                f"{ruleset.provider}: exit={outcome.raw_return_code}, "
                f"timed_out={outcome.timed_out}, signal={outcome.forwarded_signal}"
            ),
            self._raw_output(scan),
        ))
        failure = self._command_error_issue(scan, c.Infra.SG, str(ruleset.config))
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code not in {0, 1}
            or (outcome.raw_return_code == 0 and bool(scan.stderr.strip()))
        ):
            failures.append(failure)
            return False
        # DiagnosticError (exit 1) requires a valid RuleMatch array,
        # matching error count and the exact terminal diagnostic below.
        # Additional native diagnostics make that scan incomplete.
        report, expected_stderr = self._validated_scan_report(scan, ruleset)
        if scan.stderr.strip() != expected_stderr:
            # ast-grep can continue after a traversal error and still return
            # DiagnosticError because another file has an error match.
            # Only the complete terminal diagnostic proves a clean walk.
            failures.append(failure)
            return False
        found.extend(report.root)
        return True

    def _failure_gate_execution(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        failure: str,
        started: float,
    ) -> p.Infra.GateExecution:
        """Record one native codemod failure as a failed gate execution.

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
                        column=0,
                        code=self.gate_id,
                        message=failure,
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    ),
                ),
                raw_output=failure,
                started=started,
            ),
            ctx,
        )

    @staticmethod
    def _validated_scan_report(
        scan: p.Cli.CommandOutput,
        ruleset: p.Infra.CodemodRuleset,
    ) -> tuple[p.Infra.AstGrepReport, str]:
        """Validate findings and derive their exact native terminal diagnostic.

        Returns:
            The resulting ``tuple[p.Infra.AstGrepReport, str]``.

        Raises:
            ValueError: If ``(scan.outcome.raw_return_code == 1) != bool(error_count)``;
                or if ``any((finding.rule_id not in ruleset.rule_ids for finding in
                report.root))``.

        """
        report = m.Infra.AstGrepReport.model_validate_json(scan.stdout)
        error_count = sum(finding.severity == "error" for finding in report.root)
        if (scan.outcome.raw_return_code == 1) != bool(error_count):
            msg = (
                f"{ruleset.provider}: ast-grep exit {scan.outcome.raw_return_code} "
                "disagrees with the native diagnostic severities"
            )
            raise ValueError(msg)
        if any(finding.rule_id not in ruleset.rule_ids for finding in report.root):
            msg = f"{ruleset.provider}: ast-grep reported an unelected rule"
            raise ValueError(msg)
        expected_stderr = (
            "\n".join((
                c.Infra.AST_GREP_ERROR_FINDING_RECEIPT.format(count=error_count),
                c.Infra.AST_GREP_ERROR_FINDING_HELP,
            ))
            if error_count
            else ""
        )
        return report, expected_stderr

    @staticmethod
    def _scan_command(
        ruleset: p.Infra.CodemodRuleset,
        targets: Sequence[str],
        binary: Path,
        nonparticipants: frozenset[str] = frozenset(),
    ) -> Sequence[str]:
        """Canonical ast-grep invocation for one composed provider ruleset.

        Returns:
            The resulting ``Sequence[str]``.

        """
        # The gate scans the same inventory `make mod` rewrites: trees the
        # codegen artifact SSOT explicitly ignores for source scans stay outside
        # it. Generation ownership alone does not exclude a source tree.
        globs: Sequence[str] = tuple(
            f"!{dir_name}/"
            for dir_name in sorted({
                *config.Infra.codegen.check_excluded_dirs,
                *config.Infra.codegen.source_scan_ignored,
            })
        )
        globs = (
            *globs,
            *(
                glob
                for path in sorted(nonparticipants)
                for glob in (f"!/{path}", f"!/{path}/**")
            ),
        )
        cmd: list[str] = [
            str(binary),
            c.Infra.SCAN,
            "--config",
            str(ruleset.config),
            "--filter",
            u.Infra.codemod_rule_filter(ruleset.rule_ids),
            "--json=compact",
        ]
        threads = getattr(
            getattr(getattr(config.Infra, "tooling", None), "mod", None),
            "scan_threads",
            getattr(
                getattr(getattr(config.Infra, "codegen", None), "make", None),
                "scan_threads",
                4,
            ),
        )
        if threads and threads > 0:
            cmd.extend([c.Infra.SG_THREADS_FLAG, str(threads)])
        for glob in globs:
            cmd.extend([c.Infra.SG_GLOBS_FLAG, glob])
        cmd.extend(targets)
        return tuple(cmd)

    @staticmethod
    def _policy_issues(
        found: Sequence[p.Infra.AstGrepDiagnostic],
    ) -> Sequence[p.Infra.Issue]:
        """Report every native finding: ast-grep alone decides the match.

        Returns:
            One policy issue per native finding, one-based coordinates.

        """
        return [
            m.Infra.Issue(
                file=finding.file,
                line=finding.line + 1,
                column=finding.column + 1,
                code=finding.rule_id,
                message=finding.message,
                severity=finding.severity,
            )
            for finding in found
        ]


__all__: list[str] = ["FlextInfraGatesCodemod"]
