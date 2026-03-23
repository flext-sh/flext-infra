"""Detector for identifying type aliases outside canonical typings locations.

This module detects type alias definitions (TypeAlias, PEP 695) that are located
outside the canonical typing files/directories where they should be centralized.

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
    c,
    m,
    p,
    u,
)


class ManualTypingAliasDetector(
    p.Infra.Scanner,
):
    """Detector for type aliases outside canonical typings locations.

    Identifies PEP 695 type aliases and TypeAlias assignments defined outside
    the canonical typing files/directories where they should be centralized.
    """

    def __init__(
        self,
        *,
        parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the ManualTypingAliasDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for typing alias placement violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected typing alias violations.

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
                    message=f"Typing alias '{violation.name}': {violation.detail}",
                    severity="error",
                    rule_id="namespace.manual_typing_alias",
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
    ) -> Sequence[nem.ManualTypingAliasViolation]:
        """Detect type alias placement violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of ManualTypingAliasViolation objects found in the file.

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
    ) -> Sequence[nem.ManualTypingAliasViolation]:
        """Scan a file for type aliases outside canonical locations.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of ManualTypingAliasViolation for each misplaced alias found.

        """
        _ = _parse_failures
        if file_path.suffix != ".py":
            return []
        if file_path.name in c.Infra.NAMESPACE_CANONICAL_TYPINGS_FILES:
            return []
        if c.Infra.NAMESPACE_CANONICAL_TYPINGS_DIR in file_path.parts:
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            return []
        module, positions = u.Infra.cst_resolve_positions(tree)
        violations: MutableSequence[nem.ManualTypingAliasViolation] = []
        for stmt in module.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            for small_stmt in stmt.body:
                alias_name = cls._type_alias_name(stmt=small_stmt)
                if alias_name:
                    violations.append(
                        nem.ManualTypingAliasViolation.create(
                            file=str(file_path),
                            line=u.Infra.cst_line_for(
                                node=small_stmt, positions=positions
                            ),
                            name=alias_name,
                            detail=(
                                "PEP695 alias must be centralized under typings scope"
                            ),
                        ),
                    )
                    continue
                if (
                    isinstance(small_stmt, cst.AnnAssign)
                    and isinstance(small_stmt.target, cst.Name)
                    and cls._annotation_contains_type_alias(
                        annotation=small_stmt.annotation.annotation,
                    )
                ):
                    violations.append(
                        nem.ManualTypingAliasViolation.create(
                            file=str(file_path),
                            line=u.Infra.cst_line_for(
                                node=small_stmt, positions=positions
                            ),
                            name=small_stmt.target.value,
                            detail=(
                                "TypeAlias assignment must be centralized "
                                "under typings scope"
                            ),
                        ),
                    )
        return violations

    @staticmethod
    def _type_alias_name(*, stmt: cst.BaseSmallStatement) -> str:
        """Extract the name of a PEP 695 type alias statement.

        Args:
            stmt: The statement to check for a type alias.

        Returns:
            The name of the type alias, or empty string if not a type alias.

        """
        if hasattr(cst, "TypeAlias") and isinstance(stmt, cst.TypeAlias):
            return stmt.name.value
        return ""

    @staticmethod
    def _annotation_contains_type_alias(*, annotation: cst.BaseExpression) -> bool:
        """Check if an annotation contains a TypeAlias reference.

        Args:
            annotation: The annotation expression to check.

        Returns:
            True if the annotation references TypeAlias, False otherwise.

        """
        if isinstance(annotation, cst.Subscript):
            return ManualTypingAliasDetector._annotation_contains_type_alias(
                annotation=annotation.value,
            )
        return u.Infra.cst_module_to_str(annotation).endswith("TypeAlias")
