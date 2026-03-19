from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import m, p
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
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        violations: list[nem.InternalImportViolation] = []
        for stmt in cls._iter_simple_statements(tree.body):
            if not isinstance(stmt, cst.ImportFrom):
                continue
            module_name = cls._module_to_str(stmt.module)
            if module_name == "":
                continue
            if file_path.name == "__init__.py":
                continue
            if isinstance(stmt.names, cst.ImportStar):
                imported_names: list[str] = []
                import_list = "*"
            else:
                imported_names = [
                    cls._module_to_str(alias.name)
                    for alias in stmt.names
                    if cls._module_to_str(alias.name) != ""
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
                    line=0,
                    current_import=current_import,
                    detail=detail,
                ),
            )
        return violations

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
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
        for item in body:
            if isinstance(item, cst.SimpleStatementLine):
                yield from item.body
