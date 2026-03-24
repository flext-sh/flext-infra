"""Detector for identifying Pydantic model classes outside canonical locations.

This module provides detection of BaseModel subclasses that are defined outside
the standard canonical model files (_models.py, models.py) or _models/ directories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from pydantic import BaseModel

from flext_infra import (
    c,
    m,
    p,
    u,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraClassPlacementDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for Pydantic model class placement violations.

    Scans Python files to identify BaseModel subclasses defined outside
    canonical model files (models.py, _models.py) or _models/ directories.
    Enforces namespace consistency by catching models in non-standard locations.
    """

    _rule_id: ClassVar[str] = "namespace.class_placement"

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
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraClassPlacementDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a class placement violation message.

        Args:
            violation: The violation model with name and suggestion fields.

        Returns:
            Human-readable message for the class placement violation.

        """
        fields = violation.model_dump()
        name = fields.get("name", "")
        suggestion = fields.get("suggestion", "")
        return f"Model class '{name}' must be in canonical model files ({suggestion})"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect class placement violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of ClassPlacementViolation objects found.

        """
        return type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
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
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
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
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        return [
            m.Infra.ClassPlacementViolation.create(
                file=str(file_path),
                line=u.Infra.cst_line_for(node=stmt, positions=positions),
                name=stmt.name.value,
                base_class=base_class_name,
                suggestion="Move class to models.py/_models.py or _models/",
            )
            for stmt in module.body
            if isinstance(stmt, cst.ClassDef) and not stmt.name.value.startswith("_")
            for is_model_class, base_class_name in [cls.is_pydantic_model_class(stmt)]
            if is_model_class
        ]

    @staticmethod
    def is_pydantic_model_class(node: cst.ClassDef) -> t.Infra.Pair[bool, str]:
        """Check if a class definition is a Pydantic model.

        Args:
            node: A libcst ClassDef node to inspect.

        Returns:
            Tuple of (is_pydantic_model, base_class_name) where is_pydantic_model
            is True if the class inherits from a known Pydantic base, and
            base_class_name is the name of the Pydantic base class found.

        """
        for arg in node.bases:
            base_name = FlextInfraClassPlacementDetector._base_expr_name(arg.value)
            if base_name in FlextInfraClassPlacementDetector.PYDANTIC_BASE_NAMES:
                return (True, base_name)
        return (False, "")

    @staticmethod
    def _base_expr_name(base_expr: cst.BaseExpression) -> str:
        """Extract the base class name from a class base expression."""
        return u.Infra.cst_extract_base_name(base_expr)


__all__ = ["FlextInfraClassPlacementDetector"]
