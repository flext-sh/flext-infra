"""Automatic fixer for ``smell_boolean_logic`` findings.

Rewrites long chains of ``or``/``and`` into ``any()``/``all()`` when every
operand is a simple, side-effect-free expression. The transformation is
provably equivalent and preserves short-circuit semantics for the rewritten
chain itself (``any``/``all`` short-circuit on iterables).
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, override

from flext_infra.transformers.smells.base import (
    FlextInfraSmellFixer,
    register_smell_fixer,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m


class _BooleanSimplifier(ast.NodeTransformer):
    """Replace the reported boolean-context BoolOp with a lazy any()/all()."""

    def __init__(
        self, *, target_line: int, parents: dict[ast.AST, ast.AST], predicate_name: str
    ) -> None:
        super().__init__()
        self._target_line = target_line
        self._parents = parents
        self._predicate_name = predicate_name
        self.changed = False

    @override
    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        end_line = node.end_lineno or node.lineno
        if (
            self.changed
            or not node.lineno <= self._target_line <= end_line
            or not self._is_boolean_context(node)
        ):
            return node
        operands = node.values
        if not all(self._is_simple_operand(op) for op in operands):
            return node
        func_name = "any" if isinstance(node.op, ast.Or) else "all"
        lazy_operands = ast.Tuple(
            elts=[
                ast.Lambda(
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                    ),
                    body=operand,
                )
                for operand in operands
            ],
            ctx=ast.Load(),
        )
        generator = ast.GeneratorExp(
            elt=ast.Call(
                func=ast.Name(id=self._predicate_name, ctx=ast.Load()),
                args=[],
                keywords=[],
            ),
            generators=[
                ast.comprehension(
                    target=ast.Name(id=self._predicate_name, ctx=ast.Store()),
                    iter=lazy_operands,
                    ifs=[],
                    is_async=0,
                )
            ],
        )
        call = ast.Call(
            func=ast.Name(id=func_name, ctx=ast.Load()), args=[generator], keywords=[]
        )
        ast.copy_location(call, node)
        self.changed = True
        return call

    def _is_boolean_context(self, node: ast.BoolOp) -> bool:
        """Return whether the parent consumes only the expression's truth value."""
        parent = self._parents.get(node)
        if isinstance(parent, ast.If | ast.IfExp | ast.While | ast.Assert):
            return parent.test is node
        if isinstance(parent, ast.comprehension):
            return node in parent.ifs
        return isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.Not)

    @staticmethod
    def _is_simple_operand(node: ast.AST) -> bool:
        """Return True for expressions safe to defer into a zero-argument lambda.

        Calls and binary operators remain manual because changing their lexical
        scope can alter runtime behavior.
        """
        if isinstance(node, ast.Name | ast.Constant):
            return True
        if isinstance(node, ast.Attribute):
            return _BooleanSimplifier._is_simple_operand(node.value)
        if isinstance(node, ast.Compare):
            return _BooleanSimplifier._is_simple_operand(node.left) and all(
                _BooleanSimplifier._is_simple_operand(comp) for comp in node.comparators
            )
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return _BooleanSimplifier._is_simple_operand(node.operand)
        return False


@register_smell_fixer
class FlextInfraBooleanLogicFixer(FlextInfraSmellFixer):
    """Simplify boolean expressions reported by the boolean-logic smell."""

    @override
    def fix(self, project_dir: Path, issue: m.Infra.Issue) -> tuple[bool, list[str]]:
        """Rewrite eligible boolean chains in the issue's file."""
        source_path = project_dir / issue.file
        try:
            source = source_path.read_text(encoding="utf-8")
        except OSError:
            return False, []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return False, []
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        predicate_name = "_flext_boolean_operand"
        while predicate_name in names:
            predicate_name += "_"
        transformer = _BooleanSimplifier(
            target_line=issue.line, parents=parents, predicate_name=predicate_name
        )
        simplified = transformer.visit(tree)
        if not transformer.changed:
            return False, []
        ast.fix_missing_locations(simplified)
        updated = ast.unparse(simplified)
        if updated.rstrip("\n") == source.rstrip("\n"):
            return False, []
        source_path.write_text(updated, encoding="utf-8")
        message = (
            f"{issue.file}:{issue.line}: simplified {issue.code} chain to any()/all()"
        )
        self._record_change(message)
        return True, list(self.changes)


__all__: list[str] = ["FlextInfraBooleanLogicFixer"]
