from __future__ import annotations

import ast
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


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
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Model class '{violation.name}' must be in canonical "
                        f"model files ({violation.suggestion})"
                    ),
                    severity="error",
                    rule_id="namespace.class_placement",
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
        if file_path.name in cls.CANONICAL_MODEL_FILES:
            return []
        if cls.CANONICAL_MODEL_DIR in file_path.parts:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        violations: list[nem.ClassPlacementViolation] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name.startswith("_"):
                continue
            is_model_class, base_class_name = cls.is_pydantic_model_class(stmt)
            if not is_model_class:
                continue
            violations.append(
                nem.ClassPlacementViolation.create(
                    file=str(file_path),
                    line=stmt.lineno,
                    name=stmt.name,
                    base_class=base_class_name,
                    suggestion="Move class to models.py/_models.py or _models/",
                ),
            )
        return violations

    @staticmethod
    def is_pydantic_model_class(node: ast.ClassDef) -> tuple[bool, str]:
        """Return (is_model, base_class_name) for known Pydantic ancestors."""
        for base in node.bases:
            if (
                isinstance(base, ast.Name)
                and base.id in ClassPlacementDetector.PYDANTIC_BASE_NAMES
            ):
                return (True, base.id)
            if (
                isinstance(base, ast.Attribute)
                and base.attr in ClassPlacementDetector.PYDANTIC_BASE_NAMES
            ):
                return (True, base.attr)
            if isinstance(base, ast.Subscript):
                val = base.value
                if (
                    isinstance(val, ast.Attribute)
                    and val.attr in ClassPlacementDetector.PYDANTIC_BASE_NAMES
                ):
                    return (True, val.attr)
                if (
                    isinstance(val, ast.Name)
                    and val.id in ClassPlacementDetector.PYDANTIC_BASE_NAMES
                ):
                    return (True, val.id)
        return (False, "")
