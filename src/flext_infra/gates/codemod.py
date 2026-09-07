"""Codemod enforcement quality gate.

Runs ``ast-grep scan`` with the codemod rules discovered via
``importlib.resources`` cascade (ADR-014). Rules with ``severity: error``
block the build; violations are not warnings.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodemodGate(FlextInfraGate):
    """Enforce codemod rules as error gates across every project."""

    gate_id: ClassVar[str] = "codemod"
    gate_name: ClassVar[str] = "Codemod Enforcement"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["codemod"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run ast-grep scan with cascaded codemod rules."""
        started = time.monotonic()
        planned = u.Infra.codemod_rule_plan(project_dir)
        if planned.failure:
<<<<<<< HEAD
=======
            failure = planned.error
            if not failure:
                msg = "codemod rule planning failed without a diagnostic"
                raise RuntimeError(msg)
>>>>>>> origin/0.12.0-dev
            return self._build_check_gate_execution(
                project_dir,
                passed=False,
                issues=(
                    m.Infra.Issue(
                        file=c.Infra.PYPROJECT_FILENAME,
                        line=1,
                        column=0,
                        code=self.gate_id,
                        message=failure,
                        severity=str(c.Infra.GateSeverity.ERROR.value),
                    ),
                ),
                raw_output=failure,
                started=started,
            )

        issues: list[m.Infra.Issue] = []
        raw_outputs: list[str] = []
        for ruleset in planned.value.rulesets:
            scan = self._run(
<<<<<<< HEAD
                self._scan_command(ruleset, project_dir),
=======
                u.Infra.ast_grep_scan_command(
                    ruleset.config, rule_ids=ruleset.rule_ids, json_stream=True
                ),
>>>>>>> origin/0.12.0-dev
                project_dir,
                timeout=self._check_timeout(project_dir, ctx),
            )
            issues.extend(self._issues_from_scan(scan, ruleset.provider))
            raw_outputs.extend(
                output
                for output in (scan.stdout.strip(), scan.stderr.strip())
                if output
            )

        summary = (
            f"{len(planned.value.rules)} rules from "
            f"{len(planned.value.rulesets)} providers scanned, "
            f"{len(issues)} violations"
        )
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="\n".join((*raw_outputs, summary)),
            started=started,
        )

<<<<<<< HEAD
    @staticmethod
    def _scan_command(
        ruleset: m.Infra.CodemodRuleset, project_dir: Path
    ) -> t.StrSequence:
        """Canonical ast-grep invocation for one composed provider ruleset."""
        return (
            c.Infra.SG,
            c.Infra.SCAN,
            "--config",
            str(ruleset.config),
            "--filter",
            u.Infra.codemod_rule_filter(ruleset.rule_ids),
            str(project_dir),
        )

    @staticmethod
    def _rules(project_dir: Path) -> t.SequenceOf[Path]:
        """Resolve inherited rules through the public dependency utility."""
        return u.Infra.project_dependency_resource_files(
            project_dir,
            resource_parts=(c.Infra.CODEMOD_RESOURCE_DIRNAME, c.Cli.RULES_DIR_NAME),
            distribution_prefix=c.Infra.PKG_PREFIX_HYPHEN,
            suffix=c.Infra.CODEMOD_RULE_SUFFIX,
        )

=======
>>>>>>> origin/0.12.0-dev
    def _issues_from_scan(
        self, scan: p.Cli.CommandOutput, provider: str
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Turn one rule scan into issues; a scanner crash is never a silent pass."""
        if not scan.stdout.strip() and (
            not u.Cli.process_succeeded(scan.outcome) or scan.stderr.strip()
        ):
            failure = (
                "execution failed"
                if not u.Cli.process_succeeded(scan.outcome)
                else "emitted stderr"
            )
            detail = scan.stderr.strip()
            if not detail:
                detail = (
                    "ast-grep returned exit code "
                    f"{scan.outcome.raw_return_code} without diagnostics"
                )
            return (
                m.Infra.Issue(
                    file=c.Infra.PYPROJECT_FILENAME,
                    line=1,
                    column=0,
                    code=self.gate_id,
                    message=f"{provider}: ast-grep {failure} — {detail}",
                    severity=str(c.Infra.GateSeverity.ERROR.value),
                ),
            )
        return tuple(
            self._issue_from_finding(line, provider)
            for line in scan.stdout.splitlines()
            if line.strip()
        )

    def _issue_from_finding(self, line: str, provider: str) -> m.Infra.Issue:
        """Turn one ast-grep JSONL finding into an issue at its real location.

<<<<<<< HEAD
    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse a single ast-grep scan result into issues."""
        _ = ctx
        rules = self._rules(project_dir)
        rule_path = rules[0] if rules else project_dir
        issues = self._issues_from_scan(result, rule_path.name)
        return not issues, issues
=======
        The scan is requested as ``--json=stream`` rather than as ast-grep's
        human report because that report spends several lines on each
        violation -- the message, the file banner, the source excerpt and its
        carets. Reading it line by line counted every one of those lines as a
        separate violation, so thirteen real errors were reported as one
        hundred and nine, and each carried ``line=1`` against the provider name
        instead of the file and line a reader needs in order to open it.
        """
        parsed = u.Cli.json_parse(line)
        if parsed.failure:
            msg = f"{provider}: ast-grep emitted unparsable JSONL: {line}"
            raise RuntimeError(msg)
        finding = u.Cli.json_as_mapping(parsed.value)
        source_range = u.Cli.json_as_mapping(finding.get("range"))
        start = u.Cli.json_as_mapping(source_range.get("start"))
        file_path = finding.get("file")
        message = finding.get("message")
        rule_id = finding.get("ruleId")
        start_line = start.get("line")
        start_column = start.get("column")
        if (
            not isinstance(file_path, str)
            or not isinstance(message, str)
            or not isinstance(rule_id, str)
            or not isinstance(start_line, int)
            or not isinstance(start_column, int)
        ):
            msg = f"{provider}: ast-grep finding breaks its contract: {line}"
            raise TypeError(msg)
        return m.Infra.Issue(
            file=file_path,
            # ast-grep counts lines and columns from zero; every other gate in
            # this suite reports them the way an editor addresses them.
            line=start_line + 1,
            column=start_column + 1,
            code=rule_id,
            message=message,
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )
>>>>>>> origin/0.12.0-dev
