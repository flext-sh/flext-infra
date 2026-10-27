"""Shared AST, scope and line-edit helpers of import normalization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator

from flext_infra import c, m, t
from flext_infra._utilities._import_law import FlextInfraUtilitiesImportLawPolicy


class FlextInfraUtilitiesImportLawAst(FlextInfraUtilitiesImportLawPolicy):
    """Parse, scope and edit module sources for import rewrites."""

    @staticmethod
    def _import_law_iter_imports(
        tree: ast.Module,
    ) -> t.SequenceOf[ast.Import | ast.ImportFrom]:
        """Return every import statement anywhere in the module, in order.

        Returns:
            The resulting ``t.SequenceOf[ast.Import | ast.ImportFrom]``.

        """
        return sorted(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, c.Infra.AST_IMPORT_TYPES)
            ),
            key=operator.attrgetter("lineno"),
        )

    @classmethod
    def _import_law_enclosing_scope(
        cls,
        node: ast.AST,
        parents: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> t.Infra.RopeAstNode | None:
        """Return the lexical scope that evaluates one node.

        Definition headers and a comprehension's first iterable run in the
        enclosing scope. Arguments bind in their function; comprehensions
        bind targets in their own scope.

        Returns:
            The innermost enclosing scope, or ``None`` at module level.

        """
        child = node
        current = parents.get(id(child))
        while current is not None:
            if cls._import_law_scope_evaluates(node, child, current, parents):
                return current
            child = current
            current = parents.get(id(current))
        return None

    @classmethod
    def _import_law_scope_evaluates(
        cls,
        node: ast.AST,
        child: ast.AST,
        scope: ast.AST,
        parents: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> bool:
        """Return whether ``scope`` evaluates ``node`` reached through ``child``.

        Returns:
            True when ``scope`` is the lexical scope of the node.

        """
        match scope:
            case ast.FunctionDef() | ast.AsyncFunctionDef():
                return isinstance(node, ast.arg) or child in scope.body
            case ast.Lambda():
                return isinstance(node, ast.arg) or child is scope.body
            case ast.ClassDef():
                return child in scope.body
            case ast.ListComp() | ast.SetComp() | ast.DictComp() | ast.GeneratorExp():
                return cls._import_law_comprehension_owns_node(node, scope, parents)
            case _:
                return False

    @staticmethod
    def _import_law_comprehension_owns_node(
        node: ast.AST,
        scope: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
        parents: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> bool:
        """Keep the first iterable outside its comprehension's lexical bindings.

        Returns:
            Whether the original node reaches this scope without its first iterable.

        """
        first = scope.generators[0].iter
        ancestor = node
        while ancestor is not scope:
            if ancestor is first:
                return False
            parent = parents.get(id(ancestor))
            if parent is None:
                return False
            ancestor = parent
        return True

    @staticmethod
    def _import_law_is_type_checking_test(test: ast.expr) -> bool:
        """Return whether one ``if`` test is the ``TYPE_CHECKING`` guard.

        Returns:
            Whether the test names ``TYPE_CHECKING``.

        """
        return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute)
            and test.attr == "TYPE_CHECKING"
            and isinstance(test.value, ast.Name)
            and test.value.id == "typing"
        )

    @classmethod
    def _import_law_inside_type_checking(
        cls,
        node: ast.AST,
        parents: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> bool:
        """Return whether the node sits under an ``if TYPE_CHECKING:`` block.

        Returns:
            Whether the node sits under an ``if TYPE_CHECKING:`` block.

        """
        current = parents.get(id(node))
        while current is not None:
            if isinstance(current, ast.If) and cls._import_law_is_type_checking_test(
                current.test,
            ):
                return True
            current = parents.get(id(current))
        return False

    @classmethod
    def _import_law_annotation_ids(cls, state: m.Infra.ImportLawPass) -> frozenset[int]:
        """Return the ids of every node inside a non-evaluated annotation.

        Function argument and return annotations and module-level variable
        annotations are strings under ``from __future__ import annotations``.
        Class-body annotations remain runtime-sensitive unless native ancestry
        proves ordinary class construction or the declaration is a ClassVar.

        Returns:
            The resulting ``frozenset[int]``.

        """
        ids: set[int] = set()
        tree = state.tree
        for node in ast.walk(tree):
            annotations: list[ast.expr] = []
            if isinstance(node, c.Infra.AST_FUNCTION_TYPES):
                arguments = node.args
                annotations.extend(
                    argument.annotation
                    for argument in (
                        *arguments.posonlyargs,
                        *arguments.args,
                        *arguments.kwonlyargs,
                        *((arguments.vararg,) if arguments.vararg else ()),
                        *((arguments.kwarg,) if arguments.kwarg else ()),
                    )
                    if argument.annotation is not None
                )
                if node.returns is not None:
                    annotations.append(node.returns)
            for annotation in annotations:
                ids.update(id(sub) for sub in ast.walk(annotation))
        for statement in tree.body:
            if isinstance(statement, ast.AnnAssign):
                ids.update(id(sub) for sub in ast.walk(statement.annotation))
        # ``ClassVar[...]`` members are excluded from Pydantic/dataclass field
        # processing, so their class-body annotations are never evaluated at
        # runtime and must not count as runtime reads of the binding.
        for node in ast.walk(tree):
            if isinstance(
                node, ast.AnnAssign
            ) and cls._import_law_is_classvar_annotation(node.annotation):
                ids.update(id(sub) for sub in ast.walk(node.annotation))
        cls._import_law_collect_plain_namespace_annotations(state, ids)
        return frozenset(ids)

    @classmethod
    def _import_law_collect_plain_namespace_annotations(
        cls,
        state: m.Infra.ImportLawPass,
        ids: set[int],
    ) -> None:
        """Collect annotations only for positively proven namespace classes."""
        for node in ast.walk(state.tree):
            if (
                isinstance(node, ast.ClassDef)
                and node.lineno in state.deferred_class_lines
            ):
                for statement in node.body:
                    if isinstance(statement, ast.AnnAssign):
                        ids.update(id(sub) for sub in ast.walk(statement.annotation))

    @staticmethod
    def _import_law_is_classvar_annotation(annotation: ast.expr) -> bool:
        """Return whether an annotation is a ``ClassVar[...]`` subscription.

        Returns:
            Whether the annotation is a ``ClassVar[...]`` subscription.

        """
        if not isinstance(annotation, ast.Subscript):
            return False
        value = annotation.value
        return (isinstance(value, ast.Name) and value.id == "ClassVar") or (
            isinstance(value, ast.Attribute) and value.attr == "ClassVar"
        )

    @staticmethod
    def _import_law_defers_annotations(tree: ast.Module) -> bool:
        """Return whether the module defers annotation evaluation.

        Returns:
            Whether ``from __future__ import annotations`` is declared.

        """
        return any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body
        )

    @classmethod
    def _import_law_runtime_uses(
        cls,
        state: m.Infra.ImportLawPass,
        name: str,
    ) -> bool:
        """Return whether one binding is read anywhere at runtime.

        A read is typing-only when it sits inside a ``TYPE_CHECKING`` block or,
        in a module that defers annotations, inside a function signature or
        module-level variable annotation.

        Returns:
            Whether the binding has at least one runtime read.

        """
        return bool(cls._import_law_runtime_reads(state, name))

    @classmethod
    def _import_law_runtime_reads(
        cls,
        state: m.Infra.ImportLawPass,
        name: str,
    ) -> tuple[ast.Name, ...]:
        """Locate runtime reads for both placement and causal diagnostics.

        Returns:
            Loads of the binding outside deferred annotations and typing guards.

        """
        typing_only = (
            cls._import_law_annotation_ids(state)
            if cls._import_law_defers_annotations(state.tree)
            else ()
        )
        return tuple(
            node
            for node in ast.walk(state.tree)
            if isinstance(node, ast.Name)
            and node.id == name
            and isinstance(node.ctx, ast.Load)
            and id(node) not in typing_only
            and not cls._import_law_inside_type_checking(node, state.parents)
        )

    @staticmethod
    def _import_law_end_line(node: ast.stmt) -> int:
        """Return one statement's inclusive end line.

        Returns:
            The resulting ``int``.

        """
        return node.end_lineno or node.lineno

    @staticmethod
    def _import_law_line_indent(line: str) -> str:
        """Return one line's leading whitespace.

        Returns:
            The resulting ``str``.

        """
        return line[: len(line) - len(line.lstrip())]

    @staticmethod
    def _import_law_clause(alias: ast.alias) -> str:
        """Render one import alias clause.

        Returns:
            ``name`` or ``name as asname``.

        """
        return alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"

    @classmethod
    def _import_law_apply_edits(
        cls,
        source: str,
        edits: t.SequenceOf[tuple[int, int, t.StrSequence]],
    ) -> str | None:
        """Apply non-overlapping line edits; ``None`` when they collide.

        A span ``(n, n - 1)`` inserts BEFORE line ``n``; a span ``(a, b)``
        with ``b >= a`` replaces lines ``a..b``; a span with an empty
        replacement deletes its lines.

        Returns:
            The resulting ``str | None``.

        """
        lines = source.splitlines()
        ordered = sorted(edits, key=operator.itemgetter(0, 1), reverse=True)
        last_start: int | None = None
        for start, end, replacement in ordered:
            if last_start is not None and end >= last_start:
                return None
            last_start = start
            if not replacement:
                if end >= start:
                    lines[start - 1 : end] = ()
                continue
            if end < start:
                lines[start - 1 : start - 1] = list(replacement)
                continue
            lines[start - 1 : end] = list(replacement)
        return "\n".join(lines).rstrip() + "\n"


__all__: list[str] = ["FlextInfraUtilitiesImportLawAst"]
