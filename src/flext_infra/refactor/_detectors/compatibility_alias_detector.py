"""Detector for identifying removable compatibility alias assignments.

This module detects simple assignment statements that create compatibility
aliases (e.g., NewName = OldName) which may be candidates for removal after
refactoring.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

import libcst as cst

from flext_infra import p
from flext_infra.refactor._detectors.module_loader import DetectorScanResultBuilder
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

if TYPE_CHECKING:
    from flext_infra import m


class CompatibilityAliasDetector(p.Infra.Scanner):
    """Detector for compatibility alias assignment statements.

    Identifies simple name-to-name assignments that create compatibility aliases,
    particularly those where both names are capitalized (suggesting class aliases).
    """

    def __init__(
        self,
        *,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the CompatibilityAliasDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for compatibility alias violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected aliases with standardized format.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return DetectorScanResultBuilder.build(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.compatibility_alias",
            violations=violations,
            message_builder=lambda violation: (
                f"Compatibility alias '{violation.alias_name}' -> "
                f"'{violation.target_name}'"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.CompatibilityAliasViolation]:
        """Detect compatibility aliases in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of CompatibilityAliasViolation objects found in the file.

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
    ) -> list[nem.CompatibilityAliasViolation]:
        """Scan a file for removable compatibility aliases.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of CompatibilityAliasViolation for each alias found.

        """
        if file_path.suffix != ".py":
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        violations: list[nem.CompatibilityAliasViolation] = []
        for stmt in cls._iter_simple_statements(tree.body):
            if not isinstance(stmt, cst.Assign):
                continue
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0].target
            if not isinstance(target, cst.Name):
                continue
            if not isinstance(stmt.value, cst.Name):
                continue
            alias_name = target.value
            target_name = stmt.value.value
            if len(alias_name) == 1:
                continue
            if alias_name in {"__all__", "__version__", "__version_info__"}:
                continue
            if alias_name == target_name:
                continue
            if alias_name.isupper() and target_name.isupper():
                continue
            if alias_name[0].isupper() and target_name[0].isupper():
                violations.append(
                    nem.CompatibilityAliasViolation.create(
                        file=str(file_path),
                        line=0,
                        alias_name=alias_name,
                        target_name=target_name,
                    ),
                )
        return violations

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
