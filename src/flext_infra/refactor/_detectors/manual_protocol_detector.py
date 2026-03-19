from __future__ import annotations

import libcst as cst
from collections.abc import Mapping
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider
from pathlib import Path
from typing import override

from flext_infra import c, m, p
from flext_infra.refactor._detectors.module_loader import (
    DetectorScanResultBuilder,
)
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
        return DetectorScanResultBuilder.build(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.manual_protocol",
            violations=violations,
            message_builder=lambda violation: (
                f"Protocol class '{violation.name}' must be centralized "
                f"({violation.suggestion})"
            ),
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
        _ = _parse_failures
        in_canonical_file = file_path.name in cls.CANONICAL_FILE_NAMES
        in_canonical_dir = cls.CANONICAL_DIR_NAME in file_path.parts
        if in_canonical_file or in_canonical_dir:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        try:
            tree = cst.parse_module(file_path.read_text())
        except cst.ParserSyntaxError:
            return []
        wrapper = MetadataWrapper(tree)
        module = wrapper.module
        positions = wrapper.resolve(PositionProvider)
        violations: list[nem.ManualProtocolViolation] = []
        for stmt in module.body:
            if not isinstance(stmt, cst.ClassDef):
                continue
            if cls.is_protocol_class(stmt):
                violations.append(
                    nem.ManualProtocolViolation.create(
                        file=str(file_path),
                        line=cls._line_for(node=stmt, positions=positions),
                        name=stmt.name.value,
                    ),
                )
        return violations

    @staticmethod
    def is_protocol_class(node: cst.ClassDef) -> bool:
        """Return whether the class definition inherits from Protocol."""
        for base_arg in node.bases:
            if ManualProtocolDetector._base_expr_name(base_arg.value) == "Protocol":
                return True
        return False

    @staticmethod
    def _base_expr_name(base_expr: cst.BaseExpression) -> str:
        if isinstance(base_expr, cst.Subscript):
            return ManualProtocolDetector._base_expr_name(base_expr.value)
        if isinstance(base_expr, cst.Name):
            return base_expr.value
        if isinstance(base_expr, cst.Attribute):
            dotted_name = ManualProtocolDetector._module_to_str(base_expr)
            if "." in dotted_name:
                return dotted_name.rsplit(".", maxsplit=1)[1]
            return dotted_name
        return ""

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
    def _line_for(
        *,
        node: cst.CSTNode,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> int:
        code_range = positions.get(node)
        if code_range is None:
            return 1
        return code_range.start.line
