"""AST analysis for deferred self-reference and recursive model defects."""

from __future__ import annotations

import ast
from typing import ClassVar, NamedTuple


class FlextInfraUtilitiesDeferredSelfReferenceAst:
    """Collect invalid model self-references from a parsed module."""

    class Finding(NamedTuple):
        """One deferred-self-reference or recursive-model occurrence."""

        line: int
        column: int
        kind: str
        detail: str

    _DEFERRED_KIND: ClassVar[str] = "DEFERRED_SELF_REFERENCE"
    _RECURSIVE_KIND: ClassVar[str] = "RECURSIVE_MODEL"
    _FACTORY_KEYWORD: ClassVar[str] = "default_factory"
    _NON_FIELD_WRAPPERS: ClassVar[frozenset[str]] = frozenset({
        "ClassVar",
        "TypeAdapter",
    })

    @staticmethod
    def _enclosing_class_names(stack: list[ast.ClassDef]) -> frozenset[str]:
        return frozenset(node.name for node in stack)

    @staticmethod
    def _attribute_root(node: ast.expr) -> str | None:
        current = node
        while isinstance(current, ast.Attribute):
            current = current.value
        return current.id if isinstance(current, ast.Name) else None

    @classmethod
    def _referenced_roots(cls, node: ast.expr) -> frozenset[str]:
        roots: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                root = cls._attribute_root(child)
                if root is not None:
                    roots.add(root)
            elif isinstance(child, ast.Name):
                roots.add(child.id)
        return frozenset(roots)

    @staticmethod
    def _annotation_wrappers(node: ast.expr) -> frozenset[str]:
        wrappers: set[str] = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Subscript):
                continue
            value = child.value
            if isinstance(value, ast.Attribute):
                wrappers.add(value.attr)
            elif isinstance(value, ast.Name):
                wrappers.add(value.id)
        return frozenset(wrappers)

    @classmethod
    def _factory_keyword(cls, call: ast.Call) -> ast.keyword | None:
        return next(
            (item for item in call.keywords if item.arg == cls._FACTORY_KEYWORD), None
        )

    @classmethod
    def collect_deferred_self_reference_findings(
        cls, tree: ast.Module
    ) -> tuple[Finding, ...]:
        """Collect deferred factories and recursive fields in one module."""
        findings: list[FlextInfraUtilitiesDeferredSelfReferenceAst.Finding] = []
        stack: list[ast.ClassDef] = []

        def visit(node: ast.AST) -> None:
            if isinstance(node, ast.ClassDef):
                stack.append(node)
                for child in node.body:
                    visit(child)
                stack.pop()
                return
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                return
            enclosing = cls._enclosing_class_names(stack)
            if enclosing and isinstance(node, ast.Call):
                keyword = cls._factory_keyword(node)
                if keyword is not None and isinstance(keyword.value, ast.Lambda):
                    cls._append_deferred(findings, enclosing, keyword.value)
            if stack and isinstance(node, ast.AnnAssign):
                cls._append_recursive(findings, stack[-1].name, node)
            for child in ast.iter_child_nodes(node):
                visit(child)

        for child in tree.body:
            visit(child)
        return tuple(findings)

    @classmethod
    def _append_deferred(
        cls, findings: list[Finding], enclosing: frozenset[str], factory: ast.Lambda
    ) -> None:
        hit = enclosing & cls._referenced_roots(factory.body)
        if not hit:
            return
        name = min(hit)
        findings.append(
            cls.Finding(
                line=factory.lineno,
                column=factory.col_offset,
                kind=cls._DEFERRED_KIND,
                detail=(
                    f"default_factory defers resolution of {name!r} through a lambda "
                    "because the enclosing class is unbound; hoist the model into a "
                    "namespace facet, inherit it, and pass the model as the factory"
                ),
            )
        )

    @classmethod
    def _append_recursive(
        cls, findings: list[Finding], owner: str, node: ast.AnnAssign
    ) -> None:
        wrappers = cls._annotation_wrappers(node.annotation)
        if owner not in cls._referenced_roots(node.annotation) or (
            wrappers & cls._NON_FIELD_WRAPPERS
        ):
            return
        findings.append(
            cls.Finding(
                line=node.annotation.lineno,
                column=node.annotation.col_offset,
                kind=cls._RECURSIVE_KIND,
                detail=(
                    f"model {owner!r} annotates a field with itself; split the "
                    "recursive leg into a separate namespace facet composed by FLEXT"
                ),
            )
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesDeferredSelfReferenceAst",)
