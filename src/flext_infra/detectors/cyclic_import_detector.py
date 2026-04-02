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
    def _discover_package_roots(scan_dirs: Sequence[Path]) -> set[str]:
        """Discover local package roots for import filtering."""
        package_roots: set[str] = set()
        for sd in scan_dirs:
            if (sd / c.Infra.Files.INIT_PY).is_file():
                package_roots.add(sd.name)
            for entry in sd.iterdir():
                if entry.name.startswith(".") or entry.name == "__pycache__":
                    continue
                if entry.is_dir() and (entry / c.Infra.Files.INIT_PY).is_file():
                    package_roots.add(entry.name)
                elif (
                    entry.is_file()
                    and entry.suffix == c.Infra.Extensions.PYTHON
                    and entry.stem != "__init__"
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
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            return None
        base = ".".join(parts)
        if is_src:
            return base
        return f"{scan_dir.name}.{base}" if is_pkg else base

    @staticmethod
    def _build_import_graph(
        scan_dirs: Sequence[Path],
        rope_project: t.Infra.RopeProject,
        package_roots: set[str],
    ) -> t.Infra.Pair[MutableMapping[str, set[str]], t.MutableStrMapping]:
        """Build module import graph and file map from scan directories."""
        graph: MutableMapping[str, set[str]] = {}
        file_map: t.MutableStrMapping = {}
        for sd in scan_dirs:
            is_src = sd.name == c.Infra.Paths.DEFAULT_SRC_DIR
            is_pkg = (sd / c.Infra.Files.INIT_PY).is_file()
            for py_file in u.Infra.iter_directory_python_files(sd):
                mod = FlextInfraCyclicImportDetector._file_to_module(
                    py_file,
                    sd,
                    is_src=is_src,
                    is_pkg=is_pkg,
                )
                if mod is None:
                    continue
                file_map.setdefault(mod, str(py_file))
                graph.setdefault(mod, set())
                res = u.Infra.get_resource_from_path(rope_project, py_file)
                if res is None:
                    continue
                for fqn in u.Infra.get_module_imports(rope_project, res).values():
                    if fqn.split(".")[0] in package_roots:
                        graph[mod].add(fqn)
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
