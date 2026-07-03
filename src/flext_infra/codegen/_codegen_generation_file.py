"""Top-level generated file strategy selection."""

from __future__ import annotations

from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Select the canonical generation strategy for one package file."""

    @staticmethod
    def generate_file(
        exports: t.StrSequence,
        filtered: t.LazyAliasMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
        eager_imports: t.LazyAliasMap | None = None,
        type_checking_imports: t.LazyAliasMap | None = None,
        wildcard_runtime_modules: t.StrSequence | None = None,
        child_packages_for_lazy: t.StrSequence | None = None,
        excluded_lazy_names: t.StrSequence | None = None,
        registry_wrapper: m.Infra.LazyInitRegistryWrapper | None = None,
    ) -> str:
        """Generate complete module file with lazy imports and type hints."""
        if current_pkg == "flext_core":
            return FlextInfraCodegenGenerationFileMixin._generate_flext_core_root_file()
        if FlextInfraCodegenGenerationFileMixin._uses_direct_bootstrap(current_pkg):
            direct_filtered = filtered
            direct_exports = exports
            if current_pkg == "flext_core._typings":
                direct_filtered = {
                    name: target
                    for name, target in filtered.items()
                    if target[0] == "flext_core._typings.lazy"
                }
                direct_exports = tuple(
                    name for name in exports if name in direct_filtered
                )
            return FlextInfraCodegenGenerationFileMixin._generate_direct_bootstrap_file(
                direct_exports, direct_filtered, inline_constants, current_pkg
            )
        lazy_filtered: t.LazyAliasMap = dict(filtered)
        publish_all = (
            FlextInfraCodegenGenerationFileMixin._is_public_api_root_namespace(
                current_pkg
            )
        )
        published_exports = (
            FlextInfraCodegenGenerationFileMixin._build_published_exports(
                exports, lazy_filtered
            )
            if publish_all
            else tuple(sorted(exports))
        )
        children_lazy = (
            ()
            if FlextInfraCodegenGenerationFileMixin._uses_static_child_map(current_pkg)
            else tuple(child_packages_for_lazy or ())
        )
        rendered_child_module_paths = tuple(
            FlextInfraCodegenGenerationFileMixin._compact_lazy_module_path(
                current_pkg, child_module_path
            )
            for child_module_path in children_lazy
        )
        context = FlextInfraCodegenGenerationFileMixin._standard_render_context(
            current_pkg,
            inline_constants,
            published_exports,
            lazy_filtered,
            FlextInfraCodegenGenerationFileMixin._type_checking_filtered(
                type_checking_imports,
                lazy_filtered,
                frozenset(wildcard_runtime_modules or ()),
                publish_all=publish_all,
                public_export_set=frozenset(published_exports),
            ),
            FlextInfraCodegenGenerationFileMixin._runtime_import_block(
                wildcard_runtime_modules,
                eager_imports or {},
            ),
            children_lazy,
            rendered_child_module_paths,
            tuple(sorted(c.Infra.INFRA_ONLY_EXPORTS | set(excluded_lazy_names or ()))),
        )
        content = FlextInfraCodegenGenerationFileMixin._render_standard_file(context)
        if registry_wrapper is None or (
            not publish_all and len(content.splitlines()) <= c.Infra.LOC_CAP_MAX
        ):
            return content
        return FlextInfraCodegenGenerationFileMixin._generate_registry_wrapper_file(
            current_pkg,
            registry_wrapper,
            context.runtime_import_lines,
            context.type_checking_lines if publish_all else "",
            context.inline_constants,
            context.eager_export_names,
            context.exports,
            publish_all=publish_all,
        )


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
