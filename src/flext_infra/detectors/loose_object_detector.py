"""Detector for identifying loose top-level objects outside namespace classes.

This module detects module-level objects (functions, constants, type aliases) that
should be organized inside namespace classes following the flext namespace pattern.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from libcst.metadata import CodeRange
from pydantic import BaseModel

from flext_infra import (
    FlextInfraNamespaceFacadeScanner,
    c,
    m,
    p,
    t,
    u,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraLooseObjectDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for loose top-level objects outside namespace classes.

    Identifies module-level functions, constants, and type aliases that should be
    organized inside appropriate namespace classes (e.g., ProjectUtilities, ProjectConstants).
    """

    _rule_id: ClassVar[str] = "namespace.loose_object"

    ALLOWED_TOP_LEVEL = frozenset({"__all__", "__version__", "__version_info__"})

    def __init__(
        self,
        *,
        project_name: str,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraLooseObjectDetector scanner.

        Args:
            project_name: Name of the project being scanned.
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures
        self._project_name = project_name

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a loose object violation message.

        Args:
            violation: The violation model with kind and name fields.

        Returns:
            Human-readable message for the loose object violation.

        """
        fields = violation.model_dump()
        kind = fields.get("kind", "")
        name = fields.get("name", "")
        return f"Loose {kind} '{name}' outside namespace"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect loose object violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of LooseObjectViolation objects found.

        """
        return type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        project_name: str,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        """Detect loose objects in a file.

        Args:
            file_path: Path to the Python file to analyze.
            project_name: Name of the project being scanned.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of LooseObjectViolation objects found in the file.

        """
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        """Scan a file for loose top-level objects outside namespace classes.

        Args:
            file_path: Path to the Python file to scan.
            project_name: Name of the project being scanned.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of LooseObjectViolation for each loose t.NormalizedValue found.

        """
        _ = _parse_failures
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        namespace_classes = cls._find_namespace_classes(tree=module)
        class_stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        return [
            violation
            for stmt in module.body
            if (
                violation := cls._check_statement(
                    stmt=stmt,
                    namespace_classes=namespace_classes,
                    file_path=file_path,
                    class_stem=class_stem,
                    positions=positions,
                )
            )
            is not None
        ]

    @classmethod
    def _check_statement(
        cls,
        *,
        stmt: cst.BaseStatement,
        namespace_classes: t.Infra.StrSet,
        file_path: Path,
        class_stem: str,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> m.Infra.LooseObjectViolation | None:
        """Check a statement for loose objects outside namespace classes.

        Args:
            stmt: The statement to check.
            namespace_classes: Set of existing namespace class names.
            file_path: Path to the file being scanned.
            class_stem: The class stem for suggested namespace classes.
            positions: Mapping of nodes to their code ranges.

        Returns:
            LooseObjectViolation if a loose t.NormalizedValue is found, None otherwise.

        """
        match stmt:
            case cst.SimpleStatementLine():
                for small_stmt in stmt.body:
                    violation = cls._check_small_statement(
                        stmt=small_stmt,
                        file_path=file_path,
                        class_stem=class_stem,
                        positions=positions,
                    )
                    if violation is not None:
                        return violation
                return None
            case cst.If():
                return None
            case cst.ClassDef():
                _ = namespace_classes  # membership check: all paths return None
                return None
            case cst.FunctionDef():
                name = stmt.name.value
                if name.startswith("__") and name.endswith("__"):
                    return None
                if name.startswith("_"):
                    return None
                return m.Infra.LooseObjectViolation.create(
                    file=str(file_path),
                    line=u.Infra.cst_line_for(node=stmt, positions=positions),
                    name=name,
                    kind="function",
                    suggestion=f"{class_stem}Utilities",
                )
            case _:
                return None

    @classmethod
    def _check_small_statement(
        cls,
        *,
        stmt: cst.BaseSmallStatement,
        file_path: Path,
        class_stem: str,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> m.Infra.LooseObjectViolation | None:
        """Check a small statement for loose objects.

        Args:
            stmt: The small statement to check.
            file_path: Path to the file being scanned.
            class_stem: The class stem for suggested namespace classes.
            positions: Mapping of nodes to their code ranges.

        Returns:
            LooseObjectViolation if a loose t.NormalizedValue is found, None otherwise.

        """
        if isinstance(stmt, (cst.Import, cst.ImportFrom)):
            return None
        if isinstance(stmt, cst.Expr) and isinstance(
            stmt.value,
            (cst.SimpleString, cst.ConcatenatedString, cst.Integer),
        ):
            return None
        if isinstance(stmt, cst.AnnAssign) and isinstance(stmt.target, cst.Name):
            name = stmt.target.value
            if name in cls.ALLOWED_TOP_LEVEL:
                return None
            if name.startswith("_"):
                return None
            if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                return m.Infra.LooseObjectViolation.create(
                    file=str(file_path),
                    line=u.Infra.cst_line_for(node=stmt, positions=positions),
                    name=name,
                    kind="constant",
                    suggestion=f"{class_stem}Constants",
                )
        if isinstance(stmt, cst.Assign):
            for assignment_target in stmt.targets:
                target = assignment_target.target
                if not isinstance(target, cst.Name):
                    continue
                name = target.value
                if name in cls.ALLOWED_TOP_LEVEL:
                    return None
                if len(name) <= c.Infra.NAMESPACE_MIN_ALIAS_LENGTH:
                    return None
                if name.startswith("_"):
                    return None
                if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                    return m.Infra.LooseObjectViolation.create(
                        file=str(file_path),
                        line=u.Infra.cst_line_for(node=stmt, positions=positions),
                        name=name,
                        kind="constant",
                        suggestion=f"{class_stem}Constants",
                    )
        name = cls._type_alias_name(stmt=stmt)
        if name and name not in cls.ALLOWED_TOP_LEVEL:
            return m.Infra.LooseObjectViolation.create(
                file=str(file_path),
                line=u.Infra.cst_line_for(node=stmt, positions=positions),
                name=name,
                kind="typealias",
                suggestion=f"{class_stem}Types",
            )
        return None

    @staticmethod
    def _type_alias_name(*, stmt: cst.BaseSmallStatement) -> str:
        """Extract the name of a type alias statement.

        Args:
            stmt: The statement to check for a type alias.

        Returns:
            The name of the type alias, or empty string if not a type alias.

        """
        if hasattr(cst, "TypeAlias") and isinstance(stmt, cst.TypeAlias):
            return stmt.name.value
        if (
            isinstance(stmt, cst.AnnAssign)
            and isinstance(stmt.target, cst.Name)
            and u.Infra.cst_module_to_str(stmt.annotation.annotation) == "TypeAlias"
        ):
            return stmt.target.value
        return ""

    @staticmethod
    def _find_namespace_classes(*, tree: cst.Module) -> t.Infra.StrSet:
        """Find all namespace classes in a module.

        Args:
            tree: The CST module to scan.

        Returns:
            Set of namespace class names found.

        """
        classes: t.Infra.StrSet = set()
        for stmt in tree.body:
            FlextInfraLooseObjectDetector._collect_namespace_classes(
                node=stmt,
                classes=classes,
            )
        return classes

    @staticmethod
    def _collect_namespace_classes(
        *, node: cst.CSTNode, classes: t.Infra.StrSet
    ) -> None:
        """Recursively collect namespace class names from a node.

        Args:
            node: The CST node to inspect.
            classes: Set to accumulate found namespace class names.

        """
        if isinstance(node, cst.ClassDef):
            for suffix in c.Infra.FAMILY_SUFFIXES.values():
                if node.name.value.endswith(suffix):
                    classes.add(node.name.value)
                    break
        for child in node.children:
            FlextInfraLooseObjectDetector._collect_namespace_classes(
                node=child,
                classes=classes,
            )


__all__ = ["FlextInfraLooseObjectDetector"]
