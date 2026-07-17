"""Detect silent failure sentinels via Rope-backed AST scanning.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast

from flext_infra import c, m, p, t, u
from flext_infra._utilities.silent_failure_ast import collect_silent_failure_findings


class FlextInfraSilentFailureDetector:
    """Detect branches that hide failures behind generic sentinel returns."""

    @staticmethod
    def detect_file(ctx: p.Infra.DetectorContext) -> t.SequenceOf[p.Infra.Issue]:
        """Detect silent-failure findings in one Python file."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return []
        file_path = ctx.file_path
        source = resource.read()
        if not source.strip():
            return []
        display_path = file_path
        if ctx.project_root is not None and file_path.is_relative_to(ctx.project_root):
            display_path = file_path.relative_to(ctx.project_root)
        tree = _rope_module_ast(ctx.rope_project, resource)
        if tree is None:
            return []
        return tuple(
            m.Infra.Issue(
                file=str(display_path),
                line=finding.line,
                column=finding.column,
                code=finding.kind,
                message=finding.detail,
            )
            for finding in collect_silent_failure_findings(tree, source)
        )

    @classmethod
    def detect_violations(
        cls, ctx: p.Infra.DetectorContext
    ) -> t.SequenceOf[p.Infra.SilentFailureViolation]:
        """Return silent-failure violations with kind + fix_action for census."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return ()
        source = resource.read()
        if not source.strip():
            return ()
        tree = _rope_module_ast(ctx.rope_project, resource)
        if tree is None:
            return ()
        return tuple(
            m.Infra.SilentFailureViolation(
                file=str(ctx.file_path),
                line=finding.line,
                kind=finding.kind,
                detail=finding.detail,
                fix_action=finding.fix_action,
            )
            for finding in collect_silent_failure_findings(tree, source)
        )

    @classmethod
    def fixable_kinds(cls) -> frozenset[str]:
        """Kinds that ``rope_fix_silent_failure_sentinels`` can auto-correct."""
        return frozenset({"silent-failure-guard", "silent-failure-except"})


def _rope_module_ast(
    rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
) -> ast.Module | None:
    """Return the rope-backed module AST, or None on parse failure."""
    try:
        pymodule = u.Infra.get_pymodule(rope_project, resource)
        tree = pymodule.get_ast()
    except (*c.Infra.SYNTAX_ERRORS,):
        return None
    return tree if isinstance(tree, ast.Module) else None


__all__: list[str] = ["FlextInfraSilentFailureDetector"]
