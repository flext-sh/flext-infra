"""Internal helpers for the documentation auditor service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from pydantic import JsonValue, ValidationError

from flext_infra import c, m, t, u


def find_architecture_config(workspace_root: Path) -> Path | None:
    """Walk up from workspace_root looking for the architecture config."""
    for candidate in [workspace_root, *workspace_root.parents]:
        path = candidate / "docs/architecture/architecture_config.json"
        if path.exists():
            return path
    return None


def parse_audit_gate(
    audit_gate: Mapping[str, t.Infra.InfraValue],
) -> t.Infra.Pair[int | None, t.IntMapping]:
    """Extract default budget and per-scope budgets from an audit_gate mapping."""
    default_budget = audit_gate.get("max_issues_default")
    by_scope_raw_value = audit_gate.get("max_issues_by_scope")
    by_scope_raw: Mapping[str, t.Infra.InfraValue] = {}
    if u.is_mapping(by_scope_raw_value):
        try:
            by_scope_raw = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                by_scope_raw_value,
                strict=True,
            )
        except ValidationError:
            by_scope_raw = {}
    by_scope: t.MutableIntMapping = {}
    for name, value in by_scope_raw.items():
        if isinstance(value, (int, float)):
            by_scope[name] = int(value)
    resolved_default = (
        int(default_budget) if isinstance(default_budget, (int, float)) else None
    )
    return (resolved_default, by_scope)


def resolve_checks(check: str) -> set[str]:
    """Parse check string into a resolved set of check names."""
    checks = {part.strip() for part in check.split(",") if part.strip()}
    if not checks or "all" in checks:
        return {"links", "forbidden-terms"}
    return checks


def write_audit_reports(
    scope: m.Infra.DocScope,
    issues: Sequence[m.Infra.AuditIssue],
    checks: set[str],
    *,
    strict: bool,
    to_markdown_fn: Callable[
        [m.Infra.DocScope, Sequence[m.Infra.AuditIssue]], t.StrSequence
    ],
) -> None:
    """Persist JSON summary and markdown report to the scope report directory."""
    sorted_checks: list[JsonValue] = [str(ck) for ck in sorted(checks)]
    summary: dict[str, JsonValue] = {
        c.Infra.ReportKeys.SCOPE: scope.name,
        "issues": len(issues),
        c.Infra.Verbs.CHECKS: sorted_checks,
        c.Infra.Modes.STRICT: strict,
        "report_dir": scope.report_dir.as_posix(),
    }
    issues_payload: JsonValue = [
        {
            c.Infra.ReportKeys.FILE: issue.file,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            c.Infra.ReportKeys.MESSAGE: issue.message,
        }
        for issue in issues
    ]
    summary_payload: dict[str, JsonValue] = {
        c.Infra.ReportKeys.SUMMARY: summary,
        "issues": issues_payload,
    }
    _ = u.write_json(
        scope.report_dir / "audit-summary.json",
        summary_payload,
    )
    _ = u.write_markdown(
        scope.report_dir / "audit-report.md",
        to_markdown_fn(scope, issues),
    )


__all__ = [
    "find_architecture_config",
    "parse_audit_gate",
    "resolve_checks",
    "write_audit_reports",
]
