"""Shared AST, scope and line-edit helpers of import normalization.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import operator
from collections.abc import MutableMapping

from flext_infra import t


class FlextInfraImportNormalizationAstMixin:
    """Parse, scope and edit module sources for import rewrites."""

    @staticmethod
    def _parent_map(tree: ast.Module) -> t.MappingKV[int, ast.AST]:
        """Map every node id to its parent node.

        Returns:
            The resulting ``t.MappingKV[int, ast.AST]``.

        """
        parents: MutableMapping[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[id(child)] = node
        return parents

    @staticmethod
    def _iter_imports(tree: ast.Module) -> t.SequenceOf[ast.Import | ast.ImportFrom]:
        """Return every import statement anywhere in the module, in order.

        Returns:
            The resulting ``t.SequenceOf[ast.Import | ast.ImportFrom]``.

        """
        return sorted(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Import | ast.ImportFrom)
            ),
            key=operator.attrgetter("lineno"),
        )

    @classmethod
    def _enclosing_scope(
        cls,
        node: ast.AST,
        parents: t.MappingKV[int, ast.AST],
    ) -> ast.AST | None:
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
            match current:
                case ast.FunctionDef() | ast.AsyncFunctionDef():
                    if isinstance(node, ast.arg) or child in current.body:
                        return current
                case ast.Lambda():
                    if isinstance(node, ast.arg) or child is current.body:
                        return current
                case ast.ClassDef():
                    if child in current.body:
                        return current
                case (
                    ast.ListComp() | ast.SetComp() | ast.DictComp() | ast.GeneratorExp()
                ):
                    if cls._comprehension_owns_node(node, current, parents):
                        return current
                case _:
                    pass
            child = current
            current = parents.get(id(current))
        return None

    @staticmethod
    def _comprehension_owns_node(
        node: ast.AST,
        scope: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
        parents: t.MappingKV[int, ast.AST],
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
    def _is_type_checking_test(test: ast.expr) -> bool:
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
    def _inside_type_checking(
        cls,
        node: ast.AST,
        parents: t.MappingKV[int, ast.AST],
    ) -> bool:
        """Return whether the node sits under an ``if TYPE_CHECKING:`` block.

        Returns:
            Whether the node sits under an ``if TYPE_CHECKING:`` block.

        """
        current = parents.get(id(node))
        while current is not None:
            if isinstance(current, ast.If) and cls._is_type_checking_test(
                current.test,
            ):
                return True
            current = parents.get(id(current))
        return False

    @classmethod
    def _annotation_ids(cls, tree: ast.Module) -> frozenset[int]:
        """Return the ids of every node inside a non-evaluated annotation.

        Function argument and return annotations and module-level variable
        annotations are strings under ``from __future__ import annotations``.
        A class-body annotation is evaluated by Pydantic and dataclass
        machinery, so it is never typing-only.

        Returns:
            The resulting ``frozenset[int]``.

        """
        ids: set[int] = set()
        for node in ast.walk(tree):
            annotations: list[ast.expr] = []
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
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
            if isinstance(node, ast.AnnAssign) and cls._is_classvar_annotation(
                node.annotation
            ):
                ids.update(id(sub) for sub in ast.walk(node.annotation))
        cls._collect_plain_namespace_annotations(tree, ids)
        return frozenset(ids)

    @classmethod
    def _collect_plain_namespace_annotations(
        cls,
        tree: ast.Module,
        ids: set[int],
    ) -> None:
        """Collect annotation ids inside base-less class bodies.

        A class with no bases is a plain namespace holder: under deferred
        annotations its body annotations are never evaluated by anything
        (no Pydantic/dataclass machinery resolves them), so annotation-name
        reads inside it are typing-only. Based classes keep the
        conservative runtime classification — their annotations may feed
        model construction.

        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.bases:
                for statement in node.body:
                    if isinstance(statement, ast.AnnAssign):
                        ids.update(id(sub) for sub in ast.walk(statement.annotation))

    @staticmethod
    def _is_classvar_annotation(annotation: ast.expr) -> bool:
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
    def _defers_annotations(tree: ast.Module) -> bool:
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
    def _runtime_uses(
        cls,
        tree: ast.Module,
        name: str,
        parents: t.MappingKV[int, ast.AST],
    ) -> bool:
        """Return whether one binding is read anywhere at runtime.

        A read is typing-only when it sits inside a ``TYPE_CHECKING`` block or,
        in a module that defers annotations, inside a function signature or
        module-level variable annotation.

        Returns:
            Whether the binding has at least one runtime read.

        """
        typing_only = cls._annotation_ids(tree) if cls._defers_annotations(tree) else ()
        return any(
            isinstance(node, ast.Name)
            and node.id == name
            and isinstance(node.ctx, ast.Load)
            and id(node) not in typing_only
            and not cls._inside_type_checking(node, parents)
            for node in ast.walk(tree)
        )

    @staticmethod
    def _module_bindings(tree: ast.Module) -> t.MappingKV[str, ast.stmt]:
        """Return the module-level statement binding each top-level name.

        Returns:
            The resulting ``t.MappingKV[str, ast.stmt]``.

        """
        bindings: MutableMapping[str, ast.stmt] = {}
        for statement in tree.body:
            names: list[str] = []
            match statement:
                case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                    names = [
                        alias.asname or alias.name.partition(".")[0]
                        for alias in aliases
                    ]
                case (
                    ast.FunctionDef(name=name)
                    | ast.AsyncFunctionDef(name=name)
                    | ast.ClassDef(name=name)
                ):
                    names = [name]
                case ast.Assign(targets=targets):
                    names = [
                        target.id for target in targets if isinstance(target, ast.Name)
                    ]
                case ast.AnnAssign(target=ast.Name(id=name)):
                    names = [name]
                case _:
                    pass
            for bound in names:
                bindings.setdefault(bound, statement)
        return bindings

    @staticmethod
    def _end_line(node: ast.stmt) -> int:
        """Return one statement's inclusive end line.

        Returns:
            The resulting ``int``.

        """
        return node.end_lineno or node.lineno

    @staticmethod
    def _line_indent(line: str) -> str:
        """Return one line's leading whitespace.

        Returns:
            The resulting ``str``.

        """
        return line[: len(line) - len(line.lstrip())]

    @staticmethod
    def _clause(alias: ast.alias) -> str:
        """Render one import alias clause.

        Returns:
            ``name`` or ``name as asname``.

        """
        return alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"

    @classmethod
    def _apply_edits(
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


__all__: list[str] = ["FlextInfraImportNormalizationAstMixin"]
