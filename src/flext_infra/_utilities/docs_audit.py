"""Audit helpers for docs services."""

from __future__ import annotations

from flext_cli import u
from flext_infra import c, m, t
from flext_infra._utilities._docs_audit_detectors import (
    FlextInfraUtilitiesDocsAuditDetectorsMixin,
)
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsAudit(FlextInfraUtilitiesDocsAuditDetectorsMixin):
    """Reusable audit helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_is_external(target: str) -> bool:
        """Return whether a docs link target points outside the repository."""
        lower: str = u.norm_str(target, case="lower").lstrip("<")
        return lower.startswith(("http://", "https://", "mailto:", "tel:", "data:"))

    @staticmethod
    def docs_normalize_link(target: str) -> str:
        """Strip fragments and query strings from a markdown link target."""
        value = target.strip()
        if value.startswith("<") and value.endswith(">"):
            value = value[1:-1].strip()
        return value.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]

    @staticmethod
    def docs_should_skip_target(raw: str, target: str) -> bool:
        """Return whether the target should be ignored as prose, not a path."""
        if target.startswith("http"):
            return False
        looks_like_prose = ".md" not in raw and "/" not in raw
        return looks_like_prose and ("," in raw or " " in raw)

    @staticmethod
    def docs_policy_list(
        scope: m.Infra.DocScope,
        section: str,
        key: str,
    ) -> t.StrSequence:
        """Read one list of policy tokens from the minimal root docs settings."""
        workspace_root = (
            scope.path if scope.name == c.Infra.RK_ROOT else scope.path.parent
        )
        payload = FlextInfraUtilitiesDocsScope.load_config(workspace_root)
        container = payload.get(section)
        if not isinstance(container, dict):
            return []
        values = container.get(key)
        return (
            [str(item).strip() for item in values] if isinstance(values, list) else []
        )

    @staticmethod
    def docs_broken_link_issues(
        scope: m.Infra.DocScope,
    ) -> t.SequenceOf[m.Infra.AuditIssue]:
        """Collect broken internal link issues in one docs scope."""
        issues: t.MutableSequenceOf[m.Infra.AuditIssue] = []
        for md_file in FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            content = md_file.read_text(
                encoding=c.Cli.ENCODING_DEFAULT, errors=c.Infra.IGNORE
            )
            in_fenced_code = False
            for number, line in enumerate(content.splitlines(), start=1):
                stripped = line.lstrip()
                if stripped.startswith("```"):
                    in_fenced_code = not in_fenced_code
                    continue
                if in_fenced_code:
                    continue
                clean_line = c.Infra.INLINE_CODE_RE.sub("", line)
                for raw in c.Infra.MARKDOWN_LINK_URL_RE.findall(clean_line):
                    target = FlextInfraUtilitiesDocsAudit.docs_normalize_link(raw)
                    if (
                        not target
                        or target.startswith("#")
                        or FlextInfraUtilitiesDocsAudit.docs_is_external(target)
                        or FlextInfraUtilitiesDocsAudit.docs_should_skip_target(
                            raw, target
                        )
                    ):
                        continue
                    if not (md_file.parent / target).resolve().exists():
                        issues.append(
                            m.Infra.AuditIssue(
                                file=rel,
                                issue_type="broken_link",
                                severity="high",
                                message=f"line {number}: target not found -> {raw}",
                            ),
                        )
        return issues

    @staticmethod
    def docs_stale_symbol_issues(
        scope: m.Infra.DocScope,
    ) -> t.SequenceOf[m.Infra.AuditIssue]:
        """Collect stale-symbol issues outside the explicit migration docs."""
        tokens = FlextInfraUtilitiesDocsAudit.docs_policy_list(
            scope,
            section="audit",
            key="stale_symbols",
        )
        exempt_paths = set(
            FlextInfraUtilitiesDocsAudit.docs_policy_list(
                scope,
                section="audit",
                key="stale_symbol_exempt_paths",
            ),
        )
        issues: t.MutableSequenceOf[m.Infra.AuditIssue] = []
        if not tokens:
            return issues
        for md_file in FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path / c.Infra.DIR_DOCS).as_posix()
            if rel in exempt_paths:
                continue
            text = md_file.read_text(
                encoding=c.Cli.ENCODING_DEFAULT,
                errors=c.Infra.IGNORE,
            )
            for token in tokens:
                if token not in text:
                    continue
                issues.append(
                    m.Infra.AuditIssue(
                        file=md_file.relative_to(scope.path).as_posix(),
                        issue_type="stale_symbol",
                        severity="medium",
                        message=f"contains `{token}`",
                    ),
                )
        return issues

    @staticmethod
    def docs_audit_markdown(
        scope: m.Infra.DocScope,
        issues: t.SequenceOf[m.Infra.AuditIssue],
    ) -> t.StrSequence:
        """Render the standard markdown audit report."""
        return [
            "# Docs Audit Report",
            "",
            f"Scope: {scope.name}",
            f"Files scanned: {len(FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope))}",
            f"Issues: {len(issues)}",
            "",
            "| file | type | severity | message |",
            "|---|---|---|---|",
            *[
                f"| {issue.file} | {issue.issue_type} | {issue.severity} | {issue.message} |"
                for issue in issues
            ],
        ]


__all__: list[str] = ["FlextInfraUtilitiesDocsAudit"]
