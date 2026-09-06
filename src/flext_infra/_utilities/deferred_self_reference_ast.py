"""AST analysis for deferred self-reference and recursive model defects."""

from __future__ import annotations

import ast
from typing import ClassVar, NamedTuple

from flext_infra._utilities.deferred_self_reference_rewrite import (
    FlextInfraUtilitiesDeferredSelfReferenceRewrite,
)


class _DeferredSelfReferenceFinding(NamedTuple):
    """One deferred-self-reference or recursive-model occurrence."""

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


def _annotation_wrappers(node: ast.expr) -> frozenset[str]:
    """Return the trailing names of every generic wrapper in an annotation."""
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


def _factory_keyword(call: ast.Call) -> ast.keyword | None:
    """Return the ``default_factory`` keyword of a call, if present."""
    for keyword in call.keywords:
        if keyword.arg == _FACTORY_KEYWORD:
            return keyword
    return None


def _collect_deferred_self_reference_findings(
    tree: ast.Module,
) -> tuple[_DeferredSelfReferenceFinding, ...]:
    """Collect deferred-self-reference and recursive-model findings in a module."""
    findings: list[_DeferredSelfReferenceFinding] = []
    stack: list[ast.ClassDef] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.ClassDef):
            stack.append(node)
            for child in node.body:
                visit(child)

        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # A function body is executed on call, long after the class is
            # bound, so neither defect can occur there: an annotated local is
            # not a model field and a default already resolved.
            return

        enclosing = _enclosing_class_names(stack)
        if enclosing and isinstance(node, ast.Call):
            keyword = _factory_keyword(node)
            if keyword is not None and isinstance(keyword.value, ast.Lambda):
                hit = enclosing & _referenced_roots(keyword.value.body)
                if hit:
                    name = min(hit)
                    findings.append(
                        _DeferredSelfReferenceFinding(
                            line=keyword.value.lineno,
                            column=keyword.value.col_offset,
                            kind=_DEFERRED_KIND,
                            detail=(
                                f"default_factory defers resolution of {name!r} "
                                "through a lambda because the enclosing class is "
                                "still unbound. Hoist the referenced model into "
                                "its own namespace class, inherit it (diamond "
                                "FLEXT), and pass the model itself as the factory."
                            ),
                        )
                    )

        if stack and isinstance(node, ast.AnnAssign):
            owner = stack[-1].name
            annotation = node.annotation
            # ClassVar slots (singleton holders) and TypeAdapter tables are
            # never instantiated as model fields, so naming the owner there is
            # a normal self-typed reference, not a recursive model.
            annotation_roots = _referenced_roots(annotation)
            wrappers = _annotation_wrappers(annotation)
            is_field_annotation = not wrappers & _NON_FIELD_WRAPPERS
            if owner in annotation_roots and is_field_annotation:
                findings.append(
                    _DeferredSelfReferenceFinding(
                        line=annotation.lineno,
                        column=annotation.col_offset,
                        kind=_RECURSIVE_KIND,
                        detail=(
                            f"model {owner!r} annotates a field with itself. A "
                            "recursive model cannot be instantiated while its own "
                            "definition is incomplete; split the recursive leg "
                            "into a separate namespace class composed by FLEXT."
                        ),
                    )
                )

        for child in ast.iter_child_nodes(node):
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
                    "FLEXT namespace facet, inherit it, and pass the model as the factory"
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


class FlextInfraUtilitiesDeferredSelfReference(
    FlextInfraUtilitiesDeferredSelfReferenceRewrite
):
    """Public utility owner for deferred self-reference AST analysis."""

    @staticmethod
    def collect_deferred_self_reference_findings(
        tree: ast.Module,
    ) -> tuple[_DeferredSelfReferenceFinding, ...]:
        """Collect deferred-self-reference and recursive-model findings."""
        return _collect_deferred_self_reference_findings(tree)


__all__: list[str] = ["FlextInfraUtilitiesDeferredSelfReference"]
