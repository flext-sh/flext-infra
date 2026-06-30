"""Root public-export decisions for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    if TYPE_CHECKING:
        lazy_init: m.Infra.LazyInitConfig

        @staticmethod
        def _root_public_contract_exports(pkg_dir: Path) -> frozenset[str]: ...

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

    @staticmethod
    def _promote_public_root_eager_aliases(
        *,
        current_pkg: str,
        lazy_map: t.MutableLazyAliasMap,
        eager_imports: t.MutableLazyAliasMap,
    ) -> None:
        """Promote inherited root aliases to eager imports for reentrant loads."""
        current_prefix = f"{current_pkg}."
        for name, target in tuple(lazy_map.items()):
            module_path = target[0]
            if (
                name in c.Infra.ALIAS_NAMES
                and module_path != current_pkg
                and not module_path.startswith(current_prefix)
            ):
                eager_imports[name] = target
                lazy_map.pop(name, None)

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
            public_children,
            dir_exports,
        )
        child_packages_for_lazy = self._child_packages_without_main_export(
            public_children,
            dir_exports,
        )
        public_export_names = {
            name
            for name in export_names
            if name in eager_names
            or name in child_export_names
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
        }
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
        return bool(explicit_public_exports) or bool(
            set(root_namespace_files) & present_files
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
        module_path = lazy_map[name][0]
        if name in c.Infra.ALIAS_NAMES:
            return True
        if "_fixtures" in module_path.split("."):
            return True
        if name in explicit_public_exports:
            return True
        prefix = f"{root_pkg}."
        if not module_path.startswith(prefix):
            return False
        local_module = module_path.removeprefix(prefix)
        if "." in local_module or local_module.startswith("_"):
            return False
        return f"{local_module}.py" in root_namespace_files


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
