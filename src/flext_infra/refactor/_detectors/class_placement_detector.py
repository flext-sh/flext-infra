"""Detector for identifying Pydantic model classes outside canonical locations.

This module provides detection of BaseModel subclasses that are defined outside
the standard canonical model files (_models.py, models.py) or _models/ directories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

import libcst as cst
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from flext_infra import c, p
from flext_infra.refactor._detectors.module_loader import DetectorScanResultBuilder
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

if TYPE_CHECKING:
    from flext_infra import m


class ClassPlacementDetector(p.Infra.Scanner):
    """Detector for Pydantic model class placement violations.

    Scans Python files to identify BaseModel subclasses defined outside
    canonical model files (models.py, _models.py) or _models/ directories.
    Enforces namespace consistency by catching models in non-standard locations.
    """

    PYDANTIC_BASE_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "BaseModel",
            "FrozenModel",
            "ArbitraryTypesModel",
            "FrozenStrictModel",
            "FrozenValueModel",
            "TimestampedModel",
        },
    )
    CANONICAL_MODEL_FILES: ClassVar[frozenset[str]] = frozenset(
        {"models.py", "_models.py"},
    )
    CANONICAL_MODEL_DIR: ClassVar[str] = "_models"

    def __init__(
        self,
        *,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the ClassPlacementDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for class placement violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected violations with standardized format.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return DetectorScanResultBuilder.build(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.class_placement",
            violations=violations,
            message_builder=lambda violation: (
                f"Model class '{violation.name}' must be in canonical "
                f"model files ({violation.suggestion})"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ClassPlacementViolation]:
        """Detect class placement violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of ClassPlacementViolation objects found in the file.

        """
        return cls.scan_file_impl(
            file_path=file_path,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ClassPlacementViolation]:
        """Scan a file for BaseModel subclasses outside canonical locations.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of ClassPlacementViolation for each misplaced model class found.

        """
        _ = _parse_failures
        if file_path.name in cls.CANONICAL_MODEL_FILES:
            return []
        if cls.CANONICAL_MODEL_DIR in file_path.parts:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        wrapper = MetadataWrapper(tree)
        module = wrapper.module
        positions = wrapper.resolve(PositionProvider)
        violations: list[nem.ClassPlacementViolation] = []
        for stmt in module.body:
            if not isinstance(stmt, cst.ClassDef):
                continue
            if stmt.name.value.startswith("_"):
                continue
            is_model_class, base_class_name = cls.is_pydantic_model_class(stmt)
            if not is_model_class:
                continue
            violations.append(
                nem.ClassPlacementViolation.create(
                    file=str(file_path),
                    line=cls._line_for(node=stmt, positions=positions),
                    name=stmt.name.value,
                    base_class=base_class_name,
                    suggestion="Move class to models.py/_models.py or _models/",
                ),
            )
        return violations

    @staticmethod
    def is_pydantic_model_class(node: cst.ClassDef) -> tuple[bool, str]:
        """Check if a class definition is a Pydantic model.

        Args:
            node: A libcst ClassDef node to inspect.

        Returns:
            Tuple of (is_pydantic_model, base_class_name) where is_pydantic_model
            is True if the class inherits from a known Pydantic base, and
            base_class_name is the name of the Pydantic base class found.

        """
        for arg in node.bases:
            base_name = ClassPlacementDetector._base_expr_name(arg.value)
            if base_name in ClassPlacementDetector.PYDANTIC_BASE_NAMES:
                return (True, base_name)
        return (False, "")

    @staticmethod
    def _base_expr_name(base_expr: cst.BaseExpression) -> str:
        """Extract the base class name from a class base expression.

        Args:
            base_expr: A libcst expression representing a base class.

        Returns:
            The name of the base class, or empty string if unable to extract.

        """
        if isinstance(base_expr, cst.Subscript):
            return ClassPlacementDetector._base_expr_name(base_expr.value)
        if isinstance(base_expr, cst.Name):
            return base_expr.value
        if isinstance(base_expr, cst.Attribute):
            dotted_name = ClassPlacementDetector._module_to_str(base_expr)
            if "." in dotted_name:
                return dotted_name.rsplit(".", maxsplit=1)[1]
            return dotted_name
        return ""

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
        """Convert a module expression to its dotted string representation.

        Args:
            module: A libcst expression or None to convert to string.

        Returns:
            Dotted string representation of the module (e.g., 'a.b.c').

        """
        if module is None:
            return ""
        if isinstance(module, cst.Name):
            return module.value
        if isinstance(module, cst.Attribute):
            parts: list[str] = []
            current: cst.BaseExpression = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            return ".".join(reversed(parts))
        return ""

    @staticmethod
    def _line_for(
        *,
        node: cst.CSTNode,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> int:
        """Get the line number of a CST node.

        Args:
            node: A libcst node to locate.
            positions: Mapping from CST nodes to their code ranges.

        Returns:
            The line number of the node, or 1 if not found in positions.

        """
        code_range = positions.get(node)
        if code_range is None:
            return 1
        return code_range.start.line
