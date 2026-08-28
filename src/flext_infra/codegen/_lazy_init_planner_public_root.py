"""Root public-export decisions for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, t, u

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraCodegenLazyInitPlannerPublicRootMixin:
    """Public root-facade export filtering helpers."""

    def _filter_public_root_exports(
        self,
        *,
        context: m.Infra.LazyInitPackageContext,
        export_names: set[str],
        lazy_map: t.MutableLazyAliasMap,
        eager_names: frozenset[str],
    ) -> tuple[set[str], t.MutableLazyAliasMap]:
        governed_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if self._is_public_root_export(name, target, root_pkg=context.current_pkg)
        }
        lazy_map.clear()
        lazy_map.update(governed_lazy_map)
        public_export_names = {
            name
            for name in export_names
            if name in eager_names
            or (name in governed_lazy_map and name not in c.Infra.PUBLISHED_ALL_EXCLUDE)
        }
        filtered_lazy_map = {
            name: target
            for name, target in lazy_map.items()
            if name in public_export_names
        }
        return public_export_names, filtered_lazy_map

    @staticmethod
    def _is_public_root_export(name: str, target: t.StrPair, *, root_pkg: str) -> bool:
        """Publish root owners and every unit alias inherited from a base."""
        if name.startswith("_"):
            return False
        module_path, attr_name = target
        runtime_module = f"{module_path.rsplit('.', maxsplit=1)[-1]}.py"
        if u.Infra.runtime_singleton_export(runtime_module) == name:
            return True
        if module_path == root_pkg:
            return True
        if not module_path.startswith(f"{root_pkg}."):
            return (
                name.isidentifier()
                and name.islower()
                and len(name) <= c.Infra.MAX_ALIAS_LENGTH
            )
        local_parts = tuple(module_path[len(root_pkg) + 1 :].split("."))
        if len(local_parts) != 1 or local_parts[0].startswith("_"):
            return False
        return (
            not attr_name and name in c.Infra.PUBLIC_ROOT_MODULE_EXPORTS
        ) or u.Infra.matches_root_namespace_file(
            f"{local_parts[0]}{c.Infra.EXT_PYTHON}"
        )


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicRootMixin"]
