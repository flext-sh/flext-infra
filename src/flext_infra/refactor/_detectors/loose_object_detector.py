from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import c, m, p, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

from .namespace_facade_scanner import NamespaceFacadeScanner


class LooseObjectDetector(p.Infra.Scanner):
    """Detect loose top-level objects that should be inside namespace classes."""

    ALLOWED_TOP_LEVEL = frozenset({"__all__", "__version__", "__version_info__"})

    def __init__(
        self,
        *,
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._project_name = project_name
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Loose {violation.kind} '{violation.name}' outside namespace"
                    ),
                    severity="error",
                    rule_id="namespace.loose_object",
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
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.LooseObjectViolation]:
        """Scan a file and return typed namespace violations."""
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.LooseObjectViolation]:
        """Scan a file for loose top-level objects outside namespace classes."""
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        namespace_classes = cls._find_namespace_classes(tree=tree)
        violations: list[nem.LooseObjectViolation] = []
        class_stem = NamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        for stmt in tree.body:
            violation = cls._check_statement(
                stmt=stmt,
                namespace_classes=namespace_classes,
                file_path=file_path,
                class_stem=class_stem,
            )
            if violation is not None:
                violations.append(violation)
        return violations

    @classmethod
    def _check_statement(
        cls,
        *,
        stmt: ast.stmt,
        namespace_classes: set[str],
        file_path: Path,
        class_stem: str,
    ) -> nem.LooseObjectViolation | None:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            return None
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            return None
        if isinstance(stmt, ast.If):
            return None
        if isinstance(stmt, ast.ClassDef):
            if stmt.name in namespace_classes:
                return None
            return None
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if stmt.name.startswith("__") and stmt.name.endswith("__"):
                return None
            if stmt.name.startswith("_"):
                return None
            return nem.LooseObjectViolation.create(
                file=str(file_path),
                line=stmt.lineno,
                name=stmt.name,
                kind="function",
                suggestion=f"{class_stem}Utilities",
            )
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            if name in cls.ALLOWED_TOP_LEVEL:
                return None
            if name.startswith("_"):
                return None
            if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                return nem.LooseObjectViolation.create(
                    file=str(file_path),
                    line=stmt.lineno,
                    name=name,
                    kind="constant",
                    suggestion=f"{class_stem}Constants",
                )
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                if name in cls.ALLOWED_TOP_LEVEL:
                    return None
                if len(name) <= c.Infra.NAMESPACE_MIN_ALIAS_LENGTH:
                    return None
                if name.startswith("_"):
                    return None
                if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                    return nem.LooseObjectViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        name=name,
                        kind="constant",
                        suggestion=f"{class_stem}Constants",
                    )
        if isinstance(stmt, ast.TypeAlias):
            name = stmt.name.id if hasattr(stmt.name, "id") else ""
            if name and name not in cls.ALLOWED_TOP_LEVEL:
                return nem.LooseObjectViolation.create(
                    file=str(file_path),
                    line=stmt.lineno,
                    name=name,
                    kind="typealias",
                    suggestion=f"{class_stem}Types",
                )
        return None

    @staticmethod
    def _find_namespace_classes(*, tree: ast.Module) -> set[str]:
        classes: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for suffix in c.Infra.NAMESPACE_FACADE_FAMILIES.values():
                    if node.name.endswith(suffix):
                        classes.add(node.name)
                        break
        return classes
