"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import (
    c,
    m,
    t,
    u,
)
from flext_infra._constants.rope import FlextInfraConstantsRope
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class FlextInfraLooseObjectDetector:
    """Detect loose top-level objects outside namespace classes via rope."""

    @classmethod
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        if ctx.project_root is not None and not cls._is_src_file(
            file_path=ctx.file_path,
            project_root=ctx.project_root,
        ):
            return []
        if cls._is_pytest_test_module(ctx.file_path):
            return []
        if cls._is_generated_lazy_registry(ctx.file_path):
            return []
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
            ),
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
                ),
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
            ),
        )

        if not violations and not class_symbols:
            return []
        if len(class_symbols) != 1 and not cls._allows_private_base_module_classes(
            file_path=file_path,
            class_symbols=class_symbols,
        ):
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=1,
                    name=file_path.stem,
                    kind="single_class",
                    suggestion=f"{class_stem}Utilities",
                ),
            )

        return violations

    @classmethod
    def _is_src_file(cls, *, file_path: Path, project_root: Path) -> bool:
        """Return whether the path belongs to the project source tree."""
        try:
            relative_path = file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            return False
        return (
            bool(relative_path.parts)
            and relative_path.parts[0] == c.Infra.DEFAULT_SRC_DIR
        )

    @classmethod
    def _is_generated_lazy_registry(cls, file_path: Path) -> bool:
        """Return whether the file is generated lazy export registry plumbing."""
        root_exports_filename: str = c.Infra.ROOT_EXPORTS_FILENAME
        return file_path.name == root_exports_filename

    @classmethod
    def _is_pytest_test_module(cls, file_path: Path) -> bool:
        """Return whether a file is a pytest module, not a production module."""
        if c.Infra.DIR_TESTS not in file_path.parts:
            return False
        file_name = file_path.name
        return file_name.startswith(
            c.Infra.NAMESPACE_PYTEST_MODULE_PREFIX,
        ) or file_name.endswith(tuple(c.Infra.NAMESPACE_PYTEST_MODULE_SUFFIXES))

    @classmethod
    def _allows_private_base_module_classes(
        cls,
        *,
        file_path: Path,
        class_symbols: t.SequenceOf[m.Infra.SymbolInfo],
    ) -> bool:
        """Return whether a private ``_base.py`` module satisfies MRO contracts."""
        if file_path.name != c.Infra.NAMESPACE_PRIVATE_BASE_MODULE:
            return False
        if not class_symbols:
            return False
        allowed_suffixes = tuple(c.Infra.NAMESPACE_PRIVATE_BASE_CLASS_SUFFIXES)
        return all(
            symbol.name.startswith("_") and symbol.name.endswith(allowed_suffixes)
            for symbol in class_symbols
        )

    @classmethod
    def _detect_ast_loose_objects(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        file_path: Path,
        class_stem: str,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect loose Final/collection/Enum/TypeVar objects via rope structure."""
        _ = rope_project
        statements = u.Infra.logical_statements(resource.read())
        file_str = str(file_path)
        seen: set[tuple[int, str]] = set()
        violations: list[m.Infra.LooseObjectViolation] = []

        def _add(line: int, name: str, kind: str, suffix: str) -> None:
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
                ),
            )

        for statement in statements:
            cls._inspect_statement(
                statement=statement,
                file_path=file_path,
                add=_add,
            )
        return violations

    @classmethod
    def _inspect_statement(
        cls,
        *,
        statement: m.Infra.LogicalStatement,
        file_path: Path,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Inspect one module-level logical statement for loose objects."""
        if statement.enclosing_kind is not c.Infra.RopeScopeKind.MODULE:
            return
        category = statement.category
        if category is c.Infra.StatementCategory.ANN_ASSIGN:
            cls._check_loose_final(statement, add)
        elif category is c.Infra.StatementCategory.ASSIGN:
            cls._check_loose_collection_or_typevar(statement, add)
        elif category is c.Infra.StatementCategory.TYPE_ALIAS:
            cls._check_loose_typealias(statement, add)
        elif category is c.Infra.StatementCategory.CLASS_DEF:
            cls._check_loose_enum(statement, file_path, add)
            cls._check_loose_classvar(statement, file_path, add)

    @classmethod
    def _check_loose_final(
        cls,
        statement: m.Infra.LogicalStatement,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag bare ``X: Final = ...`` outside canonical constants files."""
        if u.Infra.annotation_contains(statement, "Final"):
            return
        target = u.Infra.target_name(statement)
        if target and not target.startswith("_") and target not in c.Infra.ALIAS_NAMES:
            add(statement.line, target, "final", "Constants")

    @classmethod
    def _check_loose_collection_or_typevar(
        cls,
        statement: m.Infra.LogicalStatement,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag collection/TypeVar assignments outside canonical files."""
        callee = u.Infra.call_callee_name(statement)
        if not callee:
            return
        target_name = u.Infra.target_name(statement)
        if not target_name:
            return
        if target_name in c.Infra.DUNDER_ALLOWED or target_name in c.Infra.ALIAS_NAMES:
            return
        if callee in c.Infra.COLLECTION_CALLS:
            add(statement.line, target_name, "collection", "Constants")
            return
        if callee in c.Infra.TYPEVAR_CALLABLES:
            add(statement.line, target_name, "typevar", "Types")

    @classmethod
    def _check_loose_typealias(
        cls,
        statement: m.Infra.LogicalStatement,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag bare PEP 695 ``type X = ...`` outside typings.py."""
        body = statement.text.strip().removeprefix("type").strip()
        name_str = body.split("=", maxsplit=1)[0].split("[", maxsplit=1)[0].strip()
        add(statement.line, name_str or "unknown", "typealias", "Types")

    @classmethod
    def _check_loose_enum(
        cls,
        statement: m.Infra.LogicalStatement,
        file_path: Path,
        add: Callable[[int, str, str, str], None],
    ) -> None:
        """Flag inner ``Enum``-derived classes outside the constants tree."""
        if file_path.name == c.Infra.CONSTANTS_PY:
            return
        if file_path.parent.name == "_constants":
            return
        inner_bases = u.Infra.class_base_names(statement)
        if any(base in c.Infra.ENUM_BASES for base in inner_bases):
            name = statement.enclosing_name or u.Infra.class_header_name(statement)
            add(statement.line, name or "unknown", "enum", "Constants")

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
