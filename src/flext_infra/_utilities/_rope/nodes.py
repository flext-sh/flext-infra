"""AST node primitives: kinds, names, walking, and class info."""

from __future__ import annotations

from typing import TypeGuard

from flext_infra.models import m
from flext_infra.typings import t

from .base import FlextInfraUtilitiesRopeAnalysisBase


class FlextInfraUtilitiesRopeAnalysisNodes(FlextInfraUtilitiesRopeAnalysisBase):
    """AST node primitives: kinds, names, walking, and class info."""

    @staticmethod
    def is_ast_node(obj: object) -> TypeGuard[t.Infra.RopeAstNode]:
        """Type guard to narrow to RopeAstNode via structural `_fields` check."""
        return hasattr(obj, "_fields")

    @staticmethod
    def ensure_ast_node(obj: object) -> t.Infra.RopeAstNode:
        """Ensure an object is an AST node (has `_fields`), narrowing the type."""
        if not FlextInfraUtilitiesRopeAnalysisNodes.is_ast_node(obj):
            msg = f"Expected AST node with _fields, got {type(obj).__name__}"
            raise TypeError(msg)
        return obj

    @staticmethod
    def node_kind(node: t.Infra.RopeAstNode) -> str:
        """Return an AST node's class name (e.g. ``"AnnAssign"``) without importing ast."""
        return type(node).__name__

    @staticmethod
    def name_of(node: t.Infra.RopeAstNode | None) -> str:
        """Return ``node.id`` (Name) or ``node.attr`` (Attribute) or ``""``."""
        if node is None:
            return ""
        identifier = getattr(node, "id", None)
        if isinstance(identifier, str) and identifier:
            return identifier
        attr = getattr(node, "attr", None)
        if isinstance(attr, str) and attr:
            return attr
        return ""

    @staticmethod
    def walk_ast_nodes(root: t.Infra.RopeAstNode) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Recursively yield every AST node reachable from ``root`` via ``_fields``.

        Equivalent to ``ast.walk`` but uses only public attribute access on
        rope-provided AST objects, so no ``import ast`` is needed at the
        consumer layer.
        """
        collected: list[t.Infra.RopeAstNode] = []
        stack: list[t.Infra.RopeAstNode] = [root]
        while stack:
            node = stack.pop()
            collected.append(node)
            for field_name in getattr(node, "_fields", ()):
                value = getattr(node, field_name, None)
                if isinstance(value, list):
                    stack.extend(
                        item
                        for item in value
                        if FlextInfraUtilitiesRopeAnalysisNodes.is_ast_node(item)
                    )
                elif FlextInfraUtilitiesRopeAnalysisNodes.is_ast_node(value):
                    stack.append(value)
        return collected

    @staticmethod
    def _body_nodes(node: t.Infra.RopeAstNode) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return direct AST body children for a Rope AST node."""
        body = getattr(node, "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        nodes: list[t.Infra.RopeAstNode] = [
            child
            for child in body
            if FlextInfraUtilitiesRopeAnalysisNodes.is_ast_node(child)
        ]
        return tuple(nodes)

    @staticmethod
    def _class_body_nodes(
        tree: t.Infra.RopeAstNode, *, class_name: str
    ) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return direct body nodes for a top-level class name."""
        for node in FlextInfraUtilitiesRopeAnalysisNodes._body_nodes(tree):
            if FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node) != "ClassDef":
                continue
            if getattr(node, "name", "") == class_name:
                return FlextInfraUtilitiesRopeAnalysisNodes._body_nodes(node)
        return ()

    @staticmethod
    def _class_symbol_names(
        class_body: t.SequenceOf[t.Infra.RopeAstNode],
    ) -> t.StrSequence:
        """Return direct method, nested-class and attribute symbols for a class body."""
        names: set[str] = set()
        for node in class_body:
            node_kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node)
            if node_kind in {"AsyncFunctionDef", "ClassDef", "FunctionDef"}:
                node_name = getattr(node, "name", "")
                if isinstance(node_name, str) and node_name:
                    names.add(node_name)
                continue
            names.update(
                FlextInfraUtilitiesRopeAnalysisNodes._assignment_target_names(node)
            )
        return tuple(sorted(names))

    @staticmethod
    def class_info_from_source(source: str) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return class info from the current source text without Rope resource cache."""
        pymodule = FlextInfraUtilitiesRopeAnalysisBase.parse_string_module(source)
        body = getattr(pymodule.get_ast(), "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        return tuple(
            class_info
            for node in body
            if (
                class_info := FlextInfraUtilitiesRopeAnalysisNodes._class_info_from_ast(
                    node
                )
            )
            is not None
        )

    @staticmethod
    def _class_info_from_ast(node: t.Infra.RopeAstNode) -> m.Infra.ClassInfo | None:
        """Return ClassInfo for one top-level ClassDef AST node."""
        if FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node) != "ClassDef":
            return None
        name = getattr(node, "name", "")
        if not isinstance(name, str) or not name:
            return None
        line = getattr(node, "lineno", 1)
        raw_bases = getattr(node, "bases", ())
        if not isinstance(raw_bases, (list, tuple)):
            raw_bases = ()
        return m.Infra.ClassInfo(
            name=name,
            line=line if isinstance(line, int) and line > 0 else 1,
            bases=tuple(
                base_name
                for base in raw_bases
                if (
                    base_name := FlextInfraUtilitiesRopeAnalysisNodes._class_base_name(
                        base
                    )
                )
            ),
        )

    @staticmethod
    def class_base_name(node: t.Infra.RopeAstNode) -> str:
        """Return terminal base name from an AST base expression."""
        return FlextInfraUtilitiesRopeAnalysisNodes._class_base_name(node)

    @staticmethod
    def _class_base_name(node: t.Infra.RopeAstNode) -> str:
        """Return terminal base name from an AST base expression."""
        for attr_name in ("id", "attr", "name"):
            value = getattr(node, attr_name, "")
            if isinstance(value, str) and value:
                return value
        subscript_value = getattr(node, "value", None)
        if subscript_value is not None:
            return FlextInfraUtilitiesRopeAnalysisNodes._class_base_name(
                subscript_value
            )
        return ""

    @staticmethod
    def assignment_target_names(node: t.Infra.RopeAstNode) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node."""
        return FlextInfraUtilitiesRopeAnalysisNodes._assignment_target_names(node)

    @staticmethod
    def _assignment_target_names(node: t.Infra.RopeAstNode) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node."""
        node_kind = FlextInfraUtilitiesRopeAnalysisNodes.node_kind(node)
        if node_kind == "AnnAssign":
            target_name = FlextInfraUtilitiesRopeAnalysisNodes.name_of(
                getattr(node, "target", None)
            )
            return (target_name,) if target_name else ()
        if node_kind != "Assign":
            return ()
        targets = getattr(node, "targets", ())
        if not isinstance(targets, (list, tuple)):
            return ()
        names: list[str] = []
        for target in targets:
            target_name = FlextInfraUtilitiesRopeAnalysisNodes.name_of(target)
            if target_name:
                names.append(target_name)
        return tuple(names)


__all__ = ["FlextInfraUtilitiesRopeAnalysisNodes"]
