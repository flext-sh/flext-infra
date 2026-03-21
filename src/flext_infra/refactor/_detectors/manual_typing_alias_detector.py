from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

import libcst as cst
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from flext_infra import c, p
from flext_infra.models import m
from flext_infra.refactor._detectors.python_module_loader_mixin import (
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class ManualTypingAliasDetector(
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
    p.Infra.Scanner,
):
    """Detect type aliases defined outside canonical typings files."""

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
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ManualTypingAliasViolation]:
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
    ) -> list[nem.ManualTypingAliasViolation]:
        """Scan a file for type aliases outside canonical locations."""
        _ = _parse_failures
        if file_path.suffix != ".py":
            return []
        if file_path.name in c.Infra.NAMESPACE_CANONICAL_TYPINGS_FILES:
            return []
        if c.Infra.NAMESPACE_CANONICAL_TYPINGS_DIR in file_path.parts:
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        wrapper = MetadataWrapper(tree)
        module = wrapper.module
        positions = wrapper.resolve(PositionProvider)
        violations: list[nem.ManualTypingAliasViolation] = []
        for stmt in module.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            for small_stmt in stmt.body:
                alias_name = cls._type_alias_name(stmt=small_stmt)
                if alias_name:
                    violations.append(
                        nem.ManualTypingAliasViolation.create(
                            file=str(file_path),
                            line=cls._line_for(node=small_stmt, positions=positions),
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
                            line=cls._line_for(node=small_stmt, positions=positions),
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
        if hasattr(cst, "TypeAlias") and isinstance(stmt, cst.TypeAlias):
            return stmt.name.value
        return ""

    @staticmethod
    def _annotation_contains_type_alias(*, annotation: cst.BaseExpression) -> bool:
        if isinstance(annotation, cst.Subscript):
            return ManualTypingAliasDetector._annotation_contains_type_alias(
                annotation=annotation.value,
            )
        return ManualTypingAliasDetector._module_to_str(annotation).endswith(
            "TypeAlias"
        )

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
