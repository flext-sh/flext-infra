"""Import cycle detection and resolution for intra-package dependencies.

Extracted from ``_utilities_codegen_constant_transformer.py`` to keep
each codegen module under 400 lines.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRope,
    c,
    t,
)

_logger = logging.getLogger(__name__)


class FlextInfraUtilitiesCodegenImportCycles:
    """Detects and resolves intra-package import cycles."""

    # CANONICAL_ALIASES centralized in c.Infra.Detection.CANONICAL_ALIASES

    @staticmethod
    def _build_self_import_graph(
        pkg_dir: Path,
        package_name: str,
        lazy_map: t.StrMapping,
    ) -> Mapping[str, t.Infra.StrSet]:
        """Build a dependency graph among modules within the same package."""
        graph: MutableMapping[str, t.Infra.StrSet] = {}
        with FlextInfraUtilitiesRope.open_project(pkg_dir) as rope_project:
            for py_file in pkg_dir.glob(c.Infra.Extensions.PYTHON_GLOB):
                if py_file.name == c.Infra.Files.INIT_PY:
                    continue
                stem = py_file.stem

                res = FlextInfraUtilitiesRope.get_file_resource(
                    rope_project,
                    py_file.name,
                )
                if not res:
                    continue

                try:
                    pymodule = FlextInfraUtilitiesRope.get_pymodule(rope_project, res)
                    mod_imports = (
                        FlextInfraUtilitiesRope.get_module_imports_for_pymodule(
                            rope_project,
                            pymodule,
                        )
                    )
                except Exception:
                    _logger.debug("Failed to parse imports for %s", py_file.name)
                    continue

                deps: t.Infra.StrSet = set()
                for import_stmt in FlextInfraUtilitiesRope.get_import_statements(
                    mod_imports,
                ):
                    from_import = FlextInfraUtilitiesRope.absolute_from_import_any(
                        import_stmt.import_info,
                    )
                    if from_import is None:
                        continue
                    if from_import.module_name != package_name:
                        continue

                    for name, _ in from_import.names_and_aliases:
                        if name == "*":
                            continue
                        target = lazy_map.get(name)
                        if target and target != stem:
                            deps.add(target)

                if deps:
                    graph[stem] = deps
        return graph

    @staticmethod
    def _find_import_cycles(
        graph: Mapping[str, t.Infra.StrSet],
    ) -> Sequence[t.StrSequence]:
        """Detect all cycles in the import graph via DFS."""
        cycles: MutableSequence[t.StrSequence] = []
        visited: t.Infra.StrSet = set()
        path: MutableSequence[str] = []
        path_set: t.Infra.StrSet = set()

        def dfs(node: str) -> None:
            if node in path_set:
                idx = path.index(node)
                cycles.append([*path[idx:], node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in graph.get(node, set()):
                dfs(neighbor)
            path.pop()
            path_set.remove(node)

        for start in graph:
            dfs(start)
        return cycles

    @staticmethod
    def _collect_cycle_edges(
        cycles: Sequence[t.StrSequence],
    ) -> t.Infra.StrPairSet:
        """Extract directed edges from detected cycles."""
        cycle_edges: t.Infra.StrPairSet = set()
        for cycle in cycles:
            edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]
            cycle_edges.update(edges)
        return cycle_edges

    @staticmethod
    def _resolve_target_aliases(
        lazy_map: t.StrMapping,
        target_mod: str,
    ) -> t.StrSequence:
        """Return canonical aliases that resolve to *target_mod* in the lazy map."""
        return [
            alias
            for alias, mod_stem in lazy_map.items()
            if mod_stem == target_mod and alias in c.Infra.Detection.CANONICAL_ALIASES
        ]

    @staticmethod
    def _rewrite_module_imports(
        source_file: Path,
        package_name: str,
        parent_pkg: str,
        target_aliases: t.StrSequence,
    ) -> MutableSequence[str]:
        """Rewrite imports in a module, redirecting cycle aliases to parent using regex."""
        source = source_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        lines = source.splitlines()
        changes: MutableSequence[str] = []
        target_set = frozenset(target_aliases)

        new_lines: list[str] = []

        for line in lines:
            if not line.startswith(f"from {package_name} import "):
                new_lines.append(line)
                continue

            imports_str = line[len(f"from {package_name} import ") :].strip()
            if "(" in imports_str:
                new_lines.append(line)
                continue

            aliases_str = [x.strip() for x in imports_str.split(",")]
            cycle_aliases = [x for x in aliases_str if x in target_set]
            keep_aliases = [x for x in aliases_str if x not in target_set]

            if not cycle_aliases:
                new_lines.append(line)
                continue

            if keep_aliases:
                new_lines.append(
                    f"from {package_name} import {', '.join(keep_aliases)}"
                )

            new_lines.append(f"from {parent_pkg} import {', '.join(cycle_aliases)}")

            changes.append(
                f"from {package_name} import {', '.join(cycle_aliases)}"
                f" \u2192 from {parent_pkg} import {', '.join(cycle_aliases)}",
            )

        if changes:
            source_file.write_text(
                "\\n".join(new_lines) + "\\n", encoding=c.Infra.Encoding.DEFAULT
            )

        return changes

    @staticmethod
    def break_import_cycles(pkg_dir: Path) -> t.Infra.Pair[bool, t.StrSequence]:
        """Detect and break intra-package import cycles by redirecting to parent."""
        cls = FlextInfraUtilitiesCodegenImportCycles
        targets = FlextInfraUtilitiesDiscovery.extract_lazy_import_targets(
            pkg_dir / c.Infra.Files.INIT_PY,
        )
        lazy_map: t.StrMapping = {
            alias: mod.rsplit(".", 1)[-1] for alias, mod in targets.items()
        }
        if not lazy_map:
            return False, []

        package_name = pkg_dir.name
        graph = cls._build_self_import_graph(pkg_dir, package_name, lazy_map)
        cycles = cls._find_import_cycles(graph)
        if not cycles:
            return False, []

        parent_pkg = FlextInfraUtilitiesCodegenConstantDetection.resolve_parent_package(
            pkg_dir,
        )
        if parent_pkg.startswith(f"{package_name}.") or parent_pkg == package_name:
            return False, []

        cycle_edges = cls._collect_cycle_edges(cycles)
        all_changes: MutableSequence[str] = []
        any_modified = False

        for source_mod, target_mod in cycle_edges:
            source_file = pkg_dir / f"{source_mod}.py"
            if not source_file.is_file():
                continue
            target_aliases = cls._resolve_target_aliases(lazy_map, target_mod)
            if not target_aliases:
                continue
            changes = cls._rewrite_module_imports(
                source_file,
                package_name,
                parent_pkg,
                target_aliases,
            )
            if changes:
                any_modified = True
                all_changes.extend(f"{source_mod}.py: {change}" for change in changes)

        return any_modified, all_changes


__all__ = ["FlextInfraUtilitiesCodegenImportCycles"]
