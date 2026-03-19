from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, m, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class RuntimeAliasDetector(p.Infra.Scanner):
    """Detect missing or duplicate runtime alias assignments."""

    def __init__(
        self,
        *,
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._project_name = project_name
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line if violation.line > 0 else 1,
                    message=(
                        f"Runtime alias '{violation.alias}' {violation.kind}: "
                        f"{violation.detail}"
                    ),
                    severity="error",
                    rule_id="namespace.runtime_alias",
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
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.RuntimeAliasViolation]:
        """Scan a file and return typed namespace violations."""
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
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.RuntimeAliasViolation]:
        """Scan a file for missing or duplicate runtime alias assignments."""
        if file_path.name not in c.Infra.NAMESPACE_FILE_TO_FAMILY:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        violations: list[nem.RuntimeAliasViolation] = []
        _ = project_name
        family = cls._family_for_file(file_name=file_path.name)
        if not family:
            return []
        alias_assignments: list[tuple[int, str, str]] = []
        for stmt in cls._iter_simple_statements(tree.body):
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
        if len(matches) == 0:
            violations.append(
                nem.RuntimeAliasViolation.create(
                    file=str(file_path),
                    kind="missing",
                    alias=expected_alias,
                    detail=f"No '{expected_alias} = ...' assignment found",
                ),
            )
        elif len(matches) > 1:
            violations.append(
                nem.RuntimeAliasViolation.create(
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
        return c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_name, "")

    @staticmethod
    def _iter_simple_statements(
        body: Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
    ) -> Iterator[cst.BaseSmallStatement]:
        for item in body:
            if isinstance(item, cst.SimpleStatementLine):
                yield from item.body
