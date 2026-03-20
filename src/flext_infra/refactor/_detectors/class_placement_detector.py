from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

import libcst as cst
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from flext_infra import c, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

if TYPE_CHECKING:
    from flext_infra import m


class ClassPlacementDetector(p.Infra.Scanner):
    """Detect BaseModel subclasses outside canonical model files."""

    PYDANTIC_BASE_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "BaseModel",
            "FrozenModel",
            "ArbitraryTypesModel",
            "FrozenStrictModel",
            "FrozenValueModel",
            "TimestampedModel",
        },
    )
    CANONICAL_MODEL_FILES: ClassVar[frozenset[str]] = frozenset(
        {"models.py", "_models.py"},
    )
    CANONICAL_MODEL_DIR: ClassVar[str] = "_models"

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
            rule_id="namespace.class_placement",
            violations=violations,
            message_builder=lambda violation: (
                f"Model class '{violation.name}' must be in canonical "
                f"model files ({violation.suggestion})"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ClassPlacementViolation]:
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
    ) -> list[nem.ClassPlacementViolation]:
        """Scan a file for BaseModel subclasses outside canonical model files."""
        _ = _parse_failures
        if file_path.name in cls.CANONICAL_MODEL_FILES:
            return []
        if cls.CANONICAL_MODEL_DIR in file_path.parts:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        wrapper = MetadataWrapper(tree)
        module = wrapper.module
        positions = wrapper.resolve(PositionProvider)
        violations: list[nem.ClassPlacementViolation] = []
        for stmt in module.body:
            if not isinstance(stmt, cst.ClassDef):
                continue
            if stmt.name.value.startswith("_"):
                continue
            is_model_class, base_class_name = cls.is_pydantic_model_class(stmt)
            if not is_model_class:
                continue
            violations.append(
                nem.ClassPlacementViolation.create(
                    file=str(file_path),
                    line=cls._line_for(node=stmt, positions=positions),
                    name=stmt.name.value,
                    base_class=base_class_name,
                    suggestion="Move class to models.py/_models.py or _models/",
                ),
            )
        return violations

    @staticmethod
    def is_pydantic_model_class(node: cst.ClassDef) -> tuple[bool, str]:
        """Return (is_model, base_class_name) for known Pydantic ancestors."""
        for arg in node.bases:
            base_name = ClassPlacementDetector._base_expr_name(arg.value)
            if base_name in ClassPlacementDetector.PYDANTIC_BASE_NAMES:
                return (True, base_name)
        return (False, "")

    @staticmethod
    def _base_expr_name(base_expr: cst.BaseExpression) -> str:
        if isinstance(base_expr, cst.Subscript):
            return ClassPlacementDetector._base_expr_name(base_expr.value)
        if isinstance(base_expr, cst.Name):
            return base_expr.value
        if isinstance(base_expr, cst.Attribute):
            dotted_name = ClassPlacementDetector._module_to_str(base_expr)
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
