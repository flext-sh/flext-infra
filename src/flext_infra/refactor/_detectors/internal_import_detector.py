from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import m, p, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class InternalImportDetector(p.Infra.Scanner):
    """Detect imports of private modules or symbols across boundaries."""

    def __init__(
        self,
        *,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
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
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.InternalImportViolation]:
        """Scan a file and return typed namespace violations."""
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
    ) -> list[nem.InternalImportViolation]:
        """Scan a file for private module or symbol imports."""
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        violations: list[nem.InternalImportViolation] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ImportFrom):
                continue
            if stmt.module is None:
                continue
            if file_path.name == "__init__.py":
                continue
            imported_names = [alias.name for alias in stmt.names if alias.name != "*"]
            import_list = ", ".join(imported_names) if imported_names else "*"
            current_import = f"from {stmt.module} import {import_list}"
            has_private_module = "._" in stmt.module
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
                    line=stmt.lineno,
                    current_import=current_import,
                    detail=detail,
                ),
            )
        return violations
