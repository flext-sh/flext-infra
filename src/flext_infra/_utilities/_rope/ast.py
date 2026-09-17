"""AST structural introspection above the node primitives."""

from __future__ import annotations

from collections.abc import MutableMapping

from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from .imports import FlextInfraUtilitiesRopeAnalysisImports
from .nodes import FlextInfraUtilitiesRopeAnalysisNodes
from .source import FlextInfraUtilitiesRopeAnalysisSource


class FlextInfraUtilitiesRopeAnalysisAst(FlextInfraUtilitiesRopeAnalysisSource):
    """AST structural introspection above the node primitives."""

    @staticmethod
    def decorator_names(pyfunction: t.Infra.RopePyObject) -> t.StrSequence:
        """Extract decorator names from a rope ``PyFunction`` (no ast import)."""
        decorators = getattr(pyfunction, "decorators", None) or ()
        names: list[str] = []
        for decorator in decorators:
            name = getattr(decorator, "id", None) or getattr(decorator, "attr", None)
            if isinstance(name, str) and name:
                names.append(name)
                continue
            func = getattr(decorator, "func", None)
            inner = getattr(func, "id", None) or getattr(func, "attr", None)
            if isinstance(inner, str) and inner:
                names.append(inner)
        return names

    @staticmethod
    def first_decorator_line(
        pyfunction: t.Infra.RopePyObject, *, default_line: int
    ) -> int:
        """Return the lowest line number among ``pyfunction``'s decorators."""
        decorators = getattr(pyfunction, "decorators", None) or ()
        candidate_lines = [
            decorator.lineno
            for decorator in decorators
            if isinstance(getattr(decorator, "lineno", None), int)
        ]
        return min(candidate_lines) if candidate_lines else default_line

    @staticmethod
    def ast_parent_map(
        root: t.Infra.RopeAstNode,
    ) -> MutableMapping[int, t.Infra.RopeAstNode]:
        """Return a child-id -> parent map for the full AST reachable from ``root``.

        Uses only public ``_fields`` access (no ``import ast``); the shared SSOT
        for parent lookups across every rope detector.
        """
        parent_map: MutableMapping[int, t.Infra.RopeAstNode] = {}
        stack: list[t.Infra.RopeAstNode] = [root]
        while stack:
            parent = stack.pop()
            for field_name in getattr(parent, "_fields", ()):
                value = getattr(parent, field_name, None)
                if isinstance(value, list):
                    for child in value:
                        if hasattr(child, "_fields"):
                            parent_map[id(child)] = parent
                            stack.append(child)
                elif hasattr(value, "_fields"):
                    parent_map[id(value)] = parent
                    stack.append(value)
        return parent_map

    @classmethod
    def is_module_level_node(
        cls,
        node: t.Infra.RopeAstNode,
        parent_map: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> bool:
        """Return True when ``node`` is a direct child of the module body.

        Walks the parent chain; a node nested inside any ClassDef/FunctionDef is
        NOT module-level. Shared SSOT for placement detectors.
        """
        current = node
        while True:
            parent = parent_map.get(id(current))
            if parent is None:
                return False
            parent_kind = cls.node_kind(parent)
            if parent_kind in {"ClassDef", "FunctionDef", "AsyncFunctionDef"}:
                return False
            if parent_kind == "Module":
                return True
            current = parent

    @staticmethod
    def line_col_range(node: t.Infra.RopeAstNode) -> t.Quad[int, int, int, int] | None:
        """Return ``(lineno, col_offset, end_lineno, end_col_offset)`` for an AST node."""
        lineno = getattr(node, "lineno", None)
        col_offset = getattr(node, "col_offset", None)
        end_lineno = getattr(node, "end_lineno", None) or lineno
        end_col_offset = getattr(node, "end_col_offset", None) or col_offset
        if not (
            isinstance(lineno, int)
            and isinstance(col_offset, int)
            and isinstance(end_lineno, int)
            and isinstance(end_col_offset, int)
        ):
            return None
        return (lineno, col_offset, end_lineno, end_col_offset)

    @staticmethod
    def get_class_info(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return ClassInfo (name, line, bases) for all classes in a module."""
        class_infos: t.SequenceOf[m.Infra.ClassInfo] = (
            FlextInfraUtilitiesRopeAnalysisImports.get_module_semantic_state(
                rope_project, resource
            ).class_infos
        )
        return class_infos

    @staticmethod
    def get_class_bases(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> t.StrSequence:
        """Return base class names for a given class in a module."""
        for info in FlextInfraUtilitiesRopeAnalysisAst.get_class_info(
            rope_project, resource
        ):
            if info.name == class_name:
                return list(info.bases)
        return ()

    @staticmethod
    def get_class_symbol_count(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        class_name: str,
    ) -> int:
        """Return direct symbol count for a top-level class without semantic imports."""
        pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        tree = FlextInfraUtilitiesRopeAnalysisNodes.ensure_ast_node(pymodule.get_ast())
        class_body = FlextInfraUtilitiesRopeAnalysisNodes._class_body_nodes(
            tree, class_name=class_name
        )
        return len(FlextInfraUtilitiesRopeAnalysisNodes._class_symbol_names(class_body))


__all__ = ["FlextInfraUtilitiesRopeAnalysisAst"]
