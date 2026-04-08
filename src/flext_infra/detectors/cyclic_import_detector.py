"""Detect cyclic import dependencies in projects via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraCyclicImportDetector:
    """Detect cyclic imports at project level via rope semantic import resolution."""

    @staticmethod
    def _iter_scan_dir_modules(*, scan_dir: Path) -> Sequence[tuple[str, Path]]:
        is_src = scan_dir.name == c.Infra.Paths.DEFAULT_SRC_DIR
        is_pkg = (scan_dir / c.Infra.Files.INIT_PY).is_file()
        modules: list[tuple[str, Path]] = []
        for py_file in u.Infra.iter_directory_python_files(scan_dir):
            mod = FlextInfraCyclicImportDetector._file_to_module(
                py_file,
                scan_dir,
                is_src=is_src,
                is_pkg=is_pkg,
            )
            if mod is not None:
                modules.append((mod, py_file))
        return modules

    @staticmethod
    def _module_imports(
        *,
        rope_project: t.Infra.RopeProject,
        file_path: Path,
        package_roots: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            return set()
        imports: t.Infra.StrSet = set()
        for fqn in u.Infra.get_module_imports(rope_project, resource).values():
            if fqn.split(".", maxsplit=1)[0] in package_roots:
                imports.add(fqn)
        return imports

    @staticmethod
    def _discover_package_roots(scan_dirs: Sequence[Path]) -> set[str]:
        """Discover local package roots for import filtering."""
        package_roots: set[str] = set()
        for sd in scan_dirs:
            if (sd / c.Infra.Files.INIT_PY).is_file():
                package_roots.add(sd.name)
            for entry in sd.iterdir():
                if entry.name.startswith(".") or entry.name == c.Infra.Dunders.PYCACHE:
                    continue
                if entry.is_dir() and (entry / c.Infra.Files.INIT_PY).is_file():
                    package_roots.add(entry.name)
                elif (
                    entry.is_file()
                    and entry.suffix == c.Infra.Extensions.PYTHON
                    and entry.stem != c.Infra.Dunders.INIT
                ):
                    package_roots.add(entry.stem)
        return package_roots

    @staticmethod
    def _file_to_module(
        py_file: Path, scan_dir: Path, *, is_src: bool, is_pkg: bool
    ) -> str | None:
        """Convert a Python file path to a dotted module name."""
        try:
            rel = py_file.relative_to(scan_dir)
        except ValueError:
            return None
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == c.Infra.Dunders.INIT:
            parts = parts[:-1]
        if not parts:
            return None
        base = ".".join(parts)
        if is_src:
            return base
        return f"{scan_dir.name}.{base}" if is_pkg else base

    @classmethod
    def _build_import_graph(
        cls,
        scan_dirs: Sequence[Path],
        rope_project: t.Infra.RopeProject,
        package_roots: t.Infra.StrSet,
    ) -> t.Infra.Pair[MutableMapping[str, t.Infra.StrSet], t.MutableStrMapping]:
        """Build module import graph and file map from scan directories."""
        graph: MutableMapping[str, t.Infra.StrSet] = {}
        file_map: t.MutableStrMapping = {}
        for scan_dir in scan_dirs:
            for module_name, py_file in cls._iter_scan_dir_modules(scan_dir=scan_dir):
                file_map.setdefault(module_name, str(py_file))
                graph.setdefault(module_name, set())
                graph[module_name].update(
                    cls._module_imports(
                        rope_project=rope_project,
                        file_path=py_file,
                        package_roots=package_roots,
                    ),
                )
        return (graph, file_map)

    @classmethod
    def scan_project(
        cls,
        *,
        project_root: Path,
        rope_project: t.Infra.RopeProject,
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.CyclicImportViolation]:
        """Build import graph via rope and detect cycles with topological sort."""
        del _parse_failures
        scan_dirs = [
            project_root / d
            for d in c.Infra.MRO_SCAN_DIRECTORIES
            if (project_root / d).is_dir()
        ]
        if not scan_dirs:
            return []

        package_roots = cls._discover_package_roots(scan_dirs)
        graph, file_map = cls._build_import_graph(
            scan_dirs, rope_project, package_roots
        )

        violations: MutableSequence[m.Infra.CyclicImportViolation] = []
        try:
            list(TopologicalSorter(graph).static_order())
        except CycleError as exc:
            cycle_nodes = exc.args[1] if len(exc.args) > 1 else ()
            if cycle_nodes:
                normalized = tuple(n for n in cycle_nodes if isinstance(n, str))
                violations.append(
                    m.Infra.CyclicImportViolation(
                        cycle=normalized,
                        files=tuple(file_map.get(n, n) for n in normalized),
                    ),
                )
        return violations


__all__ = ["FlextInfraCyclicImportDetector"]
