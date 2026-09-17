"""Alias resolution (local and inherited) for the lazy-init planner."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodegenLazyInitPlannerAliasesMixin:
    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl
        lazy_init: m.Infra.LazyInitConfig
        _parent_package_cache: MutableMapping[str, t.StrSequence]

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

        def _export_names_for_package(self, package_name: str) -> frozenset[str]: ...

        def _package_name_from_target(self, target: str) -> str: ...

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
        """Expose only facade aliases declared by modules in this directory."""
        del surface
        letter_module = {
            letter: filename.removesuffix(".py")
            for filename, letter in c.Infra.NAMESPACE_LAYER_BY_FILE.items()
            if letter in c.Infra.ALIAS_NAMES
        }
        for alias_name, local_stem in letter_module.items():
            if (pkg_dir / f"{local_stem}.py").is_file():
                lazy_map[alias_name] = (f"{current_pkg}.{local_stem}", alias_name)

    def _declared_parent_aliases(self, package_name: str) -> t.StrSequence:
        package_dir = self.rope_workspace.workspace_index.package_dir_by_name.get(
            package_name
        )
        if package_dir is None:
            return ()
        constants_path = package_dir / c.Infra.CONSTANTS_PY
        if self.rope_workspace.resource(constants_path) is None:
            return ()
        state = self.rope_workspace.semantic(constants_path)
        return tuple(state.declared_imports)

    def _declared_parent_aliases_for_directory(self, pkg_dir: Path) -> t.StrSequence:
        constants_path = pkg_dir / c.Infra.CONSTANTS_PY
        if self.rope_workspace.resource(constants_path) is None:
            return ()
        return tuple(self.rope_workspace.semantic(constants_path).declared_imports)

    def _local_parent_packages(self, pkg_dir: Path) -> t.StrSequence:
        constants_path = pkg_dir / c.Infra.CONSTANTS_PY
        if self.rope_workspace.resource(constants_path) is None:
            return ()
        package_entry = self._package_entry(pkg_dir)
        current_name = package_entry.package_name if package_entry is not None else ""
        state = self.rope_workspace.semantic(constants_path)
        return tuple(
            package_name
            for target in state.declared_imports.values()
            if (package_name := self._package_name_from_target(target))
            and package_name != current_name
        )

    def _local_import_alias_targets(self, pkg_dir: Path) -> t.LazyAliasMap:
        constants_path = pkg_dir / c.Infra.CONSTANTS_PY
        if self.rope_workspace.resource(constants_path) is None:
            return {}
        state = self.rope_workspace.semantic(constants_path)
        return {
            alias: (module_path, attribute)
            for alias, target in state.declared_imports.items()
            if alias != target
            if alias != "annotations" and not target.startswith("__future__")
            if (module_path := target.rpartition(".")[0])
            if (attribute := target.rpartition(".")[2])
        }

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
