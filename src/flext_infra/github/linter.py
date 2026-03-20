"""Workflow linter service for GitHub Actions validation.

Wraps actionlint execution with r error handling,
replacing scripts/github/lint_workflows.py with a service class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra import m, r, s, u


class FlextInfraWorkflowLinter(s[bool]):
    """Infrastructure service for GitHub Actions workflow linting.

    Delegates to ``actionlint`` for validation and persists JSON reports.
    """

    def lint(
        self,
        root: Path,
        *,
        report_path: Path | None = None,
        strict: bool = False,
    ) -> r[m.Infra.WorkflowLintResult]:
        """Run actionlint on the repository and return results."""
        actionlint = shutil.which("actionlint")
        if actionlint is None:
            payload_skipped = m.Infra.WorkflowLintResult(
                status="skipped",
                reason="actionlint not installed",
            )
            if report_path is not None:
                u.Infra.write_json(report_path, payload_skipped, sort_keys=True)
            return r[m.Infra.WorkflowLintResult].ok(payload_skipped)

        result = u.Infra.run([actionlint], cwd=root)
        if result.is_success:
            output = result.value
            payload = m.Infra.WorkflowLintResult(
                status="ok",
                exit_code=output.exit_code,
                stdout=output.stdout,
                stderr=output.stderr,
            )
        else:
            payload = m.Infra.WorkflowLintResult(
                status="fail",
                exit_code=1,
                detail=result.error or "",
            )

        if report_path is not None:
            u.Infra.write_json(report_path, payload, sort_keys=True)

        if payload.status == "fail" and strict:
            return r[m.Infra.WorkflowLintResult].fail(
                result.error or "actionlint found issues",
            )
        return r[m.Infra.WorkflowLintResult].ok(payload)


__all__ = ["FlextInfraWorkflowLinter"]
