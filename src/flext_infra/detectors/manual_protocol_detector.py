"""Detector for identifying Protocol classes outside canonical locations.

This module detects typing.Protocol subclasses defined outside the canonical
protocol files/directories where they should be centralized for maintainability.

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


class FlextInfraManualProtocolDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for Protocol classes outside canonical locations.

    Scans for typing.Protocol subclasses that are defined outside the canonical
    protocol files/directories where they should be centralized.
    """

    _rule_id: ClassVar[str] = "namespace.manual_protocol"

    CANONICAL_FILE_NAMES = c.Infra.NAMESPACE_CANONICAL_PROTOCOL_FILES
    CANONICAL_DIR_NAME = c.Infra.NAMESPACE_CANONICAL_PROTOCOL_DIR

    def __init__(
        self,
        *,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraManualProtocolDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a protocol placement violation message.

        Args:
            violation: The violation model with name and suggestion fields.

        Returns:
            Human-readable message for the protocol placement violation.

        """
        fields = violation.model_dump()
        name = fields.get("name", "")
        suggestion = fields.get("suggestion", "")
        return f"Protocol class '{name}' must be centralized ({suggestion})"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect protocol placement violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of ManualProtocolViolation objects found.

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
    ) -> Sequence[m.Infra.ManualProtocolViolation]:
        """Detect Protocol classes outside canonical locations.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of ManualProtocolViolation objects found in the file.

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
    ) -> Sequence[m.Infra.ManualProtocolViolation]:
        """Scan a file for Protocol classes outside canonical locations.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of ManualProtocolViolation for each misplaced Protocol found.

        """
        _ = _parse_failures
        in_canonical_file = file_path.name in cls.CANONICAL_FILE_NAMES
        in_canonical_dir = cls.CANONICAL_DIR_NAME in file_path.parts
        if in_canonical_file or in_canonical_dir:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        return [
            m.Infra.ManualProtocolViolation.create(
                file=str(file_path),
                line=u.Infra.cst_line_for(node=stmt, positions=positions),
                name=stmt.name.value,
            )
            for stmt in module.body
            if isinstance(stmt, cst.ClassDef) and cls.is_protocol_class(stmt)
        ]

    @staticmethod
    def is_protocol_class(node: cst.ClassDef) -> bool:
        """Check if a class definition inherits from Protocol.

        Args:
            node: A libcst ClassDef node to inspect.

        Returns:
            True if the class inherits from Protocol, False otherwise.

        """
        for base_arg in node.bases:
            if (
                FlextInfraManualProtocolDetector._base_expr_name(base_arg.value)
                == "Protocol"
            ):
                return True
        return False

    @staticmethod
    def _base_expr_name(base_expr: cst.BaseExpression) -> str:
        """Extract the base class name from a class base expression."""
        return u.Infra.cst_extract_base_name(base_expr)


__all__ = ["FlextInfraManualProtocolDetector"]
