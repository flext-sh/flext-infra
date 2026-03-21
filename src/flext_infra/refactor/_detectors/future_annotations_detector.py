"""Detector for identifying missing future annotations imports.

This module detects Python files that lack the 'from __future__ import annotations'
statement, which is needed for proper PEP 563 deferred evaluation of annotations.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import p
from flext_infra.models import m
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class FutureAnnotationsDetector(p.Infra.Scanner):
    """Detector for missing future annotations imports.

    Scans Python files to identify those missing the required
    'from __future__ import annotations' statement at the top.
    """

    def __init__(
        self,
        *,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FutureAnnotationsDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for missing future annotations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing violations if future annotations are missing.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=1,
                    message="Missing 'from __future__ import annotations'",
                    severity="error",
                    rule_id="namespace.future_annotations",
                )
                for _violation in violations
            ],
            detector_name=self.__class__.__name__,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.FutureAnnotationsViolation]:
        """Detect missing future annotations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of FutureAnnotationsViolation if missing from the file.

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
    ) -> list[nem.FutureAnnotationsViolation]:
        """Scan a file for missing future annotations import.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List with single FutureAnnotationsViolation if import is missing.

        """
        if file_path.name == "py.typed":
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        if len(tree.body) == 0:
            return []
        simple_statements = list(cls._iter_simple_statements(tree.body))
        if (
            len(tree.body) == 1
            and len(simple_statements) == 1
            and isinstance(simple_statements[0], cst.Expr)
            and isinstance(
                simple_statements[0].value,
                (
                    cst.SimpleString,
                    cst.ConcatenatedString,
                    cst.FormattedString,
                    cst.Integer,
                    cst.Float,
                ),
            )
        ):
            return []
        for stmt in tree.body:
            if isinstance(stmt, cst.SimpleStatementLine) and any(
                isinstance(simple_stmt, cst.ImportFrom)
                and cls._module_to_str(simple_stmt.module) == "__future__"
                and not isinstance(simple_stmt.names, cst.ImportStar)
                and any(
                    isinstance(alias.name, cst.Name)
                    and alias.name.value == "annotations"
                    for alias in simple_stmt.names
                )
                for simple_stmt in stmt.body
            ):
                return []
            if isinstance(stmt, (cst.ClassDef, cst.FunctionDef)):
                break
        return [
            nem.FutureAnnotationsViolation.create(
                file=str(file_path),
            ),
        ]

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
        """Convert a module expression to its dotted string representation.

        Args:
            module: A libcst expression or None to convert to string.

        Returns:
            Dotted module name (e.g., '__future__').

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
    def _iter_simple_statements(
        body: Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
    ) -> Iterator[cst.BaseSmallStatement]:
        """Iterate over simple statements from a module or compound body.

        Args:
            body: Sequence of statement lines or compound statements.

        Yields:
            Individual small statements from simple statement lines.

        """
        for item in body:
            if isinstance(item, cst.SimpleStatementLine):
                yield from item.body
