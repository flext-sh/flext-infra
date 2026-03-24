"""Detector for identifying imports of private modules or symbols.

This module detects imports that violate encapsulation by importing from
private modules (containing `._`) or importing private symbols (starting with `_`).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import (
    FlextInfraNamespaceEnforcerModels as nem,
    m,
    p,
    t,
    u,
)


class FlextInfraInternalImportDetector(p.Infra.Scanner):
    """Detector for private module and symbol import violations.

    Identifies imports that expose private implementation details by importing
    from private modules or importing symbols with underscore prefixes.
    """

    def __init__(
        self,
        *,
        parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraInternalImportDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for internal import violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected private import violations.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Internal import '{violation.current_import}': "
                        f"{violation.detail}"
                    ),
                    severity="error",
                    rule_id="namespace.internal_import",
                )
                for violation in violations
            ],
            detector_name=self.__class__.__name__,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.InternalImportViolation]:
        """Detect internal import violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of InternalImportViolation objects found in the file.

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
        _parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.InternalImportViolation]:
        """Scan a file for private module or symbol imports.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of InternalImportViolation for each private import found.

        """
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        violations: MutableSequence[nem.InternalImportViolation] = []
        for stmt in u.Infra.cst_iter_simple_statements(module.body):
            if not isinstance(stmt, cst.ImportFrom):
                continue
            module_name = u.Infra.cst_module_to_str(stmt.module)
            if not module_name:
                continue
            if file_path.name == "__init__.py":
                continue
            if isinstance(stmt.names, cst.ImportStar):
                imported_names: t.StrSequence = []
                import_list = "*"
            else:
                imported_names = [
                    imported_name
                    for alias in stmt.names
                    if (imported_name := u.Infra.cst_module_to_str(alias.name))
                ]
                import_list = ", ".join(imported_names) if imported_names else "*"
            current_import = f"from {module_name} import {import_list}"
            has_private_module = "._" in module_name
            has_private_symbol = any(name.startswith("_") for name in imported_names)
            if not (has_private_module or has_private_symbol):
                continue
            detail = (
                "private module import"
                if has_private_module
                else "private symbol import"
            )
            violations.append(
                nem.InternalImportViolation.create(
                    file=str(file_path),
                    line=u.Infra.cst_line_for(node=stmt, positions=positions),
                    current_import=current_import,
                    detail=detail,
                ),
            )
        return violations


__all__ = ["FlextInfraInternalImportDetector"]
