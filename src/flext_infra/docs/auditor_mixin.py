"""Auditor helper mixin for the documentation auditor service.

Provides static helper methods used by the documentation auditor service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from flext_infra import c, p, t, u

if TYPE_CHECKING:
    pass


class FlextInfraDocAuditorMixin:
    """Mixin providing helper methods for the documentation auditor."""

    @staticmethod
    def write_audit_reports(
        scope: p.Infra.DocScope,
        issues: Sequence[p.Infra.AuditIssue],
        checks: t.Infra.StrSet,
        *,
        docstring_coverage: p.Infra.DocstringCoverage | None = None,
        to_markdown_fn: Callable[
            [
                p.Infra.DocScope,
                Sequence[p.Infra.AuditIssue],
                p.Infra.DocstringCoverage | None,
            ],
            Sequence[str],
        ],
    ) -> None:
        """Persist JSON summary and markdown report to the scope report directory."""
        validated_checks = u.json_list_adapter().validate_python(sorted(checks))
        sorted_checks: list[t.JsonValue] = list(validated_checks)
        summary: t.JsonDict = {
            c.Infra.RK_SCOPE: scope.name,
            "issues": len(issues),
            c.Infra.VERB_CHECKS: sorted_checks,
            "report_dir": scope.report_dir.as_posix(),
        }
        if docstring_coverage is not None:
            summary["docstring_coverage"] = docstring_coverage.model_dump()
        issues_payload: t.JsonValue = [
            {
                c.Infra.RK_FILE: issue.file,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                c.Infra.RK_MESSAGE: issue.message,
            }
            for issue in issues
        ]
        summary_payload: t.JsonDict = {
            c.Infra.RK_SUMMARY: summary,
            "issues": issues_payload,
        }
        u.Cli.json_write(
            scope.report_dir / c.Infra.DOCS_AUDIT_SUMMARY_FILENAME,
            summary_payload,
        ).unwrap()
        u.Infra.write_markdown(
            scope.report_dir / c.Infra.DOCS_AUDIT_REPORT_FILENAME,
            to_markdown_fn(scope, issues, docstring_coverage),
        ).unwrap()
