"""Detector for identifying removable compatibility alias assignments.

This module detects simple assignment statements that create compatibility
aliases (e.g., NewName = OldName) which may be candidates for removal after
refactoring.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

import libcst as cst

from flext_infra import (
    FlextInfraNamespaceEnforcerModels as nem,
    p,
    u,
)

if TYPE_CHECKING:
    from flext_infra import m

class FlextInfraCompatibilityAliasDetector(p.Infra.Scanner):
    """Detector for compatibility alias assignment statements.

    Identifies simple name-to-name assignments that create compatibility aliases,
    particularly those where both names are capitalized (suggesting class aliases).
    """

    def __init__(
        self,
        *,
        parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraCompatibilityAliasDetector scanner.

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
        return u.Infra.build_scan_result(
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
        parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.CompatibilityAliasViolation]:
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
        _parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.CompatibilityAliasViolation]:
        """Scan a file for removable compatibility aliases.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of CompatibilityAliasViolation for each alias found.

        """
        if file_path.suffix != ".py":
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        violations: MutableSequence[nem.CompatibilityAliasViolation] = []
        for stmt in u.Infra.cst_iter_simple_statements(module.body):
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
                        line=u.Infra.cst_line_for(node=stmt, positions=positions),
                        alias_name=alias_name,
                        target_name=target_name,
                    ),
                )
        return violations

CompatibilityAliasDetector = FlextInfraCompatibilityAliasDetector

__all__ = ["CompatibilityAliasDetector", "FlextInfraCompatibilityAliasDetector"]
