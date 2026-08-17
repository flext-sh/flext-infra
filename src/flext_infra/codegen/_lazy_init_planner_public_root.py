"""Root public-export decisions for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, t, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import m, p


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    if TYPE_CHECKING:
        lazy_init: m.Infra.LazyInitConfig
        rope_workspace: p.Infra.RopeWorkspaceDsl

    def _filter_public_root_exports(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
    ) -> tuple[set[str], t.MutableLazyAliasMap]:
        """Keep only direct facades in one generated root contract."""
        # Why (mro-27a9e.1, multi-agent): generated __all__ is a projection,
        # never an ABI input. Configured source owners and MRO parents are SSOT.
        module_export_names = {
            name
            for name, target in lazy_map.items()
            if (not target[1] and name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS)
        }
        inherited_facets = self._declared_inherited_facets(context)
        governed_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if self._is_declared_root_export(
                name,
                target,
                root_pkg=context.current_pkg,
                inherited_facets=inherited_facets,
            )
        }
        lazy_map.clear()
        lazy_map.update(governed_lazy_map)
        public_export_names = {
            name
            for name in export_names
            if name in eager_names
            or (
                name in governed_lazy_map
                and self._is_public_root_export(
                    name,
                    governed_lazy_map,
                    root_pkg=context.current_pkg,
                    root_namespace_files=self.lazy_init.root_namespace_files,
                )
            )
        } | module_export_names
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in public_export_names
        }
        return public_export_names, filtered_lazy_map

    @staticmethod
    def _is_declared_root_export(
        name: str,
        target: t.StrPair,
        *,
        root_pkg: str,
        inherited_facets: frozenset[str] | None,
    ) -> bool:
        module_path, attr_name = target
        if (
            not attr_name
            or module_path == root_pkg
            or module_path.startswith(f"{root_pkg}.")
        ):
            return True
        return inherited_facets is None or name in inherited_facets

    def _declared_inherited_facets(
        self, context: m.Infra.LazyInitPackageContext
    ) -> frozenset[str] | None:
        package_entry = self.rope_workspace.package(context.pkg_dir)
        if package_entry is None or package_entry.project_root is None:
            return None
        manifest_path = (
            package_entry.project_root / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        if not manifest_path.is_file():
            return None
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            package_entry.project_root
        )
        if workspace.failure:
            msg = workspace.error or f"invalid workspace manifest: {manifest_path}"
            raise ValueError(msg)
        project = workspace.value.project
        return frozenset(project.inherited_facets if project is not None else ())

    def _is_public_root_export(
        self,
        name: str,
        lazy_map: t.LazyAliasMap,
        *,
        root_pkg: str,
        root_namespace_files: t.StrSequence,
    ) -> bool:
        """Return whether a root-facade export belongs in the external API."""
        if name in c.Infra.PUBLISHED_ALL_EXCLUDE:
            return False
        module_path, attr_name = lazy_map[name]
        if not attr_name:
            return name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS
        if name in c.Infra.ALIAS_NAMES:
            return True
        if name in c.Infra.TEST_RUNTIME_ALIAS_TARGETS:
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
