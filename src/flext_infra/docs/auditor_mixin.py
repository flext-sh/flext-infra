"""Auditor helper mixin for the documentation auditor service.

Provides static helper methods used by the documentation auditor service.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_infra import c, m, t, u


class FlextInfraDocAuditorMixin:
    """Mixin providing helper methods for the documentation auditor."""

    @staticmethod
    def find_architecture_config(workspace_root: Path) -> Path | None:
        """Walk up from workspace_root looking for the architecture config."""
        for candidate in [workspace_root, *workspace_root.parents]:
            path = candidate / "docs/architecture/architecture_config.json"
            if path.exists():
                return path
        return None

    @staticmethod
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

    @classmethod
    def load_audit_budgets(
        cls,
        workspace_root: Path,
    ) -> t.Infra.Pair[int | None, t.IntMapping]:
        """Load audit budgets from the nearest architecture config."""
        config = cls.find_architecture_config(workspace_root)
        if config is None:
            return (None, {})
        payload_result = u.Cli.json_read(config)
        if payload_result.failure or not u.is_mapping(payload_result.value):
            return (None, {})
        docs_validation = payload_result.value.get("docs_validation")
        if not isinstance(docs_validation, Mapping):
            return (None, {})
        audit_gate = docs_validation.get("audit_gate")
        if not isinstance(audit_gate, Mapping):
            return (None, {})
        try:
            validated_gate = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                audit_gate,
                strict=False,
            )
        except ValidationError:
            return (None, {})
        return cls.parse_audit_gate(validated_gate)

    @staticmethod
    def resolve_checks(check: str) -> t.Infra.StrSet:
        """Parse check string into a resolved set of check names."""
        checks = {part.strip() for part in check.split(",") if part.strip()}
        if not checks or "all" in checks:
            return {
                "links",
                "forbidden-terms",
                "placeholders",
                "stale-symbols",
                "scope-boundary",
                "generated-ownership",
                "docstrings",
            }
        return checks

    @staticmethod
    def write_audit_reports(
        scope: m.Infra.DocScope,
        issues: Sequence[m.Infra.AuditIssue],
        checks: t.Infra.StrSet,
        *,
        strict: bool,
        to_markdown_fn: Callable[
            [m.Infra.DocScope, Sequence[m.Infra.AuditIssue]], t.StrSequence
        ],
    ) -> None:
        """Persist JSON summary and markdown report to the scope report directory."""
        sorted_checks: list[t.Cli.JsonValue] = [str(ck) for ck in sorted(checks)]
        summary: dict[str, t.Cli.JsonValue] = {
            c.Infra.RK_SCOPE: scope.name,
            "issues": len(issues),
            c.Infra.VERB_CHECKS: sorted_checks,
            c.Infra.MODE_STRICT: strict,
            "report_dir": scope.report_dir.as_posix(),
        }
        issues_payload: t.Cli.JsonValue = [
            {
                c.Infra.RK_FILE: issue.file,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                c.Infra.RK_MESSAGE: issue.message,
            }
            for issue in issues
        ]
        summary_payload: dict[str, t.Cli.JsonValue] = {
            c.Infra.RK_SUMMARY: summary,
            "issues": issues_payload,
        }
        _ = u.Cli.json_write(
            scope.report_dir / "audit-summary.json",
            summary_payload,
        )
        _ = u.Infra.write_markdown(
            scope.report_dir / "audit-report.md",
            to_markdown_fn(scope, issues),
        )


__all__ = ["FlextInfraDocAuditorMixin"]
