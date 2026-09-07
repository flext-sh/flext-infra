"""Public utility facet for silent-failure AST enforcement."""

from __future__ import annotations

import ast

from flext_infra import t

from .._utilities.silent_failure_ast_rules import (
    FlextInfraUtilitiesSilentFailureAstRules,
)


class FlextInfraUtilitiesSilentFailureAst:
    """Expose detection and structural fixes through ``u.Infra``."""

    @classmethod
    def collect_silent_failure_findings(
        cls, tree: ast.Module, source: str
    ) -> t.VariadicTuple[FlextInfraUtilitiesSilentFailureAstRules.Finding]:
        """Collect all silent-failure findings in one module."""
        return FlextInfraUtilitiesSilentFailureAstRules(source).analyze(tree)

    @classmethod
    def collect_silent_failure_fixes(
        cls,
        tree: ast.Module,
        source: str,
        *,
        kinds: set[str] | frozenset[str] | None = None,
    ) -> t.VariadicTuple[t.Triple[int, int, str]]:
        """Return deterministic fixes for the selected finding kinds."""
        allowed = kinds or frozenset()
        return tuple(
            finding.replacement
            for finding in FlextInfraUtilitiesSilentFailureAstRules(source).analyze(
                tree
            )
            if finding.replacement is not None
            and (not allowed or finding.kind in allowed)
        )


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesSilentFailureAst",)
