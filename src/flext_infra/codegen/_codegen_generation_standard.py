"""Canonical public-root and static-subpackage initializer rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)

if TYPE_CHECKING:
    from flext_infra import t


# Keep lazy loading only at the public package root; templates own the exact
# generated initializer bytes.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Render the two canonical generated initializer forms."""

    @staticmethod
    def _type_checking_filtered(plan: m.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Return supported static imports with local facade classes as aliases."""
        source = plan.type_checking_map or plan.lazy_map
        public_names = frozenset(plan.exports)
        wildcard_modules = frozenset(plan.wildcard_runtime_modules)
        # mro-pulj (codex): direct imports outside __all__ remain statically
        # declared because they are part of the established root interface.
        filtered: dict[str, t.StrPair] = {
            name: target
            for name, target in source.items()
            if name in public_names
            and target[0] not in wildcard_modules
            and name not in c.Infra.ROOT_TEMPLATE_RUNTIME_IMPORTS
        }
        for (
            alias_name,
            class_suffix,
        ) in c.Infra.PUBLIC_ROOT_TYPING_FACADE_SUFFIXES.items():
            alias_target = filtered.get(alias_name)
            if alias_target is None or alias_target[1] != alias_name:
                continue
            module_name = alias_target[0]
            candidates = tuple(
                export_name
                for export_name, target in filtered.items()
                if target == (module_name, export_name)
                and export_name.endswith(class_suffix)
            )
            if len(candidates) == 1:
                filtered[alias_name] = (module_name, candidates[0])
        return filtered

    @classmethod
    def _runtime_import_lines(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render explicit eager and wildcard runtime imports."""
        lines: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(plan.wildcard_runtime_modules))
        ]
        eager_lines: t.MutableSequenceOf[str] = []
        eager_groups = cls._group_imports(plan.eager_dunders)
        previous_top: str | None = None
        for module in sorted(eager_groups, key=str.lower):
            rendered_module = cls._compact_lazy_module_path(
                plan.context.current_pkg, module
            )
            top = rendered_module.split(".", maxsplit=1)[0]
            if previous_top is not None and top != previous_top:
                eager_lines.append("")
            parts = tuple(
                f"{imported_name} as {export_name}"
                for export_name, imported_name in sorted(eager_groups[module])
                if imported_name
            )
            for part in parts:
                eager_lines.extend(cls._format_import("", rendered_module, (part,)))
            previous_top = top
        if lines and eager_lines:
            lines.append("")
        lines.extend(eager_lines)
        return "\n".join(lines)

    @classmethod
    def _root_context(cls, plan: m.Infra.LazyInitPlan) -> m.Infra.LazyInitRootRender:
        """Build one inline lazy context for a public package root."""
        current_pkg = plan.context.current_pkg
        public_names = frozenset(plan.exports)
        lazy_map = {
            name: target
            for name, target in plan.lazy_map.items()
            if name in public_names
        }
        lazy_entries = cls._build_lazy_entries(
            tuple(lazy_map),
            lazy_map,
            (current_pkg, frozenset(plan.child_packages_for_lazy), True),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        # Public root re-exports are imported at runtime so ``__all__`` binds
        # real attributes; the lazy map remains the canonical installation contract.
        public_runtime_imports = cls._type_checking_filtered(plan)
        compacted_public_runtime_imports = {
            name: (cls._compact_lazy_module_path(current_pkg, mod), attr)
            for name, (mod, attr) in public_runtime_imports.items()
        }
        public_lines = list(
            cls._generate_import_lines(
                cls._group_imports(compacted_public_runtime_imports)
            )
        )
        eager_wildcard_lines = cls._runtime_import_lines(plan)
        if public_lines and eager_wildcard_lines:
            runtime_import_lines = "\n".join([*public_lines, "", eager_wildcard_lines])
        elif public_lines:
            runtime_import_lines = "\n".join(public_lines)
        else:
            runtime_import_lines = eager_wildcard_lines
        return m.Infra.LazyInitRootRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(current_pkg),
            runtime_import_lines=runtime_import_lines,
            type_checking_lines="",
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            exports=cls._build_published_exports(plan.exports, lazy_map),
        )

    @classmethod
    def _static_context(
        cls, plan: m.Infra.LazyInitPlan
    ) -> m.Infra.StaticPackageInitRender:
        """Build a side-effect-free private or non-production initializer."""
        return m.Infra.StaticPackageInitRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                plan.context.current_pkg.rsplit(".", maxsplit=1)[-1]
            ),
        )

    @classmethod
    def _render_root(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one inline lazy public-root initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_ROOT_INIT,
            cls._root_context(plan),
            target_filename=str(plan.context.init_path),
        )

    @classmethod
    def _render_static(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one explicit static or empty subpackage initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_STATIC_INIT,
            cls._static_context(plan),
            target_filename=str(plan.context.init_path),
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
