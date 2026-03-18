from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import m, p, u
from flext_infra.refactor._detectors.module_loader import (
    DetectorScanResultBuilder,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class CompatibilityAliasDetector(p.Infra.Scanner):
    """Detect compatibility alias assignments that may be removable."""

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
            rule_id="namespace.compatibility_alias",
            violations=violations,
            message_builder=lambda violation: (
                f"Compatibility alias '{violation.alias_name}' -> "
                f"'{violation.target_name}'"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.CompatibilityAliasViolation]:
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
    ) -> list[nem.CompatibilityAliasViolation]:
        """Scan a file for compatibility aliases that may be removable."""
        if file_path.suffix != ".py":
            return []
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        violations: list[nem.CompatibilityAliasViolation] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if not isinstance(stmt.value, ast.Name):
                continue
            alias_name = target.id
            target_name = stmt.value.id
            if len(alias_name) == 1:
                continue
            if alias_name in {"__all__", "__version__", "__version_info__"}:
                continue
            if alias_name == target_name:
                continue
            if alias_name.isupper() and target_name.isupper():
                continue
            if alias_name[0].isupper() and target_name[0].isupper():
                violations.append(
                    nem.CompatibilityAliasViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        alias_name=alias_name,
                        target_name=target_name,
                    ),
                )
        return violations
