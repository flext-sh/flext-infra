"""Audit helpers for docs services."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import u
from flext_infra import c, m, t
from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns


class FlextInfraUtilitiesDocsAudit:
    """Reusable audit helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_is_external(target: str) -> bool:
        """Return whether a docs link target points outside the repository."""
        lower = u.norm_str(target, case="lower").lstrip("<")
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
        """Read one list of policy tokens from the minimal root docs config."""
        workspace_root = (
            scope.path if scope.name == c.Infra.ReportKeys.ROOT else scope.path.parent
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
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect broken internal link issues in one docs scope."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        for md_file in FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            content = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT, errors=c.Infra.IGNORE
            )
            in_fenced_code = False
            for number, line in enumerate(content.splitlines(), start=1):
                stripped = line.lstrip()
                if stripped.startswith("```"):
                    in_fenced_code = not in_fenced_code
                    continue
                if in_fenced_code:
                    continue
                clean_line = FlextInfraUtilitiesPatterns.INLINE_CODE_RE.sub("", line)
                for raw in FlextInfraUtilitiesPatterns.MARKDOWN_LINK_URL_RE.findall(
                    clean_line
                ):
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
    def docs_text_token_issues(
        scope: m.Infra.DocScope,
        *,
        tokens: Sequence[str],
        issue_type: str,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect simple token-presence issues from markdown files."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        if not tokens:
            return issues
        for md_file in FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            text = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT, errors=c.Infra.IGNORE
            )
            for token in tokens:
                if token in text:
                    issues.append(
                        m.Infra.AuditIssue(
                            file=rel,
                            issue_type=issue_type,
                            severity="medium",
                            message=f"contains `{token}`",
                        ),
                    )
        return issues

    @staticmethod
    def docs_scope_boundary_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect mentions of excluded non-FLEXT roots in root docs."""
        if scope.name != c.Infra.ReportKeys.ROOT:
            return []
        issues: MutableSequence[m.Infra.AuditIssue] = []
        excluded = sorted(FlextInfraUtilitiesDocsScope.excluded_roots(scope.path))
        for md_file in [
            scope.path / "README.md",
            *FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope),
        ]:
            if not md_file.exists():
                continue
            text = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT, errors=c.Infra.IGNORE
            )
            for token in excluded:
                if token in text:
                    issues.append(
                        m.Infra.AuditIssue(
                            file=md_file.relative_to(scope.path).as_posix(),
                            issue_type="scope_boundary",
                            severity="high",
                            message=f"root docs mention out-of-scope project `{token}`",
                        ),
                    )
        return issues

    @staticmethod
    def docs_generated_ownership_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect manual API pages that duplicate generated ownership."""
        issues: MutableSequence[m.Infra.AuditIssue] = []
        candidates: MutableSequence[Path] = [scope.path / "docs/api-reference.md"]
        for parent in (scope.path / "docs/api-reference", scope.path / "docs/api"):
            if parent.exists():
                candidates.extend(sorted(parent.rglob("*.md")))
        for path in candidates:
            if not path.exists():
                continue
            rel = path.relative_to(scope.path).as_posix()
            if path.is_relative_to(scope.path / c.Infra.Directories.DOCS) and (
                FlextInfraUtilitiesDocsScope.is_excluded_doc_path(
                    scope.path,
                    path.relative_to(scope.path / c.Infra.Directories.DOCS),
                )
            ):
                continue
            if rel == "docs/api-reference/README.md" or rel.startswith(
                "docs/api-reference/generated/"
            ):
                continue
            issues.append(
                m.Infra.AuditIssue(
                    file=rel,
                    issue_type="generated_ownership",
                    severity="medium",
                    message="manual API page duplicates generated API ownership",
                ),
            )
        return issues

    @staticmethod
    def docs_public_docstring_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Collect missing docstring issues for public exports and modules."""
        if scope.name == c.Infra.ReportKeys.ROOT or not scope.package_name:
            return []
        contract = FlextInfraUtilitiesDocsApi.public_contract(
            scope.path, scope.package_name
        )
        return FlextInfraUtilitiesDocsApi.docstring_issues(scope.path, contract)

    @staticmethod
    def docs_stale_symbol_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
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
        issues: MutableSequence[m.Infra.AuditIssue] = []
        if not tokens:
            return issues
        for md_file in FlextInfraUtilitiesDocs.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path / c.Infra.Directories.DOCS).as_posix()
            if rel in exempt_paths:
                continue
            text = md_file.read_text(
                encoding=c.Infra.Encoding.DEFAULT,
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
        issues: Sequence[m.Infra.AuditIssue],
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


__all__ = ["FlextInfraUtilitiesDocsAudit"]
