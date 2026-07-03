"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import (
    c,
    m,
    t,
    u,
)
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraLooseObjectDetector:
    """Detect loose top-level objects outside namespace classes via rope."""

    @classmethod
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        res = u.Infra.fetch_python_resource(
            ctx.rope_project,
            ctx.file_path,
            skip_protected=True,
            skip_settings=True,
            skip_alias_modules=True,
            skip_init_py=True,
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        project_name = ctx.project_name
        lines = res.read().splitlines()
        class_stem = m.derive_class_stem(project_name)
        file_str = str(file_path)
        violations = list(
            cls._detect_logger_assignments(
                lines=lines,
                file_str=file_str,
                class_stem=class_stem,
            )
        )
        logger_keys = {
            (violation.line, violation.name)
            for violation in violations
            if violation.kind == "logger"
        }

        def _add(symbol: m.Infra.SymbolInfo, kind: str, suffix: str) -> None:
            """Add."""
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=symbol.line,
                    name=symbol.name,
                    kind=kind,
                    suggestion=f"{class_stem}{suffix}",
                )
            )

        class_symbols: t.MutableSequenceOf[m.Infra.SymbolInfo] = []
        for symbol in u.Infra.get_module_symbols(rope_project, res):
            if (symbol.line, symbol.name) in logger_keys:
                continue
            if symbol.name in c.Infra.SCAN_ALLOWED_TOP_LEVEL:
                continue
            if symbol.kind == "class":
                if symbol.name in c.Infra.DETECTION_CANONICAL_ALIASES:
                    continue
                class_symbols.append(symbol)
                continue
            if symbol.kind == "function":
                _add(symbol, "function", "Utilities")
                continue
            line = lines[symbol.line - 1] if 0 < symbol.line <= len(lines) else ""
            if line.lstrip().startswith("type "):
                _add(symbol, "typealias", "Types")
                continue
            if (
                symbol.kind == "assignment"
                and len(symbol.name) > c.Infra.NAMESPACE_MIN_ALIAS_LENGTH
                and not symbol.name.startswith("_")
                and c.Infra.NAMESPACE_CONSTANT_PATTERN.match(symbol.name)
            ):
                _add(symbol, "constant", "Constants")

        violations.extend(
            cls._detect_ast_loose_objects(
                rope_project=rope_project,
                resource=res,
                file_path=file_path,
                class_stem=class_stem,
            )
        )

        if len(class_symbols) != 1:
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=1,
                    name=file_path.stem,
                    kind="single_class",
                    suggestion=f"{class_stem}Utilities",
                )
            )

        return violations

    @classmethod
    def _detect_ast_loose_objects(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        file_path: Path,
        class_stem: str,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect loose Final/collection/Enum/TypeVar objects via rope AST."""
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS:
            return []
        tree = pymodule.get_ast()
        if tree is None:
            return []
        file_str = str(file_path)
        seen: set[tuple[int, str]] = set()
        violations: list[m.Infra.LooseObjectViolation] = []

        def _add_violation(
            line: int,
            name: str,
            kind: str,
            suffix: str,
        ) -> None:
            key = (line, name)
            if key in seen:
                return
            seen.add(key)
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=line,
                    name=name,
                    kind=kind,
                    suggestion=f"{class_stem}{suffix}",
                )
            )

        body = getattr(tree, "body", []) or []
        for node in body:
            cls._inspect_module_level_node(
                node=node,
                file_path=file_path,
                add=_add_violation,
            )

        return violations

    @classmethod
    def _inspect_module_level_node(
        cls,
        *,
        node: object,
        file_path: Path,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Inspect one module-level AST node for loose objects."""
        kind = FlextInfraUtilitiesRopeAnalysis.node_kind(node)
        if kind == "AnnAssign":
            cls._check_loose_final(node, add)
            return
        if kind == "Assign":
            cls._check_loose_collection_or_typevar(node, add)
            return
        if kind == "TypeAlias":
            cls._check_loose_typealias(node, add)
            return
        if kind == "ClassDef":
            cls._check_loose_enum(node, file_path, add)
            cls._check_loose_classvar(node, file_path, add)
            return

    @classmethod
    def _annotation_contains(cls, annotation: object | None, name: str) -> bool:
        """Return True when ``name`` appears in any sub-node identifier."""
        if annotation is None:
            return False
        for sub in FlextInfraUtilitiesRopeAnalysis.walk_ast_nodes(annotation):
            if FlextInfraUtilitiesRopeAnalysis.name_of(sub) == name:
                return True
        return False

    @classmethod
    def _target_name(cls, target: object | None) -> str:
        """Return ``target.id`` when ``target`` is a ``Name`` node."""
        if target is None:
            return ""
        if FlextInfraUtilitiesRopeAnalysis.node_kind(target) != "Name":
            return ""
        identifier = getattr(target, "id", "")
        return identifier if isinstance(identifier, str) else ""

    @classmethod
    def _call_name(cls, func: object | None) -> str:
        """Return the trailing identifier of a call's callable."""
        if func is None:
            return ""
        kind = FlextInfraUtilitiesRopeAnalysis.node_kind(func)
        if kind == "Name":
            value: str = getattr(func, "id", "")
            return value
        if kind == "Attribute":
            return getattr(func, "attr", "")
        if kind == "Call":
            return cls._call_name(getattr(func, "func", None))
        return ""

    @classmethod
    def _base_text_set(cls, cls_node: object) -> set[str]:
        """Render every base of a class as the trailing identifier text."""
        bases = getattr(cls_node, "bases", []) or []
        return {cls._call_name(base) for base in bases if cls._call_name(base)}

    @classmethod
    def _check_loose_final(
        cls,
        node: object,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag bare ``X: Final = ...`` outside canonical constants files."""
        if cls._annotation_contains(getattr(node, "annotation", None), "Final"):
            return
        target = cls._target_name(getattr(node, "target", None))
        if target and not target.startswith("_"):
            add(
                getattr(node, "lineno", 1),
                target,
                "final",
                "Constants",
            )

    @classmethod
    def _check_loose_collection_or_typevar(
        cls,
        node: object,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag collection/TypeVar assignments outside canonical files."""
        value = getattr(node, "value", None)
        if FlextInfraUtilitiesRopeAnalysis.node_kind(value) != "Call":
            return
        func_name = cls._call_name(getattr(value, "func", None))
        targets = getattr(node, "targets", []) or []
        target_name = cls._target_name(targets[0]) if targets else ""
        if not target_name:
            return
        if target_name in c.Infra.DUNDER_ALLOWED or target_name in c.Infra.ALIAS_NAMES:
            return
        if func_name in c.Infra.COLLECTION_CALLS:
            add(
                getattr(node, "lineno", 1),
                target_name,
                "collection",
                "Constants",
            )
            return
        if func_name in c.Infra.TYPEVAR_CALLABLES:
            add(
                getattr(node, "lineno", 1),
                target_name,
                "typevar",
                "Types",
            )

    @classmethod
    def _check_loose_typealias(
        cls,
        node: object,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag bare PEP 695 ``type X = ...`` outside typings.py."""
        name_node = getattr(node, "name", None)
        name_str = getattr(name_node, "id", str(name_node)) if name_node else "unknown"
        add(
            getattr(node, "lineno", 1),
            name_str,
            "typealias",
            "Types",
        )

    @classmethod
    def _check_loose_enum(
        cls,
        node: object,
        file_path: Path,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag inner ``Enum``-derived classes outside the constants tree."""
        if file_path.name == c.Infra.CONSTANTS_PY:
            return
        if file_path.parent.name == "_constants":
            return
        body = getattr(node, "body", []) or []
        for inner in body:
            if FlextInfraUtilitiesRopeAnalysis.node_kind(inner) != "ClassDef":
                continue
            inner_bases = cls._base_text_set(inner)
            if any(base in c.Infra.ENUM_BASES for base in inner_bases):
                add(
                    getattr(inner, "lineno", 1),
                    getattr(inner, "name", "unknown"),
                    "enum",
                    "Constants",
                )

    @classmethod
    def _check_loose_classvar(
        cls,
        node: object,
        file_path: Path,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag ``ClassVar[...] = ...`` attributes outside Constants classes."""
        if file_path.name == c.Infra.CONSTANTS_PY:
            return
        if file_path.parent.name == "_constants":
            return
        class_name = getattr(node, "name", "")
        if isinstance(class_name, str) and class_name.endswith(
            c.Infra.CONSTANTS_CLASS_SUFFIX,
        ):
            return
        base_names = cls._base_text_set(node)
        if any(base.endswith(c.Infra.CONSTANTS_CLASS_SUFFIX) for base in base_names):
            return
        body = getattr(node, "body", []) or []
        for inner in body:
            if FlextInfraUtilitiesRopeAnalysis.node_kind(inner) != "AnnAssign":
                continue
            annotation = getattr(inner, "annotation", None)
            if not cls._annotation_contains(annotation, "ClassVar"):
                continue
            target = cls._target_name(getattr(inner, "target", None))
            if not target or target.startswith("_"):
                continue
            if target in c.Infra.CLASSVAR_EXEMPT_NAMES:
                continue
            if not c.Infra.NAMESPACE_CONSTANT_PATTERN.match(target):
                continue
            if not cls._classvar_value_permitted(getattr(inner, "value", None)):
                continue
            add(
                getattr(inner, "lineno", 1),
                target,
                "classvar",
                "Constants",
            )

    @classmethod
    def _classvar_value_permitted(cls, value: object | None) -> bool:
        """Return True when a ClassVar default is a literal/canonical constant.

        Permits literals, attributes/imports from constants, and calls to
        canonical constant factories (Path, frozenset, tuple, dict,
        MappingProxyType). Rejects calls that build runtime/infrastructure
        objects (context vars, config objects, adapters, etc.).
        """
        if value is None:
            return True
        kind = FlextInfraUtilitiesRopeAnalysis.node_kind(value)
        if kind in {"Constant", "Name", "Attribute", "Tuple", "List", "Set", "Dict"}:
            return True
        if kind == "Call":
            func = getattr(value, "func", None)
            func_name = cls._call_name(func)
            if func_name in c.Infra.CLASSVAR_ALLOWED_CALLS:
                return True
            if FlextInfraUtilitiesRopeAnalysis.node_kind(func) == "Attribute":
                base = getattr(func, "value", None)
                base_name = getattr(base, "id", "")
                return base_name in c.Infra.CLASSVAR_ALLOWED_CALLS
        return False

    @staticmethod
    def _detect_logger_assignments(
        *,
        lines: t.StrSequence,
        file_str: str,
        class_stem: str,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect top-level logger assignments directly from module source."""
        return tuple(
            m.Infra.LooseObjectViolation(
                file=file_str,
                line=line_number,
                name=match.group(1),
                kind="logger",
                suggestion=f"{class_stem}Utilities",
            )
            for line_number, line in enumerate(lines, start=1)
            if (match := c.Infra.LOGGER_ASSIGN_RE.match(line))
        )


__all__: list[str] = ["FlextInfraLooseObjectDetector"]
