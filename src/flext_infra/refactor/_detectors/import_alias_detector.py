from __future__ import annotations

import ast
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class ImportAliasDetector(p.Infra.Scanner):
    """Detect deep import paths that should use top-level aliases."""

    RUNTIME_ALIAS_NAMES_BY_PACKAGE: ClassVar[dict[str, tuple[str, ...]]] = {
        "flext_core": ("c", "m", "r", "t", "u", "p", "d", "e", "h", "s", "x"),
        "flext_infra": ("c", "m", "t", "u", "p"),
    }

    @classmethod
    def _suggest_alias_import(cls, *, package: str, imported_names: list[str]) -> str:
        allowed = cls.RUNTIME_ALIAS_NAMES_BY_PACKAGE.get(package, ())
        allowed_set = set(allowed)
        unique_names = {name for name in imported_names if name in allowed_set}
        ordered_names = [name for name in allowed if name in unique_names]
        return f"from {package} import {', '.join(ordered_names)}"

    @staticmethod
    def _is_facade_or_subclass_file(*, file_path: Path, tree: ast.Module) -> bool:
        family_file_names = set(c.Infra.NAMESPACE_FILE_TO_FAMILY)
        family_file_names.update(c.Infra.NAMESPACE_PROTECTED_FILES)
        if file_path.name in family_file_names:
            return True
        suffixes = tuple(c.Infra.NAMESPACE_FACADE_FAMILIES.values())
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name.endswith(suffixes):
                return True
            for base in stmt.bases:
                if isinstance(base, ast.Name) and base.id.endswith(suffixes):
                    return True
                if isinstance(base, ast.Attribute) and base.attr.endswith(suffixes):
                    return True
        return False

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
                        f"Deep import '{violation.current_import}' should use "
                        f"'{violation.suggested_import}'"
                    ),
                    severity="error",
                    rule_id="namespace.import_alias",
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
    ) -> list[nem.ImportAliasViolation]:
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
    ) -> list[nem.ImportAliasViolation]:
        """Scan a file for deep import paths that should use aliases."""
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return []
        if cls._is_facade_or_subclass_file(file_path=file_path, tree=tree):
            return []
        violations: list[nem.ImportAliasViolation] = []
        for stmt in tree.body:
            if not isinstance(stmt, ast.ImportFrom):
                continue
            if stmt.module is None:
                continue
            if file_path.name == "__init__.py":
                continue
            for prefix in cls.RUNTIME_ALIAS_NAMES_BY_PACKAGE:
                if stmt.module.startswith(prefix + "."):
                    if "._" in stmt.module:
                        continue
                    if any(alias.name == "*" for alias in stmt.names):
                        continue
                    if any(alias.asname is not None for alias in stmt.names):
                        continue
                    imported_names = [alias.name for alias in stmt.names]
                    if len(imported_names) == 0:
                        continue
                    allowed_names = set(
                        cls.RUNTIME_ALIAS_NAMES_BY_PACKAGE.get(prefix, ()),
                    )
                    if not all(name in allowed_names for name in imported_names):
                        continue
                    suggestion = cls._suggest_alias_import(
                        package=prefix,
                        imported_names=imported_names,
                    )
                    import_names = (
                        ", ".join(
                            alias.name for alias in stmt.names if alias.name != "*"
                        )
                        if not any(alias.name == "*" for alias in stmt.names)
                        else "*"
                    )
                    current = f"from {stmt.module} import {import_names}"
                    violations.append(
                        nem.ImportAliasViolation.create(
                            file=str(file_path),
                            line=stmt.lineno,
                            current_import=current,
                            suggested_import=suggestion,
                        ),
                    )
        return violations
