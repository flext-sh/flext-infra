"""Root public-export decisions for the lazy-init planner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, p, t, u


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Publish only symbols owned by direct root modules."""

    if TYPE_CHECKING:
        lazy_init: p.Infra.LazyInitConfig
        rope_workspace: p.Infra.RopeWorkspaceDsl

    def _root_public_contract_exports(self, pkg_dir: Path) -> frozenset[str]:
        """Return the package-root ABI declared by its existing ``__all__``."""
        init_path = pkg_dir / c.Infra.INIT_PY
        if self.rope_workspace.resource(init_path) is None:
            return frozenset()
        source = u.Cli.files_read_text(init_path).unwrap()
        return frozenset(
            u.Infra.module_assignment_strings_source(source, c.Infra.DUNDER_ALL)
        )

    def _filter_public_root_exports(
        self,
        *,
        context: p.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
    ) -> tuple[set[str], t.MutableLazyAliasMap]:
        """Keep direct public owners and reject stale root contracts."""
        # mro-wkii.17.26 (codex): a generated root is output, never an input
        # registry; only a manual root freezes a cutover contract.
        explicit_exports = (
            frozenset()
            if context.generated_init
            else self._root_public_contract_exports(context.pkg_dir)
        )
        if explicit_exports:
            missing_owners = explicit_exports.difference(export_names)
            if missing_owners:
                missing = ", ".join(sorted(missing_owners))
                msg = f"public root contract has no source owner: {missing}"
                raise ValueError(msg)
        module_export_names = {
            name
            for name, target in lazy_map.items()
            if not target[1] and name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS
        }
        public_export_names = {
            name
            for name in export_names
            if name in eager_names
            or (
                name in lazy_map
                and self._is_public_root_export(
                    name,
                    lazy_map,
                    root_pkg=context.current_pkg,
                    root_namespace_files=self.lazy_init.root_namespace_files,
                )
            )
        } | module_export_names
        if explicit_exports:
            public_export_names.intersection_update(explicit_exports)
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in public_export_names
        }
        return public_export_names, filtered_lazy_map

    def _is_public_root_export(
        self,
        name: str,
        lazy_map: t.LazyAliasMap,
        *,
        root_pkg: str,
        root_namespace_files: t.StrSequence,
    ) -> bool:
        """Return whether a root export has one direct canonical owner."""
        if name in c.Infra.PUBLISHED_ALL_EXCLUDE:
            return False
        module_path, attr_name = lazy_map[name]
        if not attr_name:
            return name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS
        if name in c.Infra.ALIAS_NAMES:
            return True
        prefix = f"{root_pkg}."
        if not module_path.startswith(prefix):
            return False
        local_module = module_path.removeprefix(prefix)
        if "." in local_module:
            return False
        runtime_singleton_export = u.Infra.runtime_singleton_export(
            f"{local_module}.py"
        )
        if runtime_singleton_export is not None:
            return name == runtime_singleton_export
        if local_module.startswith("_"):
            return False
        file_name = f"{local_module}.py"
        if file_name not in root_namespace_files:
            return False
        expected_alias = self.lazy_init.public_file_aliases.get(file_name)
        expected_suffix = self.lazy_init.public_file_suffixes.get(file_name)
        if name == expected_alias:
            return True
        if expected_suffix is not None:
            return name.endswith(expected_suffix)
        return True


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
