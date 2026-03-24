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
from typing import ClassVar, override

import libcst as cst
from pydantic import BaseModel

from flext_infra import (
    m,
    p,
    u,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraCompatibilityAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for compatibility alias assignment statements.

    Identifies simple name-to-name assignments that create compatibility aliases,
    particularly those where both names are capitalized (suggesting class aliases).
    """

    _rule_id: ClassVar[str] = "namespace.compatibility_alias"

    def __init__(
        self,
        *,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraCompatibilityAliasDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a compatibility alias violation message.

        Args:
            violation: The violation model with alias_name and target_name fields.

        Returns:
            Human-readable message for the compatibility alias violation.

        """
        fields = violation.model_dump()
        alias_name = fields.get("alias_name", "")
        target_name = fields.get("target_name", "")
        return f"Compatibility alias '{alias_name}' -> '{target_name}'"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect compatibility alias violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of CompatibilityAliasViolation objects found.

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
    ) -> Sequence[m.Infra.CompatibilityAliasViolation]:
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
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.CompatibilityAliasViolation]:
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
        violations: MutableSequence[m.Infra.CompatibilityAliasViolation] = []
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
                    m.Infra.CompatibilityAliasViolation.create(
                        file=str(file_path),
                        line=u.Infra.cst_line_for(node=stmt, positions=positions),
                        alias_name=alias_name,
                        target_name=target_name,
                    ),
                )
        return violations


__all__ = ["FlextInfraCompatibilityAliasDetector"]
