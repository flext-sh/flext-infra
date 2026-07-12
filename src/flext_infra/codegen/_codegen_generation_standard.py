"""Canonical manifest and thin-initializer rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.typings import t


# mro-i6nq.10: One renderer family replaces every removed legacy init strategy.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin,
):
    """Render the two canonical generated package artifacts."""

    @staticmethod
    def _type_checking_filtered(
        plan: m.Infra.LazyInitPlan,
    ) -> t.LazyAliasMap:
        """Return public static imports not already bound eagerly."""
        source = plan.type_checking_map or plan.lazy_map
        wildcard_modules = frozenset(plan.wildcard_runtime_modules)
        public_exports = frozenset(plan.exports)
        return {
            name: target
            for name, target in source.items()
            if target[0] not in wildcard_modules and name in public_exports
        }

    @classmethod
    def _runtime_import_lines(
        cls,
        plan: m.Infra.LazyInitPlan,
    ) -> str:
        """Render eager and wildcard runtime imports."""
        lines: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(plan.wildcard_runtime_modules))
        ]
        eager_lines: t.MutableSequenceOf[str] = []
        eager_groups = cls._group_imports(plan.eager_dunders)
        previous_top: str | None = None
        for module in sorted(eager_groups, key=str.lower):
            top = module.split(".", maxsplit=1)[0]
            if previous_top is not None and top != previous_top:
                eager_lines.append("")
            parts = tuple(
                cls._format_reexport_import_part(imported_name, export_name)
                for export_name, imported_name in sorted(eager_groups[module])
                if imported_name
            )
            eager_lines.extend(cls._format_import("", module, parts))
            previous_top = top
        if lines and eager_lines:
            lines.append("")
        lines.extend(eager_lines)
        return "\n".join(lines)

    @classmethod
    def _unit_manifest_context(
        cls,
        plan: m.Infra.LazyInitPlan,
    ) -> m.Infra.LazyInitUnitManifestRender:
        """Build a package lazy-manifest context."""
        current_pkg = plan.context.current_pkg
        lazy_entries = cls._build_lazy_entries(
            plan.exports,
            dict(plan.lazy_map),
            (
                current_pkg,
                frozenset(plan.child_packages_for_lazy),
                False,
            ),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        return m.Infra.LazyInitUnitManifestRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            current_pkg=current_pkg,
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            child_module_paths=tuple(
                cls._compact_lazy_module_path(current_pkg, child)
                for child in plan.child_packages_for_lazy
            ),
            excluded_lazy_names=tuple(sorted(plan.excluded_lazy_names)),
            exports=tuple(sorted(plan.exports)),
        )

    @classmethod
    def _root_thin_context(
        cls,
        plan: m.Infra.LazyInitPlan,
    ) -> m.Infra.LazyInitRootThinRender:
        """Build the thin project-root initializer context."""
        current_pkg = plan.context.current_pkg
        type_checking = cls._type_checking_filtered(plan)
        type_checking_lines = (
            cls.generate_type_checking(
                cls._group_imports(type_checking),
                include_flext_types=False,
                child_packages=(),
                local_package_root=current_pkg,
            )
            if type_checking
            else ()
        )
        return m.Infra.LazyInitRootThinRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(current_pkg),
            current_pkg=current_pkg,
            runtime_import_lines=cls._runtime_import_lines(plan),
            type_checking_lines="\n".join(type_checking_lines),
            has_child_paths=bool(plan.child_packages_for_lazy),
        )

    @classmethod
    def _render_unit_manifest(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the root lazy manifest."""
        return cls._render_model(
            c.Infra.TEMPLATE_UNIT_MANIFEST,
            cls._unit_manifest_context(plan),
        )

    @classmethod
    def _render_root_thin(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the thin root initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_ROOT_THIN,
            cls._root_thin_context(plan),
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
