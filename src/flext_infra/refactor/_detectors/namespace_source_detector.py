from __future__ import annotations

import ast
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p
from flext_infra.refactor._detectors.python_module_loader_mixin import (
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class NamespaceSourceDetector(
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
    p.Infra.Scanner,
):
    """Detect alias imports from wrong source packages."""

    _PROJECT_ALIAS_MAP_CACHE: ClassVar[dict[Path, dict[str, str]]] = {}

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._project_name = project_name
        self._project_root = project_root
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            project_root=self._project_root,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Wrong source for alias '{violation.alias}': "
                        f"'{violation.current_source}' -> '{violation.correct_source}'"
                    ),
                    severity="error",
                    rule_id="namespace.source_alias",
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
        project_root: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.NamespaceSourceViolation]:
        """Scan a file and return typed namespace violations."""
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            project_root=project_root,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        project_root: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.NamespaceSourceViolation]:
        """Scan a file for wrong-source alias imports."""
        if file_path.name == "__init__.py":
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_FILE_TO_FAMILY:
            return []
        parsed = cls._load_python_module(
            file_path,
            stage="namespace-source-scan",
            parse_failures=_parse_failures,
        )
        if parsed is None:
            return []
        _ = project_name
        project_alias_map = cls._build_project_alias_map(
            project_root=project_root,
            _parse_failures=_parse_failures,
        )
        if len(project_alias_map) == 0:
            return []
        violations: list[nem.NamespaceSourceViolation] = []
        for stmt in ast.walk(parsed.tree):
            if not isinstance(stmt, ast.ImportFrom):
                continue
            if stmt.module is None or stmt.level != 0:
                continue
            current_source = stmt.module.split(".", maxsplit=1)[0]
            imported_names = [alias.name for alias in stmt.names if alias.name != "*"]
            current_import = (
                f"from {stmt.module} import {', '.join(imported_names) or '*'}"
            )
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                if alias.asname is not None:
                    continue
                if alias.name not in c.Infra.RUNTIME_ALIAS_NAMES:
                    continue
                if alias.name in c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES:
                    continue
                correct_source = project_alias_map.get(alias.name)
                if correct_source is None:
                    continue
                if current_source == correct_source:
                    continue
                suggested = f"from {correct_source} import {alias.name}"
                violations.append(
                    nem.NamespaceSourceViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        alias=alias.name,
                        current_source=current_source,
                        correct_source=correct_source,
                        current_import=current_import,
                        suggested_import=suggested,
                    ),
                )
        package_name = cls._discover_project_package_name(project_root=project_root)
        if len(package_name) == 0:
            return violations
        for stmt in parsed.tree.body:
            if not isinstance(stmt, ast.ImportFrom) or stmt.module is None:
                continue
            if not stmt.module.startswith(f"{package_name}."):
                continue
            if "._" in stmt.module:
                continue
            for alias_node in stmt.names:
                if alias_node.asname is not None:
                    continue
                if alias_node.name not in project_alias_map:
                    continue
                violations.append(
                    nem.NamespaceSourceViolation.create(
                        file=str(file_path),
                        line=stmt.lineno,
                        alias=alias_node.name,
                        current_source=stmt.module,
                        correct_source=package_name,
                        current_import=f"from {stmt.module} import ...",
                        suggested_import=(
                            f"from {package_name} import {alias_node.name}"
                        ),
                    ),
                )
        return violations

    @classmethod
    def _build_project_alias_map(
        cls,
        *,
        project_root: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> dict[str, str]:
        cached = cls._PROJECT_ALIAS_MAP_CACHE.get(project_root)
        if cached is not None:
            return cached
        package_name = cls._discover_project_package_name(
            project_root=project_root,
        )
        if len(package_name) == 0:
            cls._PROJECT_ALIAS_MAP_CACHE[project_root] = {}
            return {}
        package_dir = (
            project_root / c.Infra.Paths.DEFAULT_SRC_DIR / package_name
        ).resolve()
        alias_map: dict[str, str] = {}
        family_to_file_name: dict[str, str] = {
            family: file_name
            for file_name, family in c.Infra.NAMESPACE_FILE_TO_FAMILY.items()
        }
        for family in c.Infra.FAMILY_SUFFIXES:
            file_name = family_to_file_name.get(family)
            if file_name is None:
                continue
            facade_file = package_dir / file_name
            if not facade_file.is_file():
                continue
            parsed = cls._load_python_module(
                facade_file,
                stage="namespace-source-map",
                parse_failures=_parse_failures,
            )
            if parsed is None:
                continue
            if cls._has_alias_assignment(tree=parsed.tree, alias=family):
                alias_map[family] = package_name
        cls._PROJECT_ALIAS_MAP_CACHE[project_root] = alias_map
        return alias_map

    @staticmethod
    def _discover_project_package_name(*, project_root: Path) -> str:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / "__init__.py").is_file()
        ]
        if len(package_dirs) == 0:
            return ""
        return package_dirs[0].name

    @staticmethod
    def _has_alias_assignment(*, tree: ast.Module, alias: str) -> bool:
        for stmt in tree.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if not isinstance(stmt.value, ast.Name):
                continue
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == alias:
                    return True
        return False
