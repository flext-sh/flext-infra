from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import c, m, p, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class ManualProtocolDetector(p.Infra.Scanner):
    """Detect Protocol classes defined outside canonical protocol files."""

    CANONICAL_FILE_NAMES = c.Infra.NAMESPACE_CANONICAL_PROTOCOL_FILES
    CANONICAL_DIR_NAME = c.Infra.NAMESPACE_CANONICAL_PROTOCOL_DIR

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
                        f"Protocol class '{violation.name}' must be centralized "
                        f"({violation.suggestion})"
                    ),
                    severity="error",
                    rule_id="namespace.manual_protocol",
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
    ) -> list[nem.ManualProtocolViolation]:
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
    ) -> list[nem.ManualProtocolViolation]:
        """Scan a file for Protocol classes outside canonical locations."""
        in_canonical_file = file_path.name in cls.CANONICAL_FILE_NAMES
        in_canonical_dir = cls.CANONICAL_DIR_NAME in file_path.parts
        if in_canonical_file or in_canonical_dir:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        violations: list[nem.ManualProtocolViolation] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if cls.is_protocol_class(stmt):
                violations.append(
                    nem.ManualProtocolViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        name=stmt.name,
                    ),
                )
        return violations

    @staticmethod
    def is_protocol_class(node: ast.ClassDef) -> bool:
        """Return whether the class definition inherits from Protocol."""
        for base_expr in node.bases:
            if isinstance(base_expr, ast.Name) and base_expr.id == "Protocol":
                return True
            if isinstance(base_expr, ast.Attribute) and base_expr.attr == "Protocol":
                return True
            if isinstance(base_expr, ast.Subscript):
                root_expr = base_expr.value
                if isinstance(root_expr, ast.Name) and root_expr.id == "Protocol":
                    return True
                if (
                    isinstance(root_expr, ast.Attribute)
                    and root_expr.attr == "Protocol"
                ):
                    return True
        return False
