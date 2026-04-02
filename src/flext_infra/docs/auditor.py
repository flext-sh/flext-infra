"""Documentation auditor service.

Audits documentation for broken links and forbidden terms,
returning structured r reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import JsonValue, ValidationError

from flext_core import FlextLogger
from flext_infra import c, m, r, t, u

logger = FlextLogger.create_module_logger(__name__)

_NO_BUDGETS: t.Infra.Pair[int | None, t.IntMapping] = (None, {})


class FlextInfraDocAuditor:
    """Infrastructure service for documentation auditing.

    Scans markdown documentation for broken internal links and
    forbidden terms, returning structured r reports.
    """

    @staticmethod
    def is_external(target: str) -> bool:
        """Return True when target points outside the repository."""
        lower = u.norm_str(target, case="lower").lstrip("<")
        return lower.startswith(("http://", "https://", "mailto:", "tel:", "data:"))

    @staticmethod
    def load_audit_budgets(
        workspace_root: Path,
    ) -> t.Infra.Pair[int | None, t.IntMapping]:
        """Load audit issue budgets from architecture config."""
        config_path = _find_architecture_config(workspace_root)
        if config_path is None:
            return _NO_BUDGETS
        payload_result = u.Infra.read_json(config_path)
        if payload_result.is_failure:
            return _NO_BUDGETS
        docs_validation = u.Infra.as_toml_mapping(
            payload_result.value.get("docs_validation"),
        )
        if docs_validation is None:
            return _NO_BUDGETS
        audit_gate = u.Infra.as_toml_mapping(docs_validation.get("audit_gate"))
        if audit_gate is None:
            return _NO_BUDGETS
        return _parse_audit_gate(audit_gate)

    @staticmethod
    def normalize_link(target: str) -> str:
        """Strip fragment and query-string from a markdown link target."""
        value = target.strip()
        if value.startswith("<") and value.endswith(">"):
            value = value[1:-1].strip()
        return value.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]

    @staticmethod
    def should_skip_target(raw: str, target: str) -> bool:
        """Return whether link text should be ignored as a non-path target."""
        if target.startswith("http"):
            return False
        looks_like_prose = ".md" not in raw and "/" not in raw
        if not looks_like_prose:
            return False
        return "," in raw or " " in raw

    @staticmethod
    def to_markdown(
        scope: m.Infra.DocScope,
        issues: Sequence[m.Infra.AuditIssue],
    ) -> t.StrSequence:
        """Format audit issues as a markdown report."""
        return [
            "# Docs Audit Report",
            "",
            f"Scope: {scope.name}",
            f"Files scanned: {len(u.Infra.iter_markdown_files(scope.path))}",
            f"Issues: {len(issues)}",
            "",
            "| file | type | severity | message |",
            "|---|---|---|---|",
            *[
                f"| {issue.file} | {issue.issue_type} | {issue.severity} | {issue.message} |"
                for issue in issues
            ],
        ]

    def audit(
        self,
        workspace_root: Path,
        *,
        project: str | None = None,
        projects: str | None = None,
        output_dir: str = c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        params: m.Infra.AuditScopeParams | None = None,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation audit across project scopes."""
        resolved = params or m.Infra.AuditScopeParams()
        budgets = resolved.budgets or self.load_audit_budgets(workspace_root)
        scope_params = m.Infra.AuditScopeParams(
            check=resolved.check,
            strict=resolved.strict,
            budgets=budgets,
        )
        return u.Infra.run_scoped(
            workspace_root,
            project=project,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self.audit_scope(scope, params=scope_params),
        )

    def execute_command(self, params: m.Infra.DocsAuditInput) -> r[bool]:
        """CLI handler — accepts input model, delegates to audit."""
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        scope_params = m.Infra.AuditScopeParams(
            check="all" if params.check else "",
            strict=params.strict,
        )
        result = self.audit(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            params=scope_params,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "audit failed")
        failures = u.count(result.value, lambda report: not report.passed)
        if failures:
            return r[bool].fail(f"Audit found {failures} failure(s)")
        return r[bool].ok(True)

    def audit_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        params: m.Infra.AuditScopeParams | None = None,
    ) -> m.Infra.DocsPhaseReport:
        """Run configured audit checks on a single scope."""
        resolved = params or m.Infra.AuditScopeParams()
        checks = _resolve_checks(resolved.check)

        issues: MutableSequence[m.Infra.AuditIssue] = []
        if "links" in checks:
            issues.extend(self.broken_link_issues(scope))
        if "forbidden-terms" in checks:
            issues.extend(self.forbidden_term_issues(scope))

        _write_audit_reports(scope, issues, checks, strict=resolved.strict)

        budgets = resolved.budgets or _NO_BUDGETS
        if not resolved.strict:
            passed = True
        else:
            default_limit, by_scope = budgets
            max_issues = by_scope.get(scope.name, default_limit)
            limit = 0 if max_issues is None else max_issues
            passed = len(issues) <= limit

        status = c.Infra.Status.OK if passed else c.Infra.Status.FAIL
        reason = f"issues:{len(issues)}"
        logger.info(
            "docs_audit_scope_completed",
            project=scope.name,
            phase="audit",
            result=status,
            reason=reason,
        )
        return m.Infra.DocsPhaseReport(
            phase="audit",
            scope=scope.name,
            items=[
                m.Infra.DocsPhaseItemModel(
                    phase="audit",
                    file=issue.file,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    message=issue.message,
                )
                for issue in issues
            ],
            checks=sorted(checks),
            strict=resolved.strict,
            passed=passed,
            result=status,
            reason=reason,
            message=f"issues: {len(issues)}",
        )

    def _check_links_in_file(
        self,
        md_file: Path,
        rel: str,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Check a single markdown file for broken internal links."""
        content = md_file.read_text(
            encoding=c.Infra.Encoding.DEFAULT,
            errors=c.Infra.IGNORE,
        )
        issues: MutableSequence[m.Infra.AuditIssue] = []
        in_fenced_code = False
        for number, line in enumerate(content.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("```"):
                in_fenced_code = not in_fenced_code
                continue
            if in_fenced_code:
                continue
            clean_line = u.Infra.INLINE_CODE_RE.sub("", line)
            for raw in u.Infra.MARKDOWN_LINK_URL_RE.findall(clean_line):
                issue = self._check_single_link(md_file, rel, raw, number)
                if issue is not None:
                    issues.append(issue)
        return issues

    def _check_single_link(
        self,
        md_file: Path,
        rel: str,
        raw: str,
        line_number: int,
    ) -> m.Infra.AuditIssue | None:
        """Return an AuditIssue if a single link target is broken, else None."""
        target = self.normalize_link(raw)
        if not target or target.startswith("#") or self.is_external(target):
            return None
        if self.should_skip_target(raw, target):
            return None
        path = (md_file.parent / target).resolve()
        if path.exists():
            return None
        return m.Infra.AuditIssue(
            file=rel,
            issue_type="broken_link",
            severity="high",
            message=f"line {line_number}: target not found -> {raw}",
        )

    def broken_link_issues(
        self,
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect broken internal-link issues for markdown files in scope."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        for md_file in u.Infra.iter_markdown_files(scope.path):
            rel = md_file.relative_to(scope.path).as_posix()
            issues.extend(self._check_links_in_file(md_file, rel))
        return issues

    def forbidden_term_issues(
        self,
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect forbidden-term issues for markdown files in scope."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        terms: t.StrSequence = ()
        for md_file in u.Infra.iter_markdown_files(scope.path):
            rel = md_file.relative_to(scope.path).as_posix()
            rel_lower = rel.lower()
            if scope.name == c.Infra.ReportKeys.ROOT:
                if not rel_lower.startswith("docs/"):
                    continue
            elif not scope.name.startswith("flext-"):
                continue
            content = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT,
                errors=c.Infra.IGNORE,
            ).lower()
            issues.extend(
                m.Infra.AuditIssue(
                    file=rel,
                    issue_type="forbidden_term",
                    severity="medium",
                    message=f"contains forbidden term '{term}'",
                )
                for term in terms
                if term in content
            )
        return issues

    @staticmethod
    def main() -> int:
        """CLI entry point for the documentation auditor (legacy argparse)."""
        parser = u.Infra.create_parser(
            "flext-infra docs audit",
            "Audit documentation for issues",
            flags=u.Infra.SharedFlags(
                include_apply=True,
                include_project=True,
                include_check=True,
            ),
        )
        _ = parser.add_argument("--strict", action="store_true", help="Strict mode")
        _ = parser.add_argument(
            "--output-dir",
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        )
        args = parser.parse_args()
        cli = u.Infra.resolve(args)
        auditor = FlextInfraDocAuditor()
        scope_params = m.Infra.AuditScopeParams(
            check="all" if cli.check else "none",
            strict=bool(getattr(args, "strict", False)),
        )
        result = auditor.audit(
            workspace_root=cli.workspace,
            project=cli.project,
            projects=cli.projects,
            output_dir=args.output_dir,
            params=scope_params,
        )
        if result.is_failure:
            u.Infra.error(result.error or "audit failed")
            return 1
        failures = u.count(result.value, lambda report: not report.passed)
        return 1 if failures else 0


def _find_architecture_config(workspace_root: Path) -> Path | None:
    """Walk up from workspace_root looking for the architecture config."""
    for candidate in [workspace_root, *workspace_root.parents]:
        path = candidate / "docs/architecture/architecture_config.json"
        if path.exists():
            return path
    return None


def _parse_audit_gate(
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


def _resolve_checks(check: str) -> set[str]:
    """Parse check string into a resolved set of check names."""
    checks = {part.strip() for part in check.split(",") if part.strip()}
    if not checks or "all" in checks:
        return {"links", "forbidden-terms"}
    return checks


def _write_audit_reports(
    scope: m.Infra.DocScope,
    issues: Sequence[m.Infra.AuditIssue],
    checks: set[str],
    *,
    strict: bool,
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
    _ = u.Infra.write_json(
        scope.report_dir / "audit-summary.json",
        summary_payload,
    )
    _ = u.Infra.write_markdown(
        scope.report_dir / "audit-report.md",
        FlextInfraDocAuditor.to_markdown(scope, issues),
    )


main = FlextInfraDocAuditor.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraDocAuditor.main())
__all__ = ["FlextInfraDocAuditor", "main"]
