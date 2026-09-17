"""Shared rope parsing and AST traversal primitives."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, TypeGuard

from flext_infra.models import m
from flext_infra.typings import t

from ..rope_core import FlextInfraUtilitiesRopeCore
from ..rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesRopeAnalysisAstHelpers:
    """Shared rope parsing and AST traversal primitives."""

    _parse_project: ClassVar[t.Infra.RopeProject | None] = None

    @staticmethod
    def _is_ast_node(obj: object) -> TypeGuard[t.Infra.RopeAstNode]:
        """Type guard to narrow to RopeAstNode via structural `_fields` check."""
        return hasattr(obj, "_fields")

    @staticmethod
    def _ensure_ast_node(obj: object) -> t.Infra.RopeAstNode:
        """Ensure an object is an AST node (has `_fields`), narrowing the type."""
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers._is_ast_node(obj):
            raise TypeError(f"Expected AST node with _fields, got {type(obj).__name__}")
        return obj

    @staticmethod
    def resource_cache_key(
        rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
    ) -> t.Triple[str, str, int]:
        """Resource cache key."""
        file_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            rope_project, resource
        )
        mtime_ns = (
            file_path.stat().st_mtime_ns
            if file_path is not None and file_path.exists()
            else 0
        )
        project_root = getattr(getattr(rope_project, "root", None), "real_path", "")
        return (str(project_root), resource.path, mtime_ns)

    @staticmethod
    def local_name(pyname: t.Infra.RopePyName, resource: t.Infra.RopeResource) -> bool:
        """Return whether one Rope name is defined in ``resource``."""
        # NOTE (multi-agent, flext-f8vk / kimi): p.Infra declares
        # get_definition_location() as tuple-always (every other caller
        # unpacks directly); the old None guard was dead code.
        module, line = pyname.get_definition_location()
        origin = module.get_resource() if module is not None else None
        return line is not None and origin is not None and origin.path == resource.path

    @staticmethod
    def statement_target_names(statement: t.Infra.RopeAstNode) -> list[str]:
        """Extract target names from an Assign/AnnAssign/PEP-695 TypeAlias."""
        kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(statement)
        if kind == "AnnAssign":
            target = getattr(statement, "target", None)
            name = getattr(target, "id", "") if target is not None else ""
            return [name] if name else []
        if kind == "TypeAlias":
            name_node = getattr(statement, "name", None)
            name = getattr(name_node, "id", "")
            return [name] if isinstance(name, str) and name else []
        targets = getattr(statement, "targets", []) or []
        names: list[str] = []
        for target in targets:
            name = getattr(target, "id", "")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    @staticmethod
    def parse_string_module(source: str) -> t.Infra.RopePyModule:
        """Parse ``source`` to a rope ``PyModule`` via a shared parsing project.

        Uses rope's ``libutils.get_string_module`` so callers don't need to
        manage temporary files. Parse failures raise; rope contract failures
        escape — the function never returns ``None``.
        """
        rope_project = FlextInfraUtilitiesRopeAnalysisAstHelpers._shared_parse_project()
        result: t.Infra.RopePyModule = FlextInfraUtilitiesRopeRuntime.get_string_module(
            rope_project, source
        )
        return result

    @staticmethod
    def _shared_parse_project() -> t.Infra.RopeProject:
        """Return a process-wide rope project usable for string parsing."""
        cached = FlextInfraUtilitiesRopeAnalysisAstHelpers._parse_project
        if cached is None:
            # flext-o6h5 (agent: kimi) — root-cause fix: the anchor was a hardcoded
            # operator path that crashed CI (FileNotFoundError) and silently bound
            # the parse project to the wrong tree locally. Anchor on the validated
            # settings SSOT, with cwd as last resort — both exist where CLI runs.
            # Path() coercion keeps this correct while settings migrates the
            # field from str to Path (both accepted).
            from flext_infra import settings

            repository_root = settings.Infra.repository_root
            anchor = Path(repository_root) if repository_root else Path.cwd()
            cached = FlextInfraUtilitiesRopeCore.init_rope_project(anchor)
            FlextInfraUtilitiesRopeAnalysisAstHelpers._parse_project = cached
        return cached

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
    def node_kind(node: t.Infra.RopeAstNode) -> str:
        """Return an AST node's class name (e.g. ``"AnnAssign"``) without importing ast."""
        return type(node).__name__

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
                        if FlextInfraUtilitiesRopeAnalysisAstHelpers._is_ast_node(item)
                    )
                elif FlextInfraUtilitiesRopeAnalysisAstHelpers._is_ast_node(value):
                    stack.append(value)
        return collected

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
                        if FlextInfraUtilitiesRopeAnalysisAstHelpers._is_ast_node(child):
                            parent_map[id(child)] = parent
                            stack.append(child)
                elif FlextInfraUtilitiesRopeAnalysisAstHelpers._is_ast_node(value):
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
    def _body_nodes(node: t.Infra.RopeAstNode) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return direct AST body children for a Rope AST node."""
        body = getattr(node, "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        nodes: list[t.Infra.RopeAstNode] = [
            child for child in body if hasattr(child, "_fields")
        ]
        return tuple(nodes)

    @staticmethod
    def class_body_nodes(
        tree: t.Infra.RopeAstNode, *, class_name: str
    ) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return direct body nodes for a top-level class name."""
        for node in FlextInfraUtilitiesRopeAnalysisAstHelpers._body_nodes(tree):
            if FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) != "ClassDef":
                continue
            if getattr(node, "name", "") == class_name:
                return FlextInfraUtilitiesRopeAnalysisAstHelpers._body_nodes(node)
        return ()

    @staticmethod
    def assignment_target_names(node: t.Infra.RopeAstNode) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node."""
        return FlextInfraUtilitiesRopeAnalysisAstHelpers._assignment_target_names(node)

    @staticmethod
    def _assignment_target_names(node: t.Infra.RopeAstNode) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node."""
        node_kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node)
        if node_kind == "AnnAssign":
            target_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(
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
            target_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(target)
            if target_name:
                names.append(target_name)
        return tuple(names)

    @staticmethod
    def class_symbol_names(
        class_body: t.SequenceOf[t.Infra.RopeAstNode],
    ) -> t.StrSequence:
        """Return direct method, nested-class and attribute symbols for a class body."""
        names: set[str] = set()
        for node in class_body:
            node_kind = FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node)
            if node_kind in {"AsyncFunctionDef", "ClassDef", "FunctionDef"}:
                node_name = getattr(node, "name", "")
                if isinstance(node_name, str) and node_name:
                    names.add(node_name)
                continue
            names.update(
                FlextInfraUtilitiesRopeAnalysisAstHelpers._assignment_target_names(node)
            )
        return tuple(sorted(names))

    @staticmethod
    def class_info_from_source(source: str) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return class info from the current source text without Rope resource cache."""
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        body = getattr(pymodule.get_ast(), "body", ())
        if not isinstance(body, (list, tuple)):
            return ()
        return tuple(
            class_info
            for node in body
            if (
                class_info
                := FlextInfraUtilitiesRopeAnalysisAstHelpers._class_info_from_ast(node)
            )
            is not None
        )

    @staticmethod
    def _class_info_from_ast(node: t.Infra.RopeAstNode) -> m.Infra.ClassInfo | None:
        """Return ClassInfo for one top-level ClassDef AST node."""
        if FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) != "ClassDef":
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
                    base_name
                    := FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(base)
                )
            ),
        )

    @staticmethod
    def class_base_name(node: t.Infra.RopeAstNode) -> str:
        """Return terminal base name from an AST base expression."""
        return FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(node)

    @staticmethod
    def _class_base_name(node: t.Infra.RopeAstNode) -> str:
        """Return terminal base name from an AST base expression."""
        for attr_name in ("id", "attr", "name"):
            value = getattr(node, attr_name, "")
            if isinstance(value, str) and value:
                return value
        subscript_value = getattr(node, "value", None)
        if subscript_value is not None:
            return FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(
                subscript_value
            )
        return ""
