"""Detect silent failure sentinels via Rope-backed source scanning."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, override

from flext_infra import m, t, u


class FlextInfraSilentFailureDetector:
    """Detect branches that hide failures behind generic sentinel returns."""

    CONTEXTLIB_SUPPRESS: ClassVar[str] = "contextlib.suppress"

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Detect silent-failure findings in one Python file."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return []
        file_path = ctx.file_path
        source = resource.read()
        if not source.strip():
            return []
        display_path = file_path
        if ctx.project_root is not None:
            try:
                display_path = file_path.relative_to(ctx.project_root)
            except ValueError:
                display_path = file_path
        issues: list[m.Infra.Issue] = [
            m.Infra.Issue(
                file=str(display_path),
                line=line,
                column=column,
                code=code,
                message=message,
            )
            for line, column, code, message, _change in (
                u.Infra.collect_silent_failure_findings(source)
            )
        ]
        issues.extend(
            m.Infra.Issue(
                file=str(display_path),
                line=violation.line,
                column=1,
                code=violation.kind,
                message=violation.detail or f"{violation.kind}: silent failure pattern",
            )
            for violation in FlextInfraSilentFailureDetector._detect_ast_violations(
                file_path,
                ctx.rope_project,
                resource,
            )
        )
        return issues

    @classmethod
    def detect_violations(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.SilentFailureViolation]:
        """Return silent-failure violations with kind + fix_action for census."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return ()
        source = resource.read()
        if not source.strip():
            return ()
        rope_findings = u.Infra.collect_silent_failure_findings(source)
        ast_violations = cls._detect_ast_violations(
            ctx.file_path,
            ctx.rope_project,
            resource,
        )
        violations: list[m.Infra.SilentFailureViolation] = [
            m.Infra.SilentFailureViolation(
                file=str(ctx.file_path),
                line=line,
                kind=code,
                detail=message,
                fix_action="manual",
            )
            for line, _column, code, message, _change in rope_findings
        ]
        violations.extend(ast_violations)
        return tuple(violations)

    @classmethod
    def _detect_ast_violations(
        cls,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> list[m.Infra.SilentFailureViolation]:
        """Detect exception-silencing patterns via rope-backed AST."""
        try:
            pymodule = u.Infra.get_pymodule(rope_project, resource)
            tree = pymodule.get_ast()
        except Exception:
            return []
        if not isinstance(tree, ast.Module):
            return []
        visitor = _SilentFailureVisitor(file_path=file_path)
        visitor.visit(tree)
        return visitor.violations


class _SilentFailureVisitor(ast.NodeVisitor):
    """AST visitor collecting exception-silencing patterns."""

    def __init__(
        self,
        *,
        file_path: Path,
    ) -> None:
        self.file_path = file_path
        self.violations: list[m.Infra.SilentFailureViolation] = []
        self._import_aliases: dict[str, str] = {}

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name.split(".")[0]
            self._import_aliases[bound_name] = alias.name
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_name = node.module or ""
        for alias in node.names:
            bound_name = alias.asname or alias.name
            self._import_aliases[bound_name] = (
                f"{module_name}.{alias.name}" if module_name else alias.name
            )
        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        call_name = _resolve_call_name(node, self._import_aliases)
        if call_name == FlextInfraSilentFailureDetector.CONTEXTLIB_SUPPRESS:
            self._add_violation(
                line=node.lineno,
                kind="silent-failure-suppress",
                detail=(
                    "contextlib.suppress(...) silences exceptions without logging "
                    "or propagation"
                ),
            )
        self.generic_visit(node)

    @override
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if self._is_except_pass(node):
            self._add_violation(
                line=node.lineno,
                kind="silent-failure-except-pass",
                detail="except handler with empty pass swallows the exception",
            )
        elif self._is_broad_unhandled_except(node):
            self._add_violation(
                line=node.lineno,
                kind="silent-failure-broad-except",
                detail=(
                    "broad except catches Exception/BaseException without re-raise "
                    "or r[...].fail(...) propagation"
                ),
            )
        self.generic_visit(node)

    def _is_except_pass(self, node: ast.ExceptHandler) -> bool:
        """Return True when the handler body is only Pass (or docstring constants)."""
        return all(
            isinstance(stmt, ast.Pass)
            or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
            for stmt in node.body
        ) and any(isinstance(stmt, ast.Pass) for stmt in node.body)

    def _is_broad_unhandled_except(self, node: ast.ExceptHandler) -> bool:
        """Return True for broad Exception/BaseException handlers without raise/fail."""
        if node.type is None:
            return not self._body_has_raise_or_fail(node.body)
        type_name = _expression_name(node.type, self._import_aliases)
        if type_name not in {"Exception", "BaseException"}:
            return False
        return not self._body_has_raise_or_fail(node.body)

    @staticmethod
    def _body_has_raise_or_fail(body: list[ast.stmt]) -> bool:
        """Return True if any statement contains raise or any .fail(...) call."""
        for stmt in body:
            for child in ast.walk(stmt):
                if isinstance(child, ast.Raise):
                    return True
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "fail"
                ):
                    return True
        return False

    def _add_violation(
        self,
        *,
        line: int,
        kind: str,
        detail: str,
    ) -> None:
        self.violations.append(
            m.Infra.SilentFailureViolation(
                file=str(self.file_path),
                line=line,
                kind=kind,
                detail=detail,
                fix_action="manual",
            )
        )


def _resolve_call_name(
    node: ast.Call,
    import_aliases: Mapping[str, str],
) -> str:
    """Resolve a call expression to a dotted name using alias context."""
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        base = import_aliases.get(func.value.id, func.value.id)
        return f"{base}.{func.attr}"
    if isinstance(func, ast.Name):
        return import_aliases.get(func.id, func.id)
    return ""


def _expression_name(
    node: ast.expr | None,
    import_aliases: Mapping[str, str],
) -> str:
    """Resolve a bare expression to a dotted name."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return import_aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        base = import_aliases.get(node.value.id, node.value.id)
        return f"{base}.{node.attr}"
    return ""


__all__: list[str] = ["FlextInfraSilentFailureDetector"]
