"""Detector for identifying missing or duplicate runtime alias assignments.

This module detects namespace facade files that are missing or have duplicate
runtime alias assignments (e.g., c = Constants, t = Types).

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
    c,
    m,
    p,
    u,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraRuntimeAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for missing or duplicate runtime alias assignments.

    Identifies namespace facade files that lack or have duplicate runtime alias
    assignments that expose family modules to the namespace.
    """

    _rule_id: ClassVar[str] = "namespace.runtime_alias"

    def __init__(
        self,
        *,
        project_name: str,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraRuntimeAliasDetector scanner.

        Args:
            project_name: Name of the project being scanned.
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures
        self._project_name = project_name

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a runtime alias violation message.

        Args:
            violation: The violation model with alias, kind, and detail fields.

        Returns:
            Human-readable message for the runtime alias violation.

        """
        fields = violation.model_dump()
        alias = fields.get("alias", "")
        kind = fields.get("kind", "")
        detail = fields.get("detail", "")
        return f"Runtime alias '{alias}' {kind}: {detail}"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect runtime alias violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of RuntimeAliasViolation objects found.

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
    ) -> Sequence[m.Infra.RuntimeAliasViolation]:
        """Detect runtime alias violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            project_name: Name of the project being scanned.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of RuntimeAliasViolation objects found in the file.

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
    ) -> Sequence[m.Infra.RuntimeAliasViolation]:
        """Scan a file for missing or duplicate runtime alias assignments.

        Args:
            file_path: Path to the Python file to scan.
            project_name: Name of the project being scanned.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of RuntimeAliasViolation for missing or duplicate aliases.

        """
        if file_path.name not in c.Infra.NAMESPACE_FILE_TO_FAMILY:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        violations: MutableSequence[m.Infra.RuntimeAliasViolation] = []
        _ = project_name
        family = cls._family_for_file(file_name=file_path.name)
        if not family:
            return []
        alias_assignments: MutableSequence[tuple[int, str, str]] = []
        for stmt in u.Infra.cst_iter_simple_statements(tree.body):
            if not isinstance(stmt, cst.Assign):
                continue
            for target in stmt.targets:
                target_expr = target.target
                if not isinstance(target_expr, cst.Name):
                    continue
                if len(target_expr.value) == 1 and isinstance(stmt.value, cst.Name):
                    alias_assignments.append((0, target_expr.value, stmt.value.value))
        expected_alias = family
        matches = [a for a in alias_assignments if a[1] == expected_alias]
        if not matches:
            violations.append(
                m.Infra.RuntimeAliasViolation.create(
                    file=str(file_path),
                    kind="missing",
                    alias=expected_alias,
                    detail=f"No '{expected_alias} = ...' assignment found",
                ),
            )
        elif len(matches) > 1:
            violations.append(
                m.Infra.RuntimeAliasViolation.create(
                    file=str(file_path),
                    line=matches[1][0],
                    kind="duplicate",
                    alias=expected_alias,
                    detail=f"Duplicate alias assignment at lines {', '.join(str(mv[0]) for mv in matches)}",
                ),
            )
        return violations

    @staticmethod
    def _family_for_file(*, file_name: str) -> str:
        """Get the family identifier for a namespace file name.

        Args:
            file_name: The file name to look up.

        Returns:
            The family identifier ('c', 't', 'p', 'm', 'u'), or empty string if not found.

        """
        return c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_name, "")


__all__ = ["FlextInfraRuntimeAliasDetector"]
