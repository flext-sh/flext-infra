"""Import cycle detection and resolution for intra-package dependencies.

Extracted from ``_utilities_codegen_constant_transformer.py`` to keep
each codegen module under 400 lines.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from graphlib import CycleError, TopologicalSorter
from itertools import pairwise
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRope,
    c,
    t,
)


class FlextInfraUtilitiesCodegenImportCycles:
    """Detects and resolves intra-package import cycles."""

    @staticmethod
    def break_import_cycles(pkg_dir: Path) -> t.Infra.Pair[bool, t.StrSequence]:
        """Detect and break intra-package import cycles by redirecting to parent."""
        targets = FlextInfraUtilitiesDiscovery.extract_lazy_import_targets(
            pkg_dir / c.Infra.Files.INIT_PY,
        )
        lazy_map: t.StrMapping = {
            alias: mod.rsplit(".", 1)[-1] for alias, mod in targets.items()
        }
        if not lazy_map:
            return False, []

        package_name = pkg_dir.name
        parent_candidates = FlextInfraUtilitiesDiscovery.resolve_parent_constants_mro(
            pkg_dir,
            return_module=True,
        )
        parent_pkg = (
            parent_candidates[0]
            if parent_candidates
            else c.Infra.Packages.CORE_UNDERSCORE
        )
        if parent_pkg.startswith(f"{package_name}.") or parent_pkg == package_name:
            return False, []

        all_changes: MutableSequence[str] = []
        with FlextInfraUtilitiesRope.open_project(pkg_dir) as rope_project:
            resources = {
                py_file.stem: resource
                for py_file in pkg_dir.glob(c.Infra.Extensions.PYTHON_GLOB)
                if py_file.name != c.Infra.Files.INIT_PY
                and (resource := rope_project.find_module(py_file.stem)) is not None
            }
            graph: dict[str, t.Infra.StrSet] = {stem: set() for stem in resources}
            for stem, resource in resources.items():
                for from_import in FlextInfraUtilitiesRope.get_absolute_from_imports(
                    rope_project,
                    resource,
                ):
                    if from_import.module_name != package_name:
                        continue
                    graph[stem].update(
                        target
                        for name, _alias in from_import.names_and_aliases
                        if name != "*"
                        and (target := lazy_map.get(name)) in resources
                        and target != stem
                    )
            try:
                list(TopologicalSorter(graph).static_order())
                return False, []
            except CycleError as exc:
                cycle_nodes = tuple(
                    node
                    for node in (exc.args[1] if len(exc.args) > 1 else ())
                    if isinstance(node, str)
                )
            for source_mod, target_mod in pairwise(cycle_nodes):
                resource = resources.get(source_mod)
                if resource is None:
                    continue
                target_aliases = [
                    alias
                    for alias, mod_stem in lazy_map.items()
                    if mod_stem == target_mod
                    and alias in c.Infra.Detection.CANONICAL_ALIASES
                ]
                if not target_aliases:
                    continue
                updated = FlextInfraUtilitiesRope.relocate_from_import_aliases(
                    rope_project,
                    resource,
                    source_module=package_name,
                    target_module=parent_pkg,
                    aliases=target_aliases,
                    apply=True,
                )
                if updated is None:
                    continue
                all_changes.extend(
                    f"{source_mod}.py: from {package_name} import {alias}"
                    f" -> from {parent_pkg} import {alias}"
                    for alias in target_aliases
                )

        return bool(all_changes), all_changes


__all__ = ["FlextInfraUtilitiesCodegenImportCycles"]
