"""Shared rope parsing and AST traversal primitives.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import ClassVar

from flext_cli import u

from flext_infra import c, m, p, settings, t
from flext_infra._utilities._rope.rope_ast import FlextInfraUtilitiesRopeAst
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime


class FlextInfraUtilitiesRopeAnalysisAstHelpers(FlextInfraUtilitiesRopeAst):
    """Shared rope parsing and AST traversal primitives."""

    _parse_project: ClassVar[t.Infra.RopeProject | None] = None

    @staticmethod
    def resource_cache_key(
        rope_project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
    ) -> t.Triple[str, str, str]:
        """Key export facts by authenticated source, not physical timestamps.

        Returns:
            The project, resource path, and authenticated source digest.

        Raises:
            TypeError: If the resource has no native source module.

        """
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            rope_project, resource
        ).get_module()
        if not FlextInfraUtilitiesRopeRuntime.source_module(module):
            message = "Rope export facts require an authenticated source module"
            raise TypeError(message)
        rope_project.source_bytes(Path(resource.real_path))
        digest = u.Cli.sha256_bytes(module.source_code.encode(c.DEFAULT_ENCODING))
        return (rope_project.root.real_path, resource.path, digest)

    @staticmethod
    def local_name(pyname: t.Infra.RopePyName, resource: t.Infra.RopeResource) -> bool:
        """Return whether one Rope name is defined in ``resource``.

        Returns:
            Whether one Rope name is defined in ``resource``.

        """
        if isinstance(pyname, (p.Infra.RopeImportedName, p.Infra.RopeImportedModule)):
            return False
        # p.Infra declares
        # get_definition_location() as tuple-always (every other caller
        # unpacks directly); the old None guard was dead code.
        module, line = pyname.get_definition_location()
        origin = module.get_resource() if module is not None else None
        return line is not None and origin is not None and origin.path == resource.path

    @staticmethod
    def statement_target_names(statement: t.Infra.RopeAstNode) -> list[str]:
        """Extract target names from an Assign/AnnAssign/PEP-695 TypeAlias.

        Returns:
            The resulting ``list[str]``.

        """
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
    def parse_string_module(source: str) -> t.Infra.RopeSourceModule:
        """Parse ``source`` to a rope ``PyModule`` via a shared parsing project.

        Uses rope's ``libutils.get_string_module`` so callers don't need to
        manage temporary files. Parse failures raise; rope contract failures
        escape — the function never returns ``None``.

        Returns:
            The resulting ``t.Infra.RopeSourceModule``.

        """
        rope_project = FlextInfraUtilitiesRopeAnalysisAstHelpers._shared_parse_project()
        result: t.Infra.RopeSourceModule = (
            FlextInfraUtilitiesRopeRuntime.build_string_module(rope_project, source)
        )
        return result

    @staticmethod
    def _shared_parse_project() -> t.Infra.RopeProject:
        """Return a process-wide rope project usable for string parsing.

        Returns:
            A process-wide rope project usable for string parsing.

        """
        cached = FlextInfraUtilitiesRopeAnalysisAstHelpers._parse_project
        if cached is None:
            # Root-cause fix: the anchor was a hardcoded
            # operator path that crashed CI (FileNotFoundError) and silently bound
            # the parse project to the wrong tree locally. Anchor on the validated
            # settings SSOT, with cwd as last resort — both exist where CLI runs.
            # Path() coercion keeps this correct while settings migrates the
            # field from str to Path (both accepted).
            repository_root = settings.Infra.repository_root
            anchor = Path(repository_root) if repository_root else Path.cwd()
            cached = FlextInfraUtilitiesRopeCore.init_rope_project(anchor)
            FlextInfraUtilitiesRopeAnalysisAstHelpers._parse_project = cached
        return cached

    @staticmethod
    def decorator_names(pyfunction: t.Infra.RopePyObject) -> t.StrSequence:
        """Extract decorator names from a rope ``PyFunction`` (no ast import).

        Returns:
            The resulting ``t.StrSequence``.

        """
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
        pyfunction: t.Infra.RopePyObject,
        *,
        default_line: int,
    ) -> int:
        """Return the lowest line number among ``pyfunction``'s decorators.

        Returns:
            The lowest line number among ``pyfunction``'s decorators.

        """
        decorators = getattr(pyfunction, "decorators", None) or ()
        candidate_lines = [
            decorator.lineno
            for decorator in decorators
            if isinstance(getattr(decorator, "lineno", None), int)
        ]
        return min(candidate_lines) if candidate_lines else default_line

    @staticmethod
    def node_kind(node: p.AttributeProbe) -> str:
        """Return an AST node's class name (e.g. ``"AnnAssign"``) without importing ast.

        Returns:
            An AST node's class name (e.g. ``"AnnAssign"``) without importing ast.

        """
        return type(node).__name__

    @staticmethod
    def walk_ast_nodes(root: t.Infra.RopeAstNode) -> t.SequenceOf[t.Infra.RopeAstNode]:
        """Return every AST node reachable from ``root``, ``root`` included.

        Returns:
            Every AST node reachable from ``root``, ``root`` included.

        """
        if not isinstance(root, ast.AST):
            return []
        return tuple(ast.walk(root))

    @classmethod
    def module_level_node(
        cls,
        node: t.Infra.RopeAstNode,
        parent_map: t.MappingKV[int, t.Infra.RopeAstNode],
    ) -> bool:
        """Return True when ``node`` is a direct child of the module body.

        Walks the parent chain; a node nested inside any ClassDef/FunctionDef is
        NOT module-level. Shared SSOT for placement detectors.

        Returns:
            True when ``node`` is a direct child of the module body.

        """
        current = node
        while True:
            parent = parent_map.get(id(current))
            if parent is None:
                return False
            if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(parent):
                return False
            parent_kind = cls.node_kind(parent)
            if parent_kind in {"ClassDef", "FunctionDef", "AsyncFunctionDef"}:
                return False
            if parent_kind == "Module":
                return True
            current = parent

    @staticmethod
    def name_of(node: p.AttributeProbe) -> str:
        """Return ``node.id`` (Name) or ``node.attr`` (Attribute) or ``""``.

        Returns:
            ``node.id`` (Name) or ``node.attr`` (Attribute) or ``""``.

        """
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(node):
            return ""
        identifier = getattr(node, "id", None)
        if isinstance(identifier, str) and identifier:
            return identifier
        attr = getattr(node, "attr", None)
        if isinstance(attr, str) and attr:
            return attr
        return ""

    @staticmethod
    def line_col_range(node: p.AttributeProbe) -> t.Quad[int, int, int, int] | None:
        """Return ``(lineno, col_offset, end_lineno, end_col_offset)`` for an AST node.

        Returns:
            ``(lineno, col_offset, end_lineno, end_col_offset)`` for an AST node.

        """
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(node):
            return None
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
    def assignment_target_names(node: p.AttributeProbe) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node.

        Returns:
            Direct assignment target names represented by one AST node.

        """
        return FlextInfraUtilitiesRopeAnalysisAstHelpers._assignment_target_names(node)

    @staticmethod
    def _assignment_target_names(node: p.AttributeProbe) -> t.StrSequence:
        """Return direct assignment target names represented by one AST node.

        Returns:
            Direct assignment target names represented by one AST node.

        """
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(node):
            return ()
        if isinstance(node, ast.AnnAssign):
            target_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(node.target)
            return (target_name,) if target_name else ()
        if not isinstance(node, ast.Assign):
            return ()
        names: list[str] = []
        for target in node.targets:
            target_name = FlextInfraUtilitiesRopeAnalysisAstHelpers.name_of(target)
            if target_name:
                names.append(target_name)
        return tuple(names)

    @staticmethod
    def class_info_from_source(source: str) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Return class info from the current source text without Rope resource cache.

        Returns:
            Class info from the current source text without Rope resource cache.

        """
        pymodule = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(source)
        tree = pymodule.get_ast()
        if not isinstance(tree, ast.Module):
            return ()
        return FlextInfraUtilitiesRopeAnalysisAstHelpers.class_info_from_module(tree)

    @staticmethod
    def class_info_from_module(
        tree: t.Infra.AstModule,
    ) -> t.SequenceOf[m.Infra.ClassInfo]:
        """Read top-level class facts from an existing native module tree.

        Returns:
            The same class facts as the source-text reader, without another parse.

        """
        return tuple(
            class_info
            for node in tree.body
            if (
                class_info
                := FlextInfraUtilitiesRopeAnalysisAstHelpers._class_info_from_ast(node)
            )
            is not None
        )

    @staticmethod
    def _class_info_from_ast(node: p.AttributeProbe) -> m.Infra.ClassInfo | None:
        """Return ClassInfo for one top-level ClassDef AST node.

        Returns:
            ClassInfo for one top-level ClassDef AST node.

        """
        if not isinstance(node, ast.ClassDef):
            return None
        if not node.name:
            return None
        return m.Infra.ClassInfo(
            name=node.name,
            line=node.lineno if node.lineno > 0 else 1,
            bases=tuple(
                base_name
                for base in node.bases
                if (
                    base_name
                    := FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(base)
                )
            ),
        )

    @staticmethod
    def class_base_name(node: p.AttributeProbe) -> str:
        """Return terminal base name from an AST base expression.

        Returns:
            Terminal base name from an AST base expression.

        """
        return FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(node)

    @staticmethod
    def _class_base_name(node: p.AttributeProbe) -> str:
        """Return terminal base name from an AST base expression.

        Returns:
            Terminal base name from an AST base expression.

        """
        if not FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(node):
            return ""
        for attr_name in ("id", "attr", "name"):
            value = getattr(node, attr_name, "")
            if isinstance(value, str) and value:
                return value
        subscript_value = getattr(node, "value", None)
        if (
            subscript_value is not None
            and FlextInfraUtilitiesRopeAnalysisAstHelpers.ast_node(subscript_value)
        ):
            return FlextInfraUtilitiesRopeAnalysisAstHelpers._class_base_name(
                subscript_value,
            )
        return ""


__all__: list[str] = ["FlextInfraUtilitiesRopeAnalysisAstHelpers"]
