"""Alias resolution (local and inherited) for the lazy-init planner.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, t, u


class FlextInfraCodegenLazyInitPlannerAliasesMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _parent_package_cache: dict[str, t.StrSequence]

        def _source_package_name(self, pkg_dir: Path, inherited_key: str) -> str: ...

        def _module_exports(
            self,
            py_file: Path,
            module_path: str,
            *,
            export_options: m.Infra.ExportOptions | None = None,
        ) -> t.MutableLazyAliasMap: ...

        def _package_entry(
            self, pkg_dir: Path
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def _parents_from_constants_module(
            self, module_path: Path, current_pkg: str, visited: set[str] | None = None
        ) -> t.StrSequence: ...

        def _resolve_inherited_alias_source(
            self,
            package_names: t.StrSequence,
            alias_name: str,
            *,
            current_pkg: str,
            use_test_runtime_aliases: bool,
        ) -> str: ...

    def _resolve_aliases(
        self,
        lazy_map: t.MutableLazyAliasMap,
        *,
        current_pkg: str,
        pkg_dir: Path,
        surface: str,
    ) -> None:
        """Inject inherited and local aliases into the lazy map."""
        is_test_runtime_alias_surface = c.Infra.DIR_TESTS in {
            current_pkg,
            pkg_dir.name,
            surface,
        }
        is_inherited_surface = surface in self.lazy_init.inherited_exports
        if (
            not u.Infra.matches_project_namespace_package(current_pkg)
            and not is_inherited_surface
        ):
            return
        self._resolve_local_aliases(lazy_map, current_pkg=current_pkg, pkg_dir=pkg_dir)
        inherited_key = (
            surface if surface in self.lazy_init.inherited_exports else "src"
        )
        inherited_packages = self._resolve_transitive_parent_packages((
            *self._parent_packages(pkg_dir),
            self._source_package_name(pkg_dir, inherited_key),
        ))
        runtime_alias_names: list[str] = []
        if is_test_runtime_alias_surface:
            runtime_alias_names = list(c.Infra.TEST_RUNTIME_ALIAS_TARGETS)
        alias_names = tuple(
            dict.fromkeys((
                *self.lazy_init.inherited_exports.get(inherited_key, ()),
                *runtime_alias_names,
            ))
        )
        local_alias_names = frozenset(
            alias_name
            for file_name, alias_name in self.lazy_init.public_file_aliases.items()
            if (pkg_dir / file_name).is_file()
        )
        for alias_name in alias_names:
            existing = lazy_map.get(alias_name)
            if (
                existing is not None
                and existing[0].startswith(current_pkg)
                and alias_name in local_alias_names
            ):
                continue
            package_name = self._resolve_inherited_alias_source(
                inherited_packages,
                alias_name,
                current_pkg=current_pkg,
                use_test_runtime_aliases=is_test_runtime_alias_surface,
            )
            if package_name and package_name != current_pkg:
                # mro-pulj (codex): the generated root TYPE_CHECKING contract
                # makes the public package itself the single inherited owner.
                lazy_map[alias_name] = (package_name, alias_name)

    def _resolve_local_aliases(
        self, lazy_map: t.MutableLazyAliasMap, *, current_pkg: str, pkg_dir: Path
    ) -> None:
        """Inject public_file_aliases from the lazy-init config into the lazy map."""
        alias_to_files: dict[str, list[str]] = {}
        for file_name, alias_name in self.lazy_init.public_file_aliases.items():
            alias_to_files.setdefault(alias_name, []).append(file_name)
        for alias_name, file_names in alias_to_files.items():
            existing = lazy_map.get(alias_name)
            if existing is not None and existing[0].startswith(current_pkg):
                continue
            for file_name in file_names:
                base_name = Path(file_name).stem
                module_file = pkg_dir / file_name
                package_dir = pkg_dir / base_name
                module_name = f"{current_pkg}.{base_name}"
                if module_file.is_file() and alias_name in self._module_exports(
                    module_file,
                    module_name,
                    export_options=m.Infra.ExportOptions(allow_assignments=True),
                ):
                    lazy_map[alias_name] = (module_name, alias_name)
                    break
                if package_dir.is_dir() and (package_dir / c.Infra.INIT_PY).is_file():
                    package_exports = self._module_exports(
                        package_dir / c.Infra.INIT_PY,
                        module_name,
                        export_options=m.Infra.ExportOptions(allow_assignments=True),
                    )
                    if alias_name in package_exports:
                        lazy_map[alias_name] = (module_name, alias_name)
                        break

    def _resolve_transitive_parent_packages(
        self, package_names: t.StrSequence
    ) -> t.StrSequence:
        """Return package_names plus transitive parents, ordered nearest-first.

        Breadth-first from the immediate parents outward: a directly declared
        parent (e.g. ``flext_web`` for ``flext_api``) is always resolved before
        its own ancestors (``flext_core`` and its submodules). This guarantees
        an inherited alias is sourced from the nearest owning facade rather than
        falling through to a distant root package that also re-exports it.
        """
        ordered: list[str] = []
        queue: list[str] = list(package_names)
        while queue:
            package_name = queue.pop(0)
            if not package_name or package_name in ordered:
                continue
            ordered.append(package_name)
            package_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
                package_name
            )
            if package_dir is not None:
                queue.extend(self._parent_packages(package_dir))
        return tuple(ordered)

    def _parent_packages(self, pkg_dir: Path) -> t.StrSequence:
        """Return the list of parent package names declared in constants.py."""
        cache_key = str(pkg_dir.resolve())
        cached = self._parent_package_cache.get(cache_key)
        if cached is not None:
            return cached
        package_entry = self._package_entry(pkg_dir)
        current_pkg = package_entry.package_name if package_entry is not None else ""
        constants_path = (pkg_dir / c.Infra.CONSTANTS_PY).resolve()
        if self.rope_workspace.resource(constants_path) is None:
            self._parent_package_cache[cache_key] = ()
            return ()
        parents = self._parents_from_constants_module(constants_path, current_pkg)
        self._parent_package_cache[cache_key] = parents
        return parents

    def _static_module_order(
        self, lazy_map: t.LazyAliasMap, *, current_pkg: str, pkg_dir: Path
    ) -> t.StrSequence:
        """Topologically order local modules from Rope-resolved root alias imports."""
        local_prefix = f"{current_pkg}."
        local_modules = frozenset(
            module for module, _ in lazy_map.values() if module.startswith(local_prefix)
        )
        alias_provider = {
            alias_name: module
            for alias_name, (module, _attribute) in lazy_map.items()
            if module in local_modules
        }
        dependencies: dict[str, set[str]] = {module: set() for module in local_modules}
        for module in local_modules:
            module_path = pkg_dir / f"{module.removeprefix(local_prefix)}.py"
            if not module_path.is_file():
                continue
            for target in self.rope_workspace.semantic(
                module_path
            ).semantic_imports.values():
                direct_provider = next(
                    (
                        provider
                        for provider in local_modules
                        if target == provider or target.startswith(f"{provider}.")
                    ),
                    None,
                )
                if direct_provider is not None and direct_provider != module:
                    dependencies[module].add(direct_provider)
                    continue
                root_prefix = f"{current_pkg}."
                if not target.startswith(root_prefix):
                    continue
                alias_name = target.removeprefix(root_prefix).split(".", maxsplit=1)[0]
                provider = alias_provider.get(alias_name)
                if provider is not None and provider != module:
                    dependencies[module].add(provider)

        ordered: list[str] = []
        remaining = set(local_modules)
        facade_rank = {
            alias_name: index
            for index, alias_name in enumerate(("c", "t", "p", "m", "u"))
        }
        module_rank = {
            module: facade_rank[alias_name]
            for alias_name, module in alias_provider.items()
            if alias_name in facade_rank
        }
        while remaining:
            ready = sorted(
                (
                    module
                    for module in remaining
                    if not (dependencies[module] & remaining)
                ),
                key=lambda module: (
                    module_rank.get(module, len(facade_rank)),
                    module,
                ),
            )
            if not ready:
                ready = [min(remaining)]
            ordered.extend(ready)
            remaining.difference_update(ready)
        return tuple(ordered)
