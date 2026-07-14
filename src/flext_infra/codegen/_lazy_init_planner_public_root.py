"""Root public-export decisions for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    if TYPE_CHECKING:
        from pathlib import Path

        lazy_init: m.Infra.LazyInitConfig

        # mro-pulj: this implementation is supplied by PublicApiMixin in the MRO.
        def _root_public_contract_exports(self, pkg_dir: Path) -> frozenset[str]: ...

        def _root_direct_import_contract(self, pkg_dir: Path) -> frozenset[str]: ...

        def _public_root_child_packages(
            self,
            child_packages: t.StrSequence,
            dir_exports: t.MappingKV[str, t.LazyAliasMap],
        ) -> t.StrSequence: ...

        def _public_root_child_export_names(
            self,
            child_packages: t.StrSequence,
            dir_exports: t.MappingKV[str, t.LazyAliasMap],
        ) -> frozenset[str]: ...

        def _child_packages_without_main_export(
            self,
            child_packages: t.StrSequence,
            dir_exports: t.MappingKV[str, t.LazyAliasMap],
        ) -> t.StrSequence: ...

        def _excluded_child_lazy_names(
            self,
            child_packages: t.StrSequence,
            allowed_export_names: frozenset[str],
            runtime_lazy_names: frozenset[str],
            dir_exports: t.MappingKV[str, t.LazyAliasMap],
        ) -> t.StrSequence: ...

        def _merged_child_export_names(
            self, child_package: str, dir_exports: t.MappingKV[str, t.LazyAliasMap]
        ) -> frozenset[str]: ...

        @staticmethod
        def _is_internal_root_child_package(child_package: str) -> bool: ...

    def _filter_public_root_exports(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
        child_packages: t.StrSequence,
        dir_exports: t.MappingKV[str, t.LazyAliasMap],
    ) -> tuple[set[str], t.MutableLazyAliasMap, t.StrSequence, t.StrSequence]:
        """Filter a governed root facade while preserving safe child exports."""
        explicit_exports = self._root_public_contract_exports(context.pkg_dir)
        root_contract = self._has_public_root_contract(
            root_namespace_files=self.lazy_init.root_namespace_files,
            explicit_public_exports=explicit_exports,
            present_files=frozenset(path.name for path in context.pkg_dir.iterdir()),
        )
        public_children = self._public_root_child_packages(child_packages, dir_exports)
        child_export_names = self._public_root_child_export_names(
            public_children, dir_exports
        )
        child_packages_for_lazy = self._child_packages_without_main_export(
            public_children, dir_exports
        )
        module_export_names = {
            name
            for name, target in lazy_map.items()
            if (not target[1] and name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS)
        }
        governed_root_export_names = {
            name
            for name in lazy_map
            if self._is_public_root_export(
                name,
                lazy_map,
                root_pkg=context.current_pkg,
                root_namespace_files=self.lazy_init.root_namespace_files,
                explicit_public_exports=explicit_exports,
            )
        }
        internal_children = tuple(
            child_package
            for child_package in child_packages
            if self._is_internal_root_child_package(child_package)
        )
        internal_child_export_names = {
            child_package.rsplit(".", maxsplit=1)[-1]
            for child_package in internal_children
        } | {
            name
            for child_package in internal_children
            for name in self._merged_child_export_names(child_package, dir_exports)
            if name not in governed_root_export_names
        }
        lazy_export_names = frozenset(lazy_map)
        public_export_names = {
            name
            for name in export_names | (explicit_exports & lazy_export_names)
            if (name in explicit_exports or name not in internal_child_export_names)
            and (
                name in eager_names
                or (not explicit_exports and name in child_export_names)
                or (
                    not root_contract
                    or self._is_public_root_export(
                        name,
                        lazy_map,
                        root_pkg=context.current_pkg,
                        root_namespace_files=self.lazy_init.root_namespace_files,
                        explicit_public_exports=explicit_exports,
                    )
                )
            )
        } | module_export_names
        runtime_export_names = public_export_names | {
            name
            for name, target in lazy_map.items()
            if not target[1] and target[0] in child_packages
        }
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in runtime_export_names
        }
        runtime_lazy_names = frozenset(filtered_lazy_map)
        excluded_lazy_names = self._excluded_child_lazy_names(
            child_packages_for_lazy,
            frozenset(public_export_names),
            runtime_lazy_names,
            dir_exports,
        )
        return (
            public_export_names,
            filtered_lazy_map,
            child_packages_for_lazy,
            excluded_lazy_names,
        )

    @staticmethod
    def _has_public_root_contract(
        *,
        root_namespace_files: t.StrSequence,
        explicit_public_exports: frozenset[str],
        present_files: frozenset[str],
    ) -> bool:
        """Return whether a root package uses the governed public facade contract."""
        return (
            bool(explicit_public_exports)
            or bool(set(root_namespace_files) & present_files)
            or any(
                u.Infra.runtime_singleton_export(file_name) is not None
                for file_name in present_files
            )
        )

    @staticmethod
    def _is_public_root_export(
        name: str,
        lazy_map: t.LazyAliasMap,
        *,
        root_pkg: str,
        root_namespace_files: t.StrSequence,
        explicit_public_exports: frozenset[str] = frozenset(),
    ) -> bool:
        """Return whether a root-facade export belongs in the external API."""
        if name in c.Infra.PUBLISHED_ALL_EXCLUDE:
            return False
        if explicit_public_exports:
            return name in explicit_public_exports
        module_path = lazy_map[name][0]
        if name in c.Infra.ALIAS_NAMES:
            return True
        # NOTE (multi-agent): mro-i6nq.10 keeps private descendants out of root ABI.
        prefix = f"{root_pkg}."
        if not module_path.startswith(prefix):
            return False
        local_module = module_path.removeprefix(prefix)
        runtime_singleton_export = u.Infra.runtime_singleton_export(
            f"{local_module}.py"
        )
        if runtime_singleton_export is not None:
            # mro-j47u: explicit module exports are public; consumers subclass the
            # validated loader while sharing the exact singleton identity.
            return True
        if "." in local_module or local_module.startswith("_"):
            return False
        return f"{local_module}.py" in root_namespace_files


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
