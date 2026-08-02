"""Census parent-package facade-alias inventory + collision detection."""

from __future__ import annotations

import importlib
from collections import defaultdict
from typing import TYPE_CHECKING

from flext_infra import p, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, t


class FlextInfraRefactorCensusInventoryMixin:
    """Governed-parent facade-alias inventory + workspace collision cross-ref.

    Composed into FlextInfraRefactorCensus via inheritance; ``_is_flext_owned``
    is provided by the sibling objects mixin through MRO.
    """

    if TYPE_CHECKING:

        @staticmethod
        def _is_flext_owned(value: p.ModuleOwned) -> bool: ...

    @classmethod
    def _build_parent_inventory(
        cls, workspace_root: Path
    ) -> tuple[t.MappingKV[str, t.StrSequence], t.StrMapping]:
        """Inventory governed-package alias top-level facade names.

        Discovers governed projects via ``u.Infra.projects(workspace_root)``
        (canonical workspace project discovery — SSOT). For each project
        with a discovered canonical import package, imports that package and
        walks dynamic facade aliases at depth 1
        (top-level facade attributes such as ``flext_core.c.Result``).

        Returns ``{symbol_name: (parent_path, ...)}`` so a consumer-defined
        symbol with the same name can be cross-referenced against every
        parent that declares it.

        Only ``type`` instances (classes) are inventoried; method names
        inherited from ABCs (``clear``, ``get``, …) are skipped — every
        mapping class shares them, so they are not collision candidates.

        Filters out attributes whose values' ``__module__`` is not in the
        flext package tree.

        Read-only runtime introspection — NO Rope, NO source-tree walking,
        NO subprocess. Governed-package import failures fail the inventory.
        """
        projects_result = u.Infra.projects(workspace_root)
        if projects_result.failure:
            msg = projects_result.error or "parent inventory project discovery failed"
            raise RuntimeError(msg)
        inventory: dict[str, list[str]] = defaultdict(list)
        package_by_project: dict[str, str] = {}
        for project in projects_result.unwrap():
            pkg_name = project.package_name
            if not pkg_name:
                msg = f"project discovery produced no package identity: {project.name}"
                raise RuntimeError(msg)
            package_by_project[project.name] = pkg_name
            try:
                module = importlib.import_module(pkg_name)
            except ImportError as exc:
                msg = f"failed to import governed package {pkg_name}"
                raise RuntimeError(msg) from exc
            for alias_name, module_name, _ in u.lazy_alias_suffixes(pkg_name):
                if module_name.split(".", 1)[0] != pkg_name:
                    continue
                alias = getattr(module, alias_name, None)
                if alias is None:
                    continue
                for attr in dir(alias):
                    if attr.startswith("_"):
                        continue
                    nested = getattr(alias, attr, None)
                    if (
                        nested is None
                        or not isinstance(nested, p.ModuleOwned)
                        or not cls._is_flext_owned(nested)
                    ):
                        continue
                    if not isinstance(nested, type):
                        continue
                    inventory[attr].append(f"{pkg_name}.{alias_name}.{attr}")
        return (
            {name: tuple(paths) for name, paths in inventory.items()},
            package_by_project,
        )

    @classmethod
    def parent_alias_collisions(
        cls, report: m.Infra.Census.WorkspaceReport, *, workspace_root: Path
    ) -> tuple[tuple[m.Infra.Census.Object, t.StrSequence], ...]:
        """Cross-reference workspace objects against upstream parent inventory.

        Returns ``(symbol, parent_paths)`` pairs where the consumer's
        public symbol name appears on at least one governed parent
        package's dynamically derived facade aliases. Sorted descending by the number of
        matching parent paths (broadest collision surface first).

        Self-references are filtered: a symbol in project ``flext-core``
        whose name matches a symbol on ``flext_core.<alias>.<name>`` is
        the canonical owner, not a duplicate.

        Args:
            report: A ``WorkspaceReport`` produced by ``execute()`` or
                ``_collect_report(...)``. Reusing the existing report
                avoids a second Rope-walk; the inventory is the only new
                I/O.
            workspace_root: Workspace root used to discover governed
                projects (parent packages).

        Returns:
            Tuple of ``(symbol, parent_paths)`` pairs. Empty tuple if
            no collisions are found.

        """
        inventory, package_by_project = cls._build_parent_inventory(workspace_root)
        collisions: list[tuple[m.Infra.Census.Object, t.StrSequence]] = []
        for project_report in report.projects:
            package_name = package_by_project.get(project_report.project)
            if package_name is None:
                msg = (
                    "parent inventory has no package identity for report project: "
                    f"{project_report.project}"
                )
                raise RuntimeError(msg)
            self_pkg_prefix = f"{package_name}."
            for obj in project_report.objects:
                if obj.name.startswith("_"):
                    continue
                parent_paths = inventory.get(obj.name)
                if not parent_paths:
                    continue
                foreign_paths = tuple(
                    path
                    for path in parent_paths
                    if not path.startswith(self_pkg_prefix)
                )
                if not foreign_paths:
                    continue
                collisions.append((obj, foreign_paths))
        collisions.sort(key=lambda entry: -len(entry[1]))
        return tuple(collisions)


__all__: list[str] = ["FlextInfraRefactorCensusInventoryMixin"]
