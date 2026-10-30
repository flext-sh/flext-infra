"""Issue collection helpers for FlextInfraDocAuditor.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import u

if TYPE_CHECKING:
    from collections.abc import Callable

    from flext_infra import m


class FlextInfraDocsAuditorChecks:
    """Mixin for documentation audit issue checks."""

    @staticmethod
    def forbidden_term_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return forbidden-term issues configured for one scope.

        Returns:
            Forbidden-term issues configured for one scope.

        """
        return u.Infra.docs_text_token_issues(
            scope,
            tokens=u.Infra.audit_policy(scope).forbidden_terms,
            issue_type="forbidden_term",
        )

    @staticmethod
    def placeholder_issues(scope: m.Infra.DocScope) -> Sequence[m.Infra.AuditIssue]:
        """Return placeholder-text issues for one scope.

        Returns:
            Placeholder-text issues for one scope.

        """
        return u.Infra.docs_placeholder_issues(
            scope,
            patterns=u.Infra.audit_policy(scope).placeholder_patterns,
        )

    @staticmethod
    def machine_path_issues(
        scope: m.Infra.DocScope,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return machine-local paths outside exact historical evidence files.

        Returns:
            Machine-local paths outside exact historical evidence files.

        """
        policy = u.Infra.audit_policy(scope)
        return u.Infra.docs_machine_path_issues(
            scope,
            historical_evidence_files=policy.historical_evidence_files,
            container_home_identities=policy.container_home_identities,
        )

    def _collect_issues(
        self,
        scope: m.Infra.DocScope,
        check: str,
    ) -> tuple[Sequence[str], Sequence[m.Infra.AuditIssue]]:
        """Resolve selection from the handlers and collect issues in canonical order.

        Returns:
            Sorted selected checks and their issues in handler execution order.

        """
        handlers: tuple[
            tuple[str, Callable[[m.Infra.DocScope], Sequence[m.Infra.AuditIssue]]],
            ...,
        ] = (
            ("links", u.Infra.docs_broken_link_issues),
            ("forbidden-terms", self.forbidden_term_issues),
            ("placeholders", self.placeholder_issues),
            ("machine-paths", self.machine_path_issues),
            ("stale-symbols", u.Infra.docs_stale_symbol_issues),
            ("scope-boundary", u.Infra.scope_boundary_issues),
            ("generated-ownership", u.Infra.generated_ownership_issues),
            ("command-contract", u.Infra.docs_command_contract_issues),
            ("docstrings", u.Infra.docs_public_docstring_issues),
            ("python-codeblocks", u.Infra.docs_python_codeblock_issues),
        )
        checks = {part.strip() for part in check.split(",") if part.strip()}
        if not checks or "all" in checks:
            checks = {check_name for check_name, _ in handlers}
        return sorted(checks), tuple(
            issue
            for check_name, handler in handlers
            if check_name in checks
            for issue in handler(scope)
        )


__all__: list[str] = ["FlextInfraDocsAuditorChecks"]
