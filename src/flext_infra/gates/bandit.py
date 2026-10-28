"""FLEXT bandit quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, t, u
from flext_infra.gates import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraBanditGate(FlextInfraGate):
    """Bandit security quality gate."""

    gate_id: ClassVar[str] = c.Infra.SECURITY
    gate_name: ClassVar[str] = "Bandit"
    can_fix: ClassVar[bool] = False
    requires_python_targets: ClassVar[bool] = True
    check_module_command_prefix: ClassVar[Sequence[str]] = (c.Infra.BANDIT, "-r")
    check_module_command_suffix: ClassVar[Sequence[str]] = (
        "-f",
        c.Infra.OUTPUT_JSON,
        "--quiet",
        "--skip",
        "B101",
    )

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: t.DirectoryPath,
        ctx: p.Model,
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
        """Read Bandit's JSON report; every reported result blocks the gate.

        Returns:
            The run's verdict and its findings, parse error or failed exit.

        """
        del ctx
        if not result.stdout.strip():
            if u.Cli.process_succeeded(result.outcome):
                return False, (
                    self._parse_error_issue("bandit produced no JSON output"),
                )
            return self._finalize_parse_result(result, project_dir, (), c.Infra.BANDIT)
        validated = u.validate_value(
            m.Infra.BanditReport,
            result.stdout,
            from_json=True,
            strict=True,
        )
        if validated.failure:
            return False, (
                self._parse_error_issue(
                    "Bandit report does not match its required schema",
                ),
            )
        report = validated.value
        issues = (
            *(
                m.Infra.Issue(
                    file=PurePosixPath(finding.filename).as_posix(),
                    line=finding.line_number,
                    column=0,
                    code=finding.test_id,
                    message=finding.issue_text,
                    severity=c.Infra.GateSeverity.ERROR.value,
                )
                for finding in report.results
            ),
            *(
                m.Infra.Issue(
                    file=str(PurePosixPath(error.filename)),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message="Bandit could not audit this source file",
                    severity=c.Infra.GateSeverity.ERROR.value,
                )
                for error in report.errors
            ),
        )
        if report.errors:
            return False, issues
        return self._finalize_parse_result(
            result,
            project_dir,
            issues,
            c.Infra.BANDIT,
        )

    @staticmethod
    def _parse_error_issue(message: str) -> p.Infra.Issue:
        """Build the canonical Bandit output parse issue.

        Returns:
            A blocking structural diagnostic.

        """
        return m.Infra.Issue(
            file="<bandit-output>",
            line=0,
            column=0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=message,
            severity=c.Infra.GateSeverity.ERROR.value,
        )


__all__: list[str] = ["FlextInfraBanditGate"]
