"""Issue collection helpers for FlextInfraDocAuditor.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import p, t, u

if TYPE_CHECKING:
    from collections.abc import Callable


class FlextInfraDocAuditorChecksMixin:
    """Mixin for documentation audit issue checks."""

    @staticmethod
    def _policy_token_issues(
        scope: p.Infra.DocScope, *, policy_key: str, issue_type: str
    ) -> t.SequenceOf[p.Infra.AuditIssue]:
        """Return text-token issues for one scope using the named policy list."""
        issues: t.SequenceOf[p.Infra.AuditIssue] = u.Infra.docs_text_token_issues(
            scope,
            tokens=u.Infra.docs_policy_list(scope, section="audit", key=policy_key),
            issue_type=issue_type,
        )
        return issues

    @staticmethod
    def forbidden_term_issues(
        scope: p.Infra.DocScope,
    ) -> t.SequenceOf[p.Infra.AuditIssue]:
        """Return forbidden-term issues configured for one scope."""
        return FlextInfraDocAuditorChecksMixin._policy_token_issues(
            scope, policy_key="forbidden_terms", issue_type="forbidden_term"
        )

    @staticmethod
    def placeholder_issues(scope: p.Infra.DocScope) -> t.SequenceOf[p.Infra.AuditIssue]:
        """Return placeholder-text issues for one scope."""
        return FlextInfraDocAuditorChecksMixin._policy_token_issues(
            scope, policy_key="placeholder_terms", issue_type="placeholder"
        )

    def _collect_issues(
        self, scope: p.Infra.DocScope, checks: t.StrSequence
    ) -> t.SequenceOf[p.Infra.AuditIssue]:
        """Collect issues for the requested check set in canonical order."""
        handlers: tuple[
            tuple[str, Callable[[p.Infra.DocScope], t.SequenceOf[p.Infra.AuditIssue]]],
            ...,
        ] = (
            ("links", u.Infra.docs_broken_link_issues),
            ("forbidden-terms", self.forbidden_term_issues),
            ("placeholders", self.placeholder_issues),
            ("stale-symbols", u.Infra.docs_stale_symbol_issues),
            ("scope-boundary", u.Infra.docs_scope_boundary_issues),
            ("generated-ownership", u.Infra.docs_generated_ownership_issues),
            ("docstrings", u.Infra.docs_public_docstring_issues),
            ("python-codeblocks", u.Infra.docs_python_codeblock_issues),
        )
        return tuple(
            issue
            for check_name, handler in handlers
            if check_name in checks
            for issue in handler(scope)
        )


__all__: list[str] = ["FlextInfraDocAuditorChecksMixin"]
