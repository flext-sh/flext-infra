from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class FutureAnnotationsDetector(p.Infra.Scanner):
    """Detect Python files missing the future annotations import."""

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
                    line=1,
                    message="Missing 'from __future__ import annotations'",
                    severity="error",
                    rule_id="namespace.future_annotations",
                )
                for _violation in violations
            ],
            detector_name=self.__class__.__name__,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.FutureAnnotationsViolation]:
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
    ) -> list[nem.FutureAnnotationsViolation]:
        """Scan a file for missing future annotations import."""
        if file_path.name == "py.typed":
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        if len(tree.body) == 0:
            return []
        simple_statements = list(cls._iter_simple_statements(tree.body))
        if (
            len(tree.body) == 1
            and len(simple_statements) == 1
            and isinstance(simple_statements[0], cst.Expr)
            and isinstance(
                simple_statements[0].value,
                (
                    cst.SimpleString,
                    cst.ConcatenatedString,
                    cst.FormattedString,
                    cst.Integer,
                    cst.Float,
                ),
            )
        ):
            return []
        for stmt in tree.body:
            if isinstance(stmt, cst.SimpleStatementLine) and any(
                isinstance(simple_stmt, cst.ImportFrom)
                and cls._module_to_str(simple_stmt.module) == "__future__"
                and not isinstance(simple_stmt.names, cst.ImportStar)
                and any(
                    isinstance(alias.name, cst.Name)
                    and alias.name.value == "annotations"
                    for alias in simple_stmt.names
                )
                for simple_stmt in stmt.body
            ):
                return []
            if isinstance(stmt, (cst.ClassDef, cst.FunctionDef)):
                break
        return [
            nem.FutureAnnotationsViolation.create(
                file=str(file_path),
            ),
        ]

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
