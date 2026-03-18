from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import c, m, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class ManualTypingAliasDetector(p.Infra.Scanner):
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
        if file_path.suffix != ".py":
            return []
        if file_path.name in c.Infra.NAMESPACE_CANONICAL_TYPINGS_FILES:
            return []
        if c.Infra.NAMESPACE_CANONICAL_TYPINGS_DIR in file_path.parts:
            return []
        from flext_infra.refactor.dependency_analyzer import (
            FlextInfraRefactorDependencyAnalyzerFacade,
        )

        parsed = FlextInfraRefactorDependencyAnalyzerFacade.load_python_module(
            file_path,
            stage="manual-typing-alias-scan",
            parse_failures=_parse_failures,
        )
        if parsed is None:
            return []
        source = parsed.source
        tree = parsed.tree
        violations: list[nem.ManualTypingAliasViolation] = []
        for stmt in tree.body:
            if isinstance(stmt, ast.TypeAlias):
                alias_name = stmt.name.id
                violations.append(
                    nem.ManualTypingAliasViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        name=alias_name,
                        detail="PEP695 alias must be centralized under typings scope",
                    ),
                )
                continue
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                annotation_src = ast.get_source_segment(source, stmt.annotation) or ""
                if "TypeAlias" in annotation_src:
                    violations.append(
                        nem.ManualTypingAliasViolation.create(
                            file=str(file_path),
                            line=stmt.lineno,
                            name=stmt.target.id,
                            detail="TypeAlias assignment must be centralized under typings scope",
                        ),
                    )
        return violations
