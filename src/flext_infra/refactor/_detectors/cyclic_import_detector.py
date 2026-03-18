from __future__ import annotations

import ast
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from flext_infra import c, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class CyclicImportDetector:
    """Detect cyclic import dependencies within a project."""

    # NOTE: CyclicImportDetector operates at project level, not file level — does not implement Scanner

    @classmethod
    def scan_project(
        cls,
        *,
        project_root: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.CyclicImportViolation]:
        """Scan a project for cyclic import dependencies."""
        scan_dirs = [
            project_root / directory_name
            for directory_name in c.Infra.MRO_SCAN_DIRECTORIES
            if (project_root / directory_name).is_dir()
        ]
        if len(scan_dirs) == 0:
            return []
        graph: dict[str, set[str]] = {}
        file_map: dict[str, str] = {}
        package_roots = cls._discover_package_roots(scan_dirs=scan_dirs)
        for scan_dir in scan_dirs:
            for py_file in u.Infra.iter_directory_python_files(scan_dir):
                base_module_name = cls._file_to_module(
                    file_path=py_file,
                    src_dir=scan_dir,
                )
                module_name = cls._module_name_for_scan_dir(
                    scan_dir=scan_dir,
                    base_module_name=base_module_name,
                )
                if not module_name:
                    continue
                if module_name not in file_map:
                    file_map[module_name] = str(py_file)
                graph.setdefault(module_name, set())
                tree = u.Infra.parse_module_ast(py_file)
                if tree is None:
                    continue
                for stmt in tree.body:
                    if isinstance(stmt, ast.Import):
                        for alias in stmt.names:
                            imported = alias.name
                            root_pkg = imported.split(".")[0]
                            if root_pkg in package_roots:
                                graph[module_name].add(imported)
                    if isinstance(stmt, ast.ImportFrom) and stmt.module:
                        imported = stmt.module
                        root_pkg = imported.split(".")[0]
                        if root_pkg in package_roots:
                            graph[module_name].add(imported)
        violations: list[nem.CyclicImportViolation] = []
        try:
            _ = list(TopologicalSorter(graph).static_order())
        except CycleError as exc:
            cycle_nodes = exc.args[1] if len(exc.args) > 1 else ()
            if cycle_nodes:
                normalized_cycle = tuple(
                    module_name
                    for module_name in cycle_nodes
                    if isinstance(module_name, str)
                )
                cycle_files = tuple(
                    file_map.get(module_name, module_name)
                    for module_name in normalized_cycle
                )
                violations.append(
                    nem.CyclicImportViolation.create(
                        cycle=normalized_cycle,
                        files=cycle_files,
                    ),
                )
        return violations

    @staticmethod
    def _discover_package_roots(*, scan_dirs: list[Path]) -> set[str]:
        roots: set[str] = set()
        for scan_dir in scan_dirs:
            if (scan_dir / "__init__.py").is_file():
                roots.add(scan_dir.name)
            for entry in scan_dir.iterdir():
                if entry.name.startswith(".") or entry.name == "__pycache__":
                    continue
                if entry.is_dir() and (entry / "__init__.py").is_file():
                    roots.add(entry.name)
                elif (
                    entry.is_file()
                    and entry.suffix == c.Infra.Extensions.PYTHON
                    and entry.stem != "__init__"
                ):
                    roots.add(entry.stem)
        return roots

    @staticmethod
    def _module_name_for_scan_dir(*, scan_dir: Path, base_module_name: str) -> str:
        if not base_module_name:
            return ""
        if scan_dir.name == c.Infra.Paths.DEFAULT_SRC_DIR:
            return base_module_name
        if (scan_dir / "__init__.py").is_file():
            return f"{scan_dir.name}.{base_module_name}"
        return base_module_name

    @staticmethod
    def _file_to_module(*, file_path: Path, src_dir: Path) -> str:
        try:
            rel = file_path.relative_to(src_dir)
        except ValueError:
            return ""
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else ""
