"""Child-package merging for the lazy-init planner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, p, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraCodegenLazyInitPlannerChildrenMixin:
    if TYPE_CHECKING:
        # mro-wkii.17.26 (codex): declare the validated policy supplied by the MRO base.
        lazy_init: m.Infra.LazyInitConfig
        rope_workspace: p.Infra.RopeWorkspaceDsl

        def _package_entry(
            self, pkg_dir: Path
        ) -> p.Infra.RopePackageIndexEntry | None: ...

        def _add(
            self, index: t.MutableLazyAliasMap, name: str, target: t.StrPair
        ) -> None: ...

        def _is_registered_import(
            self, project_root: Path | None, module_name: str
        ) -> bool: ...

    def _merge_children(
        self, pkg_dir: Path, lazy_map: t.MutableLazyAliasMap
    ) -> t.StrSequence:
        """Register direct child packages without flattening their exports."""
        package_entry = self._package_entry(pkg_dir)
        if package_entry is None:
            return ()
        resolved_pkg_dir = pkg_dir.resolve()
        direct: list[str] = []
        for child_dir in package_entry.descendant_child_dirs:
            # mro-pulj (codex): do not merge retired root registries into the
            # inline map that replaces them.
            if child_dir.name in c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES:
                continue
            resolved_child_dir = child_dir.resolve()
            child_init = child_dir / c.Infra.INIT_PY
            if not child_init.is_file():
                continue
            child_entry = self._package_entry(child_dir)
            if child_entry is None or not child_entry.package_name:
                continue
            if resolved_child_dir.parent != resolved_pkg_dir:
                continue
            if self._is_registered_import(
                child_entry.project_root, child_entry.package_name
            ):
                continue
            # mro-wkii.17.26 (codex): privacy controls parent publication;
            # side-effect policy controls only the child's own initializer.
            if child_dir.name.startswith("_"):
                continue
            direct.append(child_entry.package_name)
            self._add(
                lazy_map,
                child_entry.package_name.rsplit(".", maxsplit=1)[-1],
                (child_entry.package_name, ""),
            )
        return tuple(sorted(direct))

    def _is_side_effect_free_package(self, pkg_dir: Path) -> bool:
        """Return whether config forbids eager sibling imports for this package."""
        return pkg_dir.name in self.lazy_init.side_effect_free_packages
