"""Documentation auditor service.

Audits documentation for broken links and forbidden terms,
returning structured r reports.

Usage:
    python -m flext_infra docs audit --workspace flext-core

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import FlextLogger
from pydantic import JsonValue, TypeAdapter, ValidationError

from flext_infra import c, m, output, r, t, u

logger = FlextLogger.create_module_logger(__name__)

_INFRA_MAPPING_ADAPTER: TypeAdapter[Mapping[str, t.Infra.InfraValue]] = TypeAdapter(
    Mapping[str, t.Infra.InfraValue],
)


class FlextInfraDocAuditor:
    """Infrastructure service for documentation auditing.

    Scans markdown documentation for broken internal links and
    forbidden terms, returning structured r reports.
    """

    @staticmethod
    def is_external(target: str) -> bool:
        """Return True when target points outside the repository."""
        lower = target.strip().lower().lstrip("<")
        return lower.startswith(("http://", "https://", "mailto:", "tel:", "data:"))

    @staticmethod
    def load_audit_budgets(
        workspace_root: Path,
    ) -> t.Infra.Pair[int | None, Mapping[str, int]]:
        """Load audit issue budgets from architecture config."""
        config_path: Path | None = None
        for candidate in [workspace_root, *workspace_root.parents]:
            path = candidate / "docs/architecture/architecture_config.json"
            if path.exists():
                config_path = path
                break
        if config_path is None:
            return (None, {})
        payload_result = u.Infra.read_json(config_path)
        if payload_result.is_failure:
            return (None, {})
        payload = payload_result.value
        docs_validation_value = payload.get("docs_validation")
        if not isinstance(docs_validation_value, Mapping):
            return (None, {})
        audit_gate_value = docs_validation_value.get("audit_gate")
        if not isinstance(audit_gate_value, Mapping):
            return (None, {})
        default_budget = audit_gate_value.get("max_issues_default")
        by_scope_raw_value = audit_gate_value.get("max_issues_by_scope")
        by_scope_raw: Mapping[str, t.Infra.InfraValue] = {}
        if isinstance(by_scope_raw_value, Mapping):
            try:
                by_scope_raw = _INFRA_MAPPING_ADAPTER.validate_python(
                    by_scope_raw_value,
                    strict=True,
                )
            except ValidationError:
                by_scope_raw = {}
        by_scope: MutableMapping[str, int] = {}
        for name, value in by_scope_raw.items():
            if isinstance(value, (int, float)):
                by_scope[name] = int(value)
        if isinstance(default_budget, (int, float)):
            return (int(default_budget), by_scope)
        return (None, by_scope)

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
        if "," in raw and ".md" not in raw and ("/" not in raw):
            return True
        return bool(" " in raw and ".md" not in raw and ("/" not in raw))

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
        check: str = "all",
        strict: bool = True,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation audit across project scopes.

        Args:
            workspace_root: Workspace root directory.
            project: Single project name filter.
            projects: Comma-separated project names.
            output_dir: Report output directory.
            check: Comma-separated checks (links, forbidden-terms, all).
            strict: Fail on any issues found.

        Returns:
            r with list of AuditReport objects.

        """
        default_budget, by_scope_budget = self.load_audit_budgets(workspace_root)
        return u.Infra.run_scoped(
            workspace_root,
            project=project,
            projects=projects,
            output_dir=output_dir,
            handler=lambda scope: self.audit_scope(
                scope,
                check=check,
                strict=strict,
                max_issues_default=default_budget,
                max_issues_by_scope=by_scope_budget,
            ),
        )

    def execute_command(self, params: m.Infra.DocsAuditInput) -> r[bool]:
        """CLI handler — accepts input model, delegates to audit."""
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        result = self.audit(
            workspace_root=resolved_workspace,
            project=params.project,
            projects=params.projects,
            output_dir=params.output_dir,
            check="all" if params.check else "",
            strict=params.strict,
        )
        if result.is_failure:
            return r[bool].fail(result.error or "audit failed")
        failures = sum(1 for report in result.value if not report.passed)
        if failures:
            return r[bool].fail(f"Audit found {failures} failure(s)")
        return r[bool].ok(True)

    def audit_scope(
        self,
        scope: m.Infra.DocScope,
        *,
        check: str,
        strict: bool,
        max_issues_default: int | None,
        max_issues_by_scope: Mapping[str, int],
    ) -> m.Infra.DocsPhaseReport:
        """Run configured audit checks on a single scope."""
        checks = {part.strip() for part in check.split(",") if part.strip()}
        if not checks or "all" in checks:
            checks = {"links", "forbidden-terms"}
        issues: MutableSequence[m.Infra.AuditIssue] = []
        if "links" in checks:
            issues.extend(self.broken_link_issues(scope))
        if "forbidden-terms" in checks:
            issues.extend(self.forbidden_term_issues(scope))
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
            self.to_markdown(scope, issues),
        )
        max_issues = max_issues_by_scope.get(scope.name, max_issues_default)
        if strict:
            limit = 0 if max_issues is None else max_issues
            passed = len(issues) <= limit
        else:
            passed = True
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
            strict=strict,
            passed=passed,
            result=status,
            reason=reason,
            message=f"issues: {len(issues)}",
        )

    def broken_link_issues(
        self,
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect broken internal-link issues for markdown files in scope."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        for md_file in u.Infra.iter_markdown_files(scope.path):
            content = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT,
                errors=c.Infra.IGNORE,
            )
            rel = md_file.relative_to(scope.path).as_posix()
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
                    target = self.normalize_link(raw)
                    if not target or target.startswith("#") or self.is_external(target):
                        continue
                    if self.should_skip_target(raw, target):
                        continue
                    path = (md_file.parent / target).resolve()
                    if not path.exists():
                        issues.append(
                            m.Infra.AuditIssue(
                                file=rel,
                                issue_type="broken_link",
                                severity="high",
                                message=f"line {number}: target not found -> {raw}",
                            ),
                        )
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
        """CLI entry point for the documentation auditor."""
        parser = u.Infra.create_parser(
            "flext-infra docs audit",
            "Audit documentation for issues",
            include_apply=True,
            include_project=True,
            include_check=True,
        )
        _ = parser.add_argument("--strict", action="store_true", help="Strict mode")
        _ = parser.add_argument(
            "--output-dir",
            default=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        )
        args = parser.parse_args()
        cli = u.Infra.resolve(args)
        auditor = FlextInfraDocAuditor()
        result = auditor.audit(
            workspace_root=cli.workspace,
            project=cli.project,
            projects=cli.projects,
            output_dir=args.output_dir,
            check="all" if cli.check else "none",
            strict=bool(getattr(args, "strict", False)),
        )
        if result.is_failure:
            output.error(result.error or "audit failed")
            return 1
        failures = sum(1 for report in result.value if not report.passed)
        return 1 if failures else 0


main = FlextInfraDocAuditor.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraDocAuditor.main())
__all__ = ["FlextInfraDocAuditor", "main"]
