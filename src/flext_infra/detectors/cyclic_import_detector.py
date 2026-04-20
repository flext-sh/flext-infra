"""Detect cyclic import dependencies in projects via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraCyclicImportDetector:
    """Detect cyclic imports at project level via rope semantic import resolution."""

    @staticmethod
    def scan_project(
        *,
        project_root: Path,
        rope_project: t.Infra.RopeProject,
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.CyclicImportViolation]:
        """Build import graph via rope and detect cycles with topological sort."""
        del _parse_failures
        scan_dirs = [
            (project_root / d).resolve()
            for d in c.Infra.MRO_SCAN_DIRECTORIES
            if (project_root / d).is_dir()
        ]
        if not scan_dirs:
            return []

        module_resources: list[tuple[str, str, t.Infra.RopeResource]] = []
        for resource in rope_project.get_python_files():
            real_path = Path(resource.real_path).resolve()
            if not any(real_path.is_relative_to(scan_dir) for scan_dir in scan_dirs):
                continue
            try:
                module_name = u.Infra.get_pymodule(rope_project, resource).get_name()
            except (*u.Infra.RUNTIME_ERRORS, *u.Infra.SYNTAX_ERRORS, TypeError):
                continue
            if module_name:
                module_resources.append((module_name, str(real_path), resource))

        file_map: t.MutableStrMapping = {
            module_name: file_path for module_name, file_path, _ in module_resources
        }
        graph: dict[str, t.Infra.StrSet] = {module: set() for module in file_map}
        for module_name, _, resource in module_resources:
            for semantic_target in u.Infra.get_semantic_module_imports(
                rope_project,
                resource,
            ).values():
                target_module = semantic_target
                while target_module not in file_map and "." in target_module:
                    target_module = target_module.rsplit(".", maxsplit=1)[0]
                if target_module in file_map:
                    graph[module_name].add(target_module)

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


__all__: list[str] = ["FlextInfraCyclicImportDetector"]
