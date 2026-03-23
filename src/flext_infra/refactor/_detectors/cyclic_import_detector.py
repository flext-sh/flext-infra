"""Detector for identifying cyclic import dependencies in projects.

This module detects circular import cycles by analyzing import statements
across all Python files in a project and using topological sorting to identify
dependency cycles.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

import libcst as cst

from flext_infra import (
    FlextInfraNamespaceEnforcerModels as nem,
    c,
    u,
)


class CyclicImportDetector:
    """Detector for cyclic import dependencies at project level.

    Analyzes import dependencies across all Python files in a project's source
    directories and identifies circular import cycles using topological sorting.
    Note: This detector operates at project level, not file level.
    """

    # NOTE: CyclicImportDetector operates at project level, not file level — does not implement Scanner

    @classmethod
    def scan_project(
        cls,
        *,
        project_root: Path,
        _parse_failures: Sequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.CyclicImportViolation]:
        """Scan a project for cyclic import dependencies.

        Args:
            project_root: Root directory of the project to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of CyclicImportViolation objects for each cycle detected.

        """
        scan_dirs = [
            project_root / directory_name
            for directory_name in c.Infra.MRO_SCAN_DIRECTORIES
            if (project_root / directory_name).is_dir()
        ]
        if len(scan_dirs) == 0:
            return []
        graph: Mapping[str, set[str]] = {}
        file_map: Mapping[str, str] = {}
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
                tree = u.Infra.parse_module_cst(py_file)
                if tree is None:
                    continue
                for item in tree.body:
                    if isinstance(item, cst.If):
                        test = item.test
                        if isinstance(test, cst.Name) and test.value == "TYPE_CHECKING":
                            continue
                    if isinstance(item, cst.SimpleStatementLine):
                        for stmt in item.body:
                            if isinstance(stmt, cst.Import) and not isinstance(
                                stmt.names,
                                cst.ImportStar,
                            ):
                                for alias in stmt.names:
                                    imported = (
                                        alias.name.value
                                        if isinstance(alias.name, cst.Name)
                                        else u.Infra.cst_module_to_str(alias.name)
                                    )
                                    root_pkg = imported.split(".")[0]
                                    if root_pkg in package_roots:
                                        graph[module_name].add(imported)
                            elif (
                                isinstance(stmt, cst.ImportFrom)
                                and stmt.module is not None
                            ):
                                imported = u.Infra.cst_module_to_str(stmt.module)
                                root_pkg = imported.split(".")[0]
                                if root_pkg in package_roots:
                                    graph[module_name].add(imported)
        violations: Sequence[nem.CyclicImportViolation] = []
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
    def _discover_package_roots(*, scan_dirs: Sequence[Path]) -> set[str]:
        """Discover Python package names from scan directories.

        Args:
            scan_dirs: List of directories to scan for packages.

        Returns:
            Set of package root names found.

        """
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
        """Compute fully qualified module name for a file in a scan directory.

        Args:
            scan_dir: The scan directory being analyzed.
            base_module_name: The base module name relative to the scan directory.

        Returns:
            The fully qualified module name, or empty string if not applicable.

        """
        if not base_module_name:
            return ""
        if scan_dir.name == c.Infra.Paths.DEFAULT_SRC_DIR:
            return base_module_name
        if (scan_dir / "__init__.py").is_file():
            return f"{scan_dir.name}.{base_module_name}"
        return base_module_name

    @staticmethod
    def _file_to_module(*, file_path: Path, src_dir: Path) -> str:
        """Convert a file path to its module name.

        Args:
            file_path: The Python file path to convert.
            src_dir: The source directory root.

        Returns:
            Dotted module name, or empty string if path is not in src_dir.

        """
        try:
            rel = file_path.relative_to(src_dir)
        except ValueError:
            return ""
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else ""
